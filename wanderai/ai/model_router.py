"""
wanderai/ai/model_router.py
Prompt format auto-detection (migrated from original app.py _build_prompt).
Now separated as a pure function with no global state.
"""


def build_prompt_for_model(
    model_id: str, system_prompt: str, messages: list[dict]
) -> str:
    """
    Build the correctly-formatted prompt string for the given model_id.

    Supported formats (auto-detected):
      • Llama 3.x  — <|begin_of_text|>…<|eot_id|>
      • Granite     — <|system|> / <|user|> / <|assistant|>
      • Mistral     — [INST] … [/INST]
      • Fallback    — plain labels
    """
    mid = model_id.lower()

    # ── Llama 3.x / 4.x instruct ──────────────────────────
    if "llama-3" in mid or "llama-4" in mid:
        prompt = "<|begin_of_text|>"
        prompt += (
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
        )
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                prompt += (
                    f"<|start_header_id|>{role}<|end_header_id|>\n\n{content}<|eot_id|>"
                )
        prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
        return prompt

    # ── Mistral / Mixtral instruct ─────────────────────────
    if "mistral" in mid or "mixtral" in mid:
        prompt = ""
        system_injected = False
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                user_text = (
                    f"{system_prompt}\n\n{content}" if not system_injected else content
                )
                system_injected = True
                prompt += f"[INST] {user_text} [/INST]"
            elif role == "assistant":
                prompt += f" {content}</s>"
        if not system_injected:
            prompt += f"[INST] {system_prompt} [/INST]"
        return prompt

    # ── IBM Granite instruct ────────────────────────────────
    if "granite" in mid:
        prompt = f"<|system|>\n{system_prompt}\n"
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "user":
                prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                prompt += f"<|assistant|>\n{content}\n"
        prompt += "<|assistant|>\n"
        return prompt

    # ── Generic fallback ────────────────────────────────────
    prompt = f"System: {system_prompt}\n\n"
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if role == "user":
            prompt += f"User: {content}\n"
        elif role == "assistant":
            prompt += f"Assistant: {content}\n"
    prompt += "Assistant:"
    return prompt


def select_model_for_task(task: str, user_role: str, config: dict) -> str:
    """
    Route to different models based on task complexity.
    Future: add load balancing and cost-based routing here.
    """
    primary = config.get("AI_PRIMARY_MODEL", "meta-llama/llama-3-3-70b-instruct")
    # All tasks use the primary model for now
    # Extend: use smaller model for simple queries, larger for full itineraries
    return primary
