"""
wanderai/ai/agents/graph.py
LangGraph StateGraph definition for the WanderAI multi-agent system.
Compiles the full agent graph with conditional routing based on intent.
"""

from langgraph.graph import StateGraph, END
from wanderai.ai.agents.state import TravelState
from wanderai.ai.agents.coordinator import coordinator_node
from wanderai.ai.agents.planner import planner_node
from wanderai.ai.agents.reviewer import reviewer_node
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)


def _route_by_intent(state: TravelState) -> str:
    """Conditional edge — route to the right agent based on intent."""
    intent = state.get("intent", "general")
    routing = {
        "itinerary": "planner",
        "budget": "budget_agent",
        "weather": "weather_agent",
        "safety": "safety_agent",
        "destination": "destination_agent",
        "packing": "packing_agent",
        "general": "destination_agent",
    }
    return routing.get(intent, "destination_agent")


def _build_general_agent_node(agent_name: str, prompt_template: str):
    """Factory for simple single-prompt agent nodes."""

    def node_fn(state: TravelState) -> TravelState:
        from wanderai.ai.pipeline import get_client
        from wanderai.ai.prompts.system import build_system_prompt

        user_message = state.get("user_message", "")
        destination = state.get("destination", "")
        prompt = f"{prompt_template}\n\nUser question: {user_message}"
        if destination:
            prompt = f"Destination: {destination}\n\n{prompt}"

        try:
            client = get_client()
            result = client.complete(
                messages=[
                    {"role": "system", "content": build_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1500,
            )
            output = result["text"]
        except Exception as exc:
            logger.error(f"{agent_name}_failed", error=str(exc))
            output = f"⚠️ {agent_name} encountered an error: {exc}"

        outputs = {**state.get("agent_outputs", {}), agent_name: output}
        return {**state, "agent_outputs": outputs}

    node_fn.__name__ = f"{agent_name}_node"
    return node_fn


def build_travel_graph() -> StateGraph:
    """Build and compile the WanderAI LangGraph multi-agent graph."""
    graph = StateGraph(TravelState)

    # ── Add all agent nodes ────────────────────────────────
    graph.add_node("coordinator", coordinator_node)
    graph.add_node("planner", planner_node)
    graph.add_node("reviewer", reviewer_node)
    graph.add_node(
        "budget_agent",
        _build_general_agent_node(
            "budget_agent",
            "You are a travel budget expert. Provide a detailed budget breakdown.",
        ),
    )
    graph.add_node(
        "weather_agent",
        _build_general_agent_node(
            "weather_agent",
            "You are a climate and weather expert. Provide detailed seasonal travel advice.",
        ),
    )
    graph.add_node(
        "safety_agent",
        _build_general_agent_node(
            "safety_agent",
            "You are a travel safety expert. Provide current advisories and safety tips.",
        ),
    )
    graph.add_node(
        "destination_agent",
        _build_general_agent_node(
            "destination_agent",
            "You are a destination expert. Recommend and describe travel destinations.",
        ),
    )
    graph.add_node(
        "packing_agent",
        _build_general_agent_node(
            "packing_agent",
            "You are a packing and logistics expert. Create detailed packing lists.",
        ),
    )

    # ── Wire edges ─────────────────────────────────────────
    graph.set_entry_point("coordinator")

    # Conditional routing from coordinator
    graph.add_conditional_edges(
        "coordinator",
        _route_by_intent,
        {
            "planner": "planner",
            "budget_agent": "budget_agent",
            "weather_agent": "weather_agent",
            "safety_agent": "safety_agent",
            "destination_agent": "destination_agent",
            "packing_agent": "packing_agent",
        },
    )

    # All agents flow to reviewer
    for agent in [
        "planner",
        "budget_agent",
        "weather_agent",
        "safety_agent",
        "destination_agent",
        "packing_agent",
    ]:
        graph.add_edge(agent, "reviewer")

    graph.add_edge("reviewer", END)

    return graph.compile()


# Module-level compiled graph — created once at startup
_graph = None


def get_travel_graph():
    """Return the compiled LangGraph (lazy init)."""
    global _graph
    if _graph is None:
        _graph = build_travel_graph()
    return _graph


def reset_travel_graph():
    """Reset the compiled graph singleton. Useful in test teardown."""
    global _graph
    _graph = None


ALLOWED_EXTRA_KEYS = {
    "destination",
    "days",
    "budget_tier",
    "travelers",
    "interests",
    "transport",
    "accommodation",
}


def run_agent_graph(
    user_message: str,
    conversation_id: str,
    user_id: str,
    extra_context: dict | None = None,
) -> dict:
    """
    Execute the full multi-agent graph and return the final response.
    Falls back to pipeline.run_chat() if LangGraph is unavailable.
    """
    try:
        graph = get_travel_graph()
        safe_context = {
            k: v for k, v in (extra_context or {}).items() if k in ALLOWED_EXTRA_KEYS
        }
        initial_state = TravelState(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            agent_outputs={},
            errors=[],
            **safe_context,
        )
        final_state = graph.invoke(initial_state)
        return {
            "text": final_state.get("final_response", ""),
            "intent": final_state.get("intent", "general"),
            "agent_outputs": final_state.get("agent_outputs", {}),
            "errors": final_state.get("errors", []),
        }
    except ImportError:
        # LangGraph not installed — fall back to direct pipeline
        logger.info("langgraph_unavailable_fallback")
        from wanderai.ai.pipeline import run_chat

        result = run_chat(user_message, conversation_id, extra_context=extra_context)
        return {
            "text": result["text"],
            "intent": "general",
            "agent_outputs": {},
            "errors": [],
        }
