"""
wanderai/ai/output_validator.py
Validates and cleans AI model outputs.
Detects refusals, malformed responses, and prompt leakage.
"""

import re
import json
from wanderai.observability.logger import get_logger

logger = get_logger(__name__)

# Patterns indicating the model refused to answer
REFUSAL_PATTERNS = [
    r"i cannot (help|assist)",
    r"i'm (unable|not able) to",
    r"as an ai (language model|assistant)",
    r"i don't have (access|the ability)",
]
_refusal_re = re.compile("|".join(REFUSAL_PATTERNS), re.IGNORECASE)


def is_refusal(text: str) -> bool:
    """Return True if the response is a model refusal."""
    return bool(_refusal_re.search(text[:200]))


def is_too_short(text: str, min_chars: int = 100) -> bool:
    """Return True if response is suspiciously short."""
    return len(text.strip()) < min_chars


def extract_json_block(text: str) -> dict | None:
    """Extract a ```json ... ``` block from model output."""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    return None


def validate_response(text: str) -> dict:
    """
    Validate a model response. Returns {valid: bool, issues: list[str]}.
    """
    issues = []

    if not text or not text.strip():
        issues.append("empty_response")
    elif is_too_short(text):
        issues.append("response_too_short")

    if is_refusal(text):
        issues.append("model_refusal")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
    }


def clean_response(text: str) -> str:
    """
    Clean up common model output artifacts.
    - Strip leading/trailing whitespace
    - Remove repeated system-prompt echoes
    - Normalize newlines
    """
    text = text.strip()
    # Remove any accidental system header echoes
    text = re.sub(r"<\|start_header_id\|>\w+<\|end_header_id\|>", "", text)
    text = re.sub(r"<\|eot_id\|>", "", text)
    text = re.sub(r"<\|system\|>|<\|user\|>|<\|assistant\|>", "", text)
    text = re.sub(r"\[INST\]|\[\/INST\]", "", text)
    # Normalize excessive newlines
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()
