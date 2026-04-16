import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock parameters module
sys.modules['parameters'] = MagicMock(
    master_username='test_user',
    db_password='test_pass',
    endpoint='localhost',
    db_instance_name='test_db'
)

# Patch SQLAlchemy to prevent database connection
mock_db = MagicMock()
mock_sqlalchemy = MagicMock(return_value=mock_db)
sys.modules['flask_sqlalchemy'] = MagicMock(SQLAlchemy=mock_sqlalchemy)

from app import app

def test_ping():
    client = app.test_client()
    response = client.get('/ping')
    assert response.status_code == 200
    assert response.data == b'pong'
    assert 'text/plain' in response.content_type
