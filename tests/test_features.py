import io
import json
import re
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock
from flask import Flask
from services import portfolio_store as store
from services import security
from services.portfolio_public import init_app as init_public, seed_services
from routes.features_bp import features
from routes.home_bp import home_bp
from routes.admin_bp import admin_bp

ROOT=Path(__file__).resolve().parents[1]
ADMIN=(9,'Daniel','Mulatya','123','owner@example.test','', 'unused',1,datetime(2026,1,1))
PROJECT=(1,'Survey','Research software','apply.png','1','example.test','',datetime(2026,1,1),1,'Python')
MESSAGE=(7,'Client','123','client@example.test','Website enquiry','Please help with a portal.',0,datetime(2026,10,27))

class FeatureTests(TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        root=Path(self.directory.name)
        self.app=Flask(__name__,instance_path=str(root/'instance'),template_folder=str(ROOT/'templates'),static_folder=str(root/'static'))
        self.app.config.update(TESTING=True,MAIL_USERNAME='sender@example.test',PORTFOLIO_DB=str(root/'features.sqlite3'))
        security.init_app(self.app)
        self.app.register_blueprint(home_bp)
        self.app.register_blueprint(admin_bp)
        self.app.register_blueprint(features)
        init_public(self.app)
        self.client=self.app.test_client()
        self.patches=[]
        for target,value in [('routes.home_bp.get_projects',[PROJECT]),('routes.home_bp.get_categories',[(1,'Python')]),('routes.home_bp.get_project',PROJECT),('controllers.adminController.admin_log',(1,)),('routes.admin_bp.logout',None),('controllers.resumeController.get_resumes',[])]:
            active=patch(target,return_value=value)
            active.start()
            self.addCleanup(active.stop)

    def csrf(self):
        with self.client.session_transaction() as state:
            token=state.get('_csrf','test-csrf-token')
            state['_csrf']=token
        return token

    def post(self,url,data=None,**kwargs):
        data=dict(data or {})
        data['csrf_token']=self.csrf()
        return self.client.post(url,data=data,**kwargs)

    def sign_in(self):
        with patch('routes.admin_bp.login_admin',return_value=ADMIN):
            response=self.post('/dashboard/login',dict(email=ADMIN[4],password='a long password'))
        self.assertEqual(response.status_code,302)
        self.assertEqual(response.location,'/dashboard')

    def test_csrf_and_all_admin_routes_are_protected(self):
        self.assertEqual(self.client.post('/dashboard/login',data=dict(email='a',password='b')).status_code,400)
        for url in ['/dashboard/projects','/dashboard/enquiries','/dashboard/security','/dashboard/content/post','/dashboard/register']:
            response=self.client.get(url)
            self.assertEqual(response.status_code,302)
            self.assertIn('/dashboard/login',response.location)
        self.sign_in()
        self.assertEqual(self.client.get('/dashboard/project/delete/1').status_code,405)
        self.assertEqual(self.client.get('/dashboard/update/999').status_code,403)
        self.assertEqual(self.client.post('/dashboard/content/post/new',data={}).status_code,400)

    def test_blog_drafts_and_testimonial_consent(self):
        self.sign_in()
        response=self.post('/dashboard/content/post/new',dict(title='Flask notes',slug='flask-notes',summary='Practical notes',body='<script>unsafe</script>',tags='Flask, Python'))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/blog/flask-notes').status_code,404)
        with self.app.app_context(): item=store.content('post','flask-notes')
        self.post(f"/dashboard/content/post/{item['id']}/edit",dict(title='Flask notes',slug='flask-notes',summary='Practical notes',body='<script>unsafe</script>',tags='Flask, Python',published='on'))
        response=self.client.get('/blog/flask-notes')
        self.assertEqual(response.status_code,200)
        self.assertIn('&lt;script&gt;unsafe&lt;/script&gt;',response.get_data(as_text=True))
        self.assertNotIn('<script>unsafe</script>',response.get_data(as_text=True))
        response=self.post('/dashboard/content/testimonial/new',dict(title='Feedback',slug='client-one',body='Helpful work',author='Client',published='on'))
        self.assertIn('permission',response.get_data(as_text=True))
        with self.app.app_context(): self.assertEqual(store.contents('testimonial'),[])
        self.post('/dashboard/content/testimonial/new',dict(title='Feedback',slug='client-one',body='Helpful work',author='Client',published='on',consent='on',consent_note='Written permission received.'))
        self.assertIn('Helpful work',self.client.get('/testimonials').get_data(as_text=True))
        with self.app.app_context(): item=store.content('testimonial','client-one')
        self.post(f"/dashboard/content/testimonial/{item['id']}/unpublish")
        self.assertNotIn('Helpful work',self.client.get('/testimonials').get_data(as_text=True))

    def test_project_case_study_filters_and_escaping(self):
        with self.app.app_context():
            store.save_content('case','1','Research case','Summary','Extra details',dict(tags=['Flask'],industry='Research',project_type='Portal',role='Developer',problem='Complex forms',solution='Clear workflows',results='No invented metrics'),True)
        body=self.client.get('/project/1').get_data(as_text=True)
        self.assertIn('Research case',body)
        self.assertIn('No invented metrics',body)
        self.assertIn('Survey',self.client.get('/projects?tag=Flask&industry=Research&type=Portal').get_data(as_text=True))
        self.assertNotIn('View project ↗',self.client.get('/projects?q=unmatched').get_data(as_text=True))
        self.assertIn('og:image',body)

    def test_enquiry_status_changes_one_message_and_replies_are_honest(self):
        self.sign_in()
        with patch('controllers.contactController.get_message',return_value=MESSAGE):
            response=self.post('/dashboard/enquiries/7',dict(action='status',status='in_progress',note='Call tomorrow'))
            self.assertEqual(response.status_code,302)
            with self.app.app_context():
                rows=store.db().execute('SELECT * FROM enquiry_state').fetchall()
                self.assertEqual(len(rows),1)
                self.assertEqual(rows[0]['message_id'],7)
            with patch('app.mail.send',side_effect=RuntimeError('SMTP offline')):
                with self.assertLogs(level='ERROR'):
                    response=self.post('/dashboard/enquiries/7',dict(action='reply',subject='Next steps',message='A saved reply'))
                self.assertIn('could not be sent',response.get_data(as_text=True))
            with self.app.app_context():
                self.assertEqual(store.db().execute('SELECT state FROM replies').fetchone()[0],'failed')
            with patch('app.mail.send') as mail:
                response=self.post('/dashboard/enquiries/7',dict(action='reply',subject='Next steps',message='A reply'))
                self.assertEqual(response.status_code,302)
                self.assertEqual(mail.call_args.args[0].recipients,['client@example.test'])

    def test_cv_selection_and_real_download_events(self):
        self.sign_in()
        folder=Path(self.app.static_folder)/'resume'
        folder.mkdir(parents=True)
        (folder/'approved.pdf').write_bytes(b'%PDF-1.4 test')
        rows=[(1,'approved.pdf',datetime(2026,1,1)),(2,'other.pdf',datetime(2026,1,2))]
        with patch('controllers.resumeController.get_resumes',return_value=rows):
            response=self.post('/dashboard/cv',dict(action='select',resume_id='1'))
            self.assertEqual(response.status_code,302)
            with self.client.get('/resume/download') as response:
                self.assertEqual(response.status_code,200)
                self.assertIn('approved.pdf',response.headers['Content-Disposition'])
            with self.client.get('/resume/view') as response: self.assertEqual(response.status_code,200)
            with self.app.app_context():
                events=store.event_report()
                self.assertEqual(events[0]['kind'],'cv_download')
                self.assertEqual(events[0]['total'],1)
        response=self.post('/dashboard/cv',dict(file=(io.BytesIO(b'not a pdf'),'fake.pdf')),content_type='multipart/form-data')
        self.assertIn('Choose a PDF',response.get_data(as_text=True))

    def test_event_endpoint_rejects_unknown_actions_and_deduplicates(self):
        token=self.csrf()
        self.assertEqual(self.client.post('/events',json=dict(kind='contact_click',target='email')).status_code,400)
        for _ in range(2):
            self.assertEqual(self.client.post('/events',json=dict(kind='contact_click',target='email'),headers={'X-CSRFToken':token}).status_code,204)
        self.assertEqual(self.client.post('/events',json=dict(kind='arbitrary',target='anything'),headers={'X-CSRFToken':token}).status_code,400)
        with self.app.app_context(): self.assertEqual(store.event_report()[0]['total'],1)

    def test_login_throttles_and_revocable_sessions(self):
        with patch('routes.admin_bp.login_admin',return_value=None):
            for _ in range(5): self.assertEqual(self.post('/dashboard/login',dict(email='bad@test',password='bad')).status_code,200)
            self.assertEqual(self.post('/dashboard/login',dict(email='bad@test',password='bad')).status_code,429)
        # A separate address is a separate throttle bucket.
        with patch('routes.admin_bp.login_admin',return_value=ADMIN):
            response=self.post('/dashboard/login',dict(email=ADMIN[4],password='long password'),environ_overrides={'REMOTE_ADDR':'192.0.2.1'})
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/dashboard/security').status_code,200)
        with self.app.app_context():
            with store.db() as connection: connection.execute('UPDATE sessions SET revoked=1')
        self.assertEqual(self.client.get('/dashboard/security').status_code,302)

    def test_totp_rfc_vector_replay_recovery_and_encryption(self):
        secret='GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ'
        self.assertEqual(security.totp(secret,1),'287082')
        with self.app.app_context():
            encrypted=security.encrypt(secret)
            self.assertNotIn(secret,encrypted)
            self.assertEqual(security.decrypt(encrypted),secret)
            with store.db() as connection:
                connection.execute('INSERT INTO security(aid,secret,recovery) VALUES(?,?,?)',(9,encrypted,json.dumps([security.hash_token('recovery01')])))
            with patch('services.security.time.time',return_value=59):
                self.assertTrue(security.verify_factor(9,'287082'))
                self.assertFalse(security.verify_factor(9,'287082'))
            self.assertTrue(security.verify_factor(9,'recovery01'))
            self.assertFalse(security.verify_factor(9,'recovery01'))

    def test_two_factor_setup_and_login_challenge(self):
        self.sign_in()
        with patch('controllers.adminController.login_admin',return_value=ADMIN):
            response=self.post('/dashboard/security',dict(action='begin',password='a long password'))
        self.assertIn('setup key',response.get_data(as_text=True))
        with self.client.session_transaction() as state: secret=state['factor_setup']
        response=self.post('/dashboard/security',dict(action='enable',code=security.totp(secret)))
        self.assertIn('Save your recovery codes now',response.get_data(as_text=True))
        self.post('/dashboard/logout')
        with patch('routes.admin_bp.login_admin',return_value=ADMIN):
            response=self.post('/dashboard/login',dict(email=ADMIN[4],password='a long password'))
        self.assertEqual(response.location,'/dashboard/login/verify')
        self.assertEqual(self.client.get('/dashboard/security').status_code,302)

    def test_services_and_sitemap_only_published_blog(self):
        with self.app.app_context():
            seed_services()
            store.save_content('post','draft','Draft','','Hidden',{},False)
            store.save_content('post','public','Public','Summary','Body',{},True)
        self.assertIn('Web application development',self.client.get('/services').get_data(as_text=True))
        with patch('controllers.projectController.get_projects',return_value=[PROJECT]):
            body=self.client.get('/sitemap.xml').get_data(as_text=True)
        self.assertIn('/blog/public',body)
        self.assertNotIn('/blog/draft',body)
        self.assertNotIn('/dashboard',body)
        self.assertIn('Disallow: /dashboard',self.client.get('/robots.txt').get_data(as_text=True))

    def test_password_reset_is_expiring_single_use_and_revokes_sessions(self):
        self.sign_in()
        with self.app.app_context():
            with store.db() as connection:
                connection.execute('INSERT INTO reset_tokens(token,aid,expires) VALUES(?,?,?)',(security.hash_token('valid-token'),9,int(time.time())+1000))
                connection.execute('INSERT INTO reset_tokens(token,aid,expires) VALUES(?,?,?)',(security.hash_token('expired'),9,int(time.time())-1))
        self.assertEqual(self.client.get('/dashboard/password/update/expired').status_code,400)
        fake=MagicMock()
        with patch('config.database.Database.get_connection',return_value=fake):
            response=self.post('/dashboard/password/update/valid-token',dict(new_password='a new strong password',confirm_password='a new strong password'))
        self.assertEqual(response.status_code,302)
        self.assertEqual(self.client.get('/dashboard/password/update/valid-token').status_code,400)
        with self.app.app_context():
            self.assertEqual(store.db().execute('SELECT COUNT(*) FROM sessions WHERE revoked=0').fetchone()[0],0)
        from werkzeug.security import check_password_hash
        stored=fake.cursor.return_value.__enter__.return_value.execute.call_args.args[1][0]
        self.assertTrue(check_password_hash(stored,'a new strong password'))

    def test_password_model_migrates_legacy_values_after_valid_login(self):
        from models.adminModel import AdminClass
        from werkzeug.security import check_password_hash, generate_password_hash
        model=AdminClass()
        model.connection=MagicMock()
        cursor=model.connection.cursor.return_value.__enter__.return_value
        legacy=list(ADMIN)
        legacy[6]='legacy-password'
        cursor.fetchone.return_value=tuple(legacy)
        self.assertEqual(model.login_admin(ADMIN[4],'wrong',1),None)
        model.connection.commit.assert_not_called()
        self.assertEqual(model.login_admin(ADMIN[4],'legacy-password',1),tuple(legacy))
        encoded=cursor.execute.call_args.args[1][0]
        self.assertTrue(check_password_hash(encoded,'legacy-password'))
        legacy[6]=generate_password_hash('already hashed')
        cursor.fetchone.return_value=tuple(legacy)
        self.assertEqual(model.login_admin(ADMIN[4],'already hashed',1),tuple(legacy))

    def test_csrf_unicode_and_image_upload_rejection(self):
        self.csrf()
        self.assertEqual(self.client.post('/dashboard/login',data={'csrf_token':'invalid-☃'}).status_code,400)
        self.sign_in()
        with patch('controllers.projectController.get_project',return_value=PROJECT):
            response=self.post('/dashboard/content/case/new',dict(title='A case',slug='1',screenshots=(io.BytesIO(b'<svg onload="evil()">'),'bad.svg')),content_type='multipart/form-data')
        self.assertIn('Screenshots must be PNG',response.get_data(as_text=True))
        with self.app.app_context(): self.assertIsNone(store.content('case','1'))

    def test_website_enquiry_is_saved_and_notifies_the_new_inbox(self):
        payload=dict(fname='Visitor',phone='12345678',email='visitor@example.test',subject='A project',message='<b>Build a portal</b>')
        with patch('routes.home_bp.send_message',return_value=55) as save, patch('routes.home_bp.mail.send') as send:
            response=self.post('/contact',payload)
            self.assertEqual(response.status_code,302)
            save.assert_called_once()
            notification=send.call_args.args[0]
            self.assertEqual(notification.recipients,['mbuvi@cm.co.ke'])
            self.assertEqual(notification.reply_to,'visitor@example.test')
            self.assertIn('Phone: 12345678',notification.body)
            self.assertIn('&lt;b&gt;Build a portal&lt;/b&gt;',notification.html)
        with self.app.app_context():
            self.assertEqual(store.db().execute('SELECT state FROM notifications WHERE message_id=55').fetchone()[0],'sent')

    def test_failed_inbox_notification_can_be_retried_without_resaving_message(self):
        payload=dict(fname='Visitor',phone='12345678',email='visitor@example.test',subject='A project',message='A portal')
        with patch('routes.home_bp.send_message',return_value=7), patch('routes.home_bp.mail.send',side_effect=RuntimeError('SMTP offline')):
            with self.assertLogs(level='ERROR'):
                self.assertEqual(self.post('/contact',payload).status_code,302)
        with self.app.app_context():
            self.assertEqual(store.db().execute('SELECT state FROM notifications WHERE message_id=7').fetchone()[0],'failed')
        self.sign_in()
        with patch('controllers.contactController.get_message',return_value=MESSAGE), patch('app.mail.send') as send:
            self.assertEqual(self.post('/dashboard/enquiries/7',dict(action='notify')).status_code,302)
            send.assert_called_once()
            self.assertEqual(self.post('/dashboard/enquiries/7',dict(action='notify')).status_code,302)
            send.assert_called_once()
        with self.app.app_context():
            self.assertEqual(store.db().execute('SELECT state FROM notifications WHERE message_id=7').fetchone()[0],'sent')
