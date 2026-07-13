"""
wanderai/tasks/itinerary_tasks.py
Celery background tasks for itinerary generation.
"""
from wanderai.tasks import celery


@celery.task(bind=True, max_retries=3, default_retry_delay=30, name="tasks.generate_itinerary")
def generate_itinerary_task(self, trip_id: str, user_id: str) -> dict:
    """
    Async itinerary generation task.
    Runs the full AI pipeline in a background worker.
    """
    import time
    from wanderai.app import create_app
    from wanderai.extensions import db
    from wanderai.ai.pipeline import run_single_prompt
    from wanderai.ai.prompts.itinerary import ITINERARY_USER_TEMPLATE
    from wanderai.repositories.trip_repository import TripRepository, ItineraryRepository
    from jinja2 import Template

    app = create_app()
    with app.app_context():
        trip_repo = TripRepository()
        itin_repo = ItineraryRepository()
        trip = trip_repo.get_by_id(trip_id)

        if not trip:
            return {"error": "Trip not found"}

        try:
            self.update_state(state="PROGRESS", meta={"step": "Generating itinerary", "progress": 10})

            prompt = Template(ITINERARY_USER_TEMPLATE).render(
                destination=trip.destination,
                days=trip.days,
                budget=trip.budget_tier.value if trip.budget_tier else "mid-range",
                interests=", ".join(trip.interests) if trip.interests else "general",
                travelers=trip.travelers,
                transport=trip.transport_preference or "flexible",
                accommodation=trip.accommodation_preference or "hotel",
            )

            self.update_state(state="PROGRESS", meta={"step": "Calling AI model", "progress": 30})

            start = time.monotonic()
            result = run_single_prompt(prompt, task="itinerary", max_tokens=2000)
            gen_ms = round((time.monotonic() - start) * 1000)

            self.update_state(state="PROGRESS", meta={"step": "Saving to database", "progress": 90})

            itin = itin_repo.upsert(
                trip_id=trip.id,
                raw_text=result["text"],
                model_used=result.get("model", ""),
                prompt_version="2.0.0",
                generation_time_ms=gen_ms,
            )
            db.session.commit()

            return {
                "trip_id": trip_id,
                "itinerary_id": itin.id,
                "destination": trip.destination,
                "generation_time_ms": gen_ms,
            }

        except Exception as exc:
            db.session.rollback()
            raise self.retry(exc=exc)
