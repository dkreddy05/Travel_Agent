"""
wanderai/ai/agents/reviewer.py
ReviewerAgent — quality-checks and merges outputs from other agents.
This is the final node before returning the response to the user.
"""

from wanderai.ai.agents.state import TravelState
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

REVIEWER_PROMPT = """\
You are a travel content quality reviewer. Review the following travel advice and:
1. Check for factual consistency (no contradictions)
2. Ensure all sections are complete and useful
3. Add any missing critical information (safety, budget, packing)
4. Format the final response in clean Markdown

Travel content to review:
{content}

Return the improved, final version only. Do not add meta-commentary.
"""


def reviewer_node(state: TravelState) -> TravelState:
    """Review and merge agent outputs into a final polished response."""
    from wanderai.ai.pipeline import get_client

    agent_outputs = state.get("agent_outputs", {})

    if not agent_outputs:
        return {**state, "final_response": "⚠️ No content generated."}

    # For single-agent results, skip the reviewer to save LLM call
    if len(agent_outputs) == 1:
        final = list(agent_outputs.values())[0]
        return {**state, "final_response": final}

    # Merge and review multiple agent outputs
    merged = "\n\n---\n\n".join(
        f"## {name.title()} Agent Output\n{content}"
        for name, content in agent_outputs.items()
    )

    try:
        client = get_client()
        result = client.complete(
            messages=[
                {"role": "user", "content": REVIEWER_PROMPT.format(content=merged)},
            ],
            max_tokens=2000,
        )
        final = result["text"]
    except Exception as exc:
        logger.warning("reviewer_failed_using_merged", error=str(exc))
        final = merged  # fallback to raw merge

    return {**state, "final_response": final}
