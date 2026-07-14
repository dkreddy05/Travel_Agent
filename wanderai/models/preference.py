"""
wanderai/models/preference.py
UserPreference model — replaces Flask session["user_profile"].
"""

import uuid
from datetime import datetime
from wanderai.extensions import db


class UserPreference(db.Model):
    __tablename__ = "user_preferences"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    budget_tier = db.Column(db.String(20), nullable=True)  # budget / mid-range / luxury
    trip_styles = db.Column(db.JSON, default=list)  # ["Adventure", "Cultural", ...]
    dietary = db.Column(db.JSON, default=list)  # ["vegetarian", "halal", ...]
    home_country = db.Column(db.String(100), nullable=True)
    passport_country = db.Column(db.String(100), nullable=True)
    preferred_transport = db.Column(db.String(100), nullable=True)
    preferred_accommodation = db.Column(db.String(100), nullable=True)
    dream_destinations = db.Column(db.JSON, default=list)
    notes = db.Column(db.Text, nullable=True)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="preferences")

    def to_dict(self) -> dict:
        return {
            "budget_tier": self.budget_tier,
            "trip_styles": self.trip_styles,
            "dietary": self.dietary,
            "home_country": self.home_country,
            "passport_country": self.passport_country,
            "preferred_transport": self.preferred_transport,
            "preferred_accommodation": self.preferred_accommodation,
            "dream_destinations": self.dream_destinations,
            "notes": self.notes,
        }
