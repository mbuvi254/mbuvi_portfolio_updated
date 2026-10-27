import json
import click
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin
from xml.etree.ElementTree import Element, SubElement, tostring
from flask import Response, g, request, session, url_for
from services import portfolio_store as store


def init_app(app):
    app.config.setdefault('PUBLIC_BASE_URL',os.environ.get('PORTFOLIO_PUBLIC_URL','https://mbuvi.cm.co.ke').rstrip('/'))
    app.context_processor(lambda: public_context(app))
    @app.template_filter('local_timestamp')
    def local_timestamp(value):
        from services.analytics import NAIROBI
        return datetime.fromtimestamp(value,NAIROBI).strftime('%d %b %Y %H:%M')

    @app.template_filter('local_iso')
    def local_iso(value):
        from services.analytics import NAIROBI
        return datetime.fromisoformat(value).astimezone(NAIROBI).strftime('%d %b %Y, %H:%M')

    @app.after_request
    def project_engagement(response):
        if request.endpoint=='home_bp.project_route' and request.method=='GET' and response.status_code==200:
            from routes.features_bp import visitor
            try: store.event('project_view',str(request.view_args['pid']),visitor())
            except Exception: app.logger.exception('Project engagement could not be recorded')
        return response

    @app.get('/robots.txt')
    def robots():
        return Response('User-agent: *\nAllow: /\nDisallow: /dashboard\nDisallow: /admin\nSitemap: '+app.config['PUBLIC_BASE_URL']+'/sitemap.xml\n',mimetype='text/plain')

    @app.get('/sitemap.xml')
    def sitemap():
        from controllers.projectController import get_projects
        root=Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
        paths=['/','/resume','/projects','/services','/blog','/testimonials','/contact']
        paths.extend('/project/'+str(row[0]) for row in (get_projects() or []))
        paths.extend('/blog/'+item['slug'] for item in store.contents('post',True))
        for path in paths:
            item=SubElement(root,'url')
            SubElement(item,'loc').text=app.config['PUBLIC_BASE_URL']+path
        return Response(tostring(root,encoding='utf-8',xml_declaration=True),mimetype='application/xml')

    @app.cli.command('migrate-features-to-mysql')
    @click.argument('source', type=click.Path(exists=True, dir_okay=False))
    def migrate_features(source):
        from services.portfolio_migration import migrate
        for table, count in migrate(source).items():
            print(f'{table}: {count} records verified in MySQL')

    @app.cli.command('init-features')
    def init_features():
        store.init_schema()
        seed_services()
        seed_case_drafts()
        print('Portfolio content and security storage are initialized.')


def public_context(app):
    titles={'/services':'Services','/blog':'Technical notes','/projects':'Projects','/resume':'Experience & CV','/contact':'Contact','/testimonials':'Client feedback'}
    title=getattr(g,'seo_title',titles.get(request.path,'Daniel Mbuvi Mulatya')+(' · Daniel Mbuvi Mulatya' if request.path in titles else ' · Software Developer'))
    description=getattr(g,'seo_description','Software developer building web applications, business workflow tools and data-driven solutions. Explore projects and discuss your next idea.')
    image=getattr(g,'seo_image','/static/brand/social-card.png')
    canonical=app.config['PUBLIC_BASE_URL']+request.path
    structured={'@context':'https://schema.org','@type':'Person','name':'Daniel Mbuvi Mulatya','url':app.config['PUBLIC_BASE_URL'],'jobTitle':'Software Developer','sameAs':['https://github.com/mbuvi254','https://www.linkedin.com/in/daniel-mulatya-546794161/']}
    if getattr(g,'article',None):
        item=g.article
        structured={'@context':'https://schema.org','@type':'BlogPosting','headline':item['title'],'description':item['summary'],'datePublished':item['created'],'dateModified':item['updated'],'author':{'@type':'Person','name':'Daniel Mbuvi Mulatya'},'mainEntityOfPage':canonical}
    return dict(published_testimonials=store.contents('testimonial',True)[:3] if request.path=='/' else [], latest_posts=store.contents('post',True)[:3] if request.path=='/' else [], seo_title=title,seo_description=description,seo_image=urljoin(app.config['PUBLIC_BASE_URL']+'/',image),canonical_url=canonical,structured_data=structured)


def seed_services():
    if store.setting('services_initialized'): return
    if not store.contents('service'):
        for slug,title,summary,body in [
            ('web-development','Web application development','Turn an idea into a clear, usable web application.','Discuss a new website, portal or web application. We will define the users, scope and practical next steps together.'),
            ('workflow-software','Business workflow software','Simplify repetitive processes with software built around your work.','Explore tools for managing records, applications and internal workflows. Start with the problem your team needs to solve.'),
            ('data-analytics','Data analytics','Make your data easier to understand and use.','Discuss reporting, data preparation and dashboards that help you answer a concrete business question.')]:
            store.save_content('service',slug,title,summary,body,{},True)
    store.set_setting('services_initialized','1')


def seed_case_drafts():
    from controllers.projectController import get_projects
    for row in get_projects() or []:
        if not store.content('case',str(row[0])):
            store.save_content('case',str(row[0]),row[1],(row[2] or '')[:500],'',
                dict(tags=[row[9]],role='',problem='',solution='',results='',industry='',project_type='',screenshots=[]),False)
