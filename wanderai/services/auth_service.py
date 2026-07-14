"""
wanderai/services/auth_service.py
Authentication business logic — registration, login, OAuth, token management.
"""
from datetime import datetime

from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, get_jti

from wanderai.extensions import db
from wanderai.models.user import User, UserRole, AuthProvider
from wanderai.models.preference import UserPreference
from wanderai.repositories.user_repository import UserRepository, SessionRepository
from wanderai.utils.security import hash_password, verify_password, generate_token
from wanderai.utils.validators import validate_email, validate_password
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)


class AuthService:
    def __init__(self):
        self._users = UserRepository()
        self._sessions = SessionRepository()

    def register(self, email: str, password: str, username: str | None = None) -> dict:
        """Register a new user with email/password."""
        email = email.lower().strip()

        # Validate inputs
        if not validate_email(email):
            return {"success": False, "error": "Invalid email address"}

        pw_errors = validate_password(password)
        if pw_errors:
            return {"success": False, "error": pw_errors[0]}

        if self._users.email_exists(email):
            return {"success": False, "error": "Email already registered"}

        try:
            verify_token = generate_token(32)
            user = self._users.create(
                email=email,
                username=username,
                password_hash=hash_password(password),
                email_verified=False,
                role=UserRole.USER,
                provider=AuthProvider.LOCAL,
                email_verify_token=verify_token,
            )
            # Create empty preference record
            db.session.add(UserPreference(user_id=user.id))
            db.session.commit()

            logger.info("user_registered", user_id=user.id, email=email)

            # Queue verification email (non-blocking)
            try:
                from wanderai.tasks.email_tasks import send_verification_email
                send_verification_email.delay(user.id)
            except Exception:
                pass  # Don't fail registration if email task is unavailable

            return {"success": True, "user": user}
        except Exception as exc:
            db.session.rollback()
            logger.error("registration_failed", email=email, error=str(exc))
            return {"success": False, "error": "Registration failed. Please try again."}

    def login(self, email: str, password: str, device_info: str = "", ip: str = "") -> dict:
        """Authenticate user and issue JWT token pair."""
        email = email.lower().strip()
        user = self._users.get_by_email(email)

        if not user or not user.password_hash:
            return {"success": False, "error": "Invalid credentials"}

        if not verify_password(password, user.password_hash):
            logger.warning("login_failed_bad_password", email=email, ip=ip)
            return {"success": False, "error": "Invalid credentials"}

        if not user.is_active:
            return {"success": False, "error": "Account is disabled"}

        return self._issue_tokens(user, device_info=device_info, ip=ip)

    def login_oauth(
        self,
        provider: str,
        provider_id: str,
        email: str,
        username: str | None = None,
        avatar_url: str | None = None,
        device_info: str = "",
        ip: str = "",
    ) -> dict:
        """Find or create a user from OAuth provider, issue tokens."""
        user = self._users.get_by_provider(provider, provider_id)

        if not user:
            # Check if email already exists (link accounts)
            user = self._users.get_by_email(email.lower())
            if user:
                # Link OAuth to existing account
                self._users.update(user, provider=provider, provider_id=provider_id)
            else:
                # Create new OAuth user
                try:
                    user = self._users.create(
                        email=email.lower(),
                        username=username,
                        password_hash=None,
                        email_verified=True,    # OAuth emails are pre-verified
                        role=UserRole.USER,
                        provider=provider,
                        provider_id=provider_id,
                        avatar_url=avatar_url,
                    )
                    db.session.add(UserPreference(user_id=user.id))
                    db.session.commit()
                    logger.info("oauth_user_created", provider=provider, user_id=user.id)
                except Exception as exc:
                    db.session.rollback()
                    return {"success": False, "error": str(exc)}

        return self._issue_tokens(user, device_info=device_info, ip=ip)

    def verify_email(self, token: str) -> dict:
        """Verify email address using token from verification email."""
        user = self._users.get_by_verify_token(token)
        if not user:
            return {"success": False, "error": "Invalid or expired token"}
        self._users.update(user, email_verified=True, email_verify_token=None)
        db.session.commit()
        return {"success": True}

    def refresh_tokens(self, refresh_jti: str, user_id: str, device_info: str = "", ip: str = "") -> dict:
        """Issue a new access token given a valid refresh token JTI."""
        session = self._sessions.get_by_jti(refresh_jti)
        if not session or not session.is_active:
            return {"success": False, "error": "Session expired or revoked"}

        user = self._users.get_by_id(user_id)
        if not user or not user.is_active:
            return {"success": False, "error": "User not found"}

        # Revoke old session and issue new token pair
        self._sessions.update(session, is_active=False)
        return self._issue_tokens(user, device_info=device_info, ip=ip)

    def logout(self, jti: str) -> None:
        """Revoke a specific session by JTI."""
        import redis as redis_lib
        try:
            r = redis_lib.from_url(current_app.config["REDIS_URL"])
            ttl = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
            r.setex(f"session:revoked:{jti}", ttl, "1")
        except Exception as exc:
            logger.warning("session_revoke_redis_failed", jti=jti, error=str(exc))

        session = self._sessions.get_by_jti(jti)
        if session:
            self._sessions.update(session, is_active=False)
            db.session.commit()

    def _issue_tokens(self, user: User, device_info: str = "", ip: str = "") -> dict:
        """Create JWT access + refresh tokens and persist the session."""
        additional_claims = {"role": user.role.value, "email_verified": user.email_verified}
        access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
        refresh_token = create_refresh_token(identity=user.id)

        access_jti = get_jti(access_token)
        refresh_jti = get_jti(refresh_token)

        expires_at = datetime.utcnow() + current_app.config["JWT_REFRESH_TOKEN_EXPIRES"]

        try:
            self._sessions.create(
                user_id=user.id,
                token_jti=access_jti,
                refresh_jti=refresh_jti,
                device_info=device_info[:500],
                ip_address=ip[:45],
                is_active=True,
                expires_at=expires_at,
            )
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            logger.error("session_persist_failed", error=str(exc))

        return {
            "success": True,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }
