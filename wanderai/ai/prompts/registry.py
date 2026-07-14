"""
wanderai/ai/prompts/registry.py
Versioned prompt template registry.
Templates are registered here; the AI pipeline selects the correct version.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class PromptTemplate:
    """A versioned, model-family-aware prompt template."""
    name: str
    version: str
    description: str
    system: str
    user_template: str             # Jinja2-compatible template string
    output_schema: Optional[dict] = None
    max_tokens: int = 1500
    temperature: float = 0.7


_registry: dict[str, PromptTemplate] = {}


def register(template: PromptTemplate) -> PromptTemplate:
    """Register a prompt template. Key = name:version."""
    key = f"{template.name}:{template.version}"
    _registry[key] = template
    # Also register as latest for the name
    _registry[f"{template.name}:latest"] = template
    return template


def get(name: str, version: str = "latest") -> Optional[PromptTemplate]:
    return _registry.get(f"{name}:{version}")


def list_all() -> list[PromptTemplate]:
    # Return only non-'latest' aliases
    return [t for k, t in _registry.items() if not k.endswith(":latest")]
