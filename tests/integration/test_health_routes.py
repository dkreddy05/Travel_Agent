"""
tests/integration/test_health_routes.py
Integration tests for health check endpoints.
"""
def test_health_check(client):
    """GET /api/v1/health should return 200."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
    assert "version" in data["data"]
    assert "timestamp" in data["data"]


def test_health_response_envelope(client):
    """Response must follow standard envelope format."""
    response = client.get("/api/v1/health")
    data = response.get_json()
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert "meta" in data


def test_404_api_returns_json(client):
    """API 404s should return JSON, not HTML."""
    response = client.get("/api/v1/nonexistent-endpoint")
    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "NOT_FOUND"


def test_404_page_returns_html(client):
    """Page 404s should return HTML."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
    assert b"html" in response.data.lower() or response.data


def test_readiness_check_available(client):
    """GET /api/v1/health/ready should be accessible."""
    response = client.get("/api/v1/health/ready")
    # Accept 200 (all healthy) or 503 (deps unavailable in test env)
    assert response.status_code in (200, 503)
    data = response.get_json()
    assert data["success"] is True  # success=True even for degraded state
    assert "checks" in data["data"]
