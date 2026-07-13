"""
wanderai/observability/health.py
Health and readiness check logic.
"""
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)


def check_database(db) -> dict:
    """Verify PostgreSQL connectivity."""
    try:
        db.session.execute(db.text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error("db_health_check_failed", error=str(e))
        return {"status": "error", "detail": str(e)}


def check_redis(redis_client) -> dict:
    """Verify Redis connectivity."""
    try:
        redis_client.ping()
        return {"status": "ok"}
    except Exception as e:
        logger.error("redis_health_check_failed", error=str(e))
        return {"status": "error", "detail": str(e)}


def check_ai(config) -> dict:
    """Verify AI credentials are configured."""
    if config.get("WATSONX_API_KEY") and config.get("WATSONX_PROJECT_ID"):
        return {"status": "ok", "model": config.get("AI_PRIMARY_MODEL")}
    return {"status": "unconfigured", "detail": "WATSONX credentials not set"}


def get_health_report(app, db, redis_client=None) -> dict:
    from datetime import datetime
    report = {
        "status": "ok",
        "version": app.config.get("APP_VERSION", "2.0.0"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "database": check_database(db),
            "ai": check_ai(app.config),
        },
    }
    if redis_client:
        report["checks"]["redis"] = check_redis(redis_client)

    # Overall status = degraded if any check failed
    failed = [k for k, v in report["checks"].items() if v.get("status") == "error"]
    if failed:
        report["status"] = "degraded"

    return report
