from mysql_support import configure_mysql
"""Public design integration checks without database writes or outgoing mail."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import Mock, patch
from flask import Flask

ROOT = Path(__file__).resolve().parents[1]

class PublicDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names = {
            'aboutController': ['get_all_about', 'get_all_education'],
            'resumeController': ['get_resumes'],
            'contactController': ['send_message', 'user_log'],
            'projectController': ['get_projects', 'get_project', 'get_categories', 'category_projects', 'get_category'],
        }
        modules = {}
        for module, functions in names.items():
            stub = types.ModuleType('controllers.' + module)
            for name in functions:
                setattr(stub, name, Mock(return_value=[]))
            modules[stub.__name__] = stub
        spec = importlib.util.spec_from_file_location('design_routes', ROOT / 'routes/home_bp.py')
        cls.routes = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, modules):
            spec.loader.exec_module(cls.routes)
        cls.app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
        cls.app.config.update(TESTING=True, SECRET_KEY='test')
        configure_mysql(cls.app, cls.addClassCleanup)
        from services.portfolio_store import close_db
        cls.app.teardown_appcontext(close_db)
        cls.app.register_blueprint(cls.routes.home_bp)
        cls.app.add_url_rule('/dashboard', endpoint='admin_bp.admin_route', view_func=lambda: 'dashboard')

    def setUp(self):
        r = self.routes
        self.row = (7, 'Real project', '<script>alert(1)</script>', 'apply.png', '9', 'example.com', '', datetime(2025, 1, 24), 9, 'JavaScript')
        r.get_all_about.return_value = [(1, 'Daniel', 'Database biography', '20240223_050902.jpg')]
        r.get_all_education.return_value = [(1, 'Degree', 'University', datetime(2023, 12, 1))]
        r.get_resumes.return_value = [(1, 'older.pdf'), (2, 'Daniel_Mulatya_CV_Updated.pdf')]
        r.get_projects.return_value = [self.row]
        r.get_project.return_value = self.row
        r.get_categories.return_value = [(9, 'JavaScript')]
        r.get_category.return_value = (9, 'JavaScript')
        r.category_projects.return_value = [self.row]
        self.client = self.app.test_client()

    def test_public_routes_and_assets(self):
        for path in ('/', '/resume', '/projects', '/project/7', '/project/category/9', '/contact', '/static/css/site.css', '/static/js/site.js'):
            with self.subTest(path=path):
                with self.client.get(path) as response:
                    self.assertEqual(response.status_code, 200)
        home = self.client.get('/').get_data(as_text=True)
        self.assertIn('Database biography', home)
        self.assertIn('href="/dashboard"', home)
        self.assertIn('/static/about/20240223_050902.jpg', home)
        projects = self.client.get('/projects').get_data(as_text=True)
        self.assertIn('data-filter="javascript"', projects)
        self.assertIn('&lt;script&gt;', projects)
        self.assertIn('Daniel_Mulatya_CV_Updated.pdf', self.client.get('/resume').get_data(as_text=True))

    def test_missing_records(self):
        self.routes.get_project.return_value = None
        self.routes.get_category.return_value = None
        for path in ('/project/999', '/project/category/999', '/missing'):
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_contact_submission(self):
        data = dict(fname='Daniel', phone='123456', email='daniel@example.com', subject='Hello', message='<b>Idea</b>')
        with patch.object(self.routes.mail, 'send') as send:
            response = self.client.post('/contact', data=data, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('Your message has been received', response.get_data(as_text=True))
            self.assertIn('&lt;b&gt;Idea&lt;/b&gt;', send.call_args.args[0].html)
            self.routes.send_message.assert_called_with('Daniel', '123456', 'daniel@example.com', 'Hello', '<b>Idea</b>', 0)
        with patch.object(self.routes.mail, 'send') as send:
            self.assertEqual(self.client.post('/contact', data={}).status_code, 400)
            send.assert_not_called()

    def test_empty_content(self):
        for name in ('get_all_about', 'get_all_education', 'get_resumes', 'get_projects', 'get_categories'):
            getattr(self.routes, name).return_value = None
        for path in ('/', '/resume', '/projects'):
            self.assertEqual(self.client.get(path).status_code, 200)

if __name__ == '__main__':
    unittest.main()
