from flask import abort,render_template,Blueprint,request,url_for,redirect,flash,session,current_app
from controllers.aboutController import add_about,get_all_about,delete_about,edit_about,get_about,add_education,get_all_education,edit_education,get_education,delete_education
from controllers.resumeController import add_resume,get_resumes,get_resume,delete_resume
from controllers.projectController import add_project,get_projects,edit_project,get_project,delete_project,add_category,get_categories,edit_category,get_category,delete_category
from controllers.contactController import get_messages,get_message,inbox_messages,status_update,read_messages,send_reply,sent_messages,get_user_logs
import os
from flask_mail import Mail,Message
from controllers.adminController import register_admin,check_admin,login_admin,admin_activate,check_reset,forgot_password,check_password_code,update_password,admin_log,update_admin,get_admin_logs,logout
import uuid
from datetime import timedelta
from flask_session import Session
import datetime
from datetime import datetime 
from models.adminModel import AdminClass
from services.analytics import Analytics, local_today, NAIROBI
from datetime import date
from functools import wraps
from services import security
from services import portfolio_store as store
from werkzeug.security import generate_password_hash
import time
import secrets
from services.uploads import save_image

admin_model=AdminClass()
admin_bp=Blueprint('admin_bp',__name__)
mail=Mail()


STATIC_FOLDER = 'static'
UPLOAD_FOLDER = 'admin'

@admin_bp.context_processor
def inject_current_year():
    return {'current_year': datetime.now(NAIROBI).year}

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('aid') or session.get('status') != 1:
            return redirect(url_for('admin_bp.admin_login_route'))
        return view(*args, **kwargs)
    return wrapped


@admin_bp.route('/dashboard')
@admin_required
def admin_route():
    days = request.args.get('days', 30, type=int)
    if days not in (7, 30, 90):
        days = 30
    traffic = None
    try:
        traffic = Analytics().dashboard(days)
    except Exception:
        current_app.logger.exception('Traffic report unavailable')
    sent=admin_model.count_smessages()
    if sent is not None:
        sent += store.db().execute("SELECT COUNT(*) FROM replies WHERE state='sent'").fetchone()[0]
    return render_template('admin/dashboard.html', ptitle='Overview', traffic=traffic, days=days,
                           cprojects=admin_model.count_projects(), rmes=admin_model.count_rmessages(),
                           smes=sent)

@admin_bp.route('/dashboard/about')
def admin_about_route():
    ptitle="About"
    about=get_all_about()
    return render_template('admin/admin_about.html',ptitle=ptitle,about=about)

@admin_bp.route('/dashboard/about/add',methods=['POST','GET'])
def add_about_route():
    ptitle="Add About"
    if request.method == 'POST':
       aboutTitle=request.form.get('title')
       aboutDetails=request.form.get('details')
       file =request.files['file']
       aboutPhoto=save_image(file,"about")
       if aboutPhoto:
          add_about(aboutTitle,aboutDetails,aboutPhoto)
          return redirect(url_for('admin_bp.admin_about_route')) 
    return render_template('admin/add_about.html',ptitle=ptitle)

@admin_bp.route('/dashboard/about/edit/<int:id>',methods=['POST','GET'])
def edit_about_route(id):
    ptitle="Edit About"
    about=get_about(id)
    if request.method == 'POST':
       aboutTitle=request.form.get('title')
       aboutDetails=request.form.get('details')
       file =request.files['file']
       if file:
          aboutPhoto=save_image(file,"about")
       else:
           aboutPhoto=about[3]
       edit_about(aboutTitle,aboutDetails,aboutPhoto,id)
       return redirect(url_for('admin_bp.admin_about_route')) 
    return render_template('admin/edit_about.html',ptitle=ptitle,about=about)

@admin_bp.route('/dashboard/about/delete/<int:id>',methods=['POST'])
def admin_about_delete_route(id):
    delete_about(id)
    message="About Deleted Id:{id}"
    return redirect(url_for('admin_bp.admin_about_route')) 

