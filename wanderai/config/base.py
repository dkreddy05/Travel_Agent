"""
wanderai/config/base.py
Base configuration — all shared defaults.
Environment-specific configs override these values.
"""

import os
from datetime import timedelta


class BaseConfig:
    # ── Core Flask ──────────────────────────────────────────
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # ── Database ─────────────────────────────────────────────
    SQLALCHEMY_DATABASE_URI: str = os.getenv(
        "DATABASE_URL", "postgresql://wanderai:wanderai@localhost:5432/wanderai"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,  # test connections before use
        "pool_recycle": 3600,  # recycle connections every hour
    }

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_TYPE: str = "RedisCache"
    CACHE_REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CACHE_DEFAULT_TIMEOUT: int = 3600

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", os.getenv("FLASK_SECRET_KEY", "change-me")
    )
    JWT_ACCESS_TOKEN_EXPIRES: timedelta = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES: timedelta = timedelta(days=30)
    JWT_ALGORITHM: str = "HS256"
    JWT_TOKEN_LOCATION: list = ["headers"]
    JWT_HEADER_NAME: str = "Authorization"
    JWT_HEADER_TYPE: str = "Bearer"

    # ── IBM watsonx.ai ───────────────────────────────────────
    WATSONX_API_KEY: str = os.getenv("WATSONX_API_KEY", "")
    WATSONX_URL: str = os.getenv("WATSONX_URL", "")
    WATSONX_PROJECT_ID: str = os.getenv("WATSONX_PROJECT_ID", "")
    GRANITE_MODEL_ID: str = os.getenv(
        "GRANITE_MODEL_ID", "ibm/granite-13b-instruct-v2"
    )

    # ── LiteLLM / AI ─────────────────────────────────────────
    AI_PRIMARY_MODEL: str = os.getenv(
        "AI_PRIMARY_MODEL", "meta-llama/llama-3-3-70b-instruct"
    )
    AI_FALLBACK_MODEL: str = os.getenv("AI_FALLBACK_MODEL", "")
    AI_MAX_TOKENS: int = int(os.getenv("AI_MAX_TOKENS", "1500"))
    AI_TEMPERATURE: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    AI_MAX_RETRIES: int = 3
    AI_TIMEOUT_SECONDS: int = 60
    AI_CACHE_TTL: int = 3600  # 1 hour LLM response cache

    # ── Qdrant ───────────────────────────────────────────────
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY", "")
    QDRANT_COLLECTION: str = "wanderai_knowledge"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # ── Celery ───────────────────────────────────────────────
    CELERY_BROKER_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list = ["json"]
    CELERY_TIMEZONE: str = "UTC"

    # ── OAuth ────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
    GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
    OAUTH_REDIRECT_BASE: str = os.getenv("APP_URL", "http://localhost:5000")

    # ── Email ────────────────────────────────────────────────
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS: bool = True
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER: str = os.getenv("MAIL_FROM", "WanderAI <noreply@wanderai.app>")

    # ── Rate Limiting ────────────────────────────────────────
    RATELIMIT_STORAGE_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    RATELIMIT_DEFAULT: str = "200 per hour"
    RATELIMIT_AUTH: str = "10 per minute"
    RATELIMIT_AI: str = "30 per hour"

    # ── Sentry ───────────────────────────────────────────────
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # ── App Settings ─────────────────────────────────────────
    APP_URL: str = os.getenv("APP_URL", "http://localhost:5000")
    APP_NAME: str = "WanderAI"
    APP_VERSION: str = "2.0.0"
    MAX_CONTENT_LENGTH: int = 1 * 1024 * 1024  # 1 MB max request body

    # ── External Tools ───────────────────────────────────────
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    FOURSQUARE_API_KEY: str = os.getenv("FOURSQUARE_API_KEY", "")
