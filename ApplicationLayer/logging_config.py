import logging
import json
import sys
from datetime import datetime, timezone
from flask import has_request_context, g, request


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter that outputs structured logs with request context."""

    def format(self, record):
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat().replace('+00:00', 'Z'),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage()
        }

        # Add request-scoped fields if we're in a request context
        if has_request_context():
            try:
                log_data['request_id'] = g.request_id
                log_data['method'] = request.method
                log_data['path'] = request.path
            except (AttributeError, RuntimeError):
                # Gracefully handle cases where request_id or request are not available
                pass

        # Include exception info if present
        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def configure_logging(app):
    """Configure structured JSON logging for the Flask application."""
    # Create handler that writes to stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())

    # Configure only the 'app' logger namespace (not root logger)
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    app_logger.addHandler(handler)
    app_logger.propagate = False
