"""
wanderai/ai/pipeline.py
Main AI pipeline orchestrator.
Stages: Memory → RAG → PromptBuilder → ModelRouter → LLMClient → Validation → Persist
"""
import time
from typing import Optional

from wanderai.ai.client import AIClient
from wanderai.ai.memory import ConversationMemory
from wanderai.ai.output_validator import validate_response, clean_response, extract_json_block
from wanderai.ai.prompts.system import build_system_prompt
from wanderai.ai.model_router import select_model_for_task
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

# Module-level client — initialized lazily via init_pipeline()
_ai_client: Optional[AIClient] = None


def init_pipeline(config: dict, cache=None) -> None:
    """Initialize the AI pipeline with app config. Called from create_app()."""
    global _ai_client
    _ai_client = AIClient(config)
    if cache:
        _ai_client.set_cache(cache)


def get_client() -> AIClient:
    if _ai_client is None:
        raise RuntimeError("AI pipeline not initialized. Call init_pipeline() first.")
    return _ai_client


def run_chat(
    user_message: str,
    conversation_id: str,
    task: str = "general",
    user_role: str = "user",
    extra_context: dict | None = None,
) -> dict:
    """
    Full AI pipeline for a chat message.

    Args:
        user_message:    The user's text input
        conversation_id: DB conversation ID for history retrieval
        task:            Task type for model routing (general/itinerary/budget)
        user_role:       User's subscription role for model selection
        extra_context:   Optional dict with destination, days, budget, etc.

    Returns:
        {text, model, tokens_used, latency_ms, cached, json_data}
    """
    client = get_client()
    start = time.monotonic()

    # ── Stage 1: Load conversation memory from DB ────────────
    memory = ConversationMemory(conversation_id)
    history = memory.get_messages_for_llm()

    # ── Stage 2: RAG retrieval ───────────────────────────────
    rag_context = _retrieve_rag_context(user_message, extra_context)

    # ── Stage 3: Build system prompt ────────────────────────
    system_prompt = build_system_prompt(rag_context=rag_context)

    # ── Stage 4: Assemble messages for LLM ──────────────────
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    # ── Stage 5: Model routing ───────────────────────────────
    from flask import current_app
    model = select_model_for_task(task, user_role, current_app.config)

    # ── Stage 6: LLM call ────────────────────────────────────
    result = client.complete(messages=messages, model=model)

    # ── Stage 7: Validate + clean output ────────────────────
    validation = validate_response(result["text"])
    if not validation["valid"]:
        logger.warning("llm_output_invalid", issues=validation["issues"])

    clean_text = clean_response(result["text"])

    # ── Stage 8: Extract structured JSON if present ──────────
    json_data = extract_json_block(clean_text)

    total_ms = round((time.monotonic() - start) * 1000)
    logger.info(
        "ai_pipeline_complete",
        task=task,
        model=result["model"],
        total_ms=total_ms,
        cached=result["cached"],
        had_json=json_data is not None,
    )

    return {
        "text": clean_text,
        "model": result["model"],
        "tokens_used": result.get("tokens_used"),
        "latency_ms": result["latency_ms"],
        "pipeline_ms": total_ms,
        "cached": result["cached"],
        "json_data": json_data,
    }


def run_single_prompt(
    prompt: str,
    task: str = "general",
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    """
    Run a single prompt (no conversation history) through the pipeline.
    Used by itinerary, budget, weather, and recommendation endpoints.
    """
    client = get_client()

    from flask import current_app
    system_prompt = build_system_prompt()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    model = select_model_for_task(task, "user", current_app.config)
    result = client.complete(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
    )

    clean_text = clean_response(result["text"])
    json_data = extract_json_block(clean_text)

    return {
        "text": clean_text,
        "model": result["model"],
        "tokens_used": result.get("tokens_used"),
        "latency_ms": result["latency_ms"],
        "cached": result["cached"],
        "json_data": json_data,
    }


def _retrieve_rag_context(query: str, context: dict | None = None) -> list[str]:
    """
    Retrieve relevant knowledge chunks from Qdrant.
    Returns empty list if RAG is not configured.
    """
    try:
        from wanderai.ai.rag.retriever import retrieve
        destination = (context or {}).get("destination", "")
        search_query = f"{destination} {query}".strip() if destination else query
        chunks = retrieve(search_query, top_k=4)
        return [c["text"] for c in chunks]
    except Exception as exc:
        logger.debug("rag_retrieval_skipped", reason=str(exc))
        return []
