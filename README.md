# Daniel Mbuvi Mulatya — Portfolio

A Flask portfolio website and private dashboard for managing projects, case studies, services, articles, testimonials, CVs and enquiries. Includes daily traffic charts, engagement tracking, email notifications, administrator security and PWA support.

The development app currently runs at **http://127.0.0.1:7000**. Sign in at **http://127.0.0.1:7000/dashboard/login**. Legacy `/admin` URLs redirect to `/dashboard`.

## Features

| Feature | What is included |
| --- | --- |
| Project case studies | Role, problem, approach, results, technologies, industry, project type and a screenshot gallery; draft/publish controls. |
| Services | Editable service descriptions with project-enquiry buttons. |
| Enquiries | New, in-progress and resolved states, internal notes, email replies and delivery history. |
| CV management | PDF upload, public-version selection, preview and tracked downloads. |
| Project discovery | Text search, category filters, technology tags, industry and project-type filters. |
| Blog | Draft and published technical notes, stable URLs, topic filters and search. |
| Testimonials | Feedback and attribution with required permission confirmation and a private permission note. |
| Analytics | Daily page views and unique IPs, 7/30/90-day charts, top pages, searchable logs and engagement events. |
| SEO | Canonical URLs, descriptions, Open Graph sharing previews, structured data, robots.txt and sitemap.xml. |
| Dashboard security | Hashed passwords, CSRF protection, rate limits, optional authenticator-based 2FA, recovery codes and revocable sessions. |
| PWA and branding | DM monogram, standard and maskable install icons, Apple touch icon, favicon and a branded offline page. |

Feature availability does not automatically publish content or enable 2FA. Case studies begin as drafts; publish articles and genuine testimonials yourself. Industry/type filters populate from published case-study metadata. Without a manual CV selection, the latest uploaded CV is used.

## Requirements

- Python 3.11 or newer and pip.
- A running MySQL/MariaDB database for the original portfolio data and administrator accounts.
- A writable local instance directory and upload directories.
- SMTP credentials for enquiry notifications, replies and password-reset emails.
- Node.js for the service-worker tests; the `sharp` package only if rebuilding brand icons.

## Local setup

Run these commands from the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r req.txt
```

Configure the MySQL connection in `config/database.py` for your environment. The adapter also supports Flask configuration overrides named `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME`; the application does not currently map those names from `.env` automatically.

For a new installation, create a private environment file:

```bash
cp .env.example .env
chmod 600 .env
```

If `.env` already exists, edit it instead of replacing it. Add the mailbox password locally; do not put real credentials in this README, `.env.example` or source control.

Initialize the databases:

```bash
# New MySQL database only: create the original tables.
flask --app app init-db

# Initialize extension data, starting services and drafts for existing projects.
flask --app app init-features
```

`init-features` preserves existing content. It creates initial service entries only when needed and adds unpublished case-study drafts for existing project records without inventing roles or results.

Start the development server:

```bash
python app.py
```

The current `app.py` starts the development server on port **7000** with debugging enabled. Use a production WSGI server or Passenger, with debugging disabled, for deployment.

## Environment configuration

The application loads `.env` with `python-dotenv`. Existing process environment variables take precedence. `.env` is ignored by Git; `.env.example` contains placeholders.

| Variable | Purpose |
| --- | --- |
| `MAIL_SERVER` | SMTP hostname; current mailbox uses `mail.cm.co.ke`. |
| `MAIL_PORT` | SMTP port; default `587`. |
| `MAIL_USE_TLS` | Enable STARTTLS; default `true`. |
| `MAIL_USE_SSL` | Enable implicit SSL; default `false`. Do not enable both TLS modes. |
| `MAIL_USERNAME` | SMTP login address. |
| `MAIL_PASSWORD` | Private SMTP password. |
| `MAIL_DEFAULT_SENDER` | Authorized outgoing sender address. |
| `MAIL_RECIPIENT` | Inbox receiving website enquiry notifications. |
| `PORTFOLIO_PUBLIC_URL` | Public origin used in canonical URLs, sitemap entries and password-reset links. |
| `PORTFOLIO_HTTPS` | Set to `1` for secure cookies on HTTPS hosting; use `0` on HTTP localhost. |
| `PORTFOLIO_SECRET_KEY` | Optional persistent application secret of at least 32 characters. |

The public contact and notification inbox is **mbuvi@cm.co.ke**. Set `PORTFOLIO_PUBLIC_URL=http://127.0.0.1:7000` when testing local password-reset links; use your HTTPS domain in production.

### Website messages and email

1. The contact form validates the submission and saves the enquiry to MySQL.
2. The app attempts to email `MAIL_RECIPIENT` using the configured sender and SMTP credentials.
3. The visitor's address is set as **Reply-To**.
4. The enquiry records whether its notification was sent or failed. Failed notifications can be retried from the dashboard without losing the original enquiry.

Dashboard replies use the original enquiry's recipient address and retain sent/failed delivery history. A failed SMTP request is never reported as a successful email delivery. Automated tests mock email delivery rather than sending messages.

## Dashboard guide

| Area | URL |
| --- | --- |
| Overview and daily chart | `/dashboard` |
| Case studies | `/dashboard/content/case` |
| Services | `/dashboard/content/service` |
| Blog posts | `/dashboard/content/post` |
| Testimonials | `/dashboard/content/testimonial` |
| Public CV | `/dashboard/cv` |
| Enquiries | `/dashboard/enquiries` |
| Reply history | `/dashboard/replies` |
| Engagement analytics | `/dashboard/conversions` |
| Visit logs | `/dashboard/user/logs` |
| Administrator activity | `/dashboard/logs` |
| Account security and sessions | `/dashboard/security` |

