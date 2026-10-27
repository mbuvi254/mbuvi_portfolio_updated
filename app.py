from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")
from flask import Flask,Blueprint,session
from routes.home_bp import home_bp
from routes.admin_bp import admin_bp
import os 
from flask_mail import Mail, Message 
from flask_session import Session
from datetime import datetime
from datetime import timedelta


app=Flask(__name__)
from config.database import init_app as init_database
init_database(app)
from services.analytics import init_app as init_analytics
init_analytics(app)

STATIC_FOLDER = 'static'
UPLOAD_FOLDER = 'admin'


app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
from services.security import init_app as init_security
init_security(app)
Session(app)
app.config['SESSION_TYPE'] = 'filesystem'

# Mail credentials are loaded from the private .env file or deployment environment.
app.config.update(
    MAIL_SERVER=os.environ.get('MAIL_SERVER','mail.cm.co.ke'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT','587')),
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS','true').lower() in ('1','true','yes'),
    MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL','false').lower() in ('1','true','yes'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER','mbuvi@cm.co.ke'),
    MAIL_RECIPIENT=os.environ.get('MAIL_RECIPIENT','mbuvi@cm.co.ke'),
)
if app.config['MAIL_USE_TLS'] and app.config['MAIL_USE_SSL']:
    raise RuntimeError('Choose either SMTP STARTTLS or implicit SSL, not both.')

# instantiating the mail service only after the 'app.config' to avoid error   
mail = Mail(app)


app.register_blueprint(home_bp)
app.register_blueprint(admin_bp)
from routes.features_bp import features
app.register_blueprint(features)
from services.portfolio_public import init_app as init_public_features
init_public_features(app)

@app.get('/service-worker.js')
def service_worker():
    from flask import send_from_directory
    response = send_from_directory(app.static_folder + '/pwa', 'sw.js', mimetype='application/javascript')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Service-Worker-Allowed'] = '/'
    return response


@app.cli.command('harden-passwords')
def harden_passwords():
    from services.security import harden_legacy_passwords
    changed=harden_legacy_passwords()
    print(f'Upgraded password storage for {changed} administrator accounts. Existing passwords are unchanged.')


@app.cli.command('init-db')
def init_db():
    """Create missing tables explicitly when setting up a database."""
    from models.aboutModel import AboutModel
    from models.resumeModel import ResumeModel
    from models.contactModel import ContactModel
    from models.projectModel import ProjectModel
    from models.adminModel import AdminClass
    for model, methods in (
        (AboutModel(), ('create_about_table', 'create_education_table')),
        (ResumeModel(), ('create_resume_table',)),
        (ContactModel(), ('create_messages_table', 'create_user_log_table', 'create_send_messages_table')),
        (ProjectModel(), ('create_category_table', 'create_projects_table')),
        (AdminClass(), ('create_admin_table', 'create_admin_log_table', 'create_password_reset')),
    ):
        for method in methods:
            getattr(model, method)()


if __name__ == '__main__':
    app.run(host='0.0.0.0',port=7000,debug=True)
