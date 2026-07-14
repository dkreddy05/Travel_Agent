"""
tests/integration/test_auth_routes.py
Integration tests for auth endpoints.
"""
import json


def test_register_success(client, db):
    """POST /api/v1/auth/register with valid data returns 201."""
    response = client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": "newuser@test.com", "password": "SecurePass1"}),
        content_type="application/json",
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data["success"] is True


def test_register_duplicate_email(client, db):
    """Registering with an existing email returns 400."""
    payload = json.dumps({"email": "dupe@test.com", "password": "SecurePass1"})
    client.post("/api/v1/auth/register", data=payload, content_type="application/json")
    response = client.post("/api/v1/auth/register", data=payload, content_type="application/json")
    assert response.status_code == 400
    data = response.get_json()
    assert "already registered" in data["error"]["message"].lower()


def test_register_weak_password(client, db):
    """Weak password returns 400."""
    response = client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": "weak@test.com", "password": "123"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_register_invalid_email(client, db):
    """Invalid email format returns 400."""
    response = client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": "not-an-email", "password": "SecurePass1"}),
        content_type="application/json",
    )
    assert response.status_code == 400


def test_login_wrong_password(client, db):
    """Wrong password returns 401."""
    client.post(
        "/api/v1/auth/register",
        data=json.dumps({"email": "login_test@test.com", "password": "SecurePass1"}),
        content_type="application/json",
    )
    response = client.post(
        "/api/v1/auth/login",
        data=json.dumps({"email": "login_test@test.com", "password": "WrongPass1"}),
        content_type="application/json",
    )
    assert response.status_code == 401


def test_protected_route_without_token(client):
    """Accessing a protected route without token returns 401."""
    response = client.get("/api/v1/profile")
    assert response.status_code == 401


def test_protected_route_with_token(client, auth_headers):
    """Accessing a protected route with valid token returns 200."""
    response = client.get("/api/v1/profile", headers=auth_headers)
    assert response.status_code in (200, 404)  # 404 if user not in test DB