For a case study, use the existing numeric project ID as its slug. Add the missing project details, then publish. Galleries accept up to six PNG, JPEG or WebP screenshots, each up to 2 MB. CV uploads must be PDFs; the application-wide request limit is 12 MB.

Testimonials require a real author, permission confirmation and a permission note before publishing. Blog and service bodies are displayed as escaped plain text with line breaks.

### Administrator access

Existing active administrators can sign in with their existing passwords. Public account registration is disabled. A signed-in administrator can create another account through **Account security → Create administrator**.

For a completely new database with no administrator, open the application shell and create the first account interactively:

```bash
flask --app app shell
```

```python
from getpass import getpass
from models.adminModel import AdminClass

password = getpass("Initial password (12–200 characters): ")
assert 12 <= len(password) <= 200
created = AdminClass().register_admin(
    "Daniel", "Mulatya", "", "your-admin@example.com", "", password, 1
)
assert created, "Administrator creation failed"
del password
```

The model hashes the password before storing it. Replace the example email with the intended administrator login; no password email is sent.

### Two-factor authentication and sessions

Open **Account security**, confirm your password, add the setup key to an authenticator app and enter a current code. Setup expires after five minutes. Save the eight one-use recovery codes when shown; they are not displayed again.

Authenticator secrets are encrypted. Disabling 2FA or generating new recovery codes requires your password and an unused factor code. Sessions expire after two hours and can be revoked individually or in bulk. Password resets expire after 30 minutes, are single use and revoke existing sessions.

Legacy plaintext passwords are rehashed on successful login. To upgrade all legacy password records while preserving their actual passwords:

```bash
flask --app app harden-passwords
```

## Analytics definitions

- **Page view:** a successful public-page GET request. Admin pages, static files, HEAD requests, redirects, form POSTs and error responses are excluded.
- **Unique IPs:** distinct stored IP addresses, not a count of people. Shared networks and automated traffic affect these numbers.
- **Engagement:** project views, project-detail link clicks, CV downloads and contact-page/email/phone link clicks. Client-side click tracking requires JavaScript. Repeated events are deduplicated for ten seconds per address and target.
- Reports use **Africa/Nairobi (UTC+03:00)**. Visitor IPs in the engagement store are hashed with the application secret. The original visit-log table retains its existing IP records.

See [DASHBOARD.md](DASHBOARD.md) for chart, log and PWA details.

## Storage and backups

| Location | Contents |
| --- | --- |
| MySQL | Original portfolio records, administrators, CV records, incoming enquiries and visit logs. |
| `instance/portfolio.sqlite3` | New content, case-study metadata, enquiry workflow, replies, notification delivery state, engagement and security state. |
| `instance/.secret_key` | Generated application secret when no environment override is supplied. |
| `flask_session/` | Server-side session files. |
| `static/projects/gallery/` | Additional case-study screenshots. |
| `static/resume/` | CV PDFs. |
| `static/about/`, `static/admin/`, `static/projects/` | Existing uploaded images. |

Back up the MySQL database, uploads, SQLite store and matching application secret. Losing or changing the secret makes stored authenticator secrets unreadable. Use SQLite's backup API for a consistent live backup, rather than copying only its main file while WAL writes are active.

The SQLite extension store uses WAL and expects application workers on one host with shared storage. A multi-host deployment needs a shared database implementation for this extension data.

## Tests

```bash
.venv/bin/python -B -m unittest discover -s tests -v
node tests/test_service_worker.cjs
node --check static/js/engagement.js
```

The current suite contains **40 Python tests**, plus service-worker checks. Coverage includes publishing, consent rules, filters, uploads, enquiry workflow, email failure/retry, analytics, SEO, CSRF, authentication, rate limits, password migration, TOTP/recovery codes, password-reset expiry and session revocation. Tests use isolated extension stores and mock MySQL/mail where needed.

## Brand assets and PWA

The shared logo source is `static/brand/daniel-monogram.svg`; the standalone wordmark is `static/brand/daniel-wordmark.svg`. PWA icons, the favicon and the sharing image are derived from these brand assets.

To rebuild the raster assets with `sharp` available:

```bash
node scripts/build-brand-icons.cjs
```

Alternatively set `SHARP_MODULE` to the installed `sharp` module path. The worker is served at `/service-worker.js`, covers the website root, precaches branding and an offline page, and does not cache dashboard pages.

## Project layout

```text
app.py                 Flask configuration, application wiring and CLI commands
config/                MySQL connection lifecycle
routes/                Public, dashboard and feature routes
controllers/           Original portfolio controllers
models/                Original MySQL models
services/              Security, content storage, analytics, notifications and uploads
templates/             Public and dashboard Jinja templates
static/                CSS, JavaScript, branding, PWA assets and uploads
tests/                 Python regression tests and service-worker checks
scripts/               Brand-asset build script
mbuvi_update/          Original redesign reference and standalone preview
.env.example           Environment configuration template
FEATURES.md            Detailed feature behavior and operating notes
DASHBOARD.md           Traffic tracking, dashboard and PWA notes
```

For deployment behavior and the full feature workflows, see [FEATURES.md](FEATURES.md).
