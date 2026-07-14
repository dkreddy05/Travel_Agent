"""
wanderai/repositories/user_repository.py
User data access — auth lookups, OAuth upsert, session management.
"""

from typing import Optional
from wanderai.models.user import User, UserSession
from wanderai.repositories.base import BaseRepository
from wanderai.extensions import db


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)

    def get_by_email(self, email: str) -> Optional[User]:
        return User.query.filter_by(email=email.lower()).first()

    def get_by_verify_token(self, token: str) -> Optional[User]:
        return User.query.filter_by(email_verify_token=token).first()

    def get_by_reset_token(self, token: str) -> Optional[User]:
        return User.query.filter_by(password_reset_token=token).first()

    def get_by_provider(self, provider: str, provider_id: str) -> Optional[User]:
        return User.query.filter_by(provider=provider, provider_id=provider_id).first()

    def email_exists(self, email: str) -> bool:
        return db.session.query(
            User.query.filter_by(email=email.lower()).exists()
        ).scalar()


class SessionRepository(BaseRepository[UserSession]):
    def __init__(self):
        super().__init__(UserSession)

    def get_by_jti(self, jti: str) -> Optional[UserSession]:
        return UserSession.query.filter_by(token_jti=jti).first()

    def get_active_sessions(self, user_id: str) -> list[UserSession]:
        return UserSession.query.filter_by(user_id=user_id, is_active=True).all()

    def revoke_all_user_sessions(self, user_id: str) -> int:
        """Revoke all active sessions for a user. Returns count revoked."""
        count = UserSession.query.filter_by(user_id=user_id, is_active=True).update(
            {"is_active": False}
        )
        db.session.flush()
        return count
