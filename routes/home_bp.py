from flask import Flask,render_template,redirect,url_for,Blueprint,request,abort,flash,g,current_app
from controllers.aboutController import get_all_about,get_all_education
from controllers.resumeController import get_resumes
from controllers.contactController import send_message
from controllers.projectController import get_projects,get_project,get_categories,category_projects,get_category
from flask_mail import Mail,Message
from datetime import datetime
from services.analytics import NAIROBI
from urllib.parse import urlsplit
from markupsafe import escape
import re
from services import portfolio_store as store
from routes.features_bp import public_project_data

home_bp=Blueprint('home_bp',__name__)
mail=Mail()

def external_url(value):
    """Normalize stored domains and reject non-web link schemes."""
    value = (value or '').strip()
    if not value:
        return None
    if value.startswith('//'):
        value = 'https:' + value
    elif '://' not in value and ':' not in value:
        value = 'https://' + value
    parsed = urlsplit(value)
    return value if parsed.scheme in ('http', 'https') and parsed.netloc else None


def project_context(row):
    description = row[2] or ''
    date = row[7]
    return public_project_data(dict(id=row[0], title=row[1], description=description,
                summary=description if len(description) <= 160 else description[:157] + '…',
                image=url_for('static', filename='projects/' + row[3]),
                category_id=row[8], category=row[9],
                date=date.strftime('%B %d, %Y') if hasattr(date, 'strftime') else str(date or ''),
                demo=external_url(row[5]), source=external_url(row[6])))


@home_bp.context_processor
def design_context():
    return dict(year=datetime.now(NAIROBI).year, contact_mode='backend',
                contact_action=url_for('home_bp.contact_route'),
                portrait_url=url_for('static', filename='about/20240816_084420.jpg'))


@home_bp.route('/')
def about_route():
    ptitle="About"
    about=get_all_about()
    education=get_all_education()
    return render_template('index.html', ptitle=ptitle, about=about, education=education,
                           portrait_url=url_for('static', filename='about/' + about[-1][3]) if about else url_for('static', filename='about/20240816_084420.jpg'),
                           projects=[project_context(row) for row in (get_projects() or [])][:3])

@home_bp.route('/resume')
def resume_route():
    ptitle="Resume"
    resumes=get_resumes()
    latest = next((row for row in (resumes or []) if str(row[0]) == store.setting('active_resume')), max(resumes or [], key=lambda row: row[0], default=None))
    resume_url = url_for('static', filename='resume/' + (latest[1] if latest else 'Daniel_Mulatya_CV_Updated.pdf'))
    return render_template('resume.html', ptitle=ptitle, resumes=resumes, resume_url=resume_url, education=get_all_education() or [])

@home_bp.route('/projects')
def projects_route():
    ptitle="Projects"
    projects=get_projects()
    categories=get_categories()
    query=request.args.get('q','').strip()[:120]
    tag=request.args.get('tag','').strip()[:40]
    industry=request.args.get('industry','').strip()[:100]
    project_type=request.args.get('type','').strip()[:100]
    items=[project_context(row) for row in (projects or [])]
    tags=sorted({tag for item in items for tag in item['tags']})
    industries=sorted({item['industry'] for item in items if item['industry']})
    types=sorted({item['project_type'] for item in items if item['project_type']})
    if query: items=[item for item in items if query.casefold() in (item['title']+' '+item['description']+' '+' '.join(item['tags'])).casefold()]
    if tag: items=[item for item in items if tag in item['tags']]
    if industry: items=[item for item in items if industry==item['industry']]
    if project_type: items=[item for item in items if project_type==item['project_type']]
    return render_template('projects.html',ptitle=ptitle,projects=items,categories=categories or [],query=query,selected_tag=tag,tags=tags,industries=industries,types=types,selected_industry=industry,selected_type=project_type)

@home_bp.route('/project/<int:pid>')
def project_route(pid):
    project=get_project(pid)
    if not project:
        abort(404)
    ptitle=project[1]
    item=project_context(project)
    g.seo_title=item['title']+' · Daniel Mbuvi Mulatya'
    g.seo_description=item['summary'][:180]
    g.seo_image=item['image']
    return render_template('project.html',ptitle=ptitle,project=item)

@home_bp.route('/contact',methods=['POST','GET'])
def contact_route():
    if request.method == 'POST':
       fname=(request.form.get('fname') or request.form.get('name') or '').strip()
       phone=request.form.get('phone')
       email=request.form.get('email')
       subject=request.form.get('subject')
       message=request.form.get('message')
       fields = (fname, phone, email, subject, message)
       limits = (120, 30, 254, 200, 5000)
       if (any(not value or not value.strip() or len(value) > limit for value, limit in zip(fields, limits))
               or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email)
               or any(char in email + subject for char in '\r\n')):
           flash('Please complete all fields with a valid email address.', 'error')
           return render_template('contact.html', ptitle='Contact'), 400
       status=0
       try:
           message_id=send_message(fname,phone,email,subject,message,status)
       except Exception:
           current_app.logger.exception('Enquiry could not be saved')
           flash('Your message could not be saved. Please try again or email me directly.','error')
           return render_template('contact.html',ptitle='Contact'),503
       from services.mail_notifications import send_enquiry_notification
       send_enquiry_notification(mail,message_id,fname,phone,email,subject,message)
       flash("Thank you. Your message has been received.", "success")
       return redirect(url_for('home_bp.contact_route'))
    ptitle="Contact"
    return render_template('contact.html',ptitle=ptitle)

@home_bp.route('/project/category/<int:cid>')
def category_route(cid):
    category=get_category(cid)
    if not category:
        abort(404)
    ptitle=category[1]
    projects=category_projects(cid)
    return render_template('projects.html', ptitle=ptitle, projects=[project_context(row) for row in (projects or [])], categories=[category], category=category)


@home_bp.app_errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404
