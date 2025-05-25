from flask import Blueprint, request, jsonify, g
from models import UserPreferences
from services.auth_middleware import auth_required

from config import db

preferences_bp = Blueprint("preferences", __name__)

@preferences_bp.route("", methods=["POST"])
@auth_required
def save_preferences():
    data = request.json
    try:
        preferences = UserPreferences(
            answers=data.get("answers"),
            preference_time=data.get("preferenceTime"),
            preferred_days=data.get("preferredDays"),
            preferred_days_by_task=data.get("preferredDaysByTask"),
            user_id=g.user.id,
        )
        print(preferences)

        db.session.add(preferences)
        db.session.commit()

        return jsonify({"message": "Preferences saved successfully!"}), 201

    except Exception as e:
        return jsonify({"message": f"Failed to save preferences: {str(e)}"}), 400
