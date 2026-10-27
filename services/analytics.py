"""Daily traffic reports over the existing user_log table."""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from config.database import Database

NAIROBI = ZoneInfo('Africa/Nairobi')


def local_today():
    return datetime.now(NAIROBI).date()


class Analytics:
    def __init__(self):
        self.connection = Database().get_connection()

    def dashboard(self, days=30):
        today = local_today()
        start = today - timedelta(days=days - 1)
        end = today + timedelta(days=1)
        with self.connection.cursor() as cursor:
            cursor.execute('''SELECT COUNT(*), COUNT(DISTINCT user_ip),
                COALESCE(SUM(logDate >= %s), 0),
                COUNT(DISTINCT CASE WHEN logDate >= %s THEN user_ip END),
                COALESCE(SUM(logDate >= %s AND logDate < %s), 0)
                FROM user_log WHERE logDate >= %s AND logDate < %s''',
                (today, today, today - timedelta(days=1), today, start, end))
            total, unique, views_today, unique_today, yesterday = cursor.fetchone()
            cursor.execute('''SELECT DATE(logDate), COUNT(*), COUNT(DISTINCT user_ip)
                FROM user_log WHERE logDate >= %s AND logDate < %s
                GROUP BY DATE(logDate) ORDER BY DATE(logDate)''', (start, end))
            by_date = {row[0]: row[1:] for row in cursor.fetchall()}
            daily = []
            for offset in range(days):
                day = start + timedelta(days=offset)
                views, ips = by_date.get(day, (0, 0))
                daily.append(dict(date=day, views=views, unique=ips))
            cursor.execute('''SELECT page, COUNT(*) FROM user_log
                WHERE logDate >= %s AND logDate < %s
                GROUP BY page ORDER BY COUNT(*) DESC, page LIMIT 6''', (start, end))
            top_pages = cursor.fetchall()
            cursor.execute('SELECT id, user_ip, page, logDate FROM user_log ORDER BY logDate DESC, id DESC LIMIT 8')
            recent = cursor.fetchall()
        peak = max((row['views'] for row in daily), default=0)
        return dict(days=days, start=start, today=today, total=total, unique=unique,
                    views_today=views_today, unique_today=unique_today, yesterday=yesterday,
                    change=views_today-yesterday, daily=daily, peak=peak, top_pages=top_pages, recent=recent)

    def logs(self, start, end, search='', page=1, per_page=50):
        clauses, params = [], []
        if start:
            clauses.append('logDate >= %s')
            params.append(start)
        if end:
            clauses.append('logDate < %s')
            params.append(end + timedelta(days=1))
        if search:
            clauses.append('(LOCATE(%s, page) > 0 OR LOCATE(%s, user_ip) > 0)')
            params.extend((search, search))
        where = ' WHERE ' + ' AND '.join(clauses) if clauses else ''
        with self.connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM user_log' + where, tuple(params))
            total = cursor.fetchone()[0]
            pages = max(1, (total + per_page - 1) // per_page)
            page = min(page, pages)
            cursor.execute('SELECT id, user_ip, page, logDate FROM user_log' + where +
                           ' ORDER BY logDate DESC, id DESC LIMIT %s OFFSET %s',
                           tuple(params) + (per_page, (page - 1) * per_page))
            rows = cursor.fetchall()
        return dict(rows=rows, total=total, page=page, pages=pages)


def init_app(app):
    @app.after_request
    def record_page_view(response):
        from flask import request
        if request.blueprint == 'home_bp' and request.method == 'GET' and response.status_code == 200:
            try:
                from controllers.contactController import contact_model
                # remote_addr is the socket peer; trust forwarded headers only via a configured proxy.
                contact_model.save_log(request.remote_addr or 'unknown', request.path)
            except Exception:
                app.logger.exception('Could not record public page view')
        return response
