"""initial_schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("username", sa.String(80), nullable=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "email_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "role",
            sa.Enum("user", "premium", "admin", name="userrole"),
            nullable=False,
            server_default="user",
        ),
        sa.Column(
            "provider",
            sa.Enum("local", "google", "github", name="authprovider"),
            nullable=False,
            server_default="local",
        ),
        sa.Column("provider_id", sa.String(255), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verify_token", sa.String(128), nullable=True),
        sa.Column("password_reset_token", sa.String(128), nullable=True),
        sa.Column("password_reset_expires", sa.DateTime(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index(
        "ix_users_email_verify_token", "users", ["email_verify_token"], unique=False
    )
    op.create_index(
        "ix_users_password_reset_token", "users", ["password_reset_token"], unique=False
    )
    op.create_index(
        "ix_users_provider_provider_id",
        "users",
        ["provider", "provider_id"],
        unique=False,
    )

    # ── user_sessions ──────────────────────────────────────────────────────
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_jti", sa.String(255), nullable=False),
        sa.Column("refresh_jti", sa.String(255), nullable=True),
        sa.Column("device_info", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index(
        "ix_user_sessions_user_id", "user_sessions", ["user_id"], unique=False
    )
    op.create_index(
        "ix_user_sessions_token_jti", "user_sessions", ["token_jti"], unique=True
    )
    op.create_index(
        "ix_user_sessions_refresh_jti", "user_sessions", ["refresh_jti"], unique=True
    )

    # ── user_preferences ──────────────────────────────────────────────────
    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("budget_tier", sa.String(20), nullable=True),
        sa.Column("trip_styles", sa.JSON(), nullable=True),
        sa.Column("dietary", sa.JSON(), nullable=True),
        sa.Column("home_country", sa.String(100), nullable=True),
        sa.Column("passport_country", sa.String(100), nullable=True),
        sa.Column("preferred_transport", sa.String(100), nullable=True),
        sa.Column("preferred_accommodation", sa.String(100), nullable=True),
        sa.Column("dream_destinations", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index(
        "ix_user_preferences_user_id", "user_preferences", ["user_id"], unique=True
    )

    # ── trips ─────────────────────────────────────────────────────────────
    op.create_table(
        "trips",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("destination", sa.String(255), nullable=False),
        sa.Column("country_code", sa.String(3), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("days", sa.Integer(), nullable=False, server_default="7"),
        sa.Column("travelers", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "budget_tier",
            sa.Enum("budget", "mid-range", "luxury", name="budgettier"),
            nullable=True,
        ),
        sa.Column("total_budget", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column("transport_preference", sa.String(100), nullable=True),
        sa.Column("accommodation_preference", sa.String(100), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "draft", "planned", "active", "completed", "archived", name="tripstatus"
            ),
            nullable=False,
            server_default="draft",
        ),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_trips_user_id", "trips", ["user_id"], unique=False)
    op.create_index(
        "ix_trips_user_id_status", "trips", ["user_id", "status"], unique=False
    )

    # ── itineraries ───────────────────────────────────────────────────────
    op.create_table(
        "itineraries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "trip_id",
            sa.String(36),
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(20), nullable=True),
        sa.Column("generation_time_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_itineraries_trip_id", "itineraries", ["trip_id"], unique=True)

    # ── budgets ───────────────────────────────────────────────────────────
    op.create_table(
        "budgets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "trip_id",
            sa.String(36),
            sa.ForeignKey("trips.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("breakdown", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_budgets_trip_id", "budgets", ["trip_id"], unique=True)

    # ── conversations ─────────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "trip_id",
            sa.String(36),
            sa.ForeignKey("trips.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "context_mode",
            sa.Enum("general", "itinerary", "budget", name="contextmode"),
            nullable=False,
            server_default="general",
        ),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.Column(
            "updated_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index(
        "ix_conversations_user_id", "conversations", ["user_id"], unique=False
    )

    # ── messages ──────────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "conversation_id",
            sa.String(36),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "role",
            sa.Enum("user", "assistant", "system", name="messagerole"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index(
        "ix_messages_conversation_id", "messages", ["conversation_id"], unique=False
    )
    op.create_index("ix_messages_created_at", "messages", ["created_at"], unique=False)

    # ── recommendations ───────────────────────────────────────────────────
    op.create_table(
        "recommendations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column("budget_tier", sa.String(20), nullable=True),
        sa.Column("season", sa.String(20), nullable=True),
        sa.Column("from_country", sa.String(100), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("structured_json", sa.JSON(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index(
        "ix_recommendations_user_id", "recommendations", ["user_id"], unique=False
    )

    # ── feedback ──────────────────────────────────────────────────────────
    op.create_table(
        "feedback",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating"),
    )

    # ── audit_logs ────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", sa.String(36), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(300), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.text("NOW()")
        ),
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"], unique=False)
    op.create_index(
        "ix_audit_logs_created_at", "audit_logs", ["created_at"], unique=False
    )
    op.create_index(
        "ix_audit_logs_user_id_created_at",
        "audit_logs",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("feedback")
    op.drop_table("recommendations")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("budgets")
    op.drop_table("itineraries")
    op.drop_table("trips")
    op.drop_table("user_preferences")
    op.drop_table("user_sessions")
    op.drop_table("users")
    # Drop enum types (PostgreSQL keeps them after table drop)
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS authprovider")
    op.execute("DROP TYPE IF EXISTS budgettier")
    op.execute("DROP TYPE IF EXISTS tripstatus")
    op.execute("DROP TYPE IF EXISTS contextmode")
    op.execute("DROP TYPE IF EXISTS messagerole")
