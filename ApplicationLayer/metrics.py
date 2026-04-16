import json
import os
import sys
import time


def emit_latency(route, method, status_code, duration_ms):
    """Emit per-route latency metrics in CloudWatch EMF format.

    Args:
        route: Flask route pattern (e.g., '/complete/<task_id>')
        method: HTTP method (GET, POST, etc.)
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
    """
    try:
        namespace = os.environ.get('METRICS_NAMESPACE', 'FlaskApp')
        rounded_duration = round(duration_ms, 2)

        emf = {
            "_aws": {
                "Timestamp": int(time.time() * 1000),
                "CloudWatchMetrics": [
                    {
                        "Namespace": namespace,
                        "Dimensions": [["Route", "Method"]],
                        "Metrics": [
                            {"Name": "LatencyMs", "Unit": "Milliseconds"},
                            {"Name": "Count", "Unit": "Count"}
                        ]
                    }
                ]
            },
            "Route": route,
            "Method": method,
            "StatusCode": status_code,
            "LatencyMs": rounded_duration,
            "Count": 1
        }

        print(json.dumps(emf))
    except Exception as e:
        print(f"metrics-emit-error: {e}", file=sys.stderr)
