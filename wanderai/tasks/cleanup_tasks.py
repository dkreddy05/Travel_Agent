"""
wanderai/tasks/cleanup_tasks.py
Scheduled maintenance tasks.
"""

from wanderai.tasks import celery


@celery.task(name="tasks.cleanup_expired_sessions")
def cleanup_expired_sessions():
    """Remove expired DB sessions and Redis blocklist entries."""
    from wanderai.app import create_app
    from wanderai.extensions import db
    from datetime import datetime

    app = create_app()
    with app.app_context():
        from wanderai.models.user import UserSession

        expired = UserSession.query.filter(
            UserSession.expires_at < datetime.utcnow(),
            ~UserSession.is_active,
        ).delete()
        db.session.commit()

        from wanderai.observability.logger import get_logger

        get_logger(__name__).info("sessions_cleaned", count=expired)
        return {"cleaned_sessions": expired}
