"""
wanderai/routes/health.py
Health and readiness check endpoints.
"""
from datetime import datetime
from flask import Blueprint, current_app
from wanderai.extensions import db
from wanderai.utils.response import success
from wanderai.observability.health import get_health_report

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """GET /api/v1/health — basic liveness check."""
    return success({
        "status": "ok",
        "version": current_app.config.get("APP_VERSION", "2.0.0"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    })


@health_bp.get("/health/ready")
def readiness():
    """GET /api/v1/health/ready — full readiness check (DB, Redis, AI)."""
    try:
        import redis as redis_lib
        r = redis_lib.from_url(current_app.config.get("REDIS_URL", "redis://localhost:6379/0"))
    except Exception:
        r = None

    report = get_health_report(current_app, db, redis_client=r)
    status_code = 200 if report["status"] == "ok" else 503
    return success(report, status_code=status_code)
