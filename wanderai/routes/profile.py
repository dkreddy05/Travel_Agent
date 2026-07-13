"""
wanderai/routes/profile.py
User profile and preferences endpoints.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from wanderai.extensions import db
from wanderai.repositories.user_repository import UserRepository
from wanderai.utils.response import success, error

profile_bp = Blueprint("profile", __name__)
_user_repo = UserRepository()


@profile_bp.get("")
@jwt_required()
def get_profile():
    """GET /api/v1/profile"""
    user_id = get_jwt_identity()
    user = _user_repo.get_by_id(user_id)
    if not user:
        return error("User not found", 404)

    data = user.to_dict()
    if user.preferences:
        data["preferences"] = user.preferences.to_dict()
    return success(data)


@profile_bp.put("")
@jwt_required()
def update_profile():
    """PUT /api/v1/profile"""
    user_id = get_jwt_identity()
    user = _user_repo.get_by_id(user_id)
    if not user:
        return error("User not found", 404)

    data = request.get_json(silent=True) or {}
    allowed = ["username", "avatar_url"]
    updates = {k: data[k] for k in allowed if k in data}
    if updates:
        _user_repo.update(user, **updates)
        db.session.commit()

    return success(user.to_dict())


@profile_bp.put("/preferences")
@jwt_required()
def update_preferences():
    """PUT /api/v1/profile/preferences"""
    user_id = get_jwt_identity()
    user = _user_repo.get_by_id(user_id)
    if not user:
        return error("User not found", 404)

    data = request.get_json(silent=True) or {}
    pref = user.preferences

    if not pref:
        from wanderai.models.preference import UserPreference
        pref = UserPreference(user_id=user_id)
        db.session.add(pref)

    allowed = [
        "budget_tier", "trip_styles", "dietary",
        "home_country", "passport_country",
        "preferred_transport", "preferred_accommodation",
        "dream_destinations", "notes",
    ]
    for key in allowed:
        if key in data:
            setattr(pref, key, data[key])

    db.session.commit()
    return success(pref.to_dict())
