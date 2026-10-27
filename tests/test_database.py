"""Connection lifecycle regression tests; no live MySQL is needed."""
import unittest
from unittest.mock import Mock, patch
from flask import Flask
from config.database import Database, init_app
from models.aboutModel import AboutModel
from models.projectModel import ProjectModel
from models.resumeModel import ResumeModel
from models.contactModel import ContactModel
from models.adminModel import AdminClass


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.config.update(DB_HOST='test-host', DB_PORT=3307, DB_USER='test-user', DB_PASSWORD='test-password', DB_NAME='test-database')
        init_app(self.app)

    @patch('config.database.pymysql.connect')
    def test_models_do_not_connect_at_startup(self, connect):
        for model in (AboutModel, ProjectModel, ResumeModel, ContactModel, AdminClass):
            model()
        connect.assert_not_called()

    @patch('config.database.pymysql.connect')
    def test_models_share_connection_and_close_on_teardown(self, connect):
        first, second = Mock(), Mock()
        connect.side_effect = [first, second]
        about, projects = AboutModel(), ProjectModel()
        with self.app.test_request_context('/'):
            about.connection.cursor()
            projects.connection.commit()
            connect.assert_called_once()
            first.cursor.assert_called_once()
            first.commit.assert_called_once()
            first.close.assert_not_called()
        first.close.assert_called_once()
        with self.app.test_request_context('/'):
            projects.connection.cursor()
        self.assertEqual(connect.call_count, 2)
        second.close.assert_called_once()

    @patch('config.database.pymysql.connect')
    def test_error_closes_connection(self, connect):
        with self.assertRaises(ValueError):
            with self.app.test_request_context('/'):
                Database().get_connection().cursor()
                raise ValueError('request failed')
        connect.return_value.close.assert_called_once()

    @patch('config.database.pymysql.connect')
    def test_unused_request_opens_no_connection(self, connect):
        with self.app.test_request_context('/static/css/site.css'):
            Database().get_connection()
        connect.assert_not_called()

    @patch('config.database.pymysql.connect')
    def test_concurrent_contexts_do_not_share_connection(self, connect):
        first, second = Mock(), Mock()
        connect.side_effect = [first, second]
        proxy = Database().get_connection()
        with self.app.app_context():
            proxy.cursor()
            with self.app.app_context():
                proxy.commit()
            second.commit.assert_called_once()
            second.close.assert_called_once()
            first.close.assert_not_called()
            proxy.commit()
        first.commit.assert_called_once()
        first.close.assert_called_once()

    @patch('config.database.pymysql.connect')
    def test_connection_uses_current_flask_configuration(self, connect):
        model = Database()
        self.app.config['DB_USER'] = 'updated-user'
        with self.app.app_context():
            model.get_connection().cursor()
        connect.assert_called_once_with(host='test-host', port=3307,
            user='updated-user', password='test-password', database='test-database',
            connect_timeout=10, init_command="SET time_zone = '+03:00'")

    def test_environment_defaults_and_explicit_overrides(self):
        with patch.dict('os.environ', {'DB_HOST':'env-host','DB_PORT':'3308',
                'DB_USER':'env-user','DB_PASSWORD':'env-password','DB_NAME':'env-db'}):
            app = Flask(__name__)
            app.config['DB_HOST'] = 'explicit-host'
            init_app(app)
        self.assertEqual(app.config['DB_HOST'], 'explicit-host')
        self.assertEqual(app.config['DB_PORT'], 3308)
        self.assertEqual(app.config['DB_USER'], 'env-user')
        self.assertEqual(app.config['DB_PASSWORD'], 'env-password')
        self.assertEqual(app.config['DB_NAME'], 'env-db')

    @patch('config.database.pymysql.connect')
    def test_missing_credentials_fail_before_connecting(self, connect):
        self.app.config.update(DB_USER=None, DB_PASSWORD=None, DB_NAME=None)
        with self.app.app_context():
            with self.assertRaisesRegex(RuntimeError, 'Missing database settings: DB_USER, DB_PASSWORD, DB_NAME'):
                Database().get_connection().cursor()
        connect.assert_not_called()

if __name__ == '__main__':
    unittest.main()
