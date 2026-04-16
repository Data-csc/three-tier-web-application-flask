import sys
import types
from unittest.mock import MagicMock

# Mock the parameters module before importing app, since it calls
# boto3 SSM at import time and we have no AWS credentials in tests.
parameters_mock = types.ModuleType("parameters")
parameters_mock.master_username = "test_user"
parameters_mock.db_password = "test_pass"
parameters_mock.endpoint = "localhost"
parameters_mock.db_instance_name = "test_db"
sys.modules["parameters"] = parameters_mock

# Mock flask_sqlalchemy so the app can be imported without a real database.
sqlalchemy_mock = types.ModuleType("flask_sqlalchemy")
mock_db = MagicMock()
mock_db.Model = type("Model", (), {"__tablename__": "", "metadata": MagicMock()})
mock_db.Column = MagicMock()
mock_db.Integer = MagicMock()
mock_db.String = MagicMock()
mock_db.create_all = MagicMock()
sqlalchemy_mock.SQLAlchemy = MagicMock(return_value=mock_db)
sys.modules["flask_sqlalchemy"] = sqlalchemy_mock

import app as application


class TestHealthz:
    def setup_method(self):
        application.app.config["TESTING"] = True
        self.client = application.app.test_client()

    def test_healthz_returns_200(self):
        response = self.client.get("/healthz")
        assert response.status_code == 200

    def test_healthz_returns_json_status_ok(self):
        response = self.client.get("/healthz")
        data = response.get_json()
        assert data == {"status": "ok"}

    def test_healthz_content_type_is_json(self):
        response = self.client.get("/healthz")
        assert response.content_type == "application/json"
