"""Tests for AI pipeline module."""

import pytest


class TestPipelineInit:
    def test_init_pipeline_sets_global_client(self):
        from wanderai.ai import pipeline

        pipeline._ai_client = None
        pipeline.init_pipeline({"AI_PRIMARY_MODEL": "test-model"})
        assert pipeline._ai_client is not None
        assert pipeline._ai_client.primary_model == "test-model"

    def test_get_client_raises_if_not_initialized(self):
        from wanderai.ai import pipeline

        pipeline._ai_client = None
        with pytest.raises(RuntimeError, match="not initialized"):
            pipeline.get_client()

    def test_get_client_returns_initialized(self):
        from wanderai.ai import pipeline

        pipeline._ai_client = None
        pipeline.init_pipeline({"AI_PRIMARY_MODEL": "test-model"})
        client = pipeline.get_client()
        assert client is not None


class TestRunSinglePrompt:
    def test_run_single_prompt_success(self, monkeypatch):
        from wanderai.ai import pipeline

        pipeline._ai_client = None
        pipeline.init_pipeline({"AI_PRIMARY_MODEL": "test-model"})

        class FakeClient:
            def complete(self, messages, model=None, max_tokens=None, temperature=None):
                return {
                    "text": "Here is your travel plan!",
                    "model": "test-model",
                    "tokens_used": 50,
                    "latency_ms": 100,
                    "cached": False,
                }

        monkeypatch.setattr(pipeline, "_ai_client", FakeClient())

        from flask import Flask

        app = Flask(__name__)
        app.config["AI_PRIMARY_MODEL"] = "test-model"
        with app.app_context():
            result = pipeline.run_single_prompt("Plan a trip to Paris")

        assert result["text"] == "Here is your travel plan!"
        assert result["model"] == "test-model"
        assert result["tokens_used"] == 50
        assert result["latency_ms"] == 100
        assert result["cached"] is False


class TestRunChat:
    def test_run_chat_success(self, monkeypatch):
        from wanderai.ai import pipeline

        pipeline._ai_client = None
        pipeline.init_pipeline({"AI_PRIMARY_MODEL": "test-model"})

        long_response = "Here is your detailed itinerary! " * 4
        class FakeClient:
            def complete(self, messages, model=None, max_tokens=None, temperature=None):
                # Add a tiny sleep to ensure pipeline_ms > 0
                import time
                time.sleep(0.002)
                return {
                    "text": long_response,
                    "model": "test-model",
                    "tokens_used": 100,
                    "latency_ms": 200,
                    "cached": False,
                }

        monkeypatch.setattr(pipeline, "_ai_client", FakeClient())

        class FakeMemory:
            def __init__(self, conversation_id):
                pass

            def get_messages_for_llm(self):
                return [{"role": "assistant", "content": "Previous response"}]

        monkeypatch.setattr(pipeline, "ConversationMemory", FakeMemory)

        def fake_rag(query, context=None):
            return []

        monkeypatch.setattr(pipeline, "_retrieve_rag_context", fake_rag)

        from flask import Flask

        app = Flask(__name__)
        app.config["AI_PRIMARY_MODEL"] = "test-model"
        with app.app_context():
            result = pipeline.run_chat(
                user_message="Tell me about Paris",
                conversation_id="conv-123",
                task="itinerary",
            )

        assert result["text"] == long_response.strip()
        assert result["model"] == "test-model"
        assert result["pipeline_ms"] >= 0


class TestRetrieveRagContext:
    def test_retrieve_rag_returns_empty_on_error(self, monkeypatch):
        from wanderai.ai import pipeline

        def failing_retrieve(query, top_k=4):
            raise Exception("Qdrant unavailable")

        monkeypatch.setattr("wanderai.ai.rag.retriever.retrieve", failing_retrieve)

        result = pipeline._retrieve_rag_context("Paris")
        assert result == []

    def test_retrieve_rag_with_destination_context(self, monkeypatch):
        from wanderai.ai import pipeline

        def mock_retrieve(query, top_k=4):
            assert "Tokyo" in query
            return [{"text": "Tokyo is great in spring", "score": 0.9}]

        monkeypatch.setattr("wanderai.ai.rag.retriever.retrieve", mock_retrieve)

        result = pipeline._retrieve_rag_context("What to do?", {"destination": "Tokyo"})
        assert len(result) == 1
        assert "Tokyo" in result[0]
