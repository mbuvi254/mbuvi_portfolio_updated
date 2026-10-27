"""Administrator authentication, CSRF, login throttling and TOTP."""
import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import quote
from flask import abort, current_app, request, session, redirect, url_for, g
from cryptography.fernet import Fernet
from services.portfolio_store import db, close_db


def hash_token(value):
    return hashlib.sha256(value.encode()).hexdigest()


def persistent_secret(instance_path):
    override = os.environ.get('PORTFOLIO_SECRET_KEY')
    if override:
        if len(override) < 32:
            raise RuntimeError('PORTFOLIO_SECRET_KEY must contain at least 32 characters')
        return override
    path = Path(instance_path) / '.secret_key'
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent,0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return path.read_text().strip()
    with os.fdopen(descriptor, 'w') as output:
        value = secrets.token_hex(32)
        output.write(value)
    return value


def cipher():
    key = hashlib.sha256(current_app.secret_key.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt(value):
    return cipher().encrypt(value.encode()).decode()


def decrypt(value):
    return cipher().decrypt(value.encode()).decode()


def csrf_token():
    if '_csrf' not in session:
        session['_csrf'] = secrets.token_urlsafe(32)
    return session['_csrf']


def totp(secret, step=None):
    step = int(time.time() // 30) if step is None else step
    digest = hmac.new(base64.b32decode(secret + '='*((8-len(secret)%8)%8)), struct.pack('>Q', step), hashlib.sha1).digest()
    offset = digest[-1] & 15
    value = (struct.unpack('>I', digest[offset:offset+4])[0] & 0x7fffffff) % 1000000
    return str(value).zfill(6)


def matching_step(secret, code):
    now = int(time.time() // 30)
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return None
    for step in (now-1, now, now+1):
        if hmac.compare_digest(totp(secret,step),code):
            return step
    return None


def factor_enabled(aid):
    row = db().execute('SELECT secret FROM security WHERE aid=?', (aid,)).fetchone()
    return bool(row and row['secret'])


def verify_factor(aid, code):
    row = db().execute('SELECT * FROM security WHERE aid=?', (aid,)).fetchone()
    if not row or not row['secret']:
        return False
    code = code.strip().replace(' ','')
    step = matching_step(decrypt(row['secret']), code)
    if step is not None:
        with db() as connection:
            result=connection.execute('UPDATE security SET last_step=? WHERE aid=? AND last_step<?', (step,aid,step))
            return result.rowcount == 1
    import json
    hashes = json.loads(row['recovery'])
    target = hash_token(code.lower())
    if target in hashes:
        hashes.remove(target)
        with db() as connection:
            result=connection.execute('UPDATE security SET recovery=? WHERE aid=? AND recovery=?', (json.dumps(hashes),aid,row['recovery']))
            return result.rowcount == 1
    return False


def rate_key(action, identity=''):
    return hash_token(action + ':' + (request.remote_addr or 'unknown') + ':' + identity.lower().strip())


def throttled(action, identity='', limit=5, window=900):
    key=rate_key(action,identity)
    count=db().execute('SELECT COUNT(*) FROM attempts WHERE identity=? AND created>?', (key,int(time.time())-window)).fetchone()[0]
    return count >= limit


def attempt(action, identity=''):
    now=int(time.time())
    with db() as connection:
        connection.execute('DELETE FROM attempts WHERE created<?', (now-86400,))
        connection.execute('INSERT INTO attempts(identity,created) VALUES(?,?)', (rate_key(action,identity),now))


def allow_attempt(action, identity='', limit=5, window=900):
    """Atomically reserve a rate-limit slot across workers."""
    now=int(time.time())
    key=rate_key(action,identity)
    with db() as connection:
        connection.execute('BEGIN IMMEDIATE')
        count=connection.execute('SELECT COUNT(*) FROM attempts WHERE identity=? AND created>?',(key,now-window)).fetchone()[0]
        if count>=limit:
            return False
        connection.execute('DELETE FROM attempts WHERE created<?',(now-86400,))
        connection.execute('INSERT INTO attempts(identity,created) VALUES(?,?)',(key,now))
    return True


def establish_session(admin):
    # Rotate both the Flask session identifier and our revocable login token.
    session.clear()
    if hasattr(current_app.session_interface,'regenerate'):
        session['_rotation']=True
        current_app.session_interface.regenerate(session)
        session.clear()
    token=secrets.token_urlsafe(32)
    now=int(time.time())
    with db() as connection:
        connection.execute('DELETE FROM sessions WHERE expires<?', (now-86400,))
        connection.execute('INSERT INTO sessions(token,aid,ip,agent,created,seen,expires) VALUES(?,?,?,?,?,?,?)',
            (hash_token(token),admin[0],request.remote_addr or 'unknown',request.user_agent.string[:240],now,now,now+7200))
    session.update(aid=admin[0],firstName=admin[1],lastName=admin[2],phoneNumber=admin[3],email=admin[4],profile_file=admin[5],status=admin[7],auth_token=token)
    try:
        from controllers.adminController import admin_log
        from services.analytics import NAIROBI
        from datetime import datetime
        sid=admin_log(admin[4],request.remote_addr or 'unknown',datetime.now(NAIROBI).time())
        session['sid']=sid[0]
    except Exception:
        current_app.logger.exception('Admin sign-in audit could not be recorded')
    session.permanent=True
    csrf_token()


def end_session():
    token=session.get('auth_token')
    if token:
        with db() as connection:
            connection.execute('UPDATE sessions SET revoked=1 WHERE token=?', (hash_token(token),))
    session.clear()


def provisioning(secret, email):
    return 'otpauth://totp/'+quote('Daniel Mbuvi:'+email, safe='')+'?secret='+secret+'&issuer=Daniel%20Mbuvi&digits=6&period=30'


def init_app(app):
    app.config.update(SECRET_KEY=persistent_secret(app.instance_path),
                      PERMANENT_SESSION_LIFETIME=timedelta(hours=2),
                      SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                      SESSION_COOKIE_SECURE=os.environ.get('PORTFOLIO_HTTPS','0')=='1',
                      MAX_CONTENT_LENGTH=12*1024*1024)
    app.teardown_appcontext(close_db)
    app.context_processor(lambda:dict(csrf_token=csrf_token))
    public={'admin_bp.admin_login_route','admin_bp.admin_forgot_password_route','admin_bp.admin_password_update_route','admin_bp.legacy_admin_redirect','features.factor_login'}

    @app.before_request
    def protect_requests():
        g.authenticated=False
        if session.get('aid'):
            token=session.get('auth_token','')
            record=db().execute('SELECT * FROM sessions WHERE token=? AND aid=?', (hash_token(token),session['aid'])).fetchone()
            now=int(time.time())
            if not record or record['revoked'] or record['expires']<=now:
                session.clear()
            else:
                g.authenticated=True
                if now-record['seen']>=60:
                    with db() as connection:
                        connection.execute('UPDATE sessions SET seen=? WHERE token=?', (now,hash_token(token)))
        is_admin = request.path == '/dashboard' or request.path.startswith('/dashboard/')
        if is_admin and request.endpoint not in public and not g.authenticated:
            return redirect(url_for('admin_bp.admin_login_route'))
        # Activation is never authorized by possession of an email address alone.
        if request.endpoint == 'admin_bp.admin_activate_route' and request.method != 'POST':
            abort(405)
        if request.endpoint == 'admin_bp.admin_update_route' and request.view_args.get('admin_id') != session.get('aid'):
            abort(403)
        if request.endpoint == 'admin_bp.admin_profile_route' and request.view_args.get('email') != session.get('email'):
            abort(403)
        if request.method in ('POST','PUT','PATCH','DELETE') and request.endpoint != 'admin_bp.legacy_admin_redirect':
            supplied=request.form.get('csrf_token') or request.headers.get('X-CSRFToken','')
            expected=session.get('_csrf','')
            if not expected or not supplied or not hmac.compare_digest(expected.encode(),supplied.encode()):
                abort(400, description='The form expired. Reload the page and try again.')
            if request.endpoint=='home_bp.contact_route':
                if not allow_attempt('contact',limit=5,window=600): abort(429,description='Please wait before sending another enquiry.')

    @app.after_request
    def security_headers(response):
        response.headers.setdefault('X-Content-Type-Options','nosniff')
        response.headers.setdefault('X-Frame-Options','SAMEORIGIN')
        response.headers.setdefault('Referrer-Policy','strict-origin-when-cross-origin')
        if request.path.startswith(('/dashboard','/admin')):
            response.headers['Cache-Control']='no-store'
            response.headers['X-Robots-Tag']='noindex, nofollow'
        return response


def harden_legacy_passwords():
    """Preserve existing credentials while replacing legacy plaintext storage."""
    from config.database import Database
    from werkzeug.security import generate_password_hash
    connection=Database().get_connection()
    changed=0
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT aid,password FROM admin')
            rows=cursor.fetchall()
            for aid,password in rows:
                if password and not password.startswith(('scrypt:','pbkdf2:')):
                    cursor.execute('UPDATE admin SET password=%s WHERE aid=%s AND password=%s',(generate_password_hash(password),aid,password))
                    changed+=cursor.rowcount
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return changed
