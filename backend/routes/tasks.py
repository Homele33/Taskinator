#backend/routes/tasks.py
from flask import Blueprint, request, jsonify, g
from datetime import datetime, time as dtime, timedelta
from config import db
from models import Task, SubTask
from services.auth_middleware import auth_required

# BN hooks
from Ai.network.inference import (
    record_observation,
    update_observation,
    remove_observation,
)

tasks_bp = Blueprint("tasks", __name__)


# ---------- helpers ----------

def _parse_time_field(val):
    if not val:
        return None
    try:
        return dtime.fromisoformat(val if len(val) > 5 else f"{val}:00")
    except Exception:
        return None

def _safe_int(val, default=None):
    try:
        return int(val)
    except Exception:
        return default

def _task_to_obs(t: Task) -> dict:
    start = getattr(t, "scheduled_start", None) or getattr(t, "due_date", None)
    end = getattr(t, "scheduled_end", None)

    if not end and start and getattr(t, "duration_minutes", None):
        end = start + timedelta(minutes=int(t.duration_minutes or 0))

    dur = None
    if start and end:
        dur = int((end - start).total_seconds() // 60)

    return {
        "user_id": t.user_id,
        "task_type": t.task_type or "Meeting",
        "priority": t.priority or "MEDIUM",
        "scheduled_start": start,
        "scheduled_end": end,
        "duration_minutes": dur or t.duration_minutes,
    }


# ---------- routes ----------

@tasks_bp.route("", methods=["GET"])
@auth_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=g.user.id).all()
    return jsonify({"tasks": [t.to_json() for t in tasks]}), 200


@tasks_bp.route("", methods=["POST"])
@auth_required
def create_task():
    data = request.get_json(silent=True) or {}

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"message": "You must include a title"}), 400

    task_type = data.get("task_type") or "Meeting"
    description = data.get("description") or None
    priority = (data.get("priority") or "MEDIUM").upper()
    status = data.get("status") or "TODO"

    # dueDate (ISO)
    due_date = data.get("dueDate")
    due_dt = datetime.fromisoformat(due_date) if due_date else None

    # dueTime ("HH:MM" / "HH:MM:SS")
    due_time = _parse_time_field(data.get("dueTime"))

    # duration
    duration_minutes = _safe_int(
        data.get("durationMinutes") or data.get("duration_minutes"),
        default=60,
    )
    if duration_minutes is None:
        return jsonify({"message": "durationMinutes must be an integer"}), 400

    # scheduled start/end (ISO)
    scheduled_start = data.get("scheduledStart") or data.get("scheduled_start")
    scheduled_end   = data.get("scheduledEnd")   or data.get("scheduled_end")
    scheduled_start = datetime.fromisoformat(scheduled_start) if scheduled_start else None
    scheduled_end   = datetime.fromisoformat(scheduled_end) if scheduled_end else None

    # subtasks
    sub_tasks = data.get("subTasks") or []

    new_task = Task(
        title=title,
        task_type=task_type,
        description=description,
        priority=priority,
        status=status,
        user_id=g.user.id,
        due_date=due_dt,
        due_time=due_time,
        duration_minutes=duration_minutes,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
    )

    if sub_tasks:
        new_task.sub_tasks = [
            SubTask(title=st.get("title", "").strip(), description=st.get("description"))
            for st in sub_tasks
            if st.get("title")
        ]

    try:
        db.session.add(new_task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400

    # ---- BN hook: record ----
    try:
        record_observation(_task_to_obs(new_task))
    except Exception as e:
        print(f"[BN] record_observation failed: {e}")

    return jsonify({"message": "Task created!", "id": new_task.id}), 201


@tasks_bp.route("/<int:task_id>", methods=["PATCH"])
@auth_required
def update_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()
    if not task:
        return jsonify({"message": "Task Not Found"}), 404

    before = _task_to_obs(task)  

    data = request.get_json(silent=True) or {}


    if "title" in data:
        task.title = (data.get("title") or task.title) or task.title
    if "task_type" in data:
        task.task_type = data.get("task_type") or task.task_type
    if "description" in data:
        task.description = data.get("description")
    if "status" in data:
        task.status = data.get("status") or task.status
    if "priority" in data:
        task.priority = (data.get("priority") or task.priority or "MEDIUM").upper()

    # dueDate
    if "dueDate" in data:
        due_date = data.get("dueDate")
        task.due_date = datetime.fromisoformat(due_date) if due_date else None

    # dueTime
    if "dueTime" in data:
        task.due_time = _parse_time_field(data.get("dueTime"))

    # duration
    if "durationMinutes" in data or "duration_minutes" in data:
        dm = _safe_int(data.get("durationMinutes") or data.get("duration_minutes"))
        if dm is None:
            return jsonify({"message": "durationMinutes must be an integer"}), 400
        task.duration_minutes = dm

    # scheduled start/end
    if "scheduledStart" in data or "scheduled_start" in data:
        s = data.get("scheduledStart") or data.get("scheduled_start")
        task.scheduled_start = datetime.fromisoformat(s) if s else None
    if "scheduledEnd" in data or "scheduled_end" in data:
        e = data.get("scheduledEnd") or data.get("scheduled_end")
        task.scheduled_end = datetime.fromisoformat(e) if e else None

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 401

    # ---- BN hook: update ----
    try:
        after = _task_to_obs(task)
        update_observation(before, after)
    except Exception as e:
        print(f"[BN] update_observation failed: {e}")

    return jsonify({"message": "Task updated"}), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@auth_required
def delete_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()
    if not task:
        return jsonify({"message": "Task not found"}), 404

    obs = _task_to_obs(task)  

    try:
        db.session.delete(task)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 401

    # ---- BN hook: remove ----
    try:
        remove_observation(obs)
    except Exception as e:
        print(f"[BN] remove_observation failed: {e}")

    return jsonify({"message": "Task deleted"}), 200


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@auth_required
def get_task(task_id):
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()
    if not task:
        return jsonify({"message": "Task not found"}), 404
    return jsonify(task.to_json()), 200


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@auth_required
def toggle_task(task_id):
  
    task = Task.query.filter_by(user_id=g.user.id, id=task_id).first()
    if not task:
        return jsonify({"message": "Task not found"}), 404

    payload = request.get_json(silent=True)
    
    new_status = payload if isinstance(payload, str) else (payload or {}).get("status")
    if not new_status:
        return jsonify({"message": "Missing status"}), 400

    before = _task_to_obs(task) 

    try:
        task.status = new_status
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 401

  
    try:
        after = _task_to_obs(task)
        update_observation(before, after)
    except Exception as e:
        print(f"[BN] update_observation (status) failed: {e}")

    return jsonify({"message": "Task status changed"}), 200
