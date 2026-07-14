"""
wanderai/ai/agents/state.py
LangGraph shared state definition for the WanderAI multi-agent system.
TypedDict ensures type safety across all agent nodes.
"""

from typing import TypedDict


class TravelState(TypedDict, total=False):
    """
    Shared state passed between all LangGraph agent nodes.
    'total=False' means all keys are optional — agents only fill in their portion.
    """

    # Input context
    user_id: str
    conversation_id: str
    user_message: str
    intent: str  # classified by CoordinatorAgent

    # Trip parameters (extracted from user message or form)
    destination: str
    days: int
    budget_tier: str
    travelers: int
    interests: list[str]
    transport: str
    accommodation: str

    # RAG context
    rag_context: list[str]  # retrieved knowledge chunks

    # Agent outputs (keyed by agent name)
    agent_outputs: dict[str, str]  # {agent_name: markdown_output}

    # Tool outputs
    weather_data: dict
    currency_data: dict
    places_data: list[dict]

    # Final assembled response
    final_response: str

    # Error tracking
    errors: list[str]  # accumulated using operator.add

    # Metadata
    model_used: str
    total_latency_ms: int