@admin_bp.route('/dashboard/resume/add',methods=['POST','GET'])
def admin_add_resume_route():
    return redirect(url_for('features.manage_cv'),code=307 if request.method=='POST' else 302)

@admin_bp.route('/dashboard/resume')
def admin_resume_route():
    return redirect(url_for('features.manage_cv'))
       

@admin_bp.route('/dashboard/resume/read/<int:pid>', methods=['POST', 'GET'])
def admin_read_resume_route(pid):
    ptitle = "Resume"
    resume = get_resume(pid)
    return render_template('admin/read_resume.html', ptitle=ptitle, resume=resume)

@admin_bp.route('/dashboard/resume/delete/<int:rid>', methods=['POST'])
def admin_resume_delete_route(rid):
    delete_resume(rid)
    return redirect(url_for('admin_bp.admin_resume_route'))

#######################  PROJECTS ##############################

@admin_bp.route('/dashboard/projects')
def admin_projects_route():
    ptitle="Projects"
    projects=get_projects()
    return render_template('admin/projects.html',ptitle=ptitle,projects=projects)


@admin_bp.route('/dashboard/project/add',methods=['POST','GET'])
def admin_add_projetc_route():
    if request.method == 'POST':
        projectTitle=request.form.get('projectTitle')
        projectDetails=request.form.get('projectDetails')
        projectCategory=request.form.get('projectCategory')
        projectWebsite=request.form.get('projectWebsite')
        projectGithub=request.form.get('projectGithub')
        file =request.files['file']
        projectImage=save_image(file,"projects")
        add_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub)
        return redirect(url_for('admin_bp.admin_projects_route'))
    ptitle="Add Project"
    categories=get_categories()
    return render_template('admin/add_project.html',ptitle=ptitle,categories=categories)
  

@admin_bp.route('/dashboard/project/edit/<int:pid>',methods=['POST','GET'])
def admin_edit_project_route(pid):
    ptitle="Edit Project"
    project=get_project(pid)
    categories=get_categories()
    if request.method == 'POST':
        projectTitle=request.form.get('projectTitle')
        projectDetails=request.form.get('projectDetails')
        projectCategory=request.form.get('projectCategory')
        projectWebsite=request.form.get('projectWebsite')
        projectGithub=request.form.get('projectGithub')
        file =request.files['file']
        if file:
           file =request.files['file']
           projectImage=save_image(file,"projects")
        else:
            projectImage=project[3]
            edit_project(projectTitle,projectDetails,projectImage,projectCategory,projectWebsite,projectGithub,pid)
            return redirect(url_for('admin_bp.admin_projects_route'))
    return render_template('admin/edit_project.html',ptitle=ptitle,project=project,categories=categories)
    
@admin_bp.route('/dashboard/project/delete/<int:pid>', methods=['POST'])
def admin_project_delete_route(pid):
    delete_project(pid)
    return redirect(url_for('admin_bp.admin_projects_route'))  

@admin_bp.route('/dashboard/project/view/<int:pid>')
def admin_project_view_route(pid):
    project=get_project(pid)
    ptitle=project[1]
    return render_template('admin/view_project.html',ptitle=ptitle,project=project)
  
#####################  Category ######################
@admin_bp.route('/dashboard/categories')
def admin_category_route():
    ptitle="Categories"
    categories=get_categories()
    return render_template('admin/categories.html',categories=categories,ptitle=ptitle) 

@admin_bp.route('/dashboard/category/add',methods=['POST','GET'])
def add_category_route():
    ptitle="Add Category"
    if request.method == 'POST':
       categoryName=request.form.get('title')
       categoryDetails=request.form.get('details')
       add_category(categoryName,categoryDetails)
       return redirect(url_for('admin_bp.admin_category_route'))
    return render_template('admin/add_category.html',ptitle=ptitle) 

