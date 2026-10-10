"""Optional verified accounts; secrets and credentials never enter public responses."""
import hashlib
import hmac
import json
import re
import secrets
import urllib.request
from pathlib import Path
from flask import Blueprint, current_app, g, jsonify, render_template, request
from werkzeug.security import generate_password_hash, check_password_hash
from database import connect

bp = Blueprint('auth', __name__)
EMOJIS = ('🐶', '🐱', '🐰', '🦊', '🐼', '🐸', '🦋', '🐢')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL, emoji TEXT NOT NULL, verified INTEGER NOT NULL DEFAULT 0,
 disabled INTEGER NOT NULL DEFAULT 0, created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS account_tokens (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, purpose TEXT NOT NULL, expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS account_sessions (
 token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS auth_attempts (fingerprint TEXT NOT NULL, created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS auth_attempt_time ON auth_attempts(created_at);
'''

def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()

def now():
    return current_app.config['CLOCK']()

def admin(user):
    return bool(user and user['verified'] and user['email'] == current_app.config.get('ADMIN_EMAIL', '').lower())

def identity(user):
    return dict(id=user['id'], username=user['username'], emoji=user['emoji'], administrator=admin(user))

def install(app):
    with connect(app.config['DATABASE_PATH']) as db:
        db.executescript(SCHEMA)
    app.register_blueprint(bp)

    @app.before_request
    def load_account():
        g.user = None
        if not app.config['AUTH_ENABLED']:
            return
        token = request.cookies.get('huellas_session', '')
        if token and len(token) < 128:
            with connect(app.config['DATABASE_PATH']) as db:
                g.user = db.execute('SELECT u.* FROM users u JOIN account_sessions s ON s.user_id=u.id WHERE s.token_hash=? AND s.expires_at>? AND u.verified=1 AND u.disabled=0', (digest(token), now())).fetchone()
        if request.path.startswith('/api/auth/') and request.method == 'POST':
            if not request.is_json:
                return jsonify(error='Enviá JSON.'), 415
            expected = app.config['PUBLIC_ORIGIN'] or request.host_url.rstrip('/')
            if request.headers.get('Origin') != expected or request.headers.get('Sec-Fetch-Site') == 'cross-site':
                return jsonify(error='Origen no permitido.'), 403
            data = request.get_json(silent=True)
            if not isinstance(data, dict):
                return jsonify(error='Formulario inválido.'), 400
            if request.endpoint not in {'auth.logout', 'auth.admin_remove', 'auth.admin_suspend'}:
                fp = hmac.new(app.config['SECRET_KEY'].encode(), ('auth:' + (request.remote_addr or 'unknown')).encode(), hashlib.sha256).hexdigest()
                with connect(app.config['DATABASE_PATH']) as db:
                    db.execute('BEGIN IMMEDIATE')
                    db.execute('DELETE FROM auth_attempts WHERE created_at<=?', (now()-3600,))
                    db.execute('DELETE FROM account_tokens WHERE expires_at<=?', (now(),))
                    db.execute('DELETE FROM account_sessions WHERE expires_at<=?', (now(),))
                    if db.execute('SELECT COUNT(*) FROM auth_attempts WHERE fingerprint=?', (fp,)).fetchone()[0] >= 20:
                        return jsonify(error='Demasiados intentos. Volvé en una hora.'), 429
                    db.execute('INSERT INTO auth_attempts VALUES (?,?)', (fp, now()))

    @app.context_processor
    def account_context():
        return dict(account=g.get('user'), account_admin=admin(g.get('user')), accounts_enabled=app.config['AUTH_ENABLED'])


def send_link(user, purpose):
    origin = current_app.config.get('PUBLIC_ORIGIN')
    if not origin:
        raise RuntimeError('PUBLIC_ORIGIN requerido para correo')
    token = secrets.token_urlsafe(32)
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('INSERT INTO account_tokens VALUES (?,?,?,?)', (digest(token), user['id'], purpose, now() + (86400 if purpose=='verify' else 1800)))
    link = f'{origin}/account#{purpose}={token}'
    try:
        hook = current_app.config.get('MAIL_SENDER')
        if hook:
            hook(user['email'], purpose, link)
            return
        config = json.loads(Path(current_app.config['BREVO_CONFIG_PATH']).read_text())
        payload = dict(
            sender=dict(name=config['sender_name'], email=config['sender_email']),
            to=[dict(email=user['email'])],
            subject='HuellasUY — ' + ('Verificá tu cuenta' if purpose=='verify' else 'Recuperá tu contraseña'),
            textContent=f'Para continuar en HuellasUY, copiá este enlace completo en tu navegador:\n\n{link}\n\nSi no lo solicitaste, ignorá este correo.'
        )
        req = urllib.request.Request('https://api.brevo.com/v3/smtp/email', data=json.dumps(payload).encode(), headers={'api-key':config['api_key'], 'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=15) as response:
            response.read()
    except Exception:
        with connect(current_app.config['DATABASE_PATH']) as db:
            db.execute('DELETE FROM account_tokens WHERE token_hash=?', (digest(token),))
        raise

@bp.before_request
def enabled():
    if not current_app.config['AUTH_ENABLED']:
        return jsonify(error='Cuentas todavía no habilitadas.'), 404

@bp.get('/account')
def page():
    return render_template('account.html')

@bp.get('/api/auth/me')
def me():
    return jsonify(user=identity(g.user) if g.user else None)

@bp.post('/api/auth/register')
def register():
    data=request.get_json()
    username=data.get('username', '')
    email=data.get('email', '')
    password=data.get('password', '')
    if not isinstance(username,str) or not re.fullmatch(r'[a-zA-Z0-9_]{3,30}',username) or not isinstance(email,str) or len(email)>254 or not re.fullmatch(r'[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+',email) or not isinstance(password,str) or not 12<=len(password)<=128:
        return jsonify(error='Usuario: 3–30 letras, números o _. Correo válido. Contraseña: 12–128 caracteres.'),400
    username=username.lower(); email=email.lower()
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM users WHERE username=? OR email=?',(username,email)).fetchone():
            return jsonify(error='No se pudo registrar. Probá otro usuario o recuperá tu cuenta.'),400
        cursor=db.execute('INSERT INTO users(username,email,password_hash,emoji,created_at) VALUES (?,?,?,?,?)',(username,email,generate_password_hash(password),secrets.choice(EMOJIS),now()))
        user=db.execute('SELECT * FROM users WHERE id=?',(cursor.lastrowid,)).fetchone()
    try:
        send_link(user,'verify')
    except Exception:
        return jsonify(error='Cuenta pendiente. No pudimos enviar el correo; usá Reenviar verificación más tarde.'),503
    return jsonify(message='Revisá tu correo para verificar la cuenta.'),201

@bp.post('/api/auth/login')
def login():
    data=request.get_json(); username=data.get('username'); password=data.get('password')
    if not isinstance(username,str) or not isinstance(password,str) or len(username)>254 or len(password)>128:
        return jsonify(error='Credenciales inválidas.'),400
    with connect(current_app.config['DATABASE_PATH']) as db:
        user=db.execute('SELECT * FROM users WHERE username=? OR email=?',(username.lower(),username.lower())).fetchone()
        valid=check_password_hash(user['password_hash'] if user else current_app.config['DUMMY_PASSWORD_HASH'],password)
        if not user or not valid or user['disabled'] or not user['verified']:
            return jsonify(error='No pudimos entrar. Revisá tus datos y verificá tu correo.'),401
        token=secrets.token_urlsafe(32)
        db.execute('INSERT INTO account_sessions VALUES (?,?,?)',(digest(token),user['id'],now()+604800))
    response=jsonify(user=identity(user))
    response.set_cookie('huellas_session',token,max_age=604800,httponly=True,secure=current_app.config['SESSION_COOKIE_SECURE'],samesite='Lax',path='/')
    return response

@bp.post('/api/auth/logout')
def logout():
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('DELETE FROM account_sessions WHERE token_hash=?',(digest(request.cookies.get('huellas_session','')),))
    response=jsonify(message='Sesión cerrada.'); response.delete_cookie('huellas_session',path='/'); return response

@bp.post('/api/auth/verify')
@bp.post('/api/auth/reset')
def redeem():
    data=request.get_json(); token=data.get('token'); purpose='verify' if request.path.endswith('/verify') else 'reset'
    if not isinstance(token,str) or len(token)>128:
        return jsonify(error='Enlace inválido.'),400
    password=data.get('password')
    if purpose=='reset' and (not isinstance(password,str) or not 12<=len(password)<=128):
        return jsonify(error='Contraseña: 12–128 caracteres.'),400
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT t.* FROM account_tokens t JOIN users u ON u.id=t.user_id WHERE t.token_hash=? AND t.purpose=? AND t.expires_at>? AND u.disabled=0',(digest(token),purpose,now())).fetchone()
        if not row:
            return jsonify(error='Enlace inválido, vencido o ya usado.'),400
        if purpose=='verify':
            db.execute('UPDATE users SET verified=1 WHERE id=?',(row['user_id'],))
        else:
            db.execute('UPDATE users SET password_hash=? WHERE id=?',(generate_password_hash(password),row['user_id']))
            db.execute('DELETE FROM account_sessions WHERE user_id=?',(row['user_id'],))
        db.execute('DELETE FROM account_tokens WHERE user_id=? AND purpose=?',(row['user_id'],purpose))
    return jsonify(message='Cuenta verificada. Ya podés entrar.' if purpose=='verify' else 'Contraseña cambiada. Iniciá sesión nuevamente.')

@bp.post('/api/auth/forgot')
@bp.post('/api/auth/resend')
def resend():
    email=request.get_json().get('email')
    if not isinstance(email,str) or len(email)>254:
        return jsonify(error='Correo inválido.'),400
    purpose='reset' if request.path.endswith('/forgot') else 'verify'
    with connect(current_app.config['DATABASE_PATH']) as db:
        user=db.execute('SELECT * FROM users WHERE email=? AND disabled=0',(email.lower(),)).fetchone()
    if user and (purpose=='reset' and user['verified'] or purpose=='verify' and not user['verified']):
        try:
            send_link(user,purpose)
        except Exception:
            pass
    return jsonify(message='Si corresponde, recibirás un enlace. Si no llega, esperá y reintentá.')

@bp.get('/admin')
def dashboard():
    if not admin(g.user):
        return 'Acceso restringido', 403
    with connect(current_app.config['DATABASE_PATH']) as db:
        users=db.execute('SELECT id,username,emoji,disabled FROM users ORDER BY id DESC LIMIT 100').fetchall()
        reports=db.execute('SELECT r.id,r.title,r.description,u.username AS author_name,u.emoji AS author_emoji FROM reports r LEFT JOIN users u ON u.id=r.author_id WHERE r.expires_at>? ORDER BY r.id DESC LIMIT 100',(now(),)).fetchall()
    return render_template('admin.html', users=users, reports=reports)

@bp.post('/api/auth/admin/remove')
def admin_remove():
    if not admin(g.user):
        return jsonify(error='Acceso restringido.'),403
    report_id=request.get_json().get('report_id')
    if type(report_id) is not int:
        return jsonify(error='Reporte inválido.'),400
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('DELETE FROM reports WHERE id=?',(report_id,))
    return jsonify(message='Alerta retirada.')

@bp.post('/api/auth/admin/suspend')
def admin_suspend():
    if not admin(g.user):
        return jsonify(error='Acceso restringido.'),403
    user_id=request.get_json().get('user_id'); disabled=request.get_json().get('disabled')
    if type(user_id) is not int or type(disabled) is not bool or user_id==g.user['id']:
        return jsonify(error='Usuario o acción inválidos; no podés suspenderte.'),400
    with connect(current_app.config['DATABASE_PATH']) as db:
        db.execute('UPDATE users SET disabled=? WHERE id=?',(int(disabled),user_id))
        db.execute('DELETE FROM account_sessions WHERE user_id=?',(user_id,))
        db.execute('DELETE FROM account_tokens WHERE user_id=?',(user_id,))
    return jsonify(message='Cuenta suspendida.' if disabled else 'Cuenta rehabilitada.')
