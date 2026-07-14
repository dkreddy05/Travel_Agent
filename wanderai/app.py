"""
wanderai/app.py
Flask application factory.
Usage: from wanderai.app import create_app
"""

import os
import sentry_sdk
from flask import Flask
from sentry_sdk.integrations.flask import FlaskIntegration

from wanderai.config import config_map
from wanderai.extensions import (
    db,
    migrate,
    jwt,
    cache,
    limiter,
    cors,
    mail,
    init_celery,
)
from wanderai.observability.logger import configure_logging
from wanderai.observability.metrics import init_metrics
from wanderai.middleware.correlation_id import init_correlation_id
from wanderai.middleware.security_headers import init_security_headers
from wanderai.middleware.request_logger import init_request_logger


def create_app(config_name: str | None = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: One of 'development', 'production', 'testing', or None
                     (falls back to FLASK_ENV environment variable, then 'development').
    """
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )

    # ── Configure logging ───────────────────────────────────
    configure_logging(debug=config_name == "development")

    # ── Load configuration ──────────────────────────────────
    cfg = config_map.get(config_name, config_map["default"])
    app.config.from_object(cfg)
    if hasattr(cfg, "validate"):
        cfg.validate()

    # ── Sentry error tracking ───────────────────────────────
    if app.config.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()],
            traces_sample_rate=0.2,
            environment=config_name,
            release=app.config.get("APP_VERSION", "2.0.0"),
        )

    # ── Initialize extensions ───────────────────────────────
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    cors.init_app(
        app, resources={r"/api/*": {"origins": app.config.get("APP_URL", "*")}}
    )
    limiter.init_app(app)

    # ── Celery Flask context binding ────────────────────────
    init_celery(app)

    # ── Middleware ──────────────────────────────────────────
    init_correlation_id(app)
    init_security_headers(app)
    init_request_logger(app)

    # ── Prometheus metrics ──────────────────────────────────
    init_metrics(app)

    # ── JWT callbacks ───────────────────────────────────────
    _configure_jwt_callbacks(app)

    # ── Register blueprints ─────────────────────────────────
    _register_blueprints(app)

    # ── Register error handlers ─────────────────────────────
    _register_error_handlers(app)

    # ── Shell context ───────────────────────────────────────
    @app.shell_context_processor
    def _shell_ctx():
        return {"db": db, "app": app}

    return app


def _register_blueprints(app: Flask) -> None:
    """Register all route blueprints."""
    from wanderai.routes.pages import pages_bp
    from wanderai.routes.health import health_bp
    from wanderai.routes.auth import auth_bp
    from wanderai.routes.chat import chat_bp
    from wanderai.routes.trips import trips_bp
    from wanderai.routes.itinerary import itinerary_bp
    from wanderai.routes.budget import budget_bp
    from wanderai.routes.recommendations import recommendations_bp
    from wanderai.routes.profile import profile_bp
    from wanderai.routes.weather import weather_bp

    # HTML page routes (no version prefix)
    app.register_blueprint(pages_bp)

    # API v1 routes
    api_prefix = "/api/v1"
    app.register_blueprint(health_bp, url_prefix=api_prefix)
    app.register_blueprint(auth_bp, url_prefix=f"{api_prefix}/auth")
    app.register_blueprint(chat_bp, url_prefix=f"{api_prefix}/conversations")
    app.register_blueprint(trips_bp, url_prefix=f"{api_prefix}/trips")
    app.register_blueprint(itinerary_bp, url_prefix=f"{api_prefix}/itinerary")
    app.register_blueprint(budget_bp, url_prefix=f"{api_prefix}/budget")
    app.register_blueprint(
        recommendations_bp, url_prefix=f"{api_prefix}/recommendations"
    )
    app.register_blueprint(profile_bp, url_prefix=f"{api_prefix}/profile")
    app.register_blueprint(weather_bp, url_prefix=f"{api_prefix}/weather")


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""
    from wanderai.utils.response import error as api_error
    from flask import render_template, request

    @app.errorhandler(400)
    def bad_request(e):
        if request.path.startswith("/api/"):
            return api_error("Bad request", 400, "BAD_REQUEST")
        return render_template("index.html"), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return api_error("Authentication required", 401, "UNAUTHORIZED")

    @app.errorhandler(403)
    def forbidden(e):
        return api_error("Forbidden", 403, "FORBIDDEN")

    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith("/api/"):
            return api_error("Not found", 404, "NOT_FOUND")
        return render_template("index.html"), 404

    @app.errorhandler(422)
    def unprocessable(e):
        return api_error("Validation failed", 422, "VALIDATION_ERROR")

    @app.errorhandler(429)
    def rate_limited(e):
        return api_error("Rate limit exceeded. Please slow down.", 429, "RATE_LIMITED")

    @app.errorhandler(500)
    def server_error(e):
        from wanderai.observability.logger import get_logger

        get_logger(__name__).error("unhandled_server_error", error=str(e))
        return api_error("Internal server error", 500, "SERVER_ERROR")


def _configure_jwt_callbacks(app: Flask) -> None:
    """Configure JWT error and blocklist callbacks."""
    from wanderai.extensions import jwt

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_data):
        from wanderai.utils.response import error as api_error

        return api_error("Token has expired", 401, "TOKEN_EXPIRED")

    @jwt.invalid_token_loader
    def invalid_token(reason):
        from wanderai.utils.response import error as api_error

        return api_error(f"Invalid token: {reason}", 401, "TOKEN_INVALID")

    @jwt.unauthorized_loader
    def missing_token(reason):
        from wanderai.utils.response import error as api_error

        return api_error("Authentication required", 401, "UNAUTHORIZED")

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(_jwt_header, jwt_data):
        """Check Redis blocklist for revoked JWT IDs.

        Reuses the Flask-Caching extension's connection pool instead of
        opening a new Redis TCP connection on every authenticated request.
        """
        from wanderai.extensions import cache

        jti = jwt_data.get("jti", "")
        if not jti:
            return True
        try:
            return cache.get(f"session:revoked:{jti}") is not None
        except Exception:
            return False  # Fail open if Redis is unavailable
