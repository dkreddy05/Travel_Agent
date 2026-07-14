"""
wanderai/routes/chat.py
Conversation and message endpoints.
Replaces the old /api/chat with persistent DB-backed conversations.
"""

from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from wanderai.extensions import db
from wanderai.models.conversation import MessageRole, ContextMode
from wanderai.repositories.conversation_repository import (
    ConversationRepository,
    MessageRepository,
)
from wanderai.utils.response import success, created, error, not_found
from wanderai.utils.pagination import PaginationParams
from wanderai.utils.validators import detect_prompt_injection, validate_message_length
from wanderai.extensions import limiter

chat_bp = Blueprint("chat", __name__)
_conv_repo = ConversationRepository()
_msg_repo = MessageRepository()


@chat_bp.post("")
@jwt_required()
def create_conversation():
    """POST /api/v1/conversations — create a new conversation."""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    context_mode = data.get("context_mode", "general")
    try:
        mode = ContextMode(context_mode)
    except ValueError:
        mode = ContextMode.GENERAL

    conv = _conv_repo.create(user_id=user_id, context_mode=mode)
    db.session.commit()
    return created(conv.to_dict())


@chat_bp.get("")
@jwt_required()
def list_conversations():
    """GET /api/v1/conversations — list user's conversations (paginated)."""
    user_id = get_jwt_identity()
    params = PaginationParams.from_request()
    result = _conv_repo.get_user_conversations(user_id, params)
    return success(
        data=[c.to_dict() for c in result.items],
        meta=result.to_meta(),
    )


@chat_bp.get("/<conversation_id>/messages")
@jwt_required()
def get_messages(conversation_id: str):
    """GET /api/v1/conversations/{id}/messages — get paginated message history."""
    user_id = get_jwt_identity()
    conv = _conv_repo.get_user_conversation(user_id, conversation_id)
    if not conv:
        return not_found("Conversation")

    params = PaginationParams.from_request()
    result = _msg_repo.get_conversation_messages(conversation_id, params)
    return success(
        data=[m.to_dict() for m in result.items],
        meta=result.to_meta(),
    )


@chat_bp.post("/<conversation_id>/messages")
@jwt_required()
@limiter.limit("60 per hour", key_func=lambda: get_jwt_identity())
def send_message(conversation_id: str):
    """POST /api/v1/conversations/{id}/messages — send a message, get AI reply."""
    user_id = get_jwt_identity()
    conv = _conv_repo.get_user_conversation(user_id, conversation_id)
    if not conv:
        return not_found("Conversation")

    data = request.get_json(silent=True) or {}
    message_text = data.get("message", "").strip()

    if not message_text:
        return error("Message cannot be empty", 400)

    # Validate message length
    length_err = validate_message_length(message_text, max_len=2000)
    if length_err:
        return error(length_err, 400, "MESSAGE_TOO_LONG")

    # Prompt injection guard
    if detect_prompt_injection(message_text):
        return error("Message contains disallowed content", 400, "PROMPT_INJECTION")

    # Save user message
    _msg_repo.create(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=message_text,
    )

    # Run AI pipeline
    try:
        from wanderai.ai.pipeline import run_chat

        extra_context = data.get("context", {})
        result = run_chat(
            user_message=message_text,
            conversation_id=conversation_id,
            task=conv.context_mode.value,
            extra_context=extra_context,
        )
        reply_text = result["text"]
        model_used = result.get("model", "")
        tokens_used = result.get("tokens_used")
        latency_ms = result.get("latency_ms")
    except Exception as exc:
        from wanderai.observability.logger import get_logger

        get_logger(__name__).error("chat_pipeline_error", error=str(exc))
        reply_text = f"⚠️ WanderAI encountered an error: {exc}"
        model_used = ""
        tokens_used = None
        latency_ms = None

    # Save assistant message
    assistant_msg = _msg_repo.create(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=reply_text,
        model_used=model_used,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
    )

    # Update conversation title from first user message
    if not conv.title:
        _conv_repo.update(conv, title=message_text[:80])

    db.session.commit()

    return success(
        {
            "message": assistant_msg.to_dict(),
            "timestamp": datetime.utcnow().strftime("%H:%M"),
        }
    )
