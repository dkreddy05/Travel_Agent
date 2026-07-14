"""
wanderai/models/recommendation.py
Recommendation model — persists AI destination recommendations.
"""

import uuid
from datetime import datetime, timezone
from wanderai.extensions import db


class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interests = db.Column(db.JSON, default=list)
    budget_tier = db.Column(db.String(20), nullable=True)
    season = db.Column(db.String(20), nullable=True)
    from_country = db.Column(db.String(100), nullable=True)
    raw_text = db.Column(db.Text, nullable=False)
    structured_json = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "interests": self.interests,
            "budget_tier": self.budget_tier,
            "season": self.season,
            "raw_text": self.raw_text,
            "structured_json": self.structured_json,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
