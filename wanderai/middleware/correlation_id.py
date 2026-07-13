"""
wanderai/middleware/correlation_id.py
Injects a unique X-Correlation-ID into every request and response.
Used for distributed tracing — every log line for a request shares the same ID.
"""
import uuid
from structlog.contextvars import clear_contextvars, bind_contextvars


class CorrelationIdMiddleware:
    """WSGI middleware that injects a correlation ID into every request."""

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        correlation_id = (
            environ.get("HTTP_X_CORRELATION_ID")
            or str(uuid.uuid4())
        )
        environ["X_CORRELATION_ID"] = correlation_id

        def custom_start_response(status, headers, exc_info=None):
            headers.append(("X-Correlation-ID", correlation_id))
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)


def init_correlation_id(app):
    """Register correlation ID on every Flask request."""
    @app.before_request
    def _bind_correlation_id():
        from flask import request, g
        import uuid
        clear_contextvars()
        cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        g.correlation_id = cid
        bind_contextvars(correlation_id=cid)

    @app.after_request
    def _add_correlation_header(response):
        from flask import g
        cid = getattr(g, "correlation_id", "")
        if cid:
            response.headers["X-Correlation-ID"] = cid
        return response
