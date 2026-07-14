"""
wanderai/repositories/conversation_repository.py
Conversation and Message data access.
"""

from typing import Optional
from wanderai.models.conversation import Conversation, Message
from wanderai.repositories.base import BaseRepository
from wanderai.utils.pagination import PaginationParams, paginate_query, PaginatedResult


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self):
        super().__init__(Conversation)

    def get_user_conversations(
        self, user_id: str, params: PaginationParams
    ) -> PaginatedResult:
        query = Conversation.query.filter_by(user_id=user_id).order_by(
            Conversation.updated_at.desc()
        )
        return paginate_query(query, params)

    def get_user_conversation(
        self, user_id: str, conversation_id: str
    ) -> Optional[Conversation]:
        return Conversation.query.filter_by(id=conversation_id, user_id=user_id).first()


class MessageRepository(BaseRepository[Message]):
    def __init__(self):
        super().__init__(Message)

    def get_conversation_messages(
        self, conversation_id: str, params: PaginationParams
    ) -> PaginatedResult:
        query = Message.query.filter_by(conversation_id=conversation_id).order_by(
            Message.created_at.asc()
        )
        return paginate_query(query, params)

    def get_history(self, conversation_id: str, limit: int = 20) -> list[Message]:
        """Get the last N messages for LLM context."""
        return (
            Message.query.filter_by(conversation_id=conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
            .all()[::-1]  # reverse to chronological order
        )
