"""Tests for AI agents module."""

import pytest


class FakeClient:
    def complete(self, messages, model=None, max_tokens=None, temperature=None,
                 use_cache=True):
        return {"text": "Test response"}


class TestCoordinator:
    def test_coordinator_node_classifies_intent(self, monkeypatch):
        from wanderai.ai.agents.coordinator import coordinator_node
        import wanderai.ai.pipeline as pipeline_mod

        class MockClient:
            def complete(self, **kwargs):
                return {"text": "itinerary"}

        pipeline_mod._ai_client = MockClient()
        monkeypatch.setattr("wanderai.ai.pipeline._ai_client", MockClient())

        state = {
            "user_message": "Plan a 5-day trip to Paris",
            "agent_outputs": {},
        }
        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.agents.coordinator.logger",
                      type("FakeLogger", (), {"warning": lambda *a, **kw: None, "info": lambda *a, **kw: None})())
            result = coordinator_node(state)
        assert result["intent"] == "itinerary"

    def test_coordinator_defaults_to_general_on_error(self, monkeypatch):
        from wanderai.ai.agents.coordinator import coordinator_node
        import wanderai.ai.pipeline as pipeline_mod

        class FailingClient:
            def complete(self, **kwargs):
                raise RuntimeError("API down")

        pipeline_mod._ai_client = FailingClient()

        state = {
            "user_message": "Hello",
            "agent_outputs": {},
        }
        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.agents.coordinator.logger",
                      type("FakeLogger", (), {"warning": lambda *a, **kw: None, "info": lambda *a, **kw: None})())
            result = coordinator_node(state)
        assert result["intent"] == "general"

    def test_coordinator_validates_intent(self, monkeypatch):
        from wanderai.ai.agents.coordinator import coordinator_node
        import wanderai.ai.pipeline as pipeline_mod

        class MockClient:
            def complete(self, **kwargs):
                return {"text": "invalid_intent_xyz"}

        pipeline_mod._ai_client = MockClient()

        state = {
            "user_message": "Do something",
            "agent_outputs": {},
        }
        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.agents.coordinator.logger",
                      type("FakeLogger", (), {"warning": lambda *a, **kw: None, "info": lambda *a, **kw: None})())
            result = coordinator_node(state)
        assert result["intent"] == "general"


class TestPlanner:
    def test_planner_node_generates_itinerary(self, monkeypatch):
        from wanderai.ai.agents.planner import planner_node

        fake_client = FakeClient()
        original_complete = fake_client.complete

        def capturing_complete(messages, model=None, max_tokens=None, temperature=None):
            return {"text": "Day 1: Visit Eiffel Tower"}

        fake_client.complete = capturing_complete
        monkeypatch.setattr(
            "wanderai.ai.pipeline.get_client", lambda: fake_client
        )

        state = {
            "user_message": "Plan a trip to Paris",
            "destination": "Paris",
            "days": 5,
            "budget_tier": "mid-range",
            "interests": ["culture"],
            "travelers": 2,
            "transport": "public",
            "accommodation": "hotel",
            "agent_outputs": {},
            "rag_context": [],
        }
        result = planner_node(state)
        assert "planner" in result["agent_outputs"]
        assert "Eiffel Tower" in result["agent_outputs"]["planner"]

    def test_planner_with_rag_context(self, monkeypatch):
        from wanderai.ai.agents.planner import planner_node

        fake_client = FakeClient()

        def capturing_complete(messages, model=None, max_tokens=None, temperature=None):
            return {"text": "Itinerary with RAG context"}

        fake_client.complete = capturing_complete
        monkeypatch.setattr(
            "wanderai.ai.pipeline.get_client", lambda: fake_client
        )

        state = {
            "user_message": "Plan a trip",
            "destination": "Tokyo",
            "days": 3,
            "budget_tier": "budget",
            "interests": ["food"],
            "travelers": 1,
            "transport": "walking",
            "accommodation": "hostel",
            "agent_outputs": {},
            "rag_context": ["Tokyo has great street food"],
        }
        result = planner_node(state)
        assert "planner" in result["agent_outputs"]

    def test_planner_handles_error(self, monkeypatch):
        from wanderai.ai.agents.planner import planner_node

        def failing_client():
            raise RuntimeError("LLM unavailable")

        monkeypatch.setattr("wanderai.ai.pipeline.get_client", failing_client)

        state = {
            "user_message": "Plan",
            "destination": "Nowhere",
            "days": 1,
            "budget_tier": "budget",
            "interests": [],
            "travelers": 1,
            "transport": "",
            "accommodation": "",
            "agent_outputs": {},
            "rag_context": [],
        }
        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.agents.planner.logger",
                      type("FakeLogger", (), {"error": lambda *a, **kw: None})())
            result = planner_node(state)
        assert "planner" in result["agent_outputs"]
        assert "Could not generate" in result["agent_outputs"]["planner"]


