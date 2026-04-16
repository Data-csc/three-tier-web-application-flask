"""Test configuration for ApplicationLayer tests.

Mocks external dependencies (AWS SSM Parameter Store via parameters module,
and flask_sqlalchemy) at import time so that test modules can safely import
the app module without requiring AWS credentials or a real database.

Cleanup is handled by a session-scoped fixture that restores sys.modules
after all tests complete.
"""
import sys
import types
from unittest.mock import MagicMock

import pytest

# Capture originals before patching
_original_parameters = sys.modules.get("parameters")
_original_flask_sqlalchemy = sys.modules.get("flask_sqlalchemy")

# Mock the parameters module (calls boto3 SSM at import time)
_parameters_mock = types.ModuleType("parameters")
_parameters_mock.master_username = "test_user"
_parameters_mock.db_password = "test_pass"
_parameters_mock.endpoint = "localhost"
_parameters_mock.db_instance_name = "test_db"
sys.modules["parameters"] = _parameters_mock

# Mock flask_sqlalchemy so app can be imported without a real database
_mock_db = MagicMock()
_mock_db.Model = type("Model", (), {
    "__tablename__": "",
    "metadata": MagicMock(),
})
_mock_db.Column = MagicMock()
_mock_db.Integer = MagicMock()
_mock_db.String = MagicMock()
_mock_db.create_all = MagicMock()

_sqlalchemy_mock = types.ModuleType("flask_sqlalchemy")
_sqlalchemy_mock.SQLAlchemy = MagicMock(return_value=_mock_db)
sys.modules["flask_sqlalchemy"] = _sqlalchemy_mock


@pytest.fixture(scope="session", autouse=True)
def _restore_sys_modules():
    """Restore sys.modules after the test session completes."""
    yield

    if _original_parameters is not None:
        sys.modules["parameters"] = _original_parameters
    else:
        sys.modules.pop("parameters", None)

    if _original_flask_sqlalchemy is not None:
        sys.modules["flask_sqlalchemy"] = _original_flask_sqlalchemy
    else:
        sys.modules.pop("flask_sqlalchemy", None)
