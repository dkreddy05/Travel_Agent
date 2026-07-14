"""
wanderai/models/trip.py
Trip, Destination, Itinerary models.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from wanderai.extensions import db


class BudgetTier(PyEnum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"


class TripStatus(PyEnum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class Trip(db.Model):
    __tablename__ = "trips"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=True)
    destination = db.Column(db.String(255), nullable=False)
    country_code = db.Column(db.String(3), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    days = db.Column(db.Integer, nullable=False, default=7)
    travelers = db.Column(db.Integer, nullable=False, default=1)
    budget_tier = db.Column(db.Enum(BudgetTier), nullable=True)
    total_budget = db.Column(db.Numeric(10, 2), nullable=True)
    currency = db.Column(db.String(3), default="USD", nullable=False)
    interests = db.Column(db.JSON, default=list)
    transport_preference = db.Column(db.String(100), nullable=True)
    accommodation_preference = db.Column(db.String(100), nullable=True)
    status = db.Column(db.Enum(TripStatus), default=TripStatus.DRAFT, nullable=False)
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
    user = db.relationship("User", back_populates="trips")
    itinerary = db.relationship(
        "Itinerary", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    budget = db.relationship(
        "Budget", back_populates="trip", uselist=False, cascade="all, delete-orphan"
    )
    conversations = db.relationship(
        "Conversation", back_populates="trip", lazy="dynamic"
    )

    __table_args__ = (db.Index("ix_trips_user_id_status", "user_id", "status"),)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "destination": self.destination,
            "country_code": self.country_code,
            "days": self.days,
            "travelers": self.travelers,
            "budget_tier": self.budget_tier.value if self.budget_tier else None,
            "total_budget": float(self.total_budget) if self.total_budget else None,
            "currency": self.currency,
            "interests": self.interests,
            "status": self.status.value,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Itinerary(db.Model):
    __tablename__ = "itineraries"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id = db.Column(
        db.String(36),
        db.ForeignKey("trips.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    raw_text = db.Column(db.Text, nullable=False)
    structured_json = db.Column(db.JSON, nullable=True)
    model_used = db.Column(db.String(100), nullable=True)
    prompt_version = db.Column(db.String(20), nullable=True)
    generation_time_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    raw_text = db.Column(db.Text, nullable=False)
    structured_json = db.Column(db.JSON, nullable=True)
    model_used = db.Column(db.String(100), nullable=True)
    prompt_version = db.Column(db.String(20), nullable=True)
    generation_time_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    trip = db.relationship("Trip", back_populates="itinerary")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "trip_id": self.trip_id,
            "raw_text": self.raw_text,
            "structured_json": self.structured_json,
            "model_used": self.model_used,
            "prompt_version": self.prompt_version,
            "generation_time_ms": self.generation_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
