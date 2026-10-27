"""Portfolio content, enquiry workflow, conversion analytics and security screens."""
import base64
import hashlib
import json
import re
import secrets
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from flask import Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_from_directory, session, url_for, Response
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from services import portfolio_store as store
from services import security

features=Blueprint('features', __name__)
KINDS={'service':'Services','post':'Blog posts','testimonial':'Testimonials','case':'Project case studies'}
STATES=('new','in_progress','resolved')


def visitor():
    return security.hash_token((request.remote_addr or '') + current_app.secret_key)


def safe_file(filename):
    return bool(filename and Path(filename).name==filename and filename.lower().endswith('.pdf'))


def selected_resume():
    from controllers.resumeController import get_resumes
    rows=get_resumes() or []
    preferred=store.setting('active_resume')
    return next((row for row in rows if str(row[0])==preferred), max(rows,key=lambda row:row[0],default=None))


def public_project_data(project):
    case=store.content('case',str(project['id']),public=True)
    project['case']=case
    project['tags']=list(dict.fromkeys([project['category']] + (case['data'].get('tags',[]) if case else [])))
    project['industry']=case['data'].get('industry','') if case else ''
    project['project_type']=case['data'].get('project_type','') if case else ''
    return project


@features.get('/services')
def services_page():
    return render_template('services.html', items=store.contents('service',True))


@features.get('/blog')
def blog():
    query=request.args.get('q','').strip()[:120]
    tag=request.args.get('tag','').strip()[:40]
    items=store.contents('post',True)
    tags=sorted({tag for item in items for tag in item['data'].get('tags',[])})
    if query:
        items=[item for item in items if query.casefold() in (item['title']+' '+item['summary']+' '+item['body']).casefold()]
    if tag:
        items=[item for item in items if tag in item['data'].get('tags',[])]
    return render_template('blog.html',items=items,query=query,tags=tags,selected_tag=tag)


@features.get('/blog/<slug>')
def post(slug):
    item=store.content('post',slug,True)
    if not item: abort(404)
    g.seo_title=item['title']+' · Daniel Mbuvi Mulatya'
    g.seo_description=item['summary'][:180]
    g.article=item
    return render_template('post.html',item=item)


@features.get('/testimonials')
def testimonials():
    return render_template('testimonials.html',items=store.contents('testimonial',True))


@features.get('/resume/download')
def download_resume():
    selected=selected_resume()
    filename=selected[1] if selected else 'Daniel_Mulatya_CV_Updated.pdf'
    if not safe_file(filename): abort(404)
    response=send_from_directory(str(Path(current_app.static_folder)/'resume'),filename,as_attachment=True)
    if request.method=='GET' and response.status_code in (200,206):
        store.event('cv_download',str(selected[0]) if selected else 'default',visitor())
    return response


@features.get('/resume/view')
def view_resume():
    selected=selected_resume()
    filename=selected[1] if selected else 'Daniel_Mulatya_CV_Updated.pdf'
    if not safe_file(filename): abort(404)
    return send_from_directory(str(Path(current_app.static_folder)/'resume'),filename,mimetype='application/pdf')


@features.post('/events')
def track_event():
    if not request.is_json: abort(400)
    data=request.get_json(silent=True) or {}
    if data.get('kind') not in ('contact_click','project_link'): abort(400)
    target=str(data.get('target',''))
    if data['kind']=='contact_click' and target not in ('email','phone','contact_page'): abort(400)
    if data['kind']=='project_link' and not re.fullmatch(r'\d{1,10}',target): abort(400)
    if not security.allow_attempt('events',limit=100,window=60): return '',429
    store.event(data['kind'],target,visitor())
    return '',204


@features.route('/dashboard/content/<kind>',methods=['GET','POST'])
def content_list(kind):
    if kind not in KINDS: abort(404)
    return render_template('admin/content_list.html',ptitle=KINDS[kind],kind=kind,items=store.contents(kind))


