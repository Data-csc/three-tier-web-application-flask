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
# The uptime endpoint does not require the database.
with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_uptime_endpoint(client):
    """The /uptime endpoint should return JSON with uptime_seconds as a
    non-negative integer and HTTP 200 status."""
    response = client.get('/uptime')
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert "uptime_seconds" in data
    assert isinstance(data["uptime_seconds"], int)
    assert data["uptime_seconds"] >= 0
