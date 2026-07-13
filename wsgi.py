"""
wsgi.py — Gunicorn WSGI entry point.
Usage: gunicorn wsgi:application -w 4 -b 0.0.0.0:5000
"""
import os
from wanderai.app import create_app
from wanderai.ai.pipeline import init_pipeline

config_name = os.getenv("FLASK_ENV", "production")
application = create_app(config_name)

# Initialize AI pipeline at startup — non-fatal: missing credentials degrade
# gracefully rather than crashing Gunicorn boot.
with application.app_context():
    try:
        from wanderai.extensions import cache
        init_pipeline(application.config, cache=cache)
    except Exception as _exc:
        import logging
        logging.getLogger(__name__).warning(
            "AI pipeline init skipped — check WATSONX_API_KEY / WATSONX_PROJECT_ID: %s", _exc
        )
