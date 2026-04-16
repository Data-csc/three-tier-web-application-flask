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


def test_new_request_generates_uuid_in_logs(client):
    """New requests should generate a valid UUIDv4 that appears in log output."""
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

            response = client.get('/')
            request_id = response.headers.get('X-Request-ID')

            # Get captured log output
            log_output = log_capture.getvalue()
            log_lines = [line for line in log_output.split('\n') if line.strip()]

            # At least one log line should exist
            assert len(log_lines) >= 1

            # Parse first log line and verify request_id
            log_data = json.loads(log_lines[0])
            assert 'request_id' in log_data
            assert log_data['request_id'] == request_id

            # Verify it's a valid UUIDv4
            parsed = uuid.UUID(request_id)
            assert parsed.version == 4
    finally:
        app_module.logger.removeHandler(handler)


def test_incoming_request_id_preserved_in_logs(client):
    """Incoming X-Request-ID header should be preserved in log output."""
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

            # Verify the response echoes the custom ID
            assert response.headers.get('X-Request-ID') == custom_id

            # Get captured log output
            log_output = log_capture.getvalue()
            log_lines = [line for line in log_output.split('\n') if line.strip()]

            # Parse log lines and verify custom_id is present
            assert len(log_lines) >= 1
            log_data = json.loads(log_lines[0])
            assert log_data['request_id'] == custom_id
    finally:
        app_module.logger.removeHandler(handler)


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

                # Verify timestamp is valid ISO 8601 format by parsing it
                from datetime import datetime
                timestamp_str = log_data['timestamp'].replace('Z', '+00:00')
                parsed_time = datetime.fromisoformat(timestamp_str)
                assert parsed_time is not None
    finally:
        app_module.logger.removeHandler(handler)


def test_error_logging_includes_exc_info(client):
    """Error logs should include exception information."""
    # Capture stdout using a StringIO buffer
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    # Import after app is set up
    import app as app_module
    from logging_config import JSONFormatter

    handler.setFormatter(JSONFormatter())
    app_module.logger.addHandler(handler)

    try:
        # Mock the database query to trigger an exception in create route
        with patch("app.TodoTable") as mock_table:
            # Make the constructor raise an exception
            mock_table.side_effect = Exception("Database error")

            # This should trigger an exception and error logging in create route
            response = client.post('/create', data={'task': 'test task'})

            # Get captured log output
            log_output = log_capture.getvalue()
            log_lines = [line for line in log_output.split('\n') if line.strip()]

            # Should have at least entry log and error log
            assert len(log_lines) >= 1

            # Find the error log line by checking level field
            error_logs = []
            for line in log_lines:
                try:
                    log_data = json.loads(line)
                    if log_data.get('level') == 'ERROR':
                        error_logs.append(log_data)
                except:
                    pass

            # Should have at least one error log
            assert len(error_logs) >= 1

            # Verify error log has exc_info
            error_log = error_logs[0]
            assert 'exc_info' in error_log
            assert 'Database error' in error_log['exc_info']
    finally:
        app_module.logger.removeHandler(handler)


def test_logs_outside_request_context():
    """Logs outside request context should omit request-scoped fields gracefully."""
    # Capture stdout using a StringIO buffer
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)

    # Import after app is set up
    import app as app_module
    from logging_config import JSONFormatter

    handler.setFormatter(JSONFormatter())
    app_module.logger.addHandler(handler)

    try:
        # Log outside of request context
        app_module.logger.info("Test log outside request context")

        # Get captured log output
        log_output = log_capture.getvalue()
        log_lines = [line for line in log_output.split('\n') if line.strip()]

        assert len(log_lines) >= 1

        # Parse the log line
        log_data = json.loads(log_lines[0])

        # Verify core fields exist
        assert 'timestamp' in log_data
        assert 'level' in log_data
        assert 'logger' in log_data
        assert 'message' in log_data
        assert log_data['message'] == "Test log outside request context"

        # Verify request-scoped fields are absent
        assert 'request_id' not in log_data
        assert 'method' not in log_data
        assert 'path' not in log_data
    finally:
        app_module.logger.removeHandler(handler)
