"""
wanderai/middleware/request_logger.py
Logs structured request/response info for every API call.
"""
import time
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)


def init_request_logger(app):
    """Register request logging hooks."""

    @app.before_request
    def _start_timer():
        from flask import g
        g.request_start = time.monotonic()

    @app.after_request
    def _log_request(response):
        from flask import request, g
        duration_ms = round((time.monotonic() - getattr(g, "request_start", time.monotonic())) * 1000, 2)

        # Only log API routes to avoid noise from static files
        if request.path.startswith("/api/") or request.path in ("/", "/health"):
            logger.info(
                "http_request",
                method=request.method,
                path=request.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                content_length=response.content_length,
                user_agent=request.user_agent.string[:100] if request.user_agent.string else "",
            )

        return response
