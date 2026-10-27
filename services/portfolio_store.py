"""Persistent extension data, independent of the legacy MySQL schema."""
import json
import os
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from flask import current_app, g

SCHEMA = '''
CREATE TABLE IF NOT EXISTS content (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, slug TEXT NOT NULL, title TEXT NOT NULL,
 summary TEXT NOT NULL DEFAULT '', body TEXT NOT NULL DEFAULT '', data TEXT NOT NULL DEFAULT '{}',
 published INTEGER NOT NULL DEFAULT 0, consent INTEGER NOT NULL DEFAULT 0,
 created TEXT NOT NULL, updated TEXT NOT NULL, UNIQUE(kind,slug));
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY, kind TEXT NOT NULL, target TEXT NOT NULL, visitor TEXT NOT NULL,
 created INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS events_created ON events(created,kind);
CREATE TABLE IF NOT EXISTS enquiry_state (message_id INTEGER PRIMARY KEY, status TEXT NOT NULL DEFAULT 'new', note TEXT NOT NULL DEFAULT '', updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS notifications (message_id INTEGER PRIMARY KEY, state TEXT NOT NULL, updated TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY, message_id INTEGER NOT NULL, recipient TEXT NOT NULL,
 subject TEXT NOT NULL, body TEXT NOT NULL, state TEXT NOT NULL DEFAULT 'pending', created TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS security (aid INTEGER PRIMARY KEY, secret TEXT, recovery TEXT NOT NULL DEFAULT '[]', last_step INTEGER NOT NULL DEFAULT -1);
CREATE TABLE IF NOT EXISTS sessions (token TEXT PRIMARY KEY, aid INTEGER NOT NULL, ip TEXT NOT NULL,
 agent TEXT NOT NULL, created INTEGER NOT NULL, seen INTEGER NOT NULL, expires INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS session_aid ON sessions(aid);
CREATE TABLE IF NOT EXISTS attempts (id INTEGER PRIMARY KEY, identity TEXT NOT NULL, created INTEGER NOT NULL);
CREATE INDEX IF NOT EXISTS attempts_identity ON attempts(identity,created);
CREATE TABLE IF NOT EXISTS reset_tokens (token TEXT PRIMARY KEY, aid INTEGER NOT NULL, expires INTEGER NOT NULL, used INTEGER NOT NULL DEFAULT 0);
'''


def db():
    if 'portfolio_db' not in g:
        path = Path(current_app.config.get('PORTFOLIO_DB', Path(current_app.instance_path) / 'portfolio.sqlite3'))
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent,0o700)
        connection = sqlite3.connect(path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys=ON')
        connection.execute('PRAGMA journal_mode=WAL')
        initialized=current_app.extensions.setdefault('portfolio_schema_initialized',set())
        if str(path.resolve()) not in initialized:
            connection.executescript(SCHEMA)
            initialized.add(str(path.resolve()))
        os.chmod(path, 0o600)
        g.portfolio_db = connection
    return g.portfolio_db


def close_db(error=None):
    connection = g.pop('portfolio_db', None)
    if connection is not None:
        connection.close()


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def unpack(row):
    if row is None:
        return None
    item = dict(row)
    item['data'] = json.loads(item['data'])
    return item


def contents(kind, public=False):
    query = 'SELECT * FROM content WHERE kind=?'
    if public:
        query += ' AND published=1' + (' AND consent=1' if kind == 'testimonial' else '')
    return [unpack(row) for row in db().execute(query + ' ORDER BY updated DESC,id DESC', (kind,))]


def content(kind, slug, public=False):
    item = unpack(db().execute('SELECT * FROM content WHERE kind=? AND slug=?', (kind, slug)).fetchone())
    if public and item and (not item['published'] or (kind == 'testimonial' and not item['consent'])):
        return None
    return item


def save_content(kind, slug, title, summary, body, data, published=False, consent=False, item_id=None):
    now = stamp()
    with db() as connection:
        if item_id:
            connection.execute('UPDATE content SET slug=?,title=?,summary=?,body=?,data=?,published=?,consent=?,updated=? WHERE id=? AND kind=?',
                               (slug,title,summary,body,json.dumps(data),int(published),int(consent),now,item_id,kind))
        else:
            connection.execute('INSERT INTO content(kind,slug,title,summary,body,data,published,consent,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)',
                               (kind,slug,title,summary,body,json.dumps(data),int(published),int(consent),now,now))


def setting(key, default=''):
    row = db().execute('SELECT value FROM settings WHERE key=?', (key,)).fetchone()
    return row['value'] if row else default


def set_setting(key, value):
    with db() as connection:
        connection.execute('INSERT INTO settings(key,value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value', (key,str(value)))


def event(kind, target, visitor):
    now = int(time.time())
    # Suppress accidental repeated clicks/retries from the same visitor for 10 seconds.
    with db() as connection:
        connection.execute('BEGIN IMMEDIATE')
        recent = connection.execute('SELECT 1 FROM events WHERE kind=? AND target=? AND visitor=? AND created>? LIMIT 1', (kind,str(target),visitor,now-10)).fetchone()
        if not recent:
            connection.execute('INSERT INTO events(kind,target,visitor,created) VALUES(?,?,?,?)', (kind,str(target)[:200],visitor,now))


def event_report(days=30):
    start = int(time.time()) - days*86400
    return [dict(row) for row in db().execute('SELECT kind,target,COUNT(*) AS total FROM events WHERE created>=? GROUP BY kind,target ORDER BY total DESC', (start,))]
