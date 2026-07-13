"""wanderai/config/testing.py — Testing overrides."""
from .base import BaseConfig


class TestingConfig(BaseConfig):
    TESTING: bool = True
    DEBUG: bool = True
    # SQLite in-memory for fast test runs
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS: dict = {}    # no pool options for SQLite
    WTF_CSRF_ENABLED: bool = False
    RATELIMIT_ENABLED: bool = False
    CACHE_TYPE: str = "SimpleCache"
    CELERY_TASK_ALWAYS_EAGER: bool = True
    CELERY_TASK_EAGER_PROPAGATES: bool = True
    # Short token expiry for testing revocation
    JWT_ACCESS_TOKEN_EXPIRES_SECONDS: int = 30
    # Disable email sending in tests
    MAIL_SUPPRESS_SEND: bool = True