@features.route('/dashboard/content/<kind>/new',methods=['GET','POST'])
@features.route('/dashboard/content/<kind>/<int:item_id>/edit',methods=['GET','POST'])
def content_edit(kind,item_id=None):
    if kind not in KINDS: abort(404)
    item=next((item for item in store.contents(kind) if item['id']==item_id),None) if item_id else None
    if item_id and not item: abort(404)
    error=None
    if request.method=='POST':
        title=request.form.get('title','').strip()[:200]
        slug=request.form.get('slug','').strip().lower()
        summary=request.form.get('summary','').strip()[:500]
        body=request.form.get('body','').strip()[:50000]
        data={key:request.form.get(key,'').strip()[:5000] for key in ('role','problem','solution','results','industry','project_type','author','company','consent_note')}
        data['tags']=list(dict.fromkeys(tag.strip()[:40] for tag in request.form.get('tags','').split(',') if tag.strip()))[:20]
        published=request.form.get('published')=='on'
        consent=request.form.get('consent')=='on'
        if not title or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',slug) or len(slug)>160:
            error='Enter a title and a URL slug containing lowercase letters, numbers and hyphens.'
        if kind=='case':
            from controllers.projectController import get_project
            if not slug.isdigit() or not get_project(int(slug)):
                error='Use the numeric ID of an existing project as the case study slug.'
        if kind=='testimonial' and published and (not consent or not data['author'] or not data['consent_note']):
            error='Publishing a testimonial requires the author, permission confirmation and a permission note.'
        if published and kind in ('post','service','testimonial') and not body:
            error='Add the content before publishing.'
        if kind=='case':
            data['screenshots']=[] if request.form.get('clear_screenshots') else (item['data'].get('screenshots',[]) if item else [])
            uploads=[file for file in request.files.getlist('screenshots') if file.filename]
            if len(uploads)+len(data['screenshots'])>6:
                error='Use at most six gallery screenshots.'
            pending=[]
            if not error:
                for file in uploads:
                    raw=file.read(2*1024*1024+1)
                    ext='.png' if raw.startswith(b'\x89PNG\r\n\x1a\n') else '.jpg' if raw.startswith(b'\xff\xd8\xff') else '.webp' if raw[:4]==b'RIFF' and raw[8:12]==b'WEBP' else None
                    if len(raw)>2*1024*1024 or not ext:
                        error='Screenshots must be PNG, JPEG or WebP files of up to 2 MB.'
                        break
                    pending.append((raw,secrets.token_hex(16)+ext))
            if not error:
                folder=Path(current_app.static_folder)/'projects'/'gallery'
                folder.mkdir(parents=True,exist_ok=True)
                for raw,name in pending:
                    (folder/name).write_bytes(raw)
                    data['screenshots'].append('/static/projects/gallery/'+name)
        if not error:
            try:
                store.save_content(kind,slug,title,summary,body,data,published,consent,item_id)
                flash('Content saved.','success')
                return redirect(url_for('features.content_list',kind=kind))
            except sqlite3.IntegrityError:
                error='That URL slug is already in use.'
        item=dict(id=item_id,slug=slug,title=title,summary=summary,body=body,data=data,published=published,consent=consent)
    return render_template('admin/content_edit.html',ptitle=('Edit ' if item_id else 'New ')+KINDS[kind],kind=kind,item=item,error=error)


@features.post('/dashboard/content/<kind>/<int:item_id>/unpublish')
def unpublish(kind,item_id):
    if kind not in KINDS: abort(404)
    with store.db() as connection:
        connection.execute('UPDATE content SET published=0,updated=? WHERE id=? AND kind=?',(store.stamp(),item_id,kind))
    flash('Content moved to drafts.','success')
    return redirect(url_for('features.content_list',kind=kind))


@features.route('/dashboard/cv',methods=['GET','POST'])
def manage_cv():
    from controllers.resumeController import get_resumes
    rows=get_resumes() or []
    error=None
    if request.method=='POST':
        if request.form.get('action')=='select':
            selected=next((row for row in rows if str(row[0])==request.form.get('resume_id')),None)
            if not selected or not safe_file(selected[1]) or not (Path(current_app.static_folder)/'resume'/selected[1]).is_file():
                error='Select an available CV file.'
            else:
                store.set_setting('active_resume',selected[0])
                flash('Public CV updated.','success')
                return redirect(url_for('features.manage_cv'))
        else:
            upload=request.files.get('file')
            if not upload or not upload.filename.lower().endswith('.pdf') or upload.stream.read(5)!=b'%PDF-':
                error='Choose a PDF document (maximum upload size: 12 MB).'
            else:
                upload.stream.seek(0)
                name=secrets.token_hex(8)+'-'+secure_filename(upload.filename)[:150]
                folder=Path(current_app.static_folder)/'resume'
                folder.mkdir(exist_ok=True)
                destination=folder/name
                upload.save(destination)
                try:
                    from config.database import Database
                    connection=Database().get_connection()
                    with connection.cursor() as cursor:
                        cursor.execute('INSERT INTO resumes(resume) VALUES(%s)',(name,))
                        rid=cursor.lastrowid
                        connection.commit()
                    if request.form.get('make_active')=='on': store.set_setting('active_resume',rid)
                except Exception:
                    destination.unlink(missing_ok=True)
                    raise
                flash('CV uploaded.','success')
                return redirect(url_for('features.manage_cv'))
    return render_template('admin/cv_manager.html',ptitle='CV management',rows=rows,active=store.setting('active_resume'),error=error)


