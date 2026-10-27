"""One-time, verified import of the retired SQLite extension store into MySQL."""
import sqlite3
from pathlib import Path
from services import portfolio_store as store


def migrate(source):
    source = Path(source).resolve(strict=True)
    legacy = sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)
    legacy.row_factory = sqlite3.Row
    try:
        records = {table: [dict(row) for row in legacy.execute('SELECT * FROM "'+table+'"')] for table in store.TABLES}
    finally:
        legacy.close()
    store.init_schema()
    counts = {}
    # Refuse overwrites; reruns accept only byte-for-byte equivalent existing rows.
    with store.db() as target:
        target.lock('migration')
        for table, rows in records.items():
            primary = {'settings':'key','enquiry_state':'message_id','notifications':'message_id','security':'aid','sessions':'token','reset_tokens':'token'}.get(table,'id')
            for row in rows:
                existing = target.execute('SELECT * FROM '+table+' WHERE `'+primary+'`=%s',(row[primary],)).fetchone()
                if existing:
                    if dict(existing) != row:
                        raise RuntimeError('Migration conflict in '+table+'; no records were overwritten.')
                else:
                    columns = ','.join('`'+column+'`' for column in row)
                    # Use the native cursor because column identifiers are already quoted.
                    with target.connection.cursor() as cursor:
                        cursor.execute('INSERT INTO `'+store.table_prefix()+table+'` ('+columns+') VALUES ('+','.join(['%s']*len(row))+')',tuple(row.values()))
                actual = target.execute('SELECT * FROM '+table+' WHERE `'+primary+'`=%s',(row[primary],)).fetchone()
                if dict(actual) != row:
                    raise RuntimeError('Migration verification failed in '+table)
            counts[table] = len(rows)
    return counts
