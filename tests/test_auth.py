import sqlite3
from urllib.parse import urlsplit, parse_qs
import pytest
from app import create_app

@pytest.fixture
def env(tmp_path):
    mail=[]; clock=[1700000000.]
    cfg=dict(TESTING=True,AUTH_ENABLED=True,SESSION_COOKIE_SECURE=False,SECRET_KEY='test',DATABASE_PATH=str(tmp_path/'db.sqlite'),PUBLIC_ORIGIN='http://localhost',ADMIN_EMAIL='owner@example.org',CLOCK=lambda:clock[0],MAIL_SENDER=lambda email,purpose,link:mail.append((email,purpose,link)))
    app=create_app(cfg)
    return app,app.test_client(),mail,clock,cfg

def post(client,action,data):
    return client.post('/api/auth/'+action,json=data,headers={'Origin':'http://localhost'})

def register(client,email='user@example.org',username='user'):
    return post(client,'register',dict(username=username,email=email,password='long password123'))

def token(mail):
    return next(iter(parse_qs(urlsplit(mail[-1][2]).fragment).values()))[0]

def verified(client,mail,email='user@example.org',username='user'):
    assert register(client,email,username).status_code==201
    assert post(client,'verify',dict(token=token(mail))).status_code==200
    assert post(client,'login',dict(username=username,password='long password123')).status_code==200

def test_verification_login_logout_and_private_storage(env):
    app,c,mail,clock,cfg=env
    assert register(c).status_code==201
    assert post(c,'login',dict(username='user',password='long password123')).status_code==401
    t=token(mail)
    assert post(c,'verify',dict(token=t)).status_code==200
    assert post(c,'verify',dict(token=t)).status_code==400
    login=post(c,'login',dict(username='user',password='long password123'))
    assert login.status_code==200
    assert 'HttpOnly' in login.headers['Set-Cookie'] and 'SameSite=Lax' in login.headers['Set-Cookie']
    assert set(c.get('/api/auth/me').json['user'])=={'id','username','emoji','administrator'}
    with sqlite3.connect(cfg['DATABASE_PATH']) as db:
        password=db.execute('SELECT password_hash FROM users').fetchone()[0]
        assert password!='long password123'
    assert post(c,'logout',{}).status_code==200
    assert c.get('/api/auth/me').json['user'] is None

def test_server_gating_and_origin(env):
    app,c,mail,clock,cfg=env
    assert c.get('/api/reports').status_code==401
    assert c.get('/api/reports/1').status_code==401
    home=c.get('/').text
    assert 'map-preview' in home and '/static/js/app.js' not in home
    assert c.post('/api/auth/register',json={}).status_code==403
    assert c.post('/api/auth/register',json={},headers={'Origin':'https://evil.example'}).status_code==403
    assert post(c,'register',[]).status_code==400
    verified(c,mail)
    assert c.get('/api/reports').status_code==200
    assert c.post('/api/reports',json={}).status_code==403

def test_reset_revokes_sessions_and_expires(env):
    app,c,mail,clock,cfg=env
    verified(c,mail)
    assert post(c,'forgot',{'email':'user@example.org'}).status_code==200
    t=token(mail)
    clock[0]+=1800
    assert post(c,'reset',dict(token=t,password='new password123')).status_code==400
    post(c,'forgot',{'email':'user@example.org'})
    t=token(mail)
    assert post(c,'reset',dict(token=t,password='new password123')).status_code==200
    assert c.get('/api/auth/me').json['user'] is None
    assert post(c,'reset',dict(token=t,password='new password123')).status_code==400
    assert post(c,'login',dict(username='user',password='new password123')).status_code==200
    clock[0]+=604800
    assert c.get('/api/auth/me').json['user'] is None

def test_admin_only_verified_email_and_suspension(env):
    app,c,mail,clock,cfg=env
    verified(c,mail)
    assert c.get('/admin').status_code==403
    assert post(c,'admin/suspend',{'user_id':1,'disabled':True}).status_code==403
    owner=app.test_client(); verified(owner,mail,'owner@example.org','owner')
    assert owner.get('/api/auth/me').json['user']['administrator'] is True
    assert owner.get('/admin').status_code==200
    assert post(owner,'admin/suspend',{'user_id':1,'disabled':True}).status_code==200
    assert c.get('/api/reports').status_code==401
    assert post(c,'login',dict(username='user',password='long password123')).status_code==401
    assert post(owner,'admin/suspend',{'user_id':2,'disabled':True}).status_code==400