class TestReviewer:
    def test_reviewer_skips_when_single_output(self, monkeypatch):
        from wanderai.ai.agents.reviewer import reviewer_node

        state = {
            "agent_outputs": {"planner": "Final plan"},
            "user_message": "",
        }
        result = reviewer_node(state)
        assert result["final_response"] == "Final plan"

    def test_reviewer_handles_empty_outputs(self):
        from wanderai.ai.agents.reviewer import reviewer_node

        state = {
            "agent_outputs": {},
            "user_message": "",
        }
        result = reviewer_node(state)
        assert "No content generated" in result["final_response"]

    def test_reviewer_merges_multiple_outputs(self, monkeypatch):
        from wanderai.ai.agents.reviewer import reviewer_node

        fake_client = FakeClient()

        def capturing_complete(messages, model=None, max_tokens=None, temperature=None):
            return {"text": "Merged and reviewed content"}

        fake_client.complete = capturing_complete
        monkeypatch.setattr(
            "wanderai.ai.pipeline.get_client", lambda: fake_client
        )

        state = {
            "agent_outputs": {
                "planner": "Day-by-day plan",
                "budget_agent": "Cost breakdown",
            },
            "user_message": "",
        }
        result = reviewer_node(state)
        assert "final_response" in result
        assert result["final_response"] == "Merged and reviewed content"

    def test_reviewer_falls_back_to_merge_on_error(self, monkeypatch):
        from wanderai.ai.agents.reviewer import reviewer_node

        def failing_client():
            raise RuntimeError("LLM down")

        monkeypatch.setattr("wanderai.ai.pipeline.get_client", failing_client)

        state = {
            "agent_outputs": {
                "planner": "Plan content",
                "weather_agent": "Weather info",
            },
            "user_message": "",
        }
        with monkeypatch.context() as m:
            m.setattr("wanderai.ai.agents.reviewer.logger",
                      type("FakeLogger", (), {"warning": lambda *a, **kw: None})())
            result = reviewer_node(state)
        assert "Plan content" in result["final_response"]
        assert "Weather info" in result["final_response"]


class TestGraph:
    def test_route_by_intent(self):
        from wanderai.ai.agents.graph import _route_by_intent

        assert _route_by_intent({"intent": "itinerary"}) == "planner"
        assert _route_by_intent({"intent": "budget"}) == "budget_agent"
        assert _route_by_intent({"intent": "weather"}) == "weather_agent"
        assert _route_by_intent({"intent": "safety"}) == "safety_agent"
        assert _route_by_intent({"intent": "destination"}) == "destination_agent"
        assert _route_by_intent({"intent": "packing"}) == "packing_agent"
        assert _route_by_intent({"intent": "general"}) == "destination_agent"
        assert _route_by_intent({"intent": "unknown"}) == "destination_agent"
        assert _route_by_intent({}) == "destination_agent"

    def test_reset_travel_graph(self):
        from wanderai.ai.agents.graph import reset_travel_graph

        reset_travel_graph()

    def test_run_agent_graph_falls_back_on_import_error(self, monkeypatch):
        import wanderai.ai.agents.graph as graph_mod

        def raiser():
            raise ImportError("No module named 'langgraph'")

        monkeypatch.setattr(
            "wanderai.ai.agents.graph.get_travel_graph", raiser
        )

        def fake_run_chat(user_message, conversation_id, extra_context=None):
            return {"text": "Fallback response"}

        monkeypatch.setattr(
            "wanderai.ai.pipeline.run_chat", fake_run_chat
        )

        result = graph_mod.run_agent_graph(
            user_message="Hello",
            conversation_id="conv-1",
            user_id="user-1",
        )
        assert result["text"] == "Fallback response"
        assert result["intent"] == "general"

    def test_build_travel_graph_compiles(self):
        from wanderai.ai.agents.graph import build_travel_graph

        graph = build_travel_graph()
        assert graph is not None
