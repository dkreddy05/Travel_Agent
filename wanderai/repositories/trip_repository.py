"""
wanderai/repositories/trip_repository.py
Trip and Itinerary data access.
"""
from typing import Optional
from wanderai.models.trip import Trip, Itinerary, TripStatus
from wanderai.repositories.base import BaseRepository
from wanderai.utils.pagination import PaginationParams, paginate_query, PaginatedResult


class TripRepository(BaseRepository[Trip]):
    def __init__(self):
        super().__init__(Trip)

    def get_user_trips(self, user_id: str, params: PaginationParams) -> PaginatedResult:
        query = Trip.query.filter_by(user_id=user_id).order_by(Trip.updated_at.desc())
        return paginate_query(query, params)

    def get_user_trip(self, user_id: str, trip_id: str) -> Optional[Trip]:
        return Trip.query.filter_by(id=trip_id, user_id=user_id).first()

    def get_active_trips(self, user_id: str) -> list[Trip]:
        return Trip.query.filter_by(user_id=user_id, status=TripStatus.ACTIVE).all()


class ItineraryRepository(BaseRepository[Itinerary]):
    def __init__(self):
        super().__init__(Itinerary)

    def get_by_trip(self, trip_id: str) -> Optional[Itinerary]:
        return Itinerary.query.filter_by(trip_id=trip_id).first()

    def upsert(self, trip_id: str, **kwargs) -> Itinerary:
        """Create or update the itinerary for a trip."""
        existing = self.get_by_trip(trip_id)
        if existing:
            return self.update(existing, **kwargs)
        return self.create(trip_id=trip_id, **kwargs)
