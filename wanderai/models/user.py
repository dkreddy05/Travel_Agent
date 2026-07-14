"""
wanderai/models/user.py
User, UserSession models.
Uses UUID primary keys throughout for security and portability.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from wanderai.extensions import db


class UserRole(PyEnum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"


class AuthProvider(PyEnum):
    LOCAL = "local"
    GOOGLE = "google"
    GITHUB = "github"


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=True)  # null for OAuth users
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.USER, nullable=False)
    provider = db.Column(
        db.Enum(AuthProvider), default=AuthProvider.LOCAL, nullable=False
    )
    provider_id = db.Column(db.String(255), nullable=True)  # OAuth provider user ID
    avatar_url = db.Column(db.String(500), nullable=True)
    email_verify_token = db.Column(db.String(128), nullable=True, index=True)
    password_reset_token = db.Column(db.String(128), nullable=True, index=True)
    password_reset_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    sessions = db.relationship(
        "UserSession",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    trips = db.relationship(
        "Trip", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    conversations = db.relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )
    preferences = db.relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feedback = db.relationship(
        "Feedback", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )
    audit_logs = db.relationship(
        "AuditLog", back_populates="user", cascade="all, delete-orphan", lazy="dynamic"
    )

    # Composite index for OAuth lookup
    __table_args__ = (
        db.Index("ix_users_provider_provider_id", "provider", "provider_id"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "email_verified": self.email_verified,
            "role": self.role.value,
            "provider": self.provider.value,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.email}>"


class UserSession(db.Model):
    """Tracks per-device JWT sessions for multi-device revocation."""

    __tablename__ = "user_sessions"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token_jti = db.Column(db.String(255), unique=True, nullable=False, index=True)
    refresh_jti = db.Column(db.String(255), unique=True, nullable=True, index=True)
    device_info = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)  # IPv6 max 45 chars
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = db.relationship("User", back_populates="sessions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "device_info": self.device_info,
            "ip_address": self.ip_address,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
