"""
wanderai/utils/cache_keys.py
Central registry for all Redis cache key patterns.
Single source of truth — no magic strings scattered in codebase.
"""

import hashlib


def llm_response(prompt: str) -> str:
    """Cache key for LLM response based on prompt hash."""
    h = hashlib.sha256(prompt.encode()).hexdigest()[:16]
    return f"llm:resp:{h}"


def weather(destination: str, month: str) -> str:
    dest = destination.lower().replace(" ", "_")
    return f"weather:{dest}:{month.lower()}"


def currency(from_code: str, to_code: str) -> str:
    return f"currency:{from_code.upper()}:{to_code.upper()}"


def places(destination: str, category: str) -> str:
    dest = destination.lower().replace(" ", "_")
    return f"places:{dest}:{category.lower()}"


def rag_embedding(text: str) -> str:
    h = hashlib.sha256(text.encode()).hexdigest()[:16]
    return f"rag:embed:{h}"


def user_session(jti: str) -> str:
    return f"session:{jti}"


def rate_limit(user_id: str, endpoint: str) -> str:
    return f"ratelimit:{user_id}:{endpoint}"


def popular_destinations() -> str:
    return "destinations:popular"
