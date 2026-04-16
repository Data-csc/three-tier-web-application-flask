import json
import os
from unittest.mock import patch


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


def test_version_commit_default(client):
    with patch.dict(os.environ, {}, clear=True):
        os.environ.pop('GIT_COMMIT', None)
        response = client.get('/version')
        data = json.loads(response.data)
        assert data['commit'] == 'unknown'


def test_version_commit_from_env(client):
    with patch.dict(os.environ, {'GIT_COMMIT': 'abc123'}):
        response = client.get('/version')
        data = json.loads(response.data)
        assert data['commit'] == 'abc123'
