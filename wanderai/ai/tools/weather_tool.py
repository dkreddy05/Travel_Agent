"""
wanderai/ai/tools/weather_tool.py
Weather tool — calls OpenWeatherMap API, caches results in Redis.
"""
import os
import requests
from typing import Optional
from wanderai.observability.logger import get_logger
from wanderai.utils.cache_keys import weather as weather_cache_key

logger = get_logger(__name__)

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
TTL_SECONDS = 3600  # 1 hour


def get_weather(destination: str, month: str, cache=None) -> dict:
    """
    Get current weather data for a destination.
    Returns a dict with temperature, conditions, and advice.
    Falls back to AI-generated advice if API unavailable.
    """
    api_key = os.getenv("OPENWEATHER_API_KEY", "")

    # Check cache first
    if cache:
        ckey = weather_cache_key(destination, month)
        cached = cache.get(ckey)
        if cached:
            logger.debug("weather_cache_hit", destination=destination)
            return {**cached, "cached": True}

    if not api_key:
        return {"error": "Weather API not configured", "destination": destination, "month": month}

    try:
        response = requests.get(
            OPENWEATHER_URL,
            params={"q": destination, "appid": api_key, "units": "metric"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()

        result = {
            "destination": destination,
            "month": month,
            "temperature_c": data["main"]["temp"],
            "feels_like_c": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "conditions": data["weather"][0]["description"],
            "wind_speed_ms": data["wind"]["speed"],
            "cached": False,
        }

        if cache:
            cache.set(ckey, result, timeout=TTL_SECONDS)

        return result

    except Exception as exc:
        logger.warning("weather_api_failed", destination=destination, error=str(exc))
        return {
            "destination": destination,
            "month": month,
            "error": str(exc),
            "fallback": True,
        }
