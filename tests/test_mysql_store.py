"""Exercise MySQL upserts, rollback, and the legacy-data importer."""
import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase
from flask import Flask
from mysql_support import configure_mysql
from services import portfolio_store as store
from services.portfolio_migration import migrate


class MySQLStoreTests(TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        configure_mysql(self.app, self.addCleanup)

    def test_upsert_and_transaction_rollback(self):
        with self.app.app_context():
            store.set_setting('sample', 'first')
            store.set_setting('sample', 'updated')
            self.assertEqual(store.setting('sample'), 'updated')
            with self.assertRaises(RuntimeError):
                with store.db() as connection:
                    connection.execute('UPDATE settings SET value=%s WHERE `key`=%s', ('bad','sample'))
                    raise RuntimeError('cancel')
            self.assertEqual(store.setting('sample'), 'updated')

    def test_migration_preserves_ids_is_repeatable_and_rolls_back_conflicts(self):
        with tempfile.TemporaryDirectory() as folder, self.app.app_context():
            path = Path(folder)/'legacy.sqlite3'
            legacy = sqlite3.connect(path)
            # Empty source tables need only their primary key for this fixture.
            for table in store.TABLES:
                if table not in ('content','settings'):
                    legacy.execute('CREATE TABLE '+table+' (id INTEGER PRIMARY KEY)')
            legacy.execute('CREATE TABLE settings (key TEXT PRIMARY KEY,value TEXT)')
            legacy.execute('CREATE TABLE content (id INTEGER PRIMARY KEY,kind TEXT,slug TEXT,title TEXT,summary TEXT,body TEXT,data TEXT,published INTEGER,consent INTEGER,created TEXT,updated TEXT)')
            legacy.execute("INSERT INTO content VALUES(42,'post','hello','Hello','Summary','Body','{}',1,0,'now','now')")
            legacy.execute("INSERT INTO settings VALUES('sample','old')")
            legacy.commit()
            counts = migrate(path)
            self.assertEqual(counts['content'], 1)
            self.assertEqual(store.content('post','hello')['id'], 42)
            self.assertEqual(migrate(path), counts)
            store.save_content('post','next','Next','Summary','Body',{},True)
            self.assertGreater(store.content('post','next')['id'],42)
            legacy.execute("INSERT INTO content VALUES(100,'post','later','Later','Summary','Body','{}',0,0,'now','now')")
            legacy.commit()
            legacy.close()
            store.set_setting('sample','conflict')
            with self.assertRaisesRegex(RuntimeError,'conflict'):
                migrate(path)
            self.assertIsNone(store.content('post','later'))
            self.assertEqual(store.setting('sample'), 'conflict')

    def test_concurrent_rate_reservations_and_event_deduplication(self):
        from concurrent.futures import ThreadPoolExecutor
        from services import security
        self.app.secret_key = 'mysql-test-secret'
        def reserve(_):
            with self.app.test_request_context('/'):
                allowed = security.allow_attempt('parallel', limit=2)
                store.event('project_view','42','same-visitor')
                return allowed
        with ThreadPoolExecutor(max_workers=6) as pool:
            self.assertEqual(sum(pool.map(reserve, range(6))), 2)
        with self.app.app_context():
            self.assertEqual(store.db().execute('SELECT COUNT(*) FROM events').fetchone()[0], 1)