@features.get('/dashboard/enquiries')
def enquiries():
    from controllers.contactController import get_messages
    state_filter=request.args.get('status','all')
    query=request.args.get('q','').strip()[:120].casefold()
    states={row['message_id']:dict(row) for row in store.db().execute('SELECT * FROM enquiry_state')}
    items=[]
    for row in reversed(get_messages() or []):
        state=states.get(row[0],dict(status='new',note=''))
        if state_filter in STATES and state['status']!=state_filter: continue
        if query and query not in ' '.join(str(value) for value in row[1:6]).casefold(): continue
        items.append(dict(row=row,state=state))
    return render_template('admin/enquiries.html',ptitle='Enquiries',items=items,states=STATES,state_filter=state_filter,query=query)


@features.route('/dashboard/enquiries/<int:mid>',methods=['GET','POST'])
def enquiry(mid):
    from controllers.contactController import get_message
    message=get_message(mid)
    if not message: abort(404)
    error=None
    if request.method=='POST':
        action=request.form.get('action')
        if action=='status':
            status=request.form.get('status')
            if status not in STATES: abort(400)
            with store.db() as connection:
                connection.execute('INSERT INTO enquiry_state(message_id,status,note,updated) VALUES(?,?,?,?) ON CONFLICT(message_id) DO UPDATE SET status=excluded.status,note=excluded.note,updated=excluded.updated',
                    (mid,status,request.form.get('note','')[:5000],store.stamp()))
            flash('Enquiry updated.','success')
            return redirect(url_for('features.enquiry',mid=mid))
        if action=='notify':
            notification=store.db().execute('SELECT state FROM notifications WHERE message_id=?',(mid,)).fetchone()
            if notification and notification['state']=='sent':
                flash('The inbox notification was already sent.','success')
            else:
                from services.mail_notifications import send_enquiry_notification
                from app import mail
                sent=send_enquiry_notification(mail,mid,message[1],message[2],message[3],message[4],message[5])
                flash('Inbox notification sent.' if sent else 'Email notification failed. Check mail settings and try again.','success' if sent else 'error')
            return redirect(url_for('features.enquiry',mid=mid))
        if action=='reply':
            subject=request.form.get('subject','').strip()[:200]
            body=request.form.get('message','').strip()[:10000]
            if not subject or not body or '\n' in subject or '\r' in subject:
                error='Add a subject and message.'
            else:
                with store.db() as connection:
                    reply_id=connection.execute('INSERT INTO replies(message_id,recipient,subject,body,created) VALUES(?,?,?,?,?)',(mid,message[3],subject,body,store.stamp())).lastrowid
                try:
                    from flask_mail import Message
                    from app import mail
                    mail.send(Message(subject,sender=current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config['MAIL_USERNAME'],recipients=[message[3]],body=body))
                except Exception:
                    current_app.logger.exception('Enquiry reply delivery failed')
                    with store.db() as connection: connection.execute("UPDATE replies SET state='failed' WHERE id=?",(reply_id,))
                    error='The email could not be sent. Your reply is saved below; check mail settings before retrying.'
                else:
                    with store.db() as connection: connection.execute("UPDATE replies SET state='sent' WHERE id=?",(reply_id,))
                    flash('Reply sent.','success')
                    return redirect(url_for('features.enquiry',mid=mid))
    state=store.db().execute('SELECT * FROM enquiry_state WHERE message_id=?',(mid,)).fetchone()
    replies=store.db().execute('SELECT * FROM replies WHERE message_id=? ORDER BY id DESC',(mid,)).fetchall()
    notification=store.db().execute('SELECT state FROM notifications WHERE message_id=?',(mid,)).fetchone()
    return render_template('admin/enquiry.html',notification=notification,ptitle='Enquiry',message=message,state=state or dict(status='new',note=''),states=STATES,replies=replies,error=error)


@features.get('/dashboard/replies')
def reply_history():
    from controllers.contactController import sent_messages
    items=store.db().execute('SELECT * FROM replies ORDER BY id DESC LIMIT 500').fetchall()
    return render_template('admin/replies.html',ptitle='Reply history',items=items,legacy=sent_messages() or [])


