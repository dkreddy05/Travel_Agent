"""
wanderai/ai/memory.py
DB-backed conversation memory manager.
Replaces browser sessionStorage chat history with persistent DB storage.
"""

from wanderai.repositories.conversation_repository import MessageRepository
from wanderai.models.conversation import MessageRole


class ConversationMemory:
    """
    Loads and formats conversation history from the database for LLM context.
    Manages token budget — limits context to avoid exceeding model window.
    """

    # Rough estimate: 1 token ≈ 4 chars in English
    CHARS_PER_TOKEN = 4
    MAX_CONTEXT_TOKENS = 3000  # leave room for system prompt + response

    def __init__(self, conversation_id: str, max_turns: int = 20):
        self.conversation_id = conversation_id
        self.max_turns = max_turns
        self._message_repo = MessageRepository()

    def get_messages_for_llm(self) -> list[dict]:
        """
        Return the last N message turns as LLM-formatted dicts.
        Trims to MAX_CONTEXT_TOKENS from the most recent messages.
        """
        messages = self._message_repo.get_history(
            self.conversation_id, limit=self.max_turns
        )

        formatted = []
        for msg in messages:
            if msg.role in (MessageRole.USER, MessageRole.ASSISTANT):
                formatted.append(
                    {
                        "role": msg.role.value,
                        "content": msg.content,
                    }
                )

        # Trim to token budget from the tail (most recent wins)
        return self._trim_to_budget(formatted)

    def _trim_to_budget(self, messages: list[dict]) -> list[dict]:
        """Remove oldest messages until context fits within token budget."""
        total_chars = sum(len(m["content"]) for m in messages)
        while messages and total_chars > self.MAX_CONTEXT_TOKENS * self.CHARS_PER_TOKEN:
            removed = messages.pop(0)
            total_chars -= len(removed["content"])
        return messages
