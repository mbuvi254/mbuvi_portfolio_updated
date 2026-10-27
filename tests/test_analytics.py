from mysql_support import configure_mysql
from datetime import date, datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, patch
from flask import Flask, Blueprint, session
from services.analytics import Analytics, init_app

ROOT = Path(__file__).resolve().parents[1]

class AnalyticsTests(TestCase):
    @patch('services.analytics.local_today', return_value=date(2026, 10, 27))
    def test_daily_gaps_are_zero_and_totals_are_distinct(self, today):
        model = Analytics()
        model.connection = MagicMock()
        cursor = model.connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (20, 5, 8, 3, 4)
        cursor.fetchall.side_effect = [[(date(2026, 10, 27), 8, 3)], [('/projects', 8)], []]
        report = model.dashboard(7)
        self.assertEqual(len(report['daily']), 7)
        self.assertEqual(report['daily'][0]['views'], 0)
        self.assertEqual(report['daily'][-1]['views'], 8)
        self.assertEqual(report['unique'], 5)
        self.assertEqual(report['change'], 4)
        params = cursor.execute.call_args_list[0].args[1]
        self.assertEqual(params[-2:], (date(2026, 10, 21), date(2026, 10, 28)))

    def test_logs_use_bound_filters_and_clamp_pagination(self):
        model = Analytics()
        model.connection = MagicMock()
        cursor = model.connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (51,)
        cursor.fetchall.return_value = []
        report = model.logs(date(2026, 10, 1), date(2026, 10, 27), "' OR 1=1", 999)
        self.assertEqual(report['page'], 2)
        sql, values = cursor.execute.call_args.args
        self.assertNotIn("' OR 1=1", sql)
        self.assertEqual(values[-2:], (50, 50))
        self.assertEqual(values[1], date(2026, 10, 28))

    def test_tracking_only_successful_public_gets(self):
        app = Flask(__name__)
        public = Blueprint('home_bp', __name__)
        @public.route('/page', methods=['GET', 'POST'])
        def page(): return 'ok'
        @public.get('/missing')
        def missing(): return 'missing', 404
        @app.get('/dashboard')
        def admin(): return 'admin'
        app.register_blueprint(public)
        init_app(app)
        with patch('controllers.contactController.contact_model.save_log') as save:
            client = app.test_client()
            client.get('/page', headers={'X-Forwarded-For': 'untrusted'})
            save.assert_called_once_with('127.0.0.1', '/page')
            client.post('/page')
            client.head('/page')
            client.get('/missing')
            client.get('/dashboard')
            self.assertEqual(save.call_count, 1)
        with patch('controllers.contactController.contact_model.save_log', side_effect=RuntimeError('offline')):
            with self.assertLogs(app.logger, level='ERROR'):
                self.assertEqual(client.get('/page').status_code, 200)


