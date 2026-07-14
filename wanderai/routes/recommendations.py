"""
wanderai/routes/recommendations.py
Destination recommendations endpoint.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import limiter
from wanderai.utils.response import success
from wanderai.ai.pipeline import run_single_prompt

recommendations_bp = Blueprint("recommendations", __name__)

RECOMMENDATIONS_TEMPLATE = """\
Recommend 6 travel destinations for someone who loves: {interests}.
Budget: {budget}, Trip duration: {duration}, Preferred season: {season}
Departing from: {from_country}

For each destination provide:
- **Destination Name, Country**
- Why it matches the traveler's interests (2 sentences)
- Best time to visit
- Estimated daily budget
- Top 3 must-do activities
- One hidden gem tip
- Safety rating (1-5 stars)

Separate each destination with a horizontal rule (---).
"""


@recommendations_bp.post("")
@jwt_required()
@limiter.limit("10 per hour", key_func=lambda: get_jwt_identity())
def get_recommendations():
    """POST /api/v1/recommendations"""
    data = request.get_json(silent=True) or {}
    interests = data.get("interests", "general travel")
    budget = data.get("budget", "mid-range")
    duration = data.get("duration", "1 week")
    season = data.get("season", "any")
    from_country = data.get("from_country", "anywhere")

    prompt = RECOMMENDATIONS_TEMPLATE.format(
        interests=interests,
        budget=budget,
        duration=duration,
        season=season,
        from_country=from_country,
    )

    try:
        result = run_single_prompt(prompt, task="destination")
    except Exception as exc:
        return success({"recommendations": "", "error": str(exc)}), 500

    return success(
        {
            "recommendations": result["text"],
            "cached": result.get("cached", False),
            "latency_ms": result.get("latency_ms"),
        }
    )