@features.get('/dashboard/conversions')
def conversions():
    days=request.args.get('days',30,type=int)
    if days not in (7,30,90): days=30
    return render_template('admin/conversions.html',ptitle='Engagement analytics',items=store.event_report(days),days=days)


@features.route('/dashboard/login/verify',methods=['GET','POST'])
def factor_login():
    pending=session.get('pending_admin')
    if not pending or pending['expires']<time.time():
        session.pop('pending_admin',None)
        return redirect(url_for('admin_bp.admin_login_route'))
    error=None
    if request.method=='POST':
        if not security.allow_attempt('factor',str(pending['aid'])):
            return render_template('admin/factor_login.html',error='Too many attempts. Try again in 15 minutes.'),429
        if security.verify_factor(pending['aid'],request.form.get('code','')):
            from controllers.adminController import check_admin
            admin=check_admin(pending['email'])
            if not admin or admin[0]!=pending['aid'] or admin[7]!=1: abort(403)
            security.establish_session(admin)
            return redirect(url_for('admin_bp.admin_route'))
        error='That code is invalid, expired or already used.'
    return render_template('admin/factor_login.html',error=error)


@features.route('/dashboard/security',methods=['GET','POST'])
def security_settings():
    aid=session['aid']
    error=None
    recovery=None
    if request.method=='POST':
        action=request.form.get('action')
        if action in ('begin','enable','disable','recovery'):
            if not security.allow_attempt('security-factor',str(aid)):
                return render_template('admin/feature_error.html',ptitle='Account security',message='Too many attempts. Try again in 15 minutes.'),429
        if action in ('disable','recovery'):
            from controllers.adminController import login_admin
            if not login_admin(session['email'],request.form.get('password',''),1) or not security.verify_factor(aid,request.form.get('code','')):
                error='Confirm your password and a current authenticator or recovery code.'
            elif action=='disable':
                with store.db() as connection: connection.execute('DELETE FROM security WHERE aid=?',(aid,))
                flash('Two-factor authentication disabled.','success')
                return redirect(url_for('features.security_settings'))
            else:
                recovery=[secrets.token_hex(8) for _ in range(8)]
                with store.db() as connection: connection.execute('UPDATE security SET recovery=? WHERE aid=?',(json.dumps([security.hash_token(code) for code in recovery]),aid))
        elif action=='begin':
            if security.factor_enabled(aid): abort(400)
            from controllers.adminController import login_admin
            if not login_admin(session['email'],request.form.get('password',''),1):
                error='Confirm your current password to begin setup.'
            else:
                session['factor_setup']=base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')
                session['factor_setup_expires']=time.time()+300
        elif action=='enable':
            if security.factor_enabled(aid): abort(400)
            secret=session.get('factor_setup') if session.get('factor_setup_expires',0)>time.time() else None
            step=security.matching_step(secret,request.form.get('code','')) if secret else None
            if step is None: error='Enter a current six-digit code from your authenticator.'
            else:
                recovery=[secrets.token_hex(8) for _ in range(8)]
                with store.db() as connection:
                    connection.execute('INSERT INTO security(aid,secret,recovery,last_step) VALUES(?,?,?,?) ON CONFLICT(aid) DO UPDATE SET secret=excluded.secret,recovery=excluded.recovery,last_step=excluded.last_step',
                        (aid,security.encrypt(secret),json.dumps([security.hash_token(code) for code in recovery]),step))
                session.pop('factor_setup',None)
        elif action=='revoke':
            token=request.form.get('token','')
            with store.db() as connection: connection.execute('UPDATE sessions SET revoked=1 WHERE token=? AND aid=?',(token,aid))
            if token==security.hash_token(session['auth_token']):
                security.end_session()
                return redirect(url_for('admin_bp.admin_login_route'))
        elif action=='revoke_others':
            with store.db() as connection: connection.execute('UPDATE sessions SET revoked=1 WHERE aid=? AND token!=?',(aid,security.hash_token(session['auth_token'])))
    sessions=store.db().execute('SELECT * FROM sessions WHERE aid=? AND revoked=0 AND expires>? ORDER BY created DESC',(aid,int(time.time()))).fetchall()
    if session.get('factor_setup_expires',0)<=time.time():
        session.pop('factor_setup',None)
    setup=session.get('factor_setup')
    return render_template('admin/security.html',ptitle='Account security',enabled=security.factor_enabled(aid),setup=setup,
        provisioning=security.provisioning(setup,session['email']) if setup else '',recovery=recovery,error=error,sessions=sessions,current_token=security.hash_token(session['auth_token']))
