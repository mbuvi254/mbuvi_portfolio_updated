import pymysql
from flask import current_app, g
from werkzeug.local import LocalProxy


def close_connection(error=None):
    """Release this request's connection, including after a failed request."""
    connection = g.pop('_mysql_connection', None)
    if connection is not None:
        connection.close()


def init_app(app):
    app.teardown_appcontext(close_connection)


class Database:
    def __init__(self):
        self.host="localhost"
        self.user="cyberma3_cm"
        self.password="2025Cybermaisha@"
        self.database="cyberma3_mbuvi_db"
        
    
    def get_connection(self):
        # Models can be constructed at import time without opening a socket.
        return LocalProxy(self._request_connection)

    def _request_connection(self):
        if '_mysql_connection' not in g:
            g._mysql_connection = self._connect()
        return g._mysql_connection

    def _connect(self):
        return pymysql.connect(
            host=current_app.config.get("DB_HOST", self.host),
            user=current_app.config.get("DB_USER", self.user),
            password=current_app.config.get("DB_PASSWORD", self.password),
            database=current_app.config.get("DB_NAME", self.database),
            connect_timeout=10,
            init_command="SET time_zone = '+03:00'"
        )
        
