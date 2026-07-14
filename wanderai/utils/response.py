"""
wanderai/utils/response.py
Standardized API response builder.
All API routes return this envelope:

  {
    "success": true,
    "data": {...},
    "error": null,
    "meta": {"correlation_id": "...", "version": "2.0.0"}
  }
"""

from flask import jsonify, g, current_app


def success(data=None, status_code: int = 200, meta: dict | None = None) -> tuple:
    """Return a successful JSON response."""
    payload = {
        "success": True,
        "data": data,
        "error": None,
        "meta": _build_meta(meta),
    }
    return jsonify(payload), status_code


def created(data=None, meta: dict | None = None) -> tuple:
    """Return a 201 Created response."""
    return success(data=data, status_code=201, meta=meta)


def error(
    message: str,
    status_code: int = 400,
    code: str | None = None,
    details: dict | None = None,
) -> tuple:
    """Return an error JSON response."""
    payload = {
        "success": False,
        "data": None,
        "error": {
            "message": message,
            "code": code or f"HTTP_{status_code}",
            "details": details,
        },
        "meta": _build_meta(),
    }
    return jsonify(payload), status_code


def not_found(resource: str = "Resource") -> tuple:
    return error(f"{resource} not found", 404, "NOT_FOUND")


def unauthorized(message: str = "Authentication required") -> tuple:
    return error(message, 401, "UNAUTHORIZED")


def forbidden(message: str = "Insufficient permissions") -> tuple:
    return error(message, 403, "FORBIDDEN")


def validation_error(details: dict) -> tuple:
    return error("Validation failed", 422, "VALIDATION_ERROR", details)


def server_error(message: str = "Internal server error") -> tuple:
    return error(message, 500, "SERVER_ERROR")


def _build_meta(extra: dict | None = None) -> dict:
    meta = {
        "correlation_id": getattr(g, "correlation_id", ""),
        "version": current_app.config.get("APP_VERSION", "2.0.0"),
    }
    if extra:
        meta.update(extra)
    return meta
