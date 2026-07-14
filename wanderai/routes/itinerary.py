"""
wanderai/routes/itinerary.py
Itinerary generation — supports both sync and async (Celery) modes.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import db, limiter
from wanderai.repositories.trip_repository import TripRepository, ItineraryRepository
from wanderai.utils.response import success, created, error
from wanderai.utils.validators import detect_prompt_injection

itinerary_bp = Blueprint("itinerary", __name__)
_trip_repo = TripRepository()
_itin_repo = ItineraryRepository()


@itinerary_bp.post("")
@jwt_required()
@limiter.limit("10 per hour", key_func=lambda: get_jwt_identity())
def generate_itinerary():
    """
    POST /api/v1/itinerary
    Generate a full itinerary. Dispatches async Celery task if available,
    else runs synchronously (dev mode).
    """
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    # Validate required fields
    required = ["destination", "days", "budget", "interests"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        return error(f"Missing fields: {', '.join(missing)}", 400)

    destination = data["destination"].strip()
    if detect_prompt_injection(destination):
        return error("Invalid input", 400, "PROMPT_INJECTION")

    # Create trip record
    trip = _trip_repo.create(
        user_id=user_id,
        destination=destination,
        days=int(data.get("days", 7)),
        budget_tier=data.get("budget", "mid-range"),
        travelers=int(data.get("travelers", 1)),
        interests=data.get("interests", []),
        transport_preference=data.get("transport", "flexible"),
        accommodation_preference=data.get("accommodation", "hotel"),
    )
    db.session.commit()

    # Try async Celery task
    try:
        from wanderai.tasks.itinerary_tasks import generate_itinerary_task

        task = generate_itinerary_task.delay(trip.id, user_id)
        return created(
            {
                "task_id": task.id,
                "trip_id": trip.id,
                "status": "processing",
                "message": "Itinerary generation started. Poll /api/v1/itinerary/status/{task_id}",
            }
        )
    except Exception:
        # Fallback: synchronous generation (dev mode)
        return _generate_sync(trip, data)


@itinerary_bp.get("/status/<task_id>")
@jwt_required()
def get_task_status(task_id: str):
    """GET /api/v1/itinerary/status/{task_id} — poll Celery task."""
    try:
        from celery.result import AsyncResult

        task = AsyncResult(task_id)
        if task.state == "SUCCESS":
            return success({"status": "completed", "result": task.result})
        elif task.state == "FAILURE":
            return success({"status": "failed", "error": str(task.result)})
        else:
            return success(
                {"status": task.state.lower(), "progress": getattr(task, "info", {})}
            )
    except Exception as exc:
        return error(f"Could not retrieve task status: {exc}", 404)


def _generate_sync(trip, data: dict):
    """Synchronous fallback for dev mode."""
    import time
    from wanderai.ai.pipeline import run_single_prompt
    from wanderai.ai.prompts.itinerary import ITINERARY_USER_TEMPLATE
    from jinja2 import Template
    from datetime import datetime

    prompt = Template(ITINERARY_USER_TEMPLATE).render(
        destination=trip.destination,
        days=trip.days,
        budget=(
            trip.budget_tier.value
            if trip.budget_tier
            else data.get("budget", "mid-range")
        ),
        interests=(
            ", ".join(trip.interests)
            if trip.interests
            else data.get("interests", "general")
        ),
        travelers=trip.travelers,
        transport=trip.transport_preference or "flexible",
        accommodation=trip.accommodation_preference or "hotel",
    )

    start = time.monotonic()
    result = run_single_prompt(prompt, task="itinerary", max_tokens=2000)
    gen_ms = round((time.monotonic() - start) * 1000)

    itin = _itin_repo.upsert(
        trip_id=trip.id,
        raw_text=result["text"],
        model_used=result.get("model", ""),
        prompt_version="2.0.0",
        generation_time_ms=gen_ms,
    )
    db.session.commit()

    return success(
        {
            "trip_id": trip.id,
            "itinerary": itin.to_dict(),
            "destination": trip.destination,
            "days": trip.days,
            "generated_at": datetime.utcnow().strftime("%B %d, %Y"),
        }
    )
