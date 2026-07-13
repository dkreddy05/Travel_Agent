"""
wanderai/extensions.py
Flask extension singletons — instantiated here, initialized in create_app().
Importing from this module avoids circular imports.
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_mail import Mail
from celery import Celery

# SQLAlchemy ORM
db = SQLAlchemy()

# Alembic migrations
migrate = Migrate()

# JWT authentication
jwt = JWTManager()

# Redis-backed cache
cache = Cache()

# Rate limiting (Redis-backed in production)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per hour"],
    storage_uri="memory://",  # overridden in create_app with config
)

# CORS
cors = CORS()

# Email
mail = Mail()

# ── Celery ────────────────────────────────────────────────────────────────────
# Instantiated here so tasks can import `celery_app` without a circular import.
# Flask app context is injected by init_celery() called from create_app().
celery_app = Celery(
    "wanderai",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    include=[
        "wanderai.tasks.itinerary_tasks",
        "wanderai.tasks.email_tasks",
        "wanderai.tasks.cleanup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    beat_schedule={
        "cleanup-expired-sessions": {
            "task": "tasks.cleanup_expired_sessions",
            "schedule": 86400,  # daily
        },
    },
)


def init_celery(app) -> None:
    """Bind the Celery app to the Flask app context."""
    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask
    # Sync broker/backend URLs from Flask config in case they differ
    celery_app.conf.broker_url = app.config.get("CELERY_BROKER_URL", celery_app.conf.broker_url)
    celery_app.conf.result_backend = app.config.get("CELERY_RESULT_BACKEND", celery_app.conf.result_backend)
