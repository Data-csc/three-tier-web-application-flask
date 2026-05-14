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
# The status endpoint used by these tests does not require the database.
with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_status_endpoint_returns_ok(client):
    """The /status endpoint should return OK with status 200 and
    Content-Type text/plain."""
    response = client.get('/status')
    assert response.status_code == 200
    assert response.data == b'OK'
    assert response.headers.get('Content-Type') == 'text/plain'
