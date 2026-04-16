import sys
import types
from unittest.mock import patch

import pytest

# Stub the parameters module before importing app so that
# app.py can build a database URI without crashing on missing SSM params.
_params = types.ModuleType("parameters")
_params.master_username = "test"
_params.db_password = "test"
_params.endpoint = "localhost"
_params.db_instance_name = "test"
sys.modules["parameters"] = _params

# Prevent db.create_all() from connecting to the real MySQL database.
# The echo endpoint used by these tests does not require the database.
with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_valid_echo(client):
    """Test that a valid POST request with JSON body returns the echoed message."""
    response = client.post('/echo',
                          json={"message": "hi"},
                          content_type='application/json')
    assert response.status_code == 200
    assert response.content_type == 'application/json'
    data = response.get_json()
    assert data == {"echo": "hi"}


def test_missing_body_returns_400(client):
    """Test that a POST request without a body returns 400 with error."""
    response = client.post('/echo', content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data == {"error": "bad_request"}


def test_invalid_json_returns_400(client):
    """Test that a POST request with invalid JSON returns 400 with error."""
    response = client.post('/echo',
                          data='not valid json',
                          content_type='application/json')
    assert response.status_code == 400
    data = response.get_json()
    assert data == {"error": "bad_request"}