@admin_bp.route('/dashboard/category/edit/<int:cid>',methods=['POST','GET'])
def edit_category_route(cid):
    ptitle="Edit Category"
    if request.method == 'POST':
       categoryName=request.form.get('title')
       categoryDetails=request.form.get('details')
       edit_category(categoryName,categoryDetails,cid)
       return redirect(url_for('admin_bp.admin_category_route'))
    category=get_category(cid)
    return render_template('admin/edit_category.html',ptitle=ptitle,category=category) 

@admin_bp.route('/dashboard/category/delete/<int:cid>', methods=['POST'])
def admin_category_delete_route(cid):
    delete_category(cid)
    return redirect(url_for('admin_bp.admin_category_route')) 



###################  Education  ######################
@admin_bp.route('/dashboard/education',methods=['POST','GET'])
def admin_education_route():
    ptitle="Education"
    education=get_all_education()
    return render_template('admin/education.html',ptitle=ptitle,education=education)


@admin_bp.route('/dashboard/education/add',methods=['POST','GET'])
def add_education_route():
    ptitle="Add Education"
    if request.method == 'POST':
       certification=request.form.get('certification')
       institution=request.form.get('institution')
       graduation=request.form.get('graduation')
       add_education(certification,institution,graduation)
       return redirect(url_for('admin_bp.admin_education_route')) 
    return render_template('admin/add_education.html',ptitle=ptitle)

@admin_bp.route('/dashboard/education/edit/<int:eid>',methods=['POST','GET'])
def edit_education_route(eid):
    ptitle="Edit Education"
    if request.method == 'POST':
       certification=request.form.get('certification')
       institution=request.form.get('institution')
       graduation=request.form.get('graduation')
       edit_education(certification,institution,graduation,eid)
       return redirect(url_for('admin_bp.admin_education_route'))
    education=get_education(eid) 
    return render_template('admin/edit_education.html',ptitle=ptitle,education=education)

@admin_bp.route('/dashboard/education/delete/<int:eid>',methods=['POST'])
def delete_education_route(eid):
    delete_education(eid)
    return redirect(url_for('admin_bp.admin_education_route'))


#################  Messages #################
@admin_bp.route('/dashboard/messages')
def admin_messages_route():
    return redirect(url_for('features.enquiries'))


@admin_bp.route('/dashboard/messages/inbox')
def inbox_messages_route():
    return redirect(url_for('features.enquiries',status='new'))


@admin_bp.route('/dashboard/messages/read')
def read_messages_route():
    return redirect(url_for('features.enquiries',status='in_progress'))


@admin_bp.route('/dashboard/messages/sent')
def sent_messages_route():
    return redirect(url_for('features.reply_history'))


@admin_bp.route('/dashboard/message/read/<int:mid>')
def admin_read_message_route(mid):
    return redirect(url_for('features.enquiry',mid=mid))


@admin_bp.route('/dashboard/message/reply/<int:mid>',methods=['GET','POST'])
def reply_message_route(mid):
    return redirect(url_for('features.enquiry',mid=mid),code=307 if request.method=='POST' else 302)


################  User Log ################
@admin_bp.route('/dashboard/user/logs')
@admin_required
def user_log_route():
    start_text = request.args.get('start', '')
    end_text = request.args.get('end', '')
    search = request.args.get('q', '').strip()[:120]
    page = max(1, request.args.get('page', 1, type=int))
    error = None
    report = None
    try:
        start = date.fromisoformat(start_text) if start_text else None
        end = date.fromisoformat(end_text) if end_text else None
        if start and end and start > end:
            raise ValueError('Start date must be before or equal to end date.')
    except ValueError:
        error = 'Enter valid dates with the start date before or equal to the end date.'
    if not error:
        try:
            report = Analytics().logs(start, end, search, page)
        except Exception:
            current_app.logger.exception('Visit logs unavailable')
            error = 'Visit logs are temporarily unavailable. Please try again.'
    return render_template('admin/user_logs.html', ptitle='Visit logs', report=report,
                           start=start_text, end=end_text, search=search, error=error)


###################### ADMIN ############################

