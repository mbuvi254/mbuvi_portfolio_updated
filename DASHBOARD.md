# Dashboard and website traffic

The admin overview at `/dashboard` includes a locally bundled Chart.js line chart for daily page views and daily distinct IP addresses. Select 7, 30, or 90 days. Days without records display as zero. The daily data table exposes the exact chart values. Cards show today's counts, the difference from yesterday, period totals, and message counts. Top pages use the selected period; recent page views show the latest eight records overall.

`/dashboard/user/logs` supports inclusive date filters, page/IP search, and server-side pagination (50 rows). `/dashboard/logs` displays the latest 500 administrator sign-in records with client-side search. All three routes require an active administrator login.

Tracking uses the existing `user_log` table; existing records are preserved. One successful public GET request creates one record after the response is generated. Categories and project details are included. Admin requests, static files, HEAD requests, form POSTs, redirects, and error responses are excluded. Failed logging is reported through the Flask logger without interrupting the public response. New page values use URL paths; older page labels remain searchable.

Reports and new database sessions use Africa/Nairobi (UTC+03:00). `logDate` is a MySQL TIMESTAMP, interpreted in this session timezone. Existing TIMESTAMP values are not rewritten. Daily unique counts use distinct stored IPs. Period unique counts deduplicate over the whole period. These are estimates of addresses, include automated traffic, and do not represent distinct people or browser sessions. Proxies may consolidate addresses; forwarded headers are not trusted automatically.

Deploy the updated `app.py`, `config/database.py`, `routes/`, `models/`, `services/`, admin templates, `static/css/admin.css`, and `static/js/admin-dashboard.js`. Retain the existing bundled `static/dashboard/vendor/chart.js/Chart.min.js` and other admin vendor assets. Restart the Flask/Passenger process so it loads the new tracking hook and routes. No schema changes are needed on the existing database. For a new database, run `flask --app app init-db` once.

For large existing log tables, a database administrator can add an index on `user_log(logDate)` after checking whether an equivalent index already exists. The reports work without it, but date-range searches will become slower as the table grows.

Run regression tests with `.venv/bin/python -B -m unittest discover -s tests -v`. Tests use mocked database connections and do not send email or insert test visits into MySQL.

The public navigation includes a Dashboard link. The admin login is `/dashboard/login`; all management URLs now use `/dashboard`. Legacy `/admin` URLs redirect with HTTP 308, preserving query strings and POST methods. Static uploads remain at `/static/admin/`.

The website and installed app share the Daniel Mbuvi Mulatya monogram. PWA icons include 192px/512px standard and maskable PNGs, a 180px Apple touch icon, and a 32px favicon. The source is `static/brand/daniel-monogram.svg`; rebuild PNGs with `node scripts/build-brand-icons.cjs` using the `sharp` package (or set `SHARP_MODULE` to its installed path). The root `/service-worker.js` precaches branding and an offline page, replaces the old `flask-pwa-*` cache, and never caches dashboard pages. The old `static/img/cm.png` asset has been removed.
