"""wanderai/config/development.py — Development overrides."""

from datetime import timedelta

from .base import BaseConfig


class DevelopmentConfig(BaseConfig):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = False  # set True to log all SQL
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(
        hours=1
    )  # longer for dev convenience
    RATELIMIT_ENABLED: bool = False  # disable rate limiting in dev
    CACHE_TYPE: str = "SimpleCache"  # in-memory cache, no Redis needed
    CELERY_TASK_ALWAYS_EAGER: bool = True  # run tasks synchronously in dev
