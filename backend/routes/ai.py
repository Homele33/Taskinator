from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta
from flask_cors import cross_origin
from services.auth_middleware import auth_required
from models import Task, db
from Ai.NLP import handle_free_text_input, parse_free_text
from Ai.suggest_slots import suggest_slots_for_user

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

CORS_ORIGINS = ["http://localhost:3000", "*"]

@ai_bp.route("/<path:_any>", methods=["OPTIONS"])
@cross_origin(origins=CORS_ORIGINS,
              supports_credentials=True,
              allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
              methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def ai_options(_any):
    return ("", 204)

@ai_bp.route("/parseTask", methods=["POST", "OPTIONS"])
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True,
              allow_headers=["Content-Type", "Authorization", "Accept", "Origin"])
@auth_required
def parse_task():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"message": "text is required"}), 400

    result = parse_free_text(text)

    if result.get("status") == "complete":
        return jsonify(result), 200

    parsed = result.get("parsed", {}) or {}
    duration = parsed.get("durationMinutes") or 60

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    suggestions = suggest_slots_for_user(
        user_id=g.user.id,
        duration_minutes=int(duration),
        page=page,
        page_size=3,
        horizon_days=21,
        step_minutes=30,
    )

    result["suggestions"] = suggestions
    return jsonify(result), 200

@ai_bp.route("/createFromText", methods=["POST", "OPTIONS"])
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True,
              allow_headers=["Content-Type", "Authorization", "Accept", "Origin"])
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
    duration = parsed.get("durationMinutes") or 60
    end_dt = start_dt + timedelta(minutes=int(duration))

    new_task = Task(
        title=parsed.get("title") or "New task",
        task_type=parsed.get("task_type") or "Meeting",
        description="",
        status="TODO",
        priority=parsed.get("priority") or "MEDIUM",
        due_date=start_dt,
        due_time=start_dt.time(),
        duration_minutes=int(duration),
        user_id=g.user.id,
    )
    if hasattr(new_task, "scheduled_start"):
        new_task.scheduled_start = start_dt
    if hasattr(new_task, "scheduled_end"):
        new_task.scheduled_end = end_dt

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "message": "Task created",
        "source": "complete-parse",
        "scheduledStart": start_dt.isoformat(),
        "scheduledEnd": end_dt.isoformat(),
        "task": new_task.to_json() if hasattr(new_task, "to_json") else {},
    }), 201

@ai_bp.route("/createFromSuggestion", methods=["POST", "OPTIONS"])
@cross_origin(origins=CORS_ORIGINS, supports_credentials=True,
              allow_headers=["Content-Type", "Authorization", "Accept", "Origin"])
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

    new_task = Task(
        title=title,
        task_type=task_type,
        description="",
        status="TODO",
        priority=priority,
        due_date=start_dt,
        due_time=start_dt.time(),
        duration_minutes=int(duration),
        user_id=g.user.id,
    )
    if hasattr(new_task, "scheduled_start"):
        new_task.scheduled_start = start_dt
    if hasattr(new_task, "scheduled_end"):
        new_task.scheduled_end = end_dt

    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        "message": "Task created from suggestion",
        "source": "suggestion",
        "scheduledStart": start_dt.isoformat(),
        "scheduledEnd": end_dt.isoformat(),
        "task": new_task.to_json() if hasattr(new_task, "to_json") else {"id": new_task.id}
    }), 201
