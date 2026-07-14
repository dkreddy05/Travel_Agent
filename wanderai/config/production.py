"""wanderai/config/production.py — Production overrides."""

import os
from .base import BaseConfig

_WEAK_DEFAULTS = {"change-me-in-production", "change-me", ""}

_secret_key = os.getenv("FLASK_SECRET_KEY", "")
_jwt_key = os.getenv("JWT_SECRET_KEY", _secret_key)

if _secret_key in _WEAK_DEFAULTS or len(_secret_key) < 32:
    raise ValueError(
        "FLASK_SECRET_KEY must be set to a strong random value (≥32 chars) in production. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

if _jwt_key in _WEAK_DEFAULTS or len(_jwt_key) < 32:
    raise ValueError(
        "JWT_SECRET_KEY must be set to a strong random value (≥32 chars) in production."
    )


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
