import sys
import types
import uuid
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
# The health endpoint used by these tests does not require the database.
with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_request_id_generated_when_absent(client):
    """When no X-Request-ID header is sent, the response should contain a
    newly generated valid UUIDv4 in the X-Request-ID header."""
    response = client.get('/health')
    request_id = response.headers.get('X-Request-ID')
    assert request_id is not None
    parsed = uuid.UUID(request_id)
    assert parsed.version == 4


def test_request_id_echoed_when_present(client):
    """When the request includes an X-Request-ID header, the response should
    echo back the same value."""
    custom_id = str(uuid.uuid4())
    response = client.get('/health', headers={'X-Request-ID': custom_id})
    assert response.headers.get('X-Request-ID') == custom_id
