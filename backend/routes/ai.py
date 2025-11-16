from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta, time as dtime
from flask_cors import cross_origin
from services.auth_middleware import auth_required
from models import Task, db
from Ai.NLP import handle_free_text_input, parse_free_text
from Ai.suggest_slots import suggest_slots_for_user
from Ai.network.inference import record_observation  

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

CORS_ORIGINS = ["http://localhost:3000", "*"]


@ai_bp.route("/<path:_any>", methods=["OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
)
def ai_options(_any):
    return ("", 204)


# ------------ helper: infer part-of-day window from raw text ------------

def _infer_day_window(text: str):
    """
    מחזיר (day_start, day_end) לפי מילים כמו morning / afternoon / evening / night.
    אם אין מילת חלק-יום – מחזיר (None, None) ולא מגביל כלום.
    """
    t = text.lower()


    if "morning" in t:
        return dtime(8, 0), dtime(12, 0)
    if "afternoon" in t:
        return dtime(13, 0), dtime(17, 0)
    if "evening" in t:
        return dtime(18, 0), dtime(22, 0)
    if "night" in t:
        return dtime(21, 0), dtime(23, 59)

    return None, None


# ------------ /api/ai/parseTask ------------

@ai_bp.route("/parseTask", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def parse_task():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"message": "text is required"}), 400

    result = parse_free_text(text)
    parsed = result.get("parsed", {}) or {}

    duration = parsed.get("durationMinutes") or 60
    task_type = parsed.get("task_type") or "Meeting"


    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

   
    preferred_start = None
    if parsed.get("dueDateTime"):
        try:
            preferred_start = datetime.fromisoformat(parsed["dueDateTime"])
        except ValueError:
            preferred_start = None


    window_start = None
    window_end = None
    if parsed.get("windowStart"):
        try:
            window_start = datetime.fromisoformat(parsed["windowStart"])
        except ValueError:
            window_start = None
    if parsed.get("windowEnd"):
        try:
            window_end = datetime.fromisoformat(parsed["windowEnd"])
        except ValueError:
            window_end = None

 
    day_start, day_end = _infer_day_window(text)

    suggestions = suggest_slots_for_user(
        user_id=g.user.id,
        duration_minutes=int(duration),
        task_type=task_type,
        page=page,
        page_size=3,
        horizon_days=21,
        step_minutes=30,
        preferred_start=preferred_start,
        window_start=window_start,
        window_end=window_end,
        day_start=day_start,
        day_end=day_end,
    )

    result["suggestions"] = suggestions
    return jsonify(result), 200


# ------------ /api/ai/createFromText ------------

@ai_bp.route("/createFromText", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def create_from_text():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"message": "text is required"}), 400

    result = handle_free_text_input(text)
    if result.get("status") != "complete":
        return jsonify({"message": "parse not complete", "result": result}), 400

    parsed = result["parsed"]
    start_dt = datetime.fromisoformat(parsed["dueDateTime"])
    duration = int(parsed.get("durationMinutes") or 60)
    end_dt = start_dt + timedelta(minutes=duration)

    task_type = parsed.get("task_type") or "Meeting"
    priority = parsed.get("priority") or "MEDIUM"

    new_task = Task(
        title=parsed.get("title") or "New task",
        task_type=task_type,
        description="",
        status="TODO",
        priority=priority,
        due_date=start_dt,
        due_time=start_dt.time(),
        duration_minutes=duration,
        user_id=g.user.id,
    )
    if hasattr(new_task, "scheduled_start"):
        new_task.scheduled_start = start_dt
    if hasattr(new_task, "scheduled_end"):
        new_task.scheduled_end = end_dt

    db.session.add(new_task)
    db.session.commit()

    # learning update
    record_observation(
        {
            "user_id": g.user.id,
            "task_type": task_type,
            "priority": priority,
            "scheduled_start": start_dt,
            "scheduled_end": end_dt,
            "duration_minutes": duration,
        }
    )

    return jsonify(
        {
            "message": "Task created",
            "source": "complete-parse",
            "scheduledStart": start_dt.isoformat(),
            "scheduledEnd": end_dt.isoformat(),
            "task": new_task.to_json() if hasattr(new_task, "to_json") else {},
        }
    ), 201


# ------------ /api/ai/createFromSuggestion ------------

@ai_bp.route("/createFromSuggestion", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def create_from_suggestion():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "New task").strip()
    task_type = data.get("task_type") or "Meeting"
    priority = (data.get("priority") or "MEDIUM").upper()
    duration = data.get("durationMinutes")

    start_iso = data.get("scheduledStart")
    end_iso = data.get("scheduledEnd")
    if not (start_iso and end_iso):
        return jsonify({"message": "scheduledStart and scheduledEnd are required"}), 400

    try:
        start_dt = datetime.fromisoformat(start_iso)
        end_dt = datetime.fromisoformat(end_iso)
    except ValueError:
        return jsonify({"message": "Invalid ISO datetimes"}), 400

    if not duration:
        duration = int((end_dt - start_dt).total_seconds() // 60)
    else:
        duration = int(duration)

    new_task = Task(
        title=title,
        task_type=task_type,
        description="",
        status="TODO",
        priority=priority,
        due_date=start_dt,
        due_time=start_dt.time(),
        duration_minutes=duration,
        user_id=g.user.id,
    )
    if hasattr(new_task, "scheduled_start"):
        new_task.scheduled_start = start_dt
    if hasattr(new_task, "scheduled_end"):
        new_task.scheduled_end = end_dt

    db.session.add(new_task)
    db.session.commit()

    # learning update
    record_observation(
        {
            "user_id": g.user.id,
            "task_type": task_type,
            "priority": priority,
            "scheduled_start": start_dt,
            "scheduled_end": end_dt,
            "duration_minutes": duration,
        }
    )

    return jsonify(
        {
            "message": "Task created from suggestion",
            "source": "suggestion",
            "scheduledStart": start_dt.isoformat(),
            "scheduledEnd": end_dt.isoformat(),
            "task": new_task.to_json()
            if hasattr(new_task, "to_json")
            else {"id": new_task.id},
        }
    ), 201
