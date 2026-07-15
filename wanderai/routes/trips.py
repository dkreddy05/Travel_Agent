"""
wanderai/routes/trips.py
Trip CRUD endpoints.
"""

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import db
from wanderai.models.trip import BudgetTier
from wanderai.repositories.trip_repository import TripRepository
from wanderai.utils.response import success, created, error, not_found
from wanderai.utils.pagination import PaginationParams

trips_bp = Blueprint("trips", __name__)
_trip_repo = TripRepository()


@trips_bp.post("")
@jwt_required()
def create_trip():
    """POST /api/v1/trips"""
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}
    destination = data.get("destination", "").strip()
    if not destination:
        return error("Destination is required", 400)

    try:
        days = int(data.get("days", 7))
        travelers = int(data.get("travelers", 1))
    except (TypeError, ValueError):
        return error("'days' and 'travelers' must be integers", 400)

    budget_tier_str = data.get("budget_tier")
    budget_tier = None
    if budget_tier_str:
        try:
            budget_tier = BudgetTier(budget_tier_str)
        except ValueError:
            budget_tier = None

    trip = _trip_repo.create(
        user_id=user_id,
        destination=destination,
        title=data.get("title") or destination,
        days=days,
        travelers=travelers,
        budget_tier=budget_tier,
        interests=data.get("interests", []),
        transport_preference=data.get("transport"),
        accommodation_preference=data.get("accommodation"),
    )
    db.session.commit()
    return created(trip.to_dict())


@trips_bp.get("")
@jwt_required()
def list_trips():
    """GET /api/v1/trips"""
    user_id = get_jwt_identity()
    params = PaginationParams.from_request()
    result = _trip_repo.get_user_trips(user_id, params)
    return success(
        data=[t.to_dict() for t in result.items],
        meta=result.to_meta(),
    )


@trips_bp.get("/<trip_id>")
@jwt_required()
def get_trip(trip_id: str):
    """GET /api/v1/trips/{id}"""
    user_id = get_jwt_identity()
    trip = _trip_repo.get_user_trip(user_id, trip_id)
    if not trip:
        return not_found("Trip")
    data = trip.to_dict()
    if trip.itinerary:
        data["itinerary"] = trip.itinerary.to_dict()
    if trip.budget:
        data["budget"] = trip.budget.to_dict()
    return success(data)


@trips_bp.put("/<trip_id>")
@jwt_required()
def update_trip(trip_id: str):
    """PUT /api/v1/trips/{id}"""
    user_id = get_jwt_identity()
    trip = _trip_repo.get_user_trip(user_id, trip_id)
    if not trip:
        return not_found("Trip")

    data = request.get_json(silent=True) or {}
    allowed = [
        "title",
        "days",
        "travelers",
        "budget_tier",
        "status",
        "interests",
        "transport_preference",
        "accommodation_preference",
        "start_date",
        "end_date",
    ]
    updates = {k: data[k] for k in allowed if k in data}
    _trip_repo.update(trip, **updates)
    db.session.commit()
    return success(trip.to_dict())


@trips_bp.delete("/<trip_id>")
@jwt_required()
def delete_trip(trip_id: str):
    """DELETE /api/v1/trips/{id}"""
    user_id = get_jwt_identity()
    trip = _trip_repo.get_user_trip(user_id, trip_id)
    if not trip:
        return not_found("Trip")
    _trip_repo.delete(trip)
    db.session.commit()
    return success({"message": "Trip deleted"})
