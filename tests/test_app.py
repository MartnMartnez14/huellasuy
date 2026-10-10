import sqlite3
import pytest
from app import create_app

@pytest.fixture
def setup(tmp_path):
    clock = [1700000000.0]
    config = dict(TESTING=True, AUTH_ENABLED=False, DATABASE_PATH=str(tmp_path / 'test.db'), SECRET_KEY='test-secret', CLOCK=lambda: clock[0])
    app = create_app(config)
    return app, app.test_client(), clock, config


def payload(**kw):
    return dict(title='Perro blanco', description='Tiene collar azul', latitude=-34.901234, longitude=-56.164567, animal_type='dog', status_type='seen', **kw)


def publish(client):
    response = client.post('/api/reports', json=payload())
    assert response.status_code == 201
    return response.json


def test_shared_persistent_private(setup):
    app, client, clock, config = setup
    result = publish(client)
    other = create_app(config).test_client()
    report = other.get('/api/reports').json['reports'][0]
    assert report['latitude'] == -34.901
    assert report['longitude'] == -56.165
    assert 'delete_token' not in report and 'delete_token_hash' not in report
    with sqlite3.connect(config['DATABASE_PATH']) as db:
        stored = db.execute('SELECT delete_token_hash FROM reports').fetchone()[0]
        assert stored != result['delete_token']
    assert client.get('/health').json == {'status': 'ok'}

@pytest.mark.parametrize('seconds,active', [(0, True),(86340, True),(86399, True),(86400, False),(86401, False)])
def test_expiration(setup, seconds, active):
    app, client, clock, config = setup
    result = publish(client); clock[0] += seconds
    assert bool(client.get('/api/reports').json['reports']) == active
    assert client.get('/api/reports/1').status_code == (200 if active else 404)
    with sqlite3.connect(config['DATABASE_PATH']) as db:
        assert db.execute('SELECT COUNT(*) FROM reports').fetchone()[0] == int(active)


def test_delete(setup):
    _, client, _, _ = setup
    result = publish(client)
    assert client.delete('/api/reports/1', json={'delete_token':'wrong'}).status_code == 403
    assert client.delete('/api/reports/1', json={'delete_token':result['delete_token']}).status_code == 204
    assert client.get('/api/reports/1').status_code == 404

@pytest.mark.parametrize('field,value', [('title',''),('title','x'*81),('description','x'*501),('description','<script>alert(1)</script>'),('latitude',True),('latitude',91),('latitude','-34'),('longitude',float('nan')),('animal_type',[]),('status_type','invalid')])
def test_validation(setup,field,value):
    _,client,_,_ = setup
    data=payload(); data[field]=value
    assert client.post('/api/reports',json=data).status_code == 400


def test_rate_origin_and_cleanup(setup):
    app,client,clock,config=setup
    assert client.post('/api/reports',json=payload(),headers={'Origin':'https://evil.example'}).status_code == 403
    assert client.post('/api/reports',data='bad').status_code == 415
    assert client.post('/api/reports',json=[],headers={'Origin':'http://localhost'}).status_code == 400
    for _ in range(5): publish(client)
    assert client.post('/api/reports',json=payload()).status_code == 429
    clock[0] += 3600
    publish(client)
    clock[0] += 86400
    assert app.test_cli_runner().invoke(args=['cleanup']).exit_code == 0
    assert client.get('/api/reports').json['reports'] == []


def test_filters_and_pages(setup):
    _,client,_,_=setup
    publish(client)
    assert client.get('/api/reports?animal_type=cat').json['reports'] == []
    assert len(client.get('/api/reports?status_type=seen').json['reports']) == 1
    assert client.get('/api/reports?animal_type=no').status_code == 400
    for path in ['/', '/help', '/privacy', '/about','/r/1','/manage/1']:
        response=client.get(path)
        assert response.status_code == 200
        assert 'Content-Security-Policy' in response.headers
    assert client.get('/api/reports').headers['Cache-Control'] == 'no-store'
