import os
import pymysql
from flask import current_app, g
from werkzeug.local import LocalProxy


def close_connection(error=None):
    """Release this request's connection, including after a failed request."""
    connection = g.pop('_mysql_connection', None)
    if connection is not None:
        connection.close()


def init_app(app):
    # app.py loads .env before initialization; deployment environment values win.
    defaults = {
        'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
        'DB_PORT': int(os.environ.get('DB_PORT', '3306')),
        'DB_USER': os.environ.get('DB_USER'),
        'DB_PASSWORD': os.environ.get('DB_PASSWORD'),
        'DB_NAME': os.environ.get('DB_NAME'),
    }
    for key, value in defaults.items():
        app.config.setdefault(key, value)
    app.teardown_appcontext(close_connection)


class Database:
    def get_connection(self):
        # Models can be constructed at import time without opening a socket.
        return LocalProxy(self._request_connection)

    def _request_connection(self):
        if '_mysql_connection' not in g:
            g._mysql_connection = self._connect()
        return g._mysql_connection

    def _connect(self):
        config = current_app.config
        missing = [key for key in ('DB_USER', 'DB_PASSWORD', 'DB_NAME')
                   if config.get(key) is None or (key != 'DB_PASSWORD' and not config[key])]
        if missing:
            raise RuntimeError('Missing database settings: ' + ', '.join(missing) +
                               '. Configure them in .env or the deployment environment.')
        return pymysql.connect(
            host=config.get('DB_HOST', 'localhost'),
            port=int(config.get('DB_PORT', 3306)),
            user=config['DB_USER'],
            password=config['DB_PASSWORD'],
            database=config['DB_NAME'],
            connect_timeout=10,
            init_command="SET time_zone = '+03:00'"
        )
