"""
wanderai/routes/budget.py
Budget planning endpoint.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import limiter
from wanderai.utils.response import success, error
from wanderai.utils.validators import detect_prompt_injection

budget_bp = Blueprint("budget", __name__)


@budget_bp.post("")
@jwt_required()
@limiter.limit("20 per hour", key_func=lambda: get_jwt_identity())
def generate_budget():
    """POST /api/v1/budget"""
    data = request.get_json(silent=True) or {}
    destination = data.get("destination", "").strip()

    if detect_prompt_injection(destination):
        return error("Invalid input", 400, "PROMPT_INJECTION")

    days = data.get("days", 7)
    travelers = data.get("travelers", 1)
    budget_total = data.get("budget_total", 0)
    travel_style = data.get("travel_style", "mid-range")

    from wanderai.ai.prompts.budget import BUDGET_USER_TEMPLATE
    from wanderai.ai.pipeline import run_single_prompt
    from jinja2 import Template

    prompt = Template(BUDGET_USER_TEMPLATE).render(
        destination=destination,
        days=days,
        travelers=travelers,
        budget_total=budget_total,
        travel_style=travel_style,
    )

    result = run_single_prompt(prompt, task="budget")
    return success({
        "budget_plan": result["text"],
        "destination": destination,
        "total_budget": budget_total,
        "model": result.get("model"),
        "latency_ms": result.get("latency_ms"),
    })
