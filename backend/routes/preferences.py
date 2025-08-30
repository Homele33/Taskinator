from flask import Blueprint, request, jsonify, g
from datetime import time
from config import db
from models import UserPreferences
from services.auth_middleware import auth_required


preferences_bp = Blueprint("preferences", __name__)


def parse_time(value):
    """Accepts 'HH:MM' or 'HH:MM:SS' or None; returns datetime.time or None."""
    if not value:
        return None
    try:
        return time.fromisoformat(value)
    except Exception:
        if isinstance(value, str) and len(value) == 5:
            return time.fromisoformat(value + ":00")
        raise ValueError("Invalid time format (expected 'HH:MM' or 'HH:MM:SS').")


@preferences_bp.get("")
@auth_required
def get_preferences():
    pref = UserPreferences.query.filter_by(user_id=g.user.id).first()
    if not pref:
        # return default skeleton + exists=False
        return jsonify({
            "exists": False,
            "userId": g.user.id,
            "daysOff": [],
            "workdayPrefStart": None,
            "workdayPrefEnd": None,
            "focusPeakStart": None,
            "focusPeakEnd": None,
            "defaultDurationMinutes": 60,
            "deadlineBehavior": None,
            "flexibility": None,
        }), 200
    data = pref.to_json()
    data["exists"] = True
    return jsonify(data), 200


@preferences_bp.put("")
@auth_required
def upsert_preferences():
    # Block re-submission if already set once
    existing = UserPreferences.query.filter_by(user_id=g.user.id).first()
    if existing:
        return jsonify({"message": "Preferences already set and cannot be changed."}), 409

    data = request.get_json() or {}

    # validate daysOff
    days_off = data.get("daysOff", [])
    if not isinstance(days_off, list) or any(
        not isinstance(d, int) or d < 0 or d > 6 for d in days_off
    ):
        return jsonify({"message": "daysOff must be a list of integers in range 0..6"}), 400

    # parse times
    try:
        workday_pref_start = parse_time(data.get("workdayPrefStart"))
        workday_pref_end   = parse_time(data.get("workdayPrefEnd"))
        focus_peak_start   = parse_time(data.get("focusPeakStart"))
        focus_peak_end     = parse_time(data.get("focusPeakEnd"))
        
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    
    if workday_pref_start and workday_pref_end:
        if workday_pref_end <= workday_pref_start:
            return jsonify({"message": "workdayPrefEnd must be after workdayPrefStart"}), 400

    if focus_peak_start and focus_peak_end:
        if focus_peak_end <= focus_peak_start:
            return jsonify({"message": "focusPeakEnd must be after focusPeakStart"}), 400
    # enums
    deadline_behavior = data.get("deadlineBehavior")
    if deadline_behavior not in (None, "EARLY", "ON_TIME", "LAST_MINUTE"):
        return jsonify({"message": "deadlineBehavior must be one of: EARLY, ON_TIME, LAST_MINUTE"}), 400

    flexibility = data.get("flexibility")
    if flexibility not in (None, "LOW", "MEDIUM", "HIGH"):
        return jsonify({"message": "flexibility must be one of: LOW, MEDIUM, HIGH"}), 400

    # default duration
    try:
        default_duration_minutes = int(data.get("defaultDurationMinutes", 60))
    except (TypeError, ValueError):
        return jsonify({"message": "defaultDurationMinutes must be an integer"}), 400

    # create once
    pref = UserPreferences(
        user_id=g.user.id,
        days_off=days_off,
        workday_pref_start=workday_pref_start,
        workday_pref_end=workday_pref_end,
        focus_peak_start=focus_peak_start,
        focus_peak_end=focus_peak_end,
        default_duration_minutes=default_duration_minutes,
        deadline_behavior=deadline_behavior,
        flexibility=flexibility,
    )
    db.session.add(pref)
    db.session.commit()
    out = pref.to_json()
    out["exists"] = True
    return jsonify(out), 201
