"""
wanderai/utils/validators.py
Shared input validators used by schemas and services.
"""

import re
import bleach

# Allowed HTML tags for markdown rendering (used to sanitize AI output)
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "code",
    "pre",
    "blockquote",
    "hr",
    "a",
]
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}

# Prompt injection patterns to detect and reject
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|all|above)\s+instructions",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"\[INST\]",
    r"\[\/INST\]",
    r"<\|begin_of_text\|>",
    r"reveal\s+your\s+(system\s+)?prompt",
    r"print\s+your\s+instructions",
    r"disregard\s+(all\s+)?previous",
]

_injection_regex = re.compile("|".join(PROMPT_INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_html(text: str) -> str:
    """Strip disallowed HTML tags from AI-generated output."""
    return bleach.clean(text, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)


def detect_prompt_injection(text: str) -> bool:
    """Return True if the text contains a prompt injection attempt."""
    return bool(_injection_regex.search(text))


def validate_message_length(text: str, max_len: int = 2000) -> str | None:
    """Return error string if message exceeds max length, else None."""
    if len(text) > max_len:
        return f"Message too long: {len(text)} chars (max {max_len})"
    return None


def validate_email(email: str) -> bool:
    """Basic RFC 5322 email validation."""
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def validate_password(password: str) -> list[str]:
    """Return list of validation error messages (empty = valid)."""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain an uppercase letter.")
    if not re.search(r"[0-9]", password):
        errors.append("Password must contain a number.")
    return errors
