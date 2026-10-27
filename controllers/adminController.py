from flask import Flask,redirect,url_for,render_template,request
from models.adminModel import AdminClass

admin_model=AdminClass()

def register_admin(firstName, lastName, phoneNumber,email,profile_picture,password,status):
    admin=admin_model.register_admin(firstName, lastName, phoneNumber,email,profile_picture,password,status)
    if admin:
        return render_template('admin/login.html')
    else:
        return render_template('admin/register.html')
    
def update_admin(firstName, lastName, phoneNumber,email,profile_picture,password, admin_id):
    admin_model.update_admin(firstName, lastName, phoneNumber,email,profile_picture,password, admin_id)
    return redirect(url_for('admin_bp.admin_route'))

def check_admin(email):
    admin=admin_model.check_admin(email)
    return admin

def login_admin(email,password,status):
    return admin_model.login_admin(email,password,status)

def admin_activate(status,email):
    activate=admin_model.admin_activate(status,email)
    if activate:
       page_title="Login"
       message="Admin Account Activated"
       return render_template('admin/login.html', message=message, page_title=page_title)
    else:
        page_title = "Login"
        message = "Admin Account Not Activated"
        return render_template('admin/login.html', message=message, page_title=page_title)
    
def forgot_password(email,reset_code):
    password_reset=admin_model.password_reset(email,reset_code)
    if password_reset:
      page_title="Password Reset"
      message="Password Reset"
      return render_template('password_reset.html',email=email,message=message,page_title=page_title)
    else:
        message="Password Reset Failed"
        page_title="Forgot Password"
        return render_template('admin/forgot_password.html',message=message,page_title=page_title)

def check_reset(email):
    reset=admin_model.check_reset(email)
    return reset

def check_password_code(reset_code):
    code=admin_model.check_password_code(reset_code)
    return code

def update_password(password,aid,pid):
    pass_update=admin_model.password_update(password,aid,pid)
    if pass_update:
        message="Password successfully updated."
        return redirect(url_for('admin_bp.admin_login_route',message=message))
    else:
        return"Well This Failed"

def admin_log(email,ip,loginTime):
    sid=admin_model.admin_log(email,ip,loginTime)
    return sid
    
def get_admin_logs():
    admin_logs=admin_model.get_admin_logs()
    return admin_logs

def logout(logoutTime,email,sid):
    admin_model.logout(logoutTime,email,sid)
    
def get_session():
    sid=admin_model.get_session_id()
    
