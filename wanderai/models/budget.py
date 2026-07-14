"""
wanderai/models/budget.py
Budget model for storing AI-generated budget plans.
"""

import uuid
from datetime import datetime, timezone
from wanderai.extensions import db


class Budget(db.Model):
    __tablename__ = "budgets"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = db.Column(
        db.String(36),
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    raw_text = db.Column(db.Text, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), default="USD", nullable=False)
    breakdown = db.Column(
        db.JSON, nullable=True
    )  # {accommodation, food, transport, activities, misc}
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    trip = db.relationship("Trip", back_populates="budget")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "raw_text": self.raw_text,
            "total_amount": float(self.total_amount) if self.total_amount else None,
            "currency": self.currency,
            "breakdown": self.breakdown,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
