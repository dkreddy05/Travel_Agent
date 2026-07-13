"""
wanderai/tasks/email_tasks.py
Email delivery Celery tasks.
"""
from wanderai.tasks import celery


@celery.task(bind=True, max_retries=5, default_retry_delay=60, name="tasks.send_verification_email")
def send_verification_email(self, user_id: str):
    """Send email verification link to user."""
    from wanderai.app import create_app
    app = create_app()
    with app.app_context():
        from wanderai.repositories.user_repository import UserRepository
        from flask_mail import Message
        from wanderai.extensions import mail

        try:
            user = UserRepository().get_by_id(user_id)
            if not user or not user.email_verify_token:
                return

            verify_url = f"{app.config['APP_URL']}/api/v1/auth/verify-email/{user.email_verify_token}"

            msg = Message(
                subject="Verify your WanderAI account",
                recipients=[user.email],
                html=f"""
                <h2>Welcome to WanderAI! ✈️</h2>
                <p>Please verify your email address by clicking the link below:</p>
                <p><a href="{verify_url}" style="background:#3b82d4;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">Verify Email</a></p>
                <p>Link expires in 24 hours.</p>
                <p>If you didn't create an account, you can ignore this email.</p>
                """,
            )
            mail.send(msg)
        except Exception as exc:
            raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=3, name="tasks.send_password_reset")
def send_password_reset_email(self, user_id: str, reset_token: str):
    """Send password reset email."""
    from wanderai.app import create_app
    app = create_app()
    with app.app_context():
        from wanderai.repositories.user_repository import UserRepository
        from flask_mail import Message
        from wanderai.extensions import mail

        try:
            user = UserRepository().get_by_id(user_id)
            if not user:
                return

            reset_url = f"{app.config['APP_URL']}/reset-password?token={reset_token}"

            msg = Message(
                subject="Reset your WanderAI password",
                recipients=[user.email],
                html=f"""
                <h2>Password Reset Request</h2>
                <p>Click below to reset your password. Link expires in 1 hour.</p>
                <p><a href="{reset_url}">Reset Password</a></p>
                """,
            )
            mail.send(msg)
        except Exception as exc:
            raise self.retry(exc=exc)
