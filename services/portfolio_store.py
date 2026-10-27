"""Portfolio extension data stored in the configured MySQL database."""
import json
import hashlib
import time
from datetime import datetime, timezone
from flask import current_app, g

# All extension tables share the configured MySQL database with legacy records.
TABLES = {
 'content': "id BIGINT PRIMARY KEY AUTO_INCREMENT, kind VARCHAR(32) NOT NULL, slug VARCHAR(160) NOT NULL, title VARCHAR(200) NOT NULL, summary TEXT NOT NULL, body LONGTEXT NOT NULL, data LONGTEXT NOT NULL, published INT NOT NULL DEFAULT 0, consent INT NOT NULL DEFAULT 0, created VARCHAR(40) NOT NULL, updated VARCHAR(40) NOT NULL, UNIQUE KEY content_slug(kind,slug)",
 'settings': "`key` VARCHAR(191) PRIMARY KEY, value LONGTEXT NOT NULL",
 'events': "id BIGINT PRIMARY KEY AUTO_INCREMENT, kind VARCHAR(40) NOT NULL, target VARCHAR(200) NOT NULL, visitor VARCHAR(64) NOT NULL, created BIGINT NOT NULL, INDEX events_created(created,kind)",
 'enquiry_state': "message_id BIGINT PRIMARY KEY, status VARCHAR(32) NOT NULL DEFAULT 'new', note LONGTEXT NOT NULL, updated VARCHAR(40) NOT NULL",
 'notifications': "message_id BIGINT PRIMARY KEY, state VARCHAR(32) NOT NULL, updated VARCHAR(40) NOT NULL",
 'replies': "id BIGINT PRIMARY KEY AUTO_INCREMENT, message_id BIGINT NOT NULL, recipient VARCHAR(320) NOT NULL, subject TEXT NOT NULL, body LONGTEXT NOT NULL, state VARCHAR(32) NOT NULL DEFAULT 'pending', created VARCHAR(40) NOT NULL",
 'security': "aid BIGINT PRIMARY KEY, secret TEXT, recovery LONGTEXT NOT NULL, last_step BIGINT NOT NULL DEFAULT -1",
 'sessions': "token VARCHAR(64) PRIMARY KEY, aid BIGINT NOT NULL, ip VARCHAR(64) NOT NULL, agent VARCHAR(240) NOT NULL, created BIGINT NOT NULL, seen BIGINT NOT NULL, expires BIGINT NOT NULL, revoked INT NOT NULL DEFAULT 0, INDEX session_aid(aid)",
 'attempts': "id BIGINT PRIMARY KEY AUTO_INCREMENT, identity VARCHAR(64) NOT NULL, created BIGINT NOT NULL, INDEX attempts_identity(identity,created)",
 'reset_tokens': "token VARCHAR(64) PRIMARY KEY, aid BIGINT NOT NULL, expires BIGINT NOT NULL, used INT NOT NULL DEFAULT 0",
}


def table_prefix():
    import re
    prefix = current_app.config.get('PORTFOLIO_TABLE_PREFIX', 'portfolio_')
    if not re.fullmatch(r'[a-z][a-z0-9_]{0,39}', prefix):
        raise ValueError('Invalid portfolio table prefix')
    return prefix


class Row(dict):
    def __getitem__(self, key):
        return list(self.values())[key] if isinstance(key, int) else super().__getitem__(key)


class Result:
    def __init__(self, cursor):
        self.rowcount, self.lastrowid = cursor.rowcount, cursor.lastrowid
        self.rows = [Row(row) for row in cursor.fetchall()] if cursor.description else []
    def fetchone(self):
        return self.rows.pop(0) if self.rows else None
    def fetchall(self):
        rows, self.rows = self.rows, []
        return rows
    def __iter__(self):
        return iter(self.rows)


