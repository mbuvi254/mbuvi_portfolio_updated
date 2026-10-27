"""Use isolated, disposable MySQL tables; never write test data to portfolio tables."""
import uuid
from pathlib import Path
from dotenv import load_dotenv
from config.database import init_app, Database
from services import portfolio_store as store


def configure_mysql(app, cleanup):
    load_dotenv(Path(__file__).resolve().parents[1]/'.env')
    init_app(app)
    app.config['PORTFOLIO_TABLE_PREFIX'] = 'test_'+uuid.uuid4().hex[:16]+'_'
    with app.app_context():
        store.init_schema()
    def drop_tables():
        with app.app_context():
            connection = Database().get_connection()
            with connection.cursor() as cursor:
                for table in store.TABLES:
                    cursor.execute('DROP TABLE `'+store.table_prefix()+table+'`')
            connection.commit()
    cleanup(drop_tables)
