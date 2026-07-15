"""Integration tests for additional API routes."""

import json


class TestTripsRoutes:
    def test_list_trips_empty(self, client, auth_headers, app):
        """GET /api/v1/trips with no trips returns empty list."""
        with app.app_context():
            response = client.get("/api/v1/trips", headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert data["data"] == []

    def test_create_trip(self, client, auth_headers, app):
        """POST /api/v1/trips creates a trip."""
        with app.app_context():
            response = client.post(
                "/api/v1/trips",
                data=json.dumps(
                    {
                        "destination": "Paris",
                        "start_date": "2025-06-01",
                        "end_date": "2025-06-07",
                        "budget_tier": "mid-range",
                    }
                ),
                headers=auth_headers,
            )
            assert response.status_code == 201
            data = response.get_json()
            assert data["data"]["destination"] == "Paris"
            assert "id" in data["data"]


class TestProfileRoutes:
    def test_get_profile(self, client, auth_headers, app):
        """GET /api/v1/profile returns user profile."""
        with app.app_context():
            response = client.get("/api/v1/profile", headers=auth_headers)
            assert response.status_code == 200
            data = response.get_json()
            assert data["success"] is True

    def test_get_profile_unauthorized(self, client):
        """GET /api/v1/profile without token returns 401."""
        response = client.get("/api/v1/profile")
        assert response.status_code == 401


class TestItineraryRoutes:
    def test_generate_itinerary_unauthorized(self, client):
        """POST /api/v1/itinerary without auth returns 401."""
        response = client.post(
            "/api/v1/itinerary",
            data=json.dumps({"destination": "Paris", "days": 5}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestBudgetRoutes:
    def test_budget_unauthorized(self, client):
        """POST /api/v1/budget without auth returns 401."""
        response = client.post(
            "/api/v1/budget",
            data=json.dumps({"destination": "Paris", "budget": 2000}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestWeatherRoutes:
    def test_weather_unauthorized(self, client):
        """POST /api/v1/weather without auth returns 401."""
        response = client.post(
            "/api/v1/weather",
            data=json.dumps({"destination": "Paris"}),
            content_type="application/json",
        )
        assert response.status_code == 401


class TestRecommendationsRoutes:
    def test_recommendations_unauthorized(self, client):
        """POST /api/v1/recommendations without auth returns 401."""
        response = client.post(
            "/api/v1/recommendations",
            data=json.dumps({"destination": "Paris"}),
            content_type="application/json",
        )
        assert response.status_code == 401
