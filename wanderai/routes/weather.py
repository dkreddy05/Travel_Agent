"""
wanderai/routes/weather.py
Weather advice endpoint.
"""
from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import limiter
from wanderai.utils.response import success, error
from wanderai.utils.validators import detect_prompt_injection
from wanderai.ai.pipeline import run_single_prompt

weather_bp = Blueprint("weather", __name__)

WEATHER_TEMPLATE = """\
Provide weather and climate advice for traveling to {destination} in {month}.
Include:
1. **Weather Overview** – Temperature range, rainfall, humidity
2. **What to Pack** – Climate-specific clothing and gear
3. **Weather-Related Activities** – Best activities for this season
4. **Weather Warnings** – Monsoon, typhoon, extreme heat, etc.
5. **Best Micro-regions** – Where to go within the destination in this season
"""


@weather_bp.post("")
@jwt_required()
@limiter.limit("20 per hour", key_func=lambda: get_jwt_identity())
def get_weather_advice():
    """POST /api/v1/weather"""
    data = request.get_json(silent=True) or {}
    destination = data.get("destination", "").strip()
    month = data.get("month", datetime.utcnow().strftime("%B"))

    if not destination:
        return error("Destination is required", 400)

    if detect_prompt_injection(destination):
        return error("Invalid input", 400)

    # Try real weather API first
    live_weather = {}
    try:
        from wanderai.ai.tools.weather_tool import get_weather
        from wanderai.extensions import cache
        live_weather = get_weather(destination, month, cache=cache)
    except Exception:
        pass

    prompt = WEATHER_TEMPLATE.format(destination=destination, month=month)
    if live_weather.get("temperature_c"):
        prompt += (
            f"\n\nCurrent weather data: "
            f"{live_weather['temperature_c']}°C, {live_weather.get('conditions', '')}, "
            f"humidity {live_weather.get('humidity', '')}%"
        )

    result = run_single_prompt(prompt, task="weather")
    return success({
        "weather_advice": result["text"],
        "destination": destination,
        "month": month,
        "live_data": live_weather if not live_weather.get("error") else None,
        "cached": result.get("cached", False),
    })
