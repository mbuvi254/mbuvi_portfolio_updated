# Portfolio features and operations

## Public website

- **Case studies:** open Dashboard → Case studies. Set the slug to an existing project ID (shown in the Projects table). The initializer creates draft entries for existing projects using their real titles and descriptions. Add your role, the problem, approach, verifiable results/lessons, technology tags, industry and project type. Upload up to six screenshots. Publish when ready. Unpublishing leaves the original project visible but hides the additional case study.
- **Services:** `/services` contains three editable starting entries based on the existing portfolio: web applications, workflow software and data analytics. They have no invented prices or client claims. Edit, unpublish or add services in the dashboard.
- **Blog:** `/blog` lists only published notes, with topic and text search. Articles have stable slugs, summaries and sharing metadata. Drafts return 404 publicly. Bodies are plain text, escaped and displayed with line breaks; HTML is not executed.
- **Testimonials:** `/testimonials` and the home page display published feedback only when permission is recorded. Enter the real author, company/role if relevant, and a private permission note. No testimonials or client outcomes are fabricated or seeded.
- **Projects:** text search, technologies, industries and project types use published case-study metadata. The existing category buttons remain available.
- **CV:** Dashboard → Public CV uploads PDF versions and selects the public version. `/resume/download` serves the selected file as an attachment and tracks successful downloads; `/resume/view` previews it without adding a download event. If no version has been selected, the latest upload is used.
- **SEO:** public pages have canonical URLs, descriptions, Open Graph metadata, sharing images and structured data. Project detail pages use their own screenshot and description; blog posts have article metadata. `/robots.txt` and `/sitemap.xml` cover public routes and published posts. The dashboard is excluded and marked noindex.

## Enquiries and analytics

Dashboard → Enquiries has `new`, `in_progress` and `resolved` states, private notes and per-message replies. Incoming messages are saved before attempting email notification. SMTP failures do not erase received enquiries. Replies are saved as pending, then marked sent or failed; failed messages are never presented as delivered. Reply recipients come from the original enquiry, rather than a submitted recipient field. No test messages are sent by the automated tests.

Engagement analytics counts project-page views, links to project details, CV downloads and contact-page/email/phone link clicks. Client-side link counts require JavaScript. Events are deduplicated for ten seconds per address and target; addresses are hashed with the application secret in this store. Automated requests can be counted. Daily traffic and visit logs continue to use the existing MySQL `user_log` table.

## Administrator security

All dashboard management routes now require a valid, active, revocable login session. State-changing forms require CSRF tokens. Deletions, activation and logout use POST. Public account registration is disabled; a signed-in administrator can create an additional administrator via Account security. Passwords are never emailed by the new flow.

Existing legacy passwords remain usable and are rehashed on successful sign-in. To hash all existing passwords immediately, preserving the actual passwords, run:

```
.venv/bin/flask --app app harden-passwords
```

New passwords use Werkzeug's password hashing. Login attempts are limited to five per address/account bucket in fifteen minutes. Reset requests and verification attempts are also throttled. A reset link is random, expires in thirty minutes, is single use, and revokes existing sessions. Accounts with two-factor authentication must also provide a valid factor when resetting a password.

**Enable two-factor authentication individually:** Dashboard → Account security → confirm your password → enter the setup key in an authenticator app → enter a current six-digit code. The setup expires after five minutes. Save the eight one-use recovery codes when displayed; only their hashes are retained. Authenticator secrets are encrypted with Fernet using a key derived from the application's private secret. Codes cannot be replayed. Disabling two-factor authentication or regenerating recovery codes requires both a password and an unused factor code. These features are available but are not silently enabled for existing accounts.

Sessions expire after two hours. Account security lists active sessions and lets you revoke one or all other sessions. Old sessions from before this security change must sign in again. Revoked sessions lose access on their next request.

## Storage and deployment

The legacy portfolio, administrator accounts, CV records and incoming enquiries remain in **MySQL**. New content, case-study metadata, workflow states, replies, engagement events and security state use a private **SQLite extension store** at `instance/portfolio.sqlite3`. This avoids altering the existing MySQL schema or adding permanent MySQL connections. SQLite uses WAL and a busy timeout; this deployment expects workers on one host with a shared writable instance directory. For a multi-host deployment, migrate the extension store to a shared database first.

The app creates and retains `instance/.secret_key` with restricted permissions. Alternatively set a persistent `PORTFOLIO_SECRET_KEY` of at least 32 characters before starting the app. **Back up the secret and extension database together.** Losing or changing the secret makes encrypted authenticator secrets unreadable. Do not commit `instance/`, session files or secrets. For a consistent live backup, use SQLite's backup API rather than copying only its main file while WAL writes are active.

New case-study gallery uploads live in `static/projects/gallery/`; CV files remain in `static/resume/`. Back up these directories and the original MySQL database as well.

Install updated dependencies and initialize the extension store:

```
.venv/bin/pip install -r req.txt
.venv/bin/flask --app app init-features
```

Set these environment values for deployment:

- `PORTFOLIO_PUBLIC_URL`: canonical site origin, e.g. `https://mbuvi.cm.co.ke`. It is also used for password reset email links. Use `http://127.0.0.1:5000` for local reset testing.
- `PORTFOLIO_HTTPS=1`: enable secure cookies on an HTTPS deployment; keep unset on plain-HTTP localhost.
- `PORTFOLIO_SECRET_KEY`: optional alternative to the generated private key file.
- `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`: outgoing mail configuration. The sender should be an address authorized by the mail server.

Upload the changed Python modules, templates, CSS, JavaScript, brand sharing image and `req.txt`, while preserving the private instance directory and uploads. Restart the existing Flask/Passenger process. Visit `/dashboard` to manage the new features. Existing `/admin` links still redirect to `/dashboard`.

## Verification

```
.venv/bin/python -B -m unittest discover -s tests -v
node tests/test_service_worker.cjs
node --check static/js/engagement.js
```

Tests cover publishing and drafts, testimonial consent, project filters and escaped content, enquiry state isolation, email success/failure handling, CV selection/download events, CSRF, unauthorized management routes, login throttling, password hashing/migration, TOTP RFC vectors/replay rejection, recovery-code reuse, session revocation and reset expiry/single use. They use isolated extension databases and mock MySQL/mail where needed.

## Mail configuration

The app loads `.env` with python-dotenv before reading configuration. `.env` is private (mode 0600) and ignored by Git; `.env.example` lists the configuration names without a password. Deployment environment variables override `.env`. SMTP uses authenticated STARTTLS on port 587 by default. Website enquiries are saved to MySQL, then emailed to `MAIL_RECIPIENT` from `MAIL_DEFAULT_SENDER` with the visitor address in Reply-To. Each enquiry records whether its notification was sent or failed. A failed or missing notification can be retried from the enquiry screen without losing the original message. Public contact links use `mbuvi@cm.co.ke`.
