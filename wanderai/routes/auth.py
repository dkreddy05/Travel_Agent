"""
wanderai/routes/auth.py
Authentication endpoints — register, login, OAuth, refresh, logout, verify email.
"""

from flask import Blueprint, request, current_app, redirect
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from wanderai.services.auth_service import AuthService
from wanderai.utils.response import success, created, error, validation_error
from wanderai.extensions import limiter

auth_bp = Blueprint("auth", __name__)
_auth_service = AuthService()


@auth_bp.post("/register")
@limiter.limit("5 per minute")
def register():
    """POST /api/v1/auth/register"""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    username = data.get("username", "").strip() or None

    if not email or not password:
        return validation_error({"email": "required", "password": "required"})

    result = _auth_service.register(email=email, password=password, username=username)
    if not result["success"]:
        return error(result["error"], 400, "REGISTRATION_FAILED")

    return created(
        data={
            "message": "Registration successful. Please check your email to verify your account."
        },
    )


@auth_bp.post("/login")
@limiter.limit("10 per minute")
def login():
    """POST /api/v1/auth/login"""
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not email or not password:
        return validation_error({"email": "required", "password": "required"})

    device_info = request.headers.get("User-Agent", "")[:500]
    ip = request.remote_addr or ""

    result = _auth_service.login(
        email=email, password=password, device_info=device_info, ip=ip
    )
    if not result["success"]:
        return error(result["error"], 401, "AUTH_FAILED")

    return success(
        {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
            "user": result["user"],
        }
    )


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """POST /api/v1/auth/refresh — rotate the access token."""
    claims = get_jwt()
    refresh_jti = claims.get("jti")
    user_id = get_jwt_identity()
    device_info = request.headers.get("User-Agent", "")[:500]
    ip = request.remote_addr or ""

    result = _auth_service.refresh_tokens(
        refresh_jti=refresh_jti, user_id=user_id, device_info=device_info, ip=ip
    )
    if not result["success"]:
        return error(result["error"], 401, "REFRESH_FAILED")

    return success(
        {
            "access_token": result["access_token"],
            "refresh_token": result["refresh_token"],
        }
    )


@auth_bp.post("/logout")
@jwt_required()
def logout():
    """POST /api/v1/auth/logout — revoke current session."""
    jti = get_jwt().get("jti")
    if jti:
        _auth_service.logout(jti)
    return success({"message": "Logged out successfully"})


@auth_bp.get("/verify-email/<token>")
def verify_email(token: str):
    """GET /api/v1/auth/verify-email/<token>"""
    result = _auth_service.verify_email(token)
    if not result["success"]:
        return error(result["error"], 400, "VERIFY_FAILED")

    app_url = current_app.config.get("APP_URL", "/")
    return redirect(f"{app_url}/?verified=true")


@auth_bp.get("/me")
@jwt_required()
def get_me():
    """GET /api/v1/auth/me — get current user profile."""
    from wanderai.repositories.user_repository import UserRepository

    user_id = get_jwt_identity()
    user = UserRepository().get_by_id(user_id)
    if not user:
        return error("User not found", 404)
    return success(user.to_dict())
