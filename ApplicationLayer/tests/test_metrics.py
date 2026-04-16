import sys
import types
import json
from unittest.mock import patch, MagicMock

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
with patch("flask_sqlalchemy.SQLAlchemy.create_all"):
    from app import app


@pytest.fixture()
def client():
    app.config['TESTING'] = True

    # Create mock query object
    mock_query = MagicMock()
    mock_query.all.return_value = []
    mock_query.get.return_value = None

    with app.test_client() as test_client:
        with patch('app.TodoTable') as mock_model:
            mock_model.query = mock_query
            with patch('app.db.session.add'), \
                 patch('app.db.session.commit'), \
                 patch('app.db.session.delete'):
                yield test_client


def test_emf_json_shape_and_structure(client, capsys):
    """Verify that EMF JSON has the correct CloudWatch structure."""
    response = client.get('/')
    captured = capsys.readouterr()

    assert captured.out.strip() != ""
    emf = json.loads(captured.out.strip())

    assert "_aws" in emf
    assert "CloudWatchMetrics" in emf["_aws"]
    assert "Timestamp" in emf["_aws"]
    assert isinstance(emf["_aws"]["Timestamp"], int)

    metrics_config = emf["_aws"]["CloudWatchMetrics"][0]
    assert "Namespace" in metrics_config
    assert "Dimensions" in metrics_config
    assert "Metrics" in metrics_config


def test_dimensions_and_metric_names(client, capsys):
    """Verify dimensions and metric names match CloudWatch EMF spec."""
    response = client.get('/')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    metrics_config = emf["_aws"]["CloudWatchMetrics"][0]

    assert metrics_config["Dimensions"] == [["Route", "Method"]]

    metric_names = [m["Name"] for m in metrics_config["Metrics"]]
    assert "LatencyMs" in metric_names
    assert "Count" in metric_names

    latency_metric = next(m for m in metrics_config["Metrics"] if m["Name"] == "LatencyMs")
    count_metric = next(m for m in metrics_config["Metrics"] if m["Name"] == "Count")

    assert latency_metric["Unit"] == "Milliseconds"
    assert count_metric["Unit"] == "Count"


def test_top_level_fields(client, capsys):
    """Verify top-level EMF fields are present with correct values."""
    response = client.get('/')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())

    assert "Route" in emf
    assert "Method" in emf
    assert "StatusCode" in emf
    assert "LatencyMs" in emf
    assert "Count" in emf

    assert emf["Route"] == "/"
    assert emf["Method"] == "GET"
    assert emf["StatusCode"] == 200
    assert isinstance(emf["LatencyMs"], (int, float))
    assert emf["LatencyMs"] >= 0
    assert emf["Count"] == 1


def test_health_endpoint_excluded(client, capsys):
    """Verify /health endpoint does not emit metrics."""
    response = client.get('/health')
    captured = capsys.readouterr()

    assert captured.out == ""


def test_4xx_responses_emit_metrics(client, capsys):
    """Verify 4xx responses still emit metrics with correct status code."""
    response = client.post('/update', data={})
    captured = capsys.readouterr()

    assert captured.out.strip() != ""
    emf = json.loads(captured.out.strip())

    assert emf["StatusCode"] == 404
    assert emf["Route"] == "/update"
    assert emf["Method"] == "POST"


def test_dynamic_route_pattern(client, capsys):
    """Verify dynamic routes use pattern, not concrete URL."""
    response = client.post('/complete/123')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    assert emf["Route"] == "/complete/<task_id>"


def test_unknown_route_for_404(client, capsys):
    """Verify 404 to non-existent route uses UNKNOWN as route label."""
    response = client.get('/nonexistent')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    assert emf["Route"] == "UNKNOWN"
    assert emf["StatusCode"] == 404


def test_duration_precision(client, capsys):
    """Verify duration is rounded to 2 decimal places."""
    response = client.get('/')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    duration_str = str(emf["LatencyMs"])

    if '.' in duration_str:
        decimal_places = len(duration_str.split('.')[1])
        assert decimal_places <= 2


def test_metrics_namespace_default(client, capsys):
    """Verify default namespace is FlaskApp."""
    response = client.get('/')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    assert emf["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "FlaskApp"


def test_metrics_namespace_from_env(client, capsys, monkeypatch):
    """Verify namespace can be set via METRICS_NAMESPACE env var."""
    monkeypatch.setenv("METRICS_NAMESPACE", "CustomNamespace")

    response = client.get('/')
    captured = capsys.readouterr()

    emf = json.loads(captured.out.strip())
    assert emf["_aws"]["CloudWatchMetrics"][0]["Namespace"] == "CustomNamespace"