@admin_bp.route('/dashboard/register',methods=['GET','POST'])
def admin_register_route():
    error=None
    if request.method=='POST':
        email=request.form.get('email','').strip()
        password=request.form.get('password','')
        first=request.form.get('firstName','').strip()[:120]
        last=request.form.get('lastName','').strip()[:120]
        if not first or not last or '@' not in email or len(password)<12 or len(password)>200:
            error='Enter a name, valid email and a password of 12–200 characters.'
        elif check_admin(email):
            error='An account with that email already exists.'
        elif admin_model.register_admin(first,last,request.form.get('phone','')[:30],email,'',password,1):
            flash('Administrator created. Share access details privately.','success')
            return redirect(url_for('features.security_settings'))
        else:
            error='The account could not be created.'
    return render_template('admin/account_create.html',ptitle='Create administrator',error=error)


@admin_bp.route('/dashboard/update/<int:admin_id>', methods=['POST', 'GET'])
def admin_update_route(admin_id):
    if request.method == 'POST':
        firstName = request.form.get('firstName')
        lastName = request.form.get('lastName')
        email = request.form.get('email')
        phoneNumber = request.form.get('phoneNumber')
        password=request.form.get('password','')
        if not 12 <= len(password) <= 200:
            abort(400,description='Use a password of 12–200 characters.')
        file = request.files.get('file')
        # Preserve the uploaded portrait when no replacement is selected.
        profile_picture = session.get('profile_picture') or session.get('profile_file', '')

        if file:
            upload_folder = os.path.join(STATIC_FOLDER, UPLOAD_FOLDER)
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)

            profile_picture = save_image(file,"admin")

        try:
            update_admin(firstName, lastName, phoneNumber,email,profile_picture,password, admin_id)
            return redirect(url_for('admin_bp.admin_login_route'))
        except FileNotFoundError as e:
            return f'Error uploading file: {e}'
        except Exception as e:
            return f'An error occurred: {e}'

    email = session['email']
    admin = check_admin(email)
    
    if admin:
        return render_template('admin/admin_update.html', admin=admin)

@admin_bp.route('/dashboard/login',methods=['POST','GET'])
def admin_login_route():
    if session.get('aid') and session.get('status') == 1:
        return redirect(url_for('admin_bp.admin_route'))
    if request.method=='POST':
        email=request.form.get('email','').strip()[:254]
        if not security.allow_attempt('login') or not security.allow_attempt('login-account',email):
            return render_template('admin/login.html',message='Too many attempts. Try again in 15 minutes.'),429
        try:
            admin=login_admin(email,request.form.get('password',''),1)
        except Exception:
            current_app.logger.exception('Admin authentication unavailable')
            return render_template('admin/login.html',message='Sign in is temporarily unavailable. Please try again.'),503
        if admin and admin[7]==1:
            if security.factor_enabled(admin[0]):
                session.clear()
                session['pending_admin']=dict(aid=admin[0],email=admin[4],expires=time.time()+300)
                security.csrf_token()
                return redirect(url_for('features.factor_login'))
            security.establish_session(admin)
            return redirect(url_for('admin_bp.admin_route'))
        return render_template('admin/login.html',message='Account Not Activated or Check Your Password')
    return render_template('admin/login.html',ptitle='Sign in')


@admin_bp.route('/dashboard/logout',methods=['POST'])
def admin_logout_route():
    if session.get('sid'):
        logout(datetime.now(NAIROBI).time(),session.get('email'),session['sid'])
    security.end_session()
    return redirect(url_for('admin_bp.admin_login_route'))


@admin_bp.route('/dashboard/activate/<email>',methods=['POST'])
def admin_activate_route(email):
    admin_model.admin_activate(1,email)
    flash('Account activated.','success')
    return redirect(url_for('admin_bp.admin_route'))


