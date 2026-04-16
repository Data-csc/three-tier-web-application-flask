import os
import sys
import types
from unittest.mock import MagicMock

import pytest


@pytest.fixture()
def client():
    """Create a Flask test client with database and parameters stubbed."""
    # Build a fake 'parameters' module
    fake_params = types.ModuleType('parameters')
    fake_params.master_username = 'test'
    fake_params.db_password = 'test'
    fake_params.endpoint = 'localhost'
    fake_params.db_instance_name = 'testdb'

    # Build a fake 'flask_sqlalchemy' module with a MagicMock SQLAlchemy
    fake_sqla_module = types.ModuleType('flask_sqlalchemy')
    mock_db = MagicMock()
    mock_db.Model = type('Model', (), {})
    fake_sqla_module.SQLAlchemy = lambda app=None, **kw: mock_db

    saved_modules = {}
    for mod_name in ('parameters', 'flask_sqlalchemy', 'app'):
        saved_modules[mod_name] = sys.modules.pop(mod_name, None)

    sys.modules['parameters'] = fake_params
    sys.modules['flask_sqlalchemy'] = fake_sqla_module

    import app as app_module

    app_module.app.config['TESTING'] = True
    with app_module.app.test_client() as c:
        yield c

    # Restore original module state
    sys.modules.pop('app', None)
    for mod_name, mod in saved_modules.items():
        if mod is not None:
            sys.modules[mod_name] = mod
        else:
            sys.modules.pop(mod_name, None)
