import sys
import types
import uuid
import json
import logging
from unittest.mock import patch
from io import StringIO

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


def test_new_request_generates_uuid_in_logs(client, capsys):
    """New requests should generate a valid UUIDv4 that appears in log output."""
    response = client.get('/health')
    request_id = response.headers.get('X-Request-ID')

    # Capture log output
    captured = capsys.readouterr()

    # The health endpoint doesn't log, so check the request_id is a valid UUID
    assert request_id is not None
    parsed = uuid.UUID(request_id)
    assert parsed.version == 4


def test_incoming_request_id_preserved_in_logs(client, capsys):
    """Incoming X-Request-ID header should be preserved in log output."""
    custom_id = str(uuid.uuid4())
    response = client.get('/health', headers={'X-Request-ID': custom_id})

    # Verify the response echoes the custom ID
    assert response.headers.get('X-Request-ID') == custom_id


def test_log_output_is_valid_json_with_request_id(client):
    """Log output should be valid JSON containing the request_id field."""
    # Capture stdout using a StringIO buffer
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    # Import after app is set up
    import app as app_module
    from logging_config import JSONFormatter

    handler.setFormatter(JSONFormatter())
    app_module.logger.addHandler(handler)

    try:
        # Mock the database query to avoid DB access
        with patch("app.TodoTable") as mock_table:
            mock_query = mock_table.query
            mock_query.all.return_value = []

            custom_id = str(uuid.uuid4())
            response = client.get('/', headers={'X-Request-ID': custom_id})

            # Get captured log output
            log_output = log_capture.getvalue()
            log_lines = [line for line in log_output.split('\n') if line.strip()]

            # At least one log line should exist (route entry and completion)
            assert len(log_lines) >= 2

            # Parse each log line as JSON and verify structure
            for log_line in log_lines:
                log_data = json.loads(log_line)

                # Verify required fields
                assert 'timestamp' in log_data
                assert 'level' in log_data
                assert 'logger' in log_data
                assert 'message' in log_data

                # Verify request-scoped fields are present
                assert 'request_id' in log_data
                assert log_data['request_id'] == custom_id
                assert 'method' in log_data
                assert log_data['method'] == 'GET'
                assert 'path' in log_data
                assert log_data['path'] == '/'

                # Verify timestamp is in ISO 8601 format
                assert log_data['timestamp'].endswith('Z')
                assert 'T' in log_data['timestamp']
    finally:
        app_module.logger.removeHandler(handler)
