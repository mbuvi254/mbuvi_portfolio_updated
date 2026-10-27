"""Standalone preview; adapt contexts to your existing Flask application."""
from flask import Flask, render_template, abort
import json
from pathlib import Path
app=Flask(__name__)
projects=json.loads((Path(__file__).parent/'projects.json').read_text())
@app.context_processor
def context():
    return dict(portrait_url='https://mbuvi.cm.co.ke/static/about/20240816_084420.jpg',resume_url='https://mbuvi.cm.co.ke/static/resume/Daniel%20Mbuvi%20Mulatya%20%20-%20CV.pdf',contact_mode='email',year=2026)
@app.get('/')
def home():return render_template('index.html',projects=projects)
@app.get('/resume')
def resume():return render_template('resume.html')
@app.get('/contact')
def contact():return render_template('contact.html')
@app.get('/projects')
def all_projects():return render_template('projects.html',projects=projects)
@app.get('/project/category/<int:category_id>')
def category(category_id):return render_template('projects.html',projects=[p for p in projects if p['category_id']==category_id])
@app.get('/project/<int:project_id>')
def project(project_id):
    item=next((p for p in projects if p['id']==project_id),None)
    if not item:abort(404)
    return render_template('project.html',project=item)
@app.errorhandler(404)
def missing(e):return render_template('404.html'),404
if __name__=='__main__':app.run(host='127.0.0.1',port=5000)
