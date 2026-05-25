from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def token(email, name):
    client.post('/auth/register', json={'email': email, 'password': '1234', 'name': name})
    return client.post('/auth/login', json={'email': email, 'password': '1234'}).json()['token']


def test_family_and_personal_isolation():
    t1 = token('a@test.com', 'A')
    t2 = token('b@test.com', 'B')
    h1 = {'Authorization': f'Bearer {t1}'}
    h2 = {'Authorization': f'Bearer {t2}'}
    client.post('/family/create', json={'name': 'Home'}, headers=h1)
    client.post('/family/add-member', json={'member_email': 'b@test.com'}, headers=h1)
    client.post('/items', json={'name': '牛奶', 'qty_needed': 1, 'list_type': 'personal'}, headers=h1)
    client.post('/items', json={'name': '水果', 'qty_needed': 1, 'list_type': 'family'}, headers=h1)
    # member buys family item should deduct family not A personal
    r = client.post('/purchase', json={'item_name': '蘋果', 'for_list_type': 'family'}, headers=h2)
    assert r.status_code == 200
    me = client.get('/items/me', headers=h1).json()
    assert len(me['personal']) == 1


def test_siri_voice_add():
    t = token('c@test.com', 'C')
    h = {'Authorization': f'Bearer {t}'}
    r = client.post('/voice/siri', json={'phrase': '幫我在管家紀錄要買阿猴鮮奶 2 個', 'list_type': 'personal'}, headers=h)
    assert r.status_code == 200
    assert r.json()['added'] == '牛奶'
    assert r.json()['qty_needed'] == 2


def test_oauth_config_and_unconfigured_start():
    config = client.get('/auth/oauth/config').json()
    assert set(config) == {'apple', 'line', 'google'}
    r = client.get('/auth/oauth/apple/start')
    assert r.status_code == 501
    callback = client.get('/auth/oauth/google/callback')
    assert callback.status_code == 501