@admin_bp.route('/dashboard/password/forgot',methods=['POST','GET'])
def admin_forgot_password_route():
    notice=None
    if request.method=='POST':
        if not security.allow_attempt('reset',limit=3,window=3600):
            return render_template('admin/password_help.html',notice='Please wait before requesting another reset.'),429
        email=request.form.get('email','').strip()[:254]
        admin=check_admin(email)
        if admin and admin[7]==1:
            token=secrets.token_urlsafe(32)
            with store.db() as connection:
                connection.execute('UPDATE reset_tokens SET used=1 WHERE aid=?',(admin[0],))
                connection.execute('INSERT INTO reset_tokens(token,aid,expires) VALUES(?,?,?)',(security.hash_token(token),admin[0],int(time.time())+1800))
            link=current_app.config['PUBLIC_BASE_URL']+url_for('admin_bp.admin_password_update_route',reset_code=token)
            try:
                mail.send(Message('Reset your portfolio password',sender=current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config['MAIL_USERNAME'],recipients=[email],body='Reset your password within 30 minutes: '+link))
            except Exception:
                current_app.logger.exception('Password reset email failed')
        notice='If an active account exists, a password reset link will be sent to its email address.'
    return render_template('admin/password_help.html',notice=notice)


@admin_bp.route('/dashboard/password/update/<reset_code>',methods=['POST','GET'])
def admin_password_update_route(reset_code):
    record=store.db().execute('SELECT * FROM reset_tokens WHERE token=? AND used=0 AND expires>?',(security.hash_token(reset_code),int(time.time()))).fetchone()
    if not record:
        return render_template('admin/password_help.html',notice='This reset link is invalid or expired. Request another.'),400
    error=None
    if request.method=='POST':
        if not security.allow_attempt('reset-confirm',limit=5): abort(429)
        password=request.form.get('new_password','')
        if len(password)<12 or len(password)>200 or password!=request.form.get('confirm_password'):
            error='Use 12–200 characters and enter the same password twice.'
        else:
            if security.factor_enabled(record['aid']) and not security.verify_factor(record['aid'],request.form.get('code','')):
                error='Enter a valid authenticator or recovery code.'
            else:
                with store.db() as connection:
                    consumed=connection.execute('UPDATE reset_tokens SET used=1 WHERE token=? AND used=0',(record['token'],))
                    if consumed.rowcount!=1: abort(400)
                try:
                    from config.database import Database
                    mysql=Database().get_connection()
                    with mysql.cursor() as cursor:
                        cursor.execute('UPDATE admin SET password=%s WHERE aid=%s',(generate_password_hash(password),record['aid']))
                        mysql.commit()
                except Exception:
                    with store.db() as connection: connection.execute('UPDATE reset_tokens SET used=0 WHERE token=?',(record['token'],))
                    raise
                with store.db() as connection: connection.execute('UPDATE sessions SET revoked=1 WHERE aid=?',(record['aid'],))
                session.clear()
                flash('Password updated. Sign in again.','success')
                return redirect(url_for('admin_bp.admin_login_route'))
    return render_template('admin/password_change.html',error=error,factor=security.factor_enabled(record['aid']))


@admin_bp.route('/dashboard/profile/<email>',methods=['POST','GET'])
def admin_profile_route(email):
    admin=check_admin(email)
    if admin:
        ptitle="Admin Profile"
        return render_template('admin/profile.html',admin=admin,ptitle=ptitle)
    else:
        return "Admin Not Found"


################  Admin Log ################
@admin_bp.route('/dashboard/logs')
@admin_required
def admin_log_route():
    ptitle="Admin Logs"
    error = None
    try:
        admin_logs=get_admin_logs()
    except Exception:
        current_app.logger.exception('Admin activity logs unavailable')
        admin_logs=[]
        error='Admin activity logs are temporarily unavailable.'
    return render_template('admin/admin_logs.html',ptitle=ptitle,admin_logs=admin_logs,error=error)





@admin_bp.route('/admin', defaults={'legacy_path': ''}, methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
@admin_bp.route('/admin/<path:legacy_path>', methods=['GET', 'POST', 'HEAD', 'OPTIONS'])
def legacy_admin_redirect(legacy_path):
    target = '/dashboard' + ('/' + legacy_path if legacy_path else '')
    if request.query_string:
        target += '?' + request.query_string.decode('latin-1')
    return redirect(target, code=308)
