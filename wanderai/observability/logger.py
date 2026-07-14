"""
wanderai/observability/logger.py
Structured JSON logger using structlog.
Every log entry includes correlation_id (injected by middleware).
"""

import logging
import sys
import structlog
from structlog.contextvars import merge_contextvars


def configure_logging(debug: bool = False) -> None:
    """Configure structlog for the application."""
    level = logging.DEBUG if debug else logging.INFO

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    structlog.configure(
        processors=[
            merge_contextvars,  # inject correlation_id etc.
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            (
                structlog.dev.ConsoleRenderer()
                if debug
                else structlog.processors.JSONRenderer()
            ),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Return a bound logger for the given module name."""
    return structlog.get_logger(name)
