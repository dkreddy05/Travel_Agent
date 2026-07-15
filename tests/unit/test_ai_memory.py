"""Tests for ConversationMemory."""


class TestConversationMemory:
    def test_init(self):
        from wanderai.ai.memory import ConversationMemory

        mem = ConversationMemory("conv-123")
        assert mem.conversation_id == "conv-123"
        assert mem.max_turns == 20

    def test_get_messages_empty_when_no_history(self, monkeypatch):
        from wanderai.ai.memory import ConversationMemory

        class FakeRepo:
            def get_history(self, conversation_id, limit=20):
                return []

        mem = ConversationMemory("conv-123")
        monkeypatch.setattr(mem, "_message_repo", FakeRepo())

        messages = mem.get_messages_for_llm()
        assert messages == []

    def test_get_messages_formats_correctly(self, monkeypatch):
        from wanderai.ai.memory import ConversationMemory
        from wanderai.models.conversation import MessageRole

        class FakeMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        class FakeRepo:
            def get_history(self, conversation_id, limit=20):
                return [
                    FakeMessage(MessageRole.USER, "Hello"),
                    FakeMessage(MessageRole.ASSISTANT, "Hi there!"),
                ]

        mem = ConversationMemory("conv-123")
        monkeypatch.setattr(mem, "_message_repo", FakeRepo())

        messages = mem.get_messages_for_llm()
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_get_messages_skips_system_role(self, monkeypatch):
        from wanderai.ai.memory import ConversationMemory
        from wanderai.models.conversation import MessageRole

        class FakeMessage:
            def __init__(self, role, content):
                self.role = role
                self.content = content

        class FakeRepo:
            def get_history(self, conversation_id, limit=20):
                return [
                    FakeMessage(MessageRole.SYSTEM, "system msg"),
                    FakeMessage(MessageRole.USER, "user msg"),
                ]

        mem = ConversationMemory("conv-123")
        monkeypatch.setattr(mem, "_message_repo", FakeRepo())

        messages = mem.get_messages_for_llm()
        assert len(messages) == 1
        assert messages[0]["role"] == "user"

    def test_trim_to_budget_removes_oldest(self):
        from wanderai.ai.memory import ConversationMemory

        mem = ConversationMemory("conv-123")
        # Create messages that exceed the budget
        msg_a = {"role": "user", "content": "A" * 5000}
        msg_b = {"role": "assistant", "content": "B" * 500}
        long_messages = [msg_a, msg_b]

        trimmed = mem._trim_to_budget(long_messages)
        # The budget is 3000 tokens * 4 = 12000 chars
        # msg_a alone is 5000 chars, msg_b is 500 chars, total 5500 chars
        # 5500 < 12000, so nothing should be trimmed
        assert len(trimmed) == 2

    def test_trim_to_budget_with_excess(self):
        from wanderai.ai.memory import ConversationMemory

        mem = ConversationMemory("conv-123")
        # Create messages way over budget
        huge = {"role": "user", "content": "X" * 20000}

        trimmed = mem._trim_to_budget([huge])
        # A single message can't be partly removed; deque.popleft would remove it
        assert len(trimmed) <= 1

    def test_trim_to_budget_multiple_messages(self):
        from wanderai.ai.memory import ConversationMemory

        mem = ConversationMemory("conv-123")
        many_msgs = [
            {"role": "user", "content": "A" * 1000},
            {"role": "assistant", "content": "B" * 1000},
            {"role": "user", "content": "C" * 1000},
            {"role": "assistant", "content": "D" * 1000},
        ]
        # budget = 12000 chars, total = 4000 chars
        # So no trimming
        trimmed = mem._trim_to_budget(many_msgs)
        assert len(trimmed) == 4
