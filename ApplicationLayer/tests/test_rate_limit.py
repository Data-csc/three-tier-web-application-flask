import sys
import types
import time
from unittest.mock import patch, MagicMock

import pytest

_params = types.ModuleType("parameters")
_params.master_username = "test"
_params.db_password = "test"
_params.endpoint = "localhost"
_params.db_instance_name = "test"
sys.modules["parameters"] = _params

with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app, rate_limiter


@pytest.fixture()
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with patch("app.TodoTable") as mock_table:
            mock_table.query.all.return_value = []
            yield client


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Reset rate limiter state before each test."""
    rate_limiter.buckets.clear()
    yield


def test_under_limit_requests_pass(client):
    """Requests under the rate limit should return normal responses."""
    for i in range(5):
        response = client.get('/')
        assert response.status_code == 200


def test_burst_capacity_exceeded_returns_429(client):
    """Requests exceeding burst capacity should return 429."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        response = client.get('/')
        assert response.status_code == 200

    response = client.get('/')
    assert response.status_code == 429
    data = response.get_json()
    assert data['error'] == 'rate_limited'
    assert 'retry_after_seconds' in data
    assert isinstance(data['retry_after_seconds'], int)


def test_429_response_includes_retry_after_header(client):
    """429 responses should include Retry-After header."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        client.get('/')

    response = client.get('/')
    assert response.status_code == 429
    assert 'Retry-After' in response.headers
    retry_after = int(response.headers['Retry-After'])
    assert retry_after > 0


def test_exempt_path_health_never_rate_limited(client):
    """The /health endpoint should never be rate limited."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit + 10):
        response = client.get('/health')
        assert response.status_code == 200
        assert response.data == b'Successful health check for ALB!'


def test_exempt_path_alive_never_rate_limited(client):
    """The /alive endpoint should never be rate limited (if it exists)."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit + 10):
        response = client.get('/alive')
        if response.status_code != 404:
            assert response.status_code != 429


def test_retry_after_calculation_accuracy(client):
    """Retry-After value should accurately reflect time until next token."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        client.get('/')

    response = client.get('/')
    assert response.status_code == 429
    data = response.get_json()
    retry_after = data['retry_after_seconds']

    assert retry_after > 0
    expected_min = 1.0 / rate_limiter.rate_per_second
    assert retry_after <= int(expected_min) + 2


def test_tokens_refill_over_time(client):
    """Tokens should refill at the configured rate over time."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        response = client.get('/')
        assert response.status_code == 200

    response = client.get('/')
    assert response.status_code == 429

    sleep_duration = 1.0 / rate_limiter.rate_per_second + 0.01
    time.sleep(sleep_duration)

    response = client.get('/')
    assert response.status_code == 200


def test_different_ips_have_independent_limits(client):
    """Different IP addresses should have independent rate limits."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        response = client.get('/', environ_base={'REMOTE_ADDR': '192.168.1.1'})
        assert response.status_code == 200

    response = client.get('/', environ_base={'REMOTE_ADDR': '192.168.1.1'})
    assert response.status_code == 429

    response = client.get('/', environ_base={'REMOTE_ADDR': '192.168.1.2'})
    assert response.status_code == 200


def test_rate_limiter_allow_method():
    """Test the RateLimiter.allow() method directly."""
    from rate_limit import RateLimiter
    limiter = RateLimiter(rate_per_second=2, burst=3)

    assert limiter.allow('test_key') is True
    assert limiter.allow('test_key') is True
    assert limiter.allow('test_key') is True
    assert limiter.allow('test_key') is False


def test_rate_limiter_get_retry_after():
    """Test the RateLimiter.get_retry_after() method."""
    from rate_limit import RateLimiter
    limiter = RateLimiter(rate_per_second=10, burst=5)

    for i in range(5):
        limiter.allow('test_key')

    limiter.allow('test_key')

    retry_after = limiter.get_retry_after('test_key')
    assert retry_after >= 1
    assert retry_after <= 2


def test_retry_after_decreases_after_partial_refill(client):
    """Retry-After should decrease as tokens refill over time."""
    burst_limit = rate_limiter.burst

    for i in range(burst_limit):
        client.get('/')

    response = client.get('/')
    assert response.status_code == 429
    initial_retry_after = response.get_json()['retry_after_seconds']

    time.sleep(0.05)

    response = client.get('/')
    assert response.status_code == 429
    later_retry_after = response.get_json()['retry_after_seconds']

    assert later_retry_after <= initial_retry_after
