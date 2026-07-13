"""wanderai/config/production.py — Production overrides."""
from .base import BaseConfig


class ProductionConfig(BaseConfig):
    DEBUG: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        **BaseConfig.SQLALCHEMY_ENGINE_OPTIONS,
        "pool_size": 20,
        "max_overflow": 40,
    }
    # Force HTTPS cookies in production
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    REMEMBER_COOKIE_SECURE: bool = True
    PREFERRED_URL_SCHEME: str = "https"