class Store:
    def __init__(self, connection):
        self.connection = connection
        self.locks = set()
    def execute(self, sql, params=()):
        # Parameter binding remains delegated to PyMySQL; values never enter SQL text.
        import re
        import pymysql.cursors
        sql = re.sub(r'\b(FROM|INTO|UPDATE|JOIN)\s+('+'|'.join(TABLES)+r')\b',
                     lambda match: match[1]+' `'+table_prefix()+match[2]+'`', sql)
        with self.connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params)
            return Result(cursor)
    def lock(self, name):
        # A named lock serializes reservations, including an initially empty table.
        name = 'portfolio:' + hashlib.sha256((current_app.config['DB_NAME']+':'+table_prefix()+':'+name).encode()).hexdigest()[:48]
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT GET_LOCK(%s,15)', (name,))
            if cursor.fetchone()[0] != 1:
                raise RuntimeError('Timed out acquiring portfolio write lock')
        self.locks.add(name)
    def __enter__(self):
        self.connection.commit()
        return self
    def __exit__(self, typ, value, traceback):
        try:
            self.connection.rollback() if typ else self.connection.commit()
        finally:
            for name in self.locks:
                with self.connection.cursor() as cursor:
                    cursor.execute('SELECT RELEASE_LOCK(%s)', (name,))
            self.locks.clear()


def init_schema():
    from config.database import Database
    connection = Database().get_connection()
    with connection.cursor() as cursor:
        for name, columns in TABLES.items():
            cursor.execute('CREATE TABLE IF NOT EXISTS `'+table_prefix()+name+'` ('+columns+') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin')
    connection.commit()


def db():
    if 'portfolio_db' not in g:
        from config.database import Database
        g.portfolio_db = Store(Database().get_connection())
    return g.portfolio_db


def close_db(error=None):
    g.pop('portfolio_db', None)  # Shared MySQL connection closes in database teardown.


def stamp():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def unpack(row):
    if row is None:
        return None
    item = dict(row)
    item['data'] = json.loads(item['data'])
    return item


def contents(kind, public=False):
    query = 'SELECT * FROM content WHERE kind=%s'
    if public:
        query += ' AND published=1' + (' AND consent=1' if kind == 'testimonial' else '')
    return [unpack(row) for row in db().execute(query + ' ORDER BY updated DESC,id DESC', (kind,))]


def content(kind, slug, public=False):
    item = unpack(db().execute('SELECT * FROM content WHERE kind=%s AND slug=%s', (kind, slug)).fetchone())
    if public and item and (not item['published'] or (kind == 'testimonial' and not item['consent'])):
        return None
    return item


def save_content(kind, slug, title, summary, body, data, published=False, consent=False, item_id=None):
    now = stamp()
    with db() as connection:
        if item_id:
            connection.execute('UPDATE content SET slug=%s,title=%s,summary=%s,body=%s,data=%s,published=%s,consent=%s,updated=%s WHERE id=%s AND kind=%s',
                               (slug,title,summary,body,json.dumps(data),int(published),int(consent),now,item_id,kind))
        else:
            connection.execute('INSERT INTO content(kind,slug,title,summary,body,data,published,consent,created,updated) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                               (kind,slug,title,summary,body,json.dumps(data),int(published),int(consent),now,now))


def setting(key, default=''):
    row = db().execute('SELECT value FROM settings WHERE `key`=%s', (key,)).fetchone()
    return row['value'] if row else default


def set_setting(key, value):
    with db() as connection:
        connection.execute('INSERT INTO settings(`key`,value) VALUES(%s,%s) ON DUPLICATE KEY UPDATE value=VALUES(value)', (key,str(value)))


def event(kind, target, visitor):
    now = int(time.time())
    # Suppress accidental repeated clicks/retries from the same visitor for 10 seconds.
    with db() as connection:
        connection.lock('write')
        recent = connection.execute('SELECT 1 FROM events WHERE kind=%s AND target=%s AND visitor=%s AND created>%s LIMIT 1', (kind,str(target),visitor,now-10)).fetchone()
        if not recent:
            connection.execute('INSERT INTO events(kind,target,visitor,created) VALUES(%s,%s,%s,%s)', (kind,str(target)[:200],visitor,now))


def event_report(days=30):
    start = int(time.time()) - days*86400
    return [dict(row) for row in db().execute('SELECT kind,target,COUNT(*) AS total FROM events WHERE created>=%s GROUP BY kind,target ORDER BY total DESC', (start,))]
