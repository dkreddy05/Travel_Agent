"""
wanderai/ai/agents/coordinator.py
CoordinatorAgent — classifies user intent and routes to specialized agents.
This is the entry node for every LangGraph execution.
"""

from wanderai.ai.agents.state import TravelState
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

# Intent classification system prompt
COORDINATOR_PROMPT = """
You are a travel assistant orchestrator. Given a user's message, classify it into exactly one intent:

- "itinerary" — user wants to plan a day-by-day trip
- "budget" — user wants budget breakdown or cost estimate
- "weather" — user wants weather or climate advice
- "safety" — user wants safety information or travel warnings
- "destination" — user wants destination recommendations
- "packing" — user wants packing advice
- "general" — any other travel question

Reply with ONLY the intent word. No explanation.
"""


def coordinator_node(state: TravelState) -> TravelState:
    """Classify user intent and route the workflow."""
    from flask import current_app
    from wanderai.ai.client import AIClient

    message = state.get("user_message", "")
    logger.info("coordinator_classifying", message_preview=message[:80])

    try:
        client = AIClient(current_app.config)
        result = client.complete(
            messages=[
                {"role": "system", "content": COORDINATOR_PROMPT},
                {"role": "user", "content": message},
            ],
            max_tokens=10,
            temperature=0.0,
            use_cache=True,
        )
        words = result["text"].strip().lower().split()
        intent = words[0] if words else "general"
        # Validate against allowed intents
        allowed = {
            "itinerary",
            "budget",
            "weather",
            "safety",
            "destination",
            "packing",
            "general",
        }
        if intent not in allowed:
            intent = "general"
    except Exception as exc:
        logger.warning("coordinator_classification_failed", error=str(exc))
        intent = "general"

    logger.info("coordinator_routed", intent=intent)
    return {**state, "intent": intent, "agent_outputs": state.get("agent_outputs", {})}
