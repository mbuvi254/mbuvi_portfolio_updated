# Daniel Mulatya portfolio redesign

Reviewed public pages at mbuvi.cm.co.ke on 13 October 2026: About, Resume, Projects, Survey System detail and Contact. The original resume embeds a PDF; its contents were not extracted. The public project inventory contains Survey System, Loan App and BMI APP. No project outcomes or client testimonials are invented.

## Preview
Create a virtual environment, install `pip install -r requirements.txt`, then run `python preview.py`. Open http://127.0.0.1:5000. The preview contact form prepares an email draft, not a database submission.

## Integrating with the existing Flask app
Back up current templates and static assets. Copy `templates/` and `static/` into your app. Preserve your existing routes, authentication, database and contact submission logic. The original backend/source was not available, so these templates are an adaptation package, not guaranteed drop-in replacements.

Render `index.html`, `resume.html`, `projects.html`, `project.html`, `contact.html` as shown in preview.py. Category pages reuse projects.html. Project objects use the schema in projects.json: id, title, category, category_id, date, summary, description, image, demo, source. Map your database model fields into this schema. Keep HTML autoescaping enabled; description is rendered as plain text.

Supply portrait_url and resume_url via a context processor. Existing public image and PDF URLs are used so you can retain your original assets. They are not bundled; copy your local originals to static and change these URLs for an entirely self-contained deployment. Google Fonts is optional and falls back to system sans-serif. No Bootstrap or JavaScript CDN is required.

For contact: pass contact_mode='backend' and contact_action pointing to your existing POST handler. Match input names (name, phone, email, subject, message) to that handler. The template includes csrf_token() when Flask-WTF exposes it. Enforce server-side validation, CSRF protection, spam/rate controls, delivery and success/error feedback before enabling submissions. Do not claim delivery unless your handler confirms it. No email credentials or new database are included.

The resume page uses the previously requested Founder & CEO / Cybermaisha Solutions / 2026–present and skills supplied by Daniel. Its PDF link still points to the site's existing CV: replace it with your latest approved CV to align the download with this page.

## Design
Responsive blue-green visual system, real portrait and project screenshots, accessible labels, keyboard focus, skip link, mobile navigation, dark theme, reduced motion and project filters. Existing public route patterns and contact/social destinations retained. No deployment performed.

## Validation
Flask preview render checks cover every route and category, missing project handling, template parsing and HTML page generation. Visual browser QA was not performed on the redesign; review at mobile and desktop widths in your local browser before replacing production templates.