def test_mail_failure_resend_and_limits(env):
    app,c,mail,clock,cfg=env
    app.config['MAIL_SENDER']=lambda *args: (_ for _ in ()).throw(RuntimeError('mail unavailable'))
    assert register(c).status_code==503
    app.config['MAIL_SENDER']=cfg['MAIL_SENDER']
    assert post(c,'resend',{'email':'user@example.org'}).status_code==200
    assert mail
    for _ in range(18): post(c,'forgot',{'email':'missing@example.org'})
    assert post(c,'forgot',{'email':'missing@example.org'}).status_code==429
    clock[0]+=3600
    assert post(c,'forgot',{'email':'missing@example.org'}).status_code==200

def test_migration_preserves_old_reports_and_verify_expiration(env):
    app,c,mail,clock,cfg=env
    register(c)
    t=token(mail); clock[0]+=86400
    assert post(c,'verify',dict(token=t)).status_code==400
    post(c,'resend',{'email':'user@example.org'})
    assert post(c,'verify',dict(token=token(mail))).status_code==200
    assert post(c,'login',dict(username='user',password='long password123')).status_code==200
    from tests.test_app import payload
    response=c.post('/api/reports',json=payload(),headers={'Origin':'http://localhost'})
    assert response.status_code==201
    with sqlite3.connect(cfg['DATABASE_PATH']) as db:
        assert db.execute('SELECT author_id FROM reports').fetchone()[0]==1
    assert create_app(cfg).test_client().get('/api/reports').status_code==401


def test_secure_cookie(env):
    app,c,mail,clock,cfg=env
    verified(c,mail)
    app.config['SESSION_COOKIE_SECURE']=True
    response=post(c,'login',dict(username='user',password='long password123'))
    assert 'Secure' in response.headers['Set-Cookie']

def test_ownership_admin_and_old_private_links(env):
    app,c,mail,clock,cfg=env
    verified(c,mail)
    from tests.test_app import payload
    result=c.post('/api/reports',json=payload(),headers={'Origin':'http://localhost'}).json
    report_id=result['report']['id']
    assert result['report']['can_delete'] is True
    stranger=app.test_client(); verified(stranger,mail,'stranger@example.org','stranger')
    assert stranger.get('/api/reports').json['reports'][0]['can_delete'] is False
    assert stranger.delete(f'/api/reports/{report_id}',json={},headers={'Origin':'http://localhost'}).status_code==403
    assert c.delete(f'/api/reports/{report_id}',json={},headers={'Origin':'http://localhost'}).status_code==204
    other=c.post('/api/reports',json=payload(),headers={'Origin':'http://localhost'}).json
    anonymous=app.test_client()
    assert anonymous.get('/api/reports').status_code==401
    assert anonymous.delete(f"/api/reports/{other['report']['id']}",json={'delete_token':other['delete_token']},headers={'Origin':'http://localhost'}).status_code==204


def test_email_transport_uses_private_config_and_fragment(env,tmp_path,monkeypatch):
    import json
    app,c,mail,clock,cfg=env
    app.config.pop('MAIL_SENDER')
    path=tmp_path/'brevo.json'
    path.write_text(json.dumps({'api_key':'fake-local-test-key','sender_name':'HuellasUY','sender_email':'sender@example.org'}))
    app.config['BREVO_CONFIG_PATH']=str(path)
    sent=[]
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return b'{}'
    def transport(req,timeout):
        sent.append(json.loads(req.data)); assert timeout==15
        assert req.get_header('Api-key')=='fake-local-test-key'
        return Response()
    monkeypatch.setattr('auth.urllib.request.urlopen',transport)
    assert register(c).status_code==201
    assert '#verify=' in sent[0]['textContent']
    assert 'htmlContent' not in sent[0] and 'trackClicks' not in sent[0]
    with sqlite3.connect(cfg['DATABASE_PATH']) as db:
        stored=db.execute('SELECT token_hash FROM account_tokens').fetchone()[0]
        assert stored not in sent[0]['textContent']


def test_failed_email_removes_pending_token(env):
    app,c,mail,clock,cfg=env
    app.config['MAIL_SENDER']=lambda *args: (_ for _ in ()).throw(RuntimeError('failure'))
    assert register(c).status_code==503
    with sqlite3.connect(cfg['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM account_tokens').fetchone()[0]==0
