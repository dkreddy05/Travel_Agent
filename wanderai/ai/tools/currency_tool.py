"""
wanderai/ai/tools/currency_tool.py
Currency exchange rate tool — free tier of exchangerate.host, cached 6h.
"""
import os
import requests
from wanderai.observability.logger import get_logger
from wanderai.utils.cache_keys import currency as currency_cache_key

logger = get_logger(__name__)

EXCHANGE_URL = "https://api.exchangerate.host/latest"
TTL_SECONDS = 6 * 3600  # 6 hours


def get_exchange_rate(from_code: str = "USD", to_code: str = "EUR", cache=None) -> dict:
    """Get exchange rate between two currencies."""
    if cache:
        ckey = currency_cache_key(from_code, to_code)
        cached = cache.get(ckey)
        if cached:
            return {**cached, "cached": True}

    try:
        response = requests.get(
            EXCHANGE_URL,
            params={"base": from_code, "symbols": to_code},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
        rate = data.get("rates", {}).get(to_code)

        result = {
            "from": from_code,
            "to": to_code,
            "rate": rate,
            "date": data.get("date"),
            "cached": False,
        }

        if cache and rate:
            cache.set(ckey, result, timeout=TTL_SECONDS)

        return result

    except Exception as exc:
        logger.warning("currency_api_failed", from_code=from_code, error=str(exc))
        return {"from": from_code, "to": to_code, "error": str(exc)}
