"""
wanderai/models/feedback.py
Feedback and AuditLog models.
"""
import uuid
from datetime import datetime
from wanderai.extensions import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False)  # itinerary | budget | message
    entity_id = db.Column(db.String(36), nullable=False)
    rating = db.Column(db.Integer, nullable=False)           # 1–5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="feedback")

    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLog(db.Model):
    """
    Immutable audit trail for all state-changing operations.
    Written by middleware — routes should NOT write to this directly.
    """
    __tablename__ = "audit_logs"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = db.Column(db.String(100), nullable=False, index=True)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)
    metadata = db.Column(db.JSON, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = db.relationship("User", back_populates="audit_logs")

    __table_args__ = (
        db.Index("ix_audit_logs_user_id_created_at", "user_id", "created_at"),
    )
