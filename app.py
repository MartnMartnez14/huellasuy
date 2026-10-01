"""HuellasUY: same-origin temporary animal reports."""
import hashlib
import hmac
import math
import secrets
import time
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

from config import Config
from database import cleanup, connect, initialize

ANIMALS = {'dog', 'cat', 'other'}
STATUSES = {'lost', 'seen', 'found', 'abandoned'}
COLORS = ['#FFD6A5', '#CAFFBF', '#A0C4FF', '#BDB2FF', '#FFC6FF']


def public_report(row):
    data = {k: row[k] for k in ('id', 'title', 'description', 'animal_type',
                               'status_type', 'latitude', 'longitude')}
    for k in ('created_at', 'expires_at'):
        data[k] = datetime.fromtimestamp(row[k], timezone.utc).isoformat()
    data['pastel_color'] = COLORS[row['id'] % len(COLORS)]
    return data


def validate(data, max_title=80, max_description=500):
    if not isinstance(data, dict):
        raise ValueError('Enviá un formulario válido.')
    result = {}
    for field, limit in [('title', max_title), ('description', max_description)]:
        value = data.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > limit:
            raise ValueError(f'{"Título" if field == "title" else "Descripción"}: entre 1 y {limit} caracteres.')
        if '<' in value or '>' in value or any(ord(c) < 32 and c not in '\n\t' for c in value):
            raise ValueError('Usá texto simple, sin etiquetas HTML.')
        result[field] = value.strip()
    for field, allowed, default in [('animal_type', ANIMALS, 'other'), ('status_type', STATUSES, 'seen')]:
        value = data.get(field, default)
        if not isinstance(value, str) or value not in allowed:
            raise ValueError('Elegí una categoría válida.')
        result[field] = value
    for field, limit in [('latitude', 90), ('longitude', 180)]:
        value = data.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
            raise ValueError('Seleccioná una ubicación válida en el mapa.')
        result[field] = round(value, 3)
    return result


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    app.config.setdefault('CLOCK', time.time)
    # Persistent secret prevents rate-limit identity changing on restart.
    if not app.config['SECRET_KEY']:
        from pathlib import Path
        path = Path(app.config['DATABASE_PATH']).parent / '.secret'
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open('x') as file:
                file.write(secrets.token_hex(32))
            path.chmod(0o600)
        except FileExistsError:
            pass
        app.config['SECRET_KEY'] = path.read_text().strip()
    initialize(app.config['DATABASE_PATH'])
    with connect(app.config['DATABASE_PATH']) as db:
        cleanup(db, app.config['CLOCK']())

    @app.before_request
    def check_write():
        if request.path.startswith('/api/') and request.method in {'POST', 'DELETE'}:
            if not request.is_json:
                return jsonify(error='Enviá datos en formato JSON.'), 415
            origin = request.headers.get('Origin')
            expected = app.config['PUBLIC_ORIGIN'] or request.host_url.rstrip('/')
            if origin and origin != expected:
                return jsonify(error='Origen no permitido.'), 403
            if request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return jsonify(error='Origen no permitido.'), 403

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(self), camera=(), microphone=()'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' https://unpkg.com; style-src 'self' 'unsafe-inline' https://unpkg.com; img-src 'self' data: https://tile.openstreetmap.org https://unpkg.com; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
        if request.path.startswith('/api/'):
            response.headers['Cache-Control'] = 'no-store'
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api/'):
            return jsonify(error='No pudimos procesar la solicitud.'), error.code
        return error

    @app.get('/')
    @app.get('/r/<int:report_id>')
    @app.get('/manage/<int:report_id>')
    def home(report_id=None):
        return render_template('index.html')

    @app.get('/<page>')
    def info(page):
        if page not in {'about', 'privacy', 'help'}:
            return 'Página no encontrada', 404
        return render_template('info.html', page=page)

    @app.get('/health')
    def health():
        with connect(app.config['DATABASE_PATH']) as db:
            db.execute('SELECT 1')
        return jsonify(status='ok')

    @app.get('/api/reports')
    @app.get('/api/reports/<int:report_id>')
    def reports(report_id=None):
        now = app.config['CLOCK']()
        with connect(app.config['DATABASE_PATH']) as db:
            cleanup(db, now)
            if report_id is not None:
                row = db.execute('SELECT * FROM reports WHERE id=? AND expires_at>?', (report_id, now)).fetchone()
                if not row:
                    return jsonify(error='Esta alerta ya expiró o fue eliminada.'), 404
                return jsonify(report=public_report(row), server_time=now)
            query = 'SELECT * FROM reports WHERE expires_at>?'
            params = [now]
            for field, allowed in [('animal_type', ANIMALS), ('status_type', STATUSES)]:
                value = request.args.get(field)
                if value:
                    if value not in allowed:
                        return jsonify(error='Filtro inválido.'), 400
                    query += f' AND {field}=?'
                    params.append(value)
            rows = db.execute(query + ' ORDER BY created_at DESC', params).fetchall()
        return jsonify(reports=[public_report(row) for row in rows], server_time=now)

    @app.post('/api/reports')
    def publish():
        try:
            data = validate(request.get_json(), app.config['MAX_TITLE_LENGTH'], app.config['MAX_DESCRIPTION_LENGTH'])
        except ValueError as error:
            return jsonify(error=str(error)), 400
        now = app.config['CLOCK']()
        fingerprint = hmac.new(app.config['SECRET_KEY'].encode(), (request.remote_addr or 'unknown').encode(), hashlib.sha256).hexdigest()
        token = secrets.token_urlsafe(32)
        with connect(app.config['DATABASE_PATH']) as db:
            db.execute('BEGIN IMMEDIATE')
            cleanup(db, now)
            count = db.execute('SELECT COUNT(*) FROM rate_limits WHERE fingerprint=?', (fingerprint,)).fetchone()[0]
            if count >= 5:
                return jsonify(error='Llegaste a 5 alertas por hora. Intentá más tarde.'), 429
            db.execute('INSERT INTO rate_limits VALUES (?, ?)', (fingerprint, now))
            values = [data[k] for k in ('title', 'description', 'animal_type', 'status_type', 'latitude', 'longitude')]
            cursor = db.execute('INSERT INTO reports (title,description,animal_type,status_type,latitude,longitude,created_at,expires_at,delete_token_hash) VALUES (?,?,?,?,?,?,?,?,?)', values + [now, now + app.config['REPORT_TTL_HOURS'] * 3600, hashlib.sha256(token.encode()).hexdigest()])
            row = db.execute('SELECT * FROM reports WHERE id=?', (cursor.lastrowid,)).fetchone()
        return jsonify(report=public_report(row), delete_token=token, server_time=now), 201

    @app.delete('/api/reports/<int:report_id>')
    def remove(report_id):
        data = request.get_json()
        token = data.get('delete_token') if isinstance(data, dict) else None
        if not isinstance(token, str) or len(token) > 128:
            return jsonify(error='Enlace privado inválido.'), 403
        with connect(app.config['DATABASE_PATH']) as db:
            cleanup(db, app.config['CLOCK']())
            row = db.execute('SELECT delete_token_hash FROM reports WHERE id=?', (report_id,)).fetchone()
            if not row:
                return jsonify(error='Esta alerta ya expiró o fue eliminada.'), 404
            if not hmac.compare_digest(row[0], hashlib.sha256(token.encode()).hexdigest()):
                return jsonify(error='Enlace privado inválido.'), 403
            db.execute('DELETE FROM reports WHERE id=?', (report_id,))
        return '', 204

    @app.cli.command('cleanup')
    def cleanup_command():
        with connect(app.config['DATABASE_PATH']) as db:
            cleanup(db, app.config['CLOCK']())
        print('Limpieza completada.')

    return app


if __name__ == '__main__':
    create_app().run(host='127.0.0.1', port=5000, debug=False)
