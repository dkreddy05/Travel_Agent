"""
wanderai/ai/agents/planner.py
PlannerAgent — generates the multi-day itinerary structure.
"""
from wanderai.ai.agents.state import TravelState
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)


def planner_node(state: TravelState) -> TravelState:
    """Generate a full day-by-day itinerary."""
    from flask import current_app
    from wanderai.ai.client import AIClient
    from wanderai.ai.prompts.itinerary import ITINERARY_USER_TEMPLATE
    from jinja2 import Template

    destination = state.get("destination", "the destination")
    days = state.get("days", 7)
    budget = state.get("budget_tier", "mid-range")
    interests = ", ".join(state.get("interests", ["general"]))
    travelers = state.get("travelers", 1)
    transport = state.get("transport", "flexible")
    accommodation = state.get("accommodation", "hotel")

    prompt = Template(ITINERARY_USER_TEMPLATE).render(
        destination=destination,
        days=days,
        budget=budget,
        interests=interests,
        travelers=travelers,
        transport=transport,
        accommodation=accommodation,
    )

    # Inject RAG context if available
    rag = state.get("rag_context", [])
    if rag:
        rag_block = "\n\nContext from knowledge base:\n" + "\n---\n".join(rag[:3])
        prompt += rag_block

    try:
        client = AIClient(current_app.config)
        from wanderai.ai.prompts.system import build_system_prompt
        result = client.complete(
            messages=[
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            max_tokens=2000,
        )
        output = result["text"]
    except Exception as exc:
        logger.error("planner_agent_failed", error=str(exc))
        output = f"⚠️ Could not generate itinerary: {exc}"

    outputs = {**state.get("agent_outputs", {}), "planner": output}
    return {**state, "agent_outputs": outputs}
