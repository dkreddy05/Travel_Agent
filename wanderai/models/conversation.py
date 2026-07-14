"""
wanderai/models/conversation.py
Conversation and Message models — replaces browser sessionStorage chat history.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from wanderai.extensions import db


class ContextMode(PyEnum):
    GENERAL = "general"
    ITINERARY = "itinerary"
    BUDGET = "budget"


class MessageRole(PyEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Conversation(db.Model):
    __tablename__ = "conversations"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    trip_id = db.Column(
        db.String(36), db.ForeignKey("trips.id", ondelete="SET NULL"), nullable=True
    )
    context_mode = db.Column(
        db.Enum(ContextMode), default=ContextMode.GENERAL, nullable=False
    )
    title = db.Column(
        db.String(255), nullable=True
    )  # auto-generated from first message
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    user = db.relationship("User", back_populates="conversations")
    trip = db.relationship("Trip", back_populates="conversations")
    messages = db.relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
        lazy="dynamic",
    )

    def to_dict(self, include_messages: bool = False) -> dict:
        d = {
            "id": self.id,
            "trip_id": self.trip_id,
            "context_mode": self.context_mode.value,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages:
            d["messages"] = [m.to_dict() for m in self.messages]
        return d


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = db.Column(
        db.String(36),
        db.ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role = db.Column(db.Enum(MessageRole), nullable=False)
    content = db.Column(db.Text, nullable=False)
    model_used = db.Column(db.String(100), nullable=True)
    tokens_used = db.Column(db.Integer, nullable=True)
    latency_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    conversation = db.relationship("Conversation", back_populates="messages")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role.value,
            "content": self.content,
            "model_used": self.model_used,
            "tokens_used": self.tokens_used,
            "latency_ms": self.latency_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
