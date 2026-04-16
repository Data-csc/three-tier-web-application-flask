import json


def test_version_returns_200(client):
    response = client.get('/version')
    assert response.status_code == 200


def test_version_json_shape(client):
    response = client.get('/version')
    data = json.loads(response.data)
    assert 'version' in data
    assert 'commit' in data


def test_version_static_value(client):
    response = client.get('/version')
    data = json.loads(response.data)
    assert data['version'] == '1.0.0'


def test_version_commit_default(client, monkeypatch):
    monkeypatch.delenv('GIT_COMMIT', raising=False)
    response = client.get('/version')
    data = json.loads(response.data)
    assert data['commit'] == 'unknown'


def test_version_commit_from_env(client, monkeypatch):
    monkeypatch.setenv('GIT_COMMIT', 'abc123')
    response = client.get('/version')
    data = json.loads(response.data)
    assert data['commit'] == 'abc123'