class AdminDashboardTests(TestCase):
    @classmethod
    def setUpClass(cls):
        import routes.admin_bp as routes
        cls.routes = routes
        cls.app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
        cls.app.config.update(TESTING=True, SECRET_KEY='test')
        configure_mysql(cls.app, cls.addClassCleanup)
        from services.portfolio_store import close_db
        cls.app.teardown_appcontext(close_db)
        cls.app.register_blueprint(routes.admin_bp)

    def setUp(self):
        self.client = self.app.test_client()

    def sign_in(self):
        with self.client.session_transaction() as state:
            state.update(aid=1, status=1, firstName='Daniel', lastName='Mulatya', profile_file='20240223_050902.jpg')

    def test_dashboard_and_logs_require_admin_login(self):
        for url in ('/dashboard', '/dashboard/user/logs', '/dashboard/logs'):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/dashboard/login', response.location)
        with self.client.session_transaction() as state:
            state['unrelated'] = True
        self.assertEqual(self.client.get('/dashboard').status_code, 302)

    def test_chart_renders_stored_data_and_range(self):
        self.sign_in()
        report = dict(start=date(2026,10,21), today=date(2026,10,27), views_today=8, unique_today=3,
                      total=20, unique=5, change=4, daily=[dict(date=date(2026,10,27), views=8, unique=3)],
                      top_pages=[('/projects',8)], recent=[(1,'127.0.0.1','/projects',datetime(2026,10,27,10))])
        with patch.object(self.routes.Analytics, 'dashboard', return_value=report) as dashboard, \
             patch.object(self.routes.admin_model, 'count_projects', return_value=3), \
             patch.object(self.routes.admin_model, 'count_rmessages', return_value=5), \
             patch.object(self.routes.admin_model, 'count_smessages', return_value=2):
            response = self.client.get('/dashboard?days=7')
            self.assertEqual(response.status_code, 200)
            body = response.get_data(as_text=True)
            self.assertIn('id="traffic-chart"', body)
            self.assertIn('"views": [8]', body)
            self.assertIn('/static/js/admin-dashboard.js', body)
            dashboard.assert_called_once_with(7)
            self.client.get('/dashboard?days=999')
            dashboard.assert_called_with(30)

    def test_log_filters_and_invalid_dates(self):
        self.sign_in()
        with patch.object(self.routes.Analytics, 'logs', return_value=dict(rows=[], total=0, page=1, pages=1)) as logs:
            response = self.client.get('/dashboard/user/logs?start=2026-10-01&end=2026-10-27&q=projects&page=0')
            self.assertEqual(response.status_code, 200)
            logs.assert_called_once_with(date(2026,10,1), date(2026,10,27), 'projects', 1)
            logs.reset_mock()
            response = self.client.get('/dashboard/user/logs?start=invalid')
            self.assertIn('Enter valid dates', response.get_data(as_text=True))
            logs.assert_not_called()

    def test_admin_logs_render(self):
        self.sign_in()
        with patch.object(self.routes, 'get_admin_logs', return_value=[]):
            self.assertEqual(self.client.get('/dashboard/logs').status_code, 200)

class DashboardLoginTests(TestCase):
    @classmethod
    def setUpClass(cls):
        import routes.admin_bp as routes
        cls.routes = routes
        cls.app = Flask(__name__, template_folder=str(ROOT / 'templates'), static_folder=str(ROOT / 'static'))
        cls.app.config.update(TESTING=True, SECRET_KEY='test')
        configure_mysql(cls.app, cls.addClassCleanup)
        from services.portfolio_store import close_db
        cls.app.teardown_appcontext(close_db)
        cls.app.register_blueprint(routes.admin_bp)

    def test_login_renders_new_form(self):
        client = self.app.test_client()
        response = client.get('/dashboard/login')
        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        self.assertIn('Sign in to dashboard', body)
        self.assertIn('action="/dashboard/login"', body)
        self.assertIn('autocomplete="current-password"', body)
        self.assertIn('/static/css/auth.css', body)

    def test_legacy_redirect_preserves_query_and_post(self):
        client = self.app.test_client()
        for path, expected in [('/admin', '/dashboard'), ('/admin/login', '/dashboard/login'), ('/admin/user/logs?q=projects', '/dashboard/user/logs?q=projects')]:
            response = client.get(path)
            self.assertEqual(response.status_code, 308)
            self.assertEqual(response.location, expected)
        response = client.post('/admin/login', data={'email': 'test@example.com', 'password': 'test'})
        self.assertEqual(response.status_code, 308)
        self.assertEqual(response.location, '/dashboard/login')

    def test_failed_login_shows_error_without_password(self):
        with patch.object(self.routes, 'login_admin', return_value=None):
            response = self.app.test_client().post('/dashboard/login', data={'email': 'test@example.com', 'password': 'private-test-value'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Check Your Password', response.get_data(as_text=True))
        self.assertNotIn('private-test-value', response.get_data(as_text=True))

    def test_authenticated_login_redirects_to_dashboard(self):
        client = self.app.test_client()
        with client.session_transaction() as state:
            state.update(aid=1, status=1)
        response = client.get('/dashboard/login')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, '/dashboard')
