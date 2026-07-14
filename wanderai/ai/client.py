"""
wanderai/ai/client.py
LiteLLM-based model-agnostic AI client.
Supports IBM watsonx.ai as primary, any LiteLLM provider as fallback.
"""

import time
from typing import Optional

from wanderai.observability.logger import get_logger
from wanderai.utils.cache_keys import llm_response as llm_cache_key

logger = get_logger(__name__)


def _get_watsonx_messages_completion(
    messages: list[dict], model_id: str, **params
) -> str:
    """
    Direct IBM watsonx.ai call using the existing ibm-watsonx-ai SDK.
    Used as primary path when LiteLLM watsonx adapter is unavailable.
    """
    import os
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

    credentials = Credentials(
        url=os.getenv("WATSONX_URL", ""),
        api_key=os.getenv("WATSONX_API_KEY", ""),
    )
    client = APIClient(
        credentials=credentials, project_id=os.getenv("WATSONX_PROJECT_ID", "")
    )
    model = ModelInference(
        model_id=model_id,
        api_client=client,
        params={
            GenParams.MAX_NEW_TOKENS: params.get("max_tokens", 1500),
            GenParams.MIN_NEW_TOKENS: 50,
            GenParams.TEMPERATURE: params.get("temperature", 0.7),
            GenParams.TOP_P: 0.9,
            GenParams.TOP_K: 50,
            GenParams.REPETITION_PENALTY: 1.1,
        },
    )

    # Build prompt string (auto-detects model format)
    from wanderai.ai.model_router import build_prompt_for_model

    system_prompt = next((m["content"] for m in messages if m["role"] == "system"), "")
    conv_messages = [m for m in messages if m["role"] != "system"]
    prompt_str = build_prompt_for_model(model_id, system_prompt, conv_messages)

    response = model.generate_text(prompt=prompt_str)
    return response.strip() if isinstance(response, str) else str(response)


class AIClient:
    """
    Model-agnostic AI client. Uses IBM watsonx.ai SDK directly.
    Designed to support LiteLLM integration as a drop-in upgrade.
    """

    def __init__(self, config: dict):
        self.primary_model = config.get(
            "AI_PRIMARY_MODEL", "meta-llama/llama-3-3-70b-instruct"
        )
        self.fallback_model = config.get("AI_FALLBACK_MODEL", "")
        self.max_tokens = config.get("AI_MAX_TOKENS", 1500)
        self.temperature = config.get("AI_TEMPERATURE", 0.7)
        self.max_retries = config.get("AI_MAX_RETRIES", 3)
        self.timeout = config.get("AI_TIMEOUT_SECONDS", 60)
        self._cache = None

    def set_cache(self, cache):
        """Inject a Flask-Cache instance for response caching."""
        self._cache = cache

    def complete(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        use_cache: bool = True,
    ) -> dict:
        """
        Send messages to the LLM and return a result dict.

        Returns:
            {text: str, model: str, tokens_used: int, latency_ms: int, cached: bool}
        """
        target_model = model or self.primary_model
        params = {
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
            "temperature": temperature if temperature is not None else self.temperature,
        }

        # ── Cache check ──────────────────────────────────────
        # Key only on the last user message + model so that identical
        # single-prompt calls (itinerary, budget, recommendations) can hit
        # the cache. Full conversation history is never included because it
        # would produce a unique key on every multi-turn message and would
        # risk leaking one user's reply to another user with an identical
        # history prefix.
        cache_key = None
        if use_cache and self._cache:
            import json

            last_user = next(
                (m["content"] for m in reversed(messages) if m.get("role") == "user"),
                "",
            )
            cache_key = llm_cache_key(
                json.dumps({"msg": last_user, "model": target_model}, sort_keys=True)
            )
            cached = self._cache.get(cache_key)
            if cached:
                logger.info("llm_cache_hit", model=target_model)
                return {**cached, "cached": True}

        # ── Primary model call ───────────────────────────────
        start = time.monotonic()
        text = ""
        used_model = target_model
        error_msg = None

        for attempt in range(1, self.max_retries + 1):
            try:
                text = _get_watsonx_messages_completion(
                    messages, target_model, **params
                )
                break
            except Exception as exc:
                error_msg = str(exc)
                logger.warning(
                    "llm_call_failed",
                    attempt=attempt,
                    model=target_model,
                    error=error_msg,
                )
                if attempt == self.max_retries:
                    # Try fallback model
                    if self.fallback_model:
                        try:
                            logger.info(
                                "llm_fallback_attempt",
                                fallback_model=self.fallback_model,
                            )
                            text = _get_watsonx_messages_completion(
                                messages, self.fallback_model, **params
                            )
                            used_model = self.fallback_model
                            break
                        except Exception as fallback_exc:
                            logger.error("llm_fallback_failed", error=str(fallback_exc))
                    text = f"⚠️ WanderAI encountered an error: {error_msg}"

        is_error = text.startswith("⚠️")

        latency_ms = round((time.monotonic() - start) * 1000)
        logger.info("llm_call_complete", model=used_model, latency_ms=latency_ms)

        result = {
            "text": text,
            "model": used_model,
            "tokens_used": None,
            "latency_ms": latency_ms,
            "cached": False,
            "is_error": is_error,
        }

        # ── Cache result ──────────────────────────────────────
        if cache_key and self._cache and not result.get("is_error"):
            self._cache.set(cache_key, result, timeout=3600)

        return result
