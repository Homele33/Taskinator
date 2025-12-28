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

# Conflict detection
from Ai.suggest_slots import _slot_is_free, _load_busy_intervals

tasks_bp = Blueprint("tasks", __name__)


# ---------- exceptions ----------

class TimeConflictError(Exception):
    """Raised when a task's time slot conflicts with existing tasks."""
    pass


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


def create_task_with_bn_update(
    user_id: int,
    title: str,
    task_type: str,
    priority: str,
    status: str,
    description: str = None,
    due_date: datetime = None,
    due_time: dtime = None,
    duration_minutes: int = 60,
    scheduled_start: datetime = None,
    scheduled_end: datetime = None,
    sub_tasks: list = None
) -> Task:
    """
    Create a task and update BN with the observation.
    
    This is the shared helper used by all task creation flows:
    - Manual task creation (POST /api/tasks)
    - NLP direct creation when all D/T/L present (CASE 2.A)
    - Suggestion-based creation (CASE 2.B)
    
    Args:
        user_id: User ID
        title: Task title (required)
        task_type: Task type (Meeting/Training/Studies)
        priority: Priority level (LOW/MEDIUM/HIGH)
        status: Task status (TODO/IN_PROGRESS/DONE)
        description: Task description (optional)
        due_date: Due date (optional)
        due_time: Due time (optional)
        duration_minutes: Duration in minutes (default 60)
        scheduled_start: Scheduled start datetime (optional)
        scheduled_end: Scheduled end datetime (optional)
        sub_tasks: List of subtask dicts with 'title' and 'description' (optional)
    
    Returns:
        Created Task object
        
    Raises:
        TimeConflictError: If the time slot conflicts with existing tasks
        Exception: If DB commit fails
    """
    # Conflict detection guard: Check for time slot conflicts BEFORE creating task
    print(f"\n[CONFLICT DEBUG] ============================================")
    print(f"[CONFLICT DEBUG] Checking slot: {scheduled_start} to {scheduled_end}")
    if scheduled_start and scheduled_end:
        busy_intervals = _load_busy_intervals(user_id)
        print(f"[CONFLICT DEBUG] Loaded {len(busy_intervals)} busy intervals:")
        for i, (b_start, b_end) in enumerate(busy_intervals):
            print(f"[CONFLICT DEBUG]   Interval {i+1}: {b_start} to {b_end}")
        
        is_free = _slot_is_free(scheduled_start, scheduled_end, busy_intervals)
        print(f"[CONFLICT DEBUG] Slot is FREE? {is_free}")
        
        if not is_free:
            print(f"[CONFLICT DEBUG] ❌ CONFLICT DETECTED! Raising TimeConflictError")
            print(f"[CONFLICT DEBUG] ============================================\n")
            raise TimeConflictError("TimeConflict: Proposed time slot is already busy.")
        else:
            print(f"[CONFLICT DEBUG] ✅ No conflicts, proceeding with task creation")
    else:
        print(f"[CONFLICT DEBUG] No scheduled times, skipping conflict check")
    print(f"[CONFLICT DEBUG] ============================================\n")
    
    # Create Task object
    new_task = Task(
        title=title,
        task_type=task_type,
        description=description,
        priority=priority,
        status=status,
        user_id=user_id,
        due_date=due_date,
        due_time=due_time,
        duration_minutes=duration_minutes,
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
    )
    
    # Add subtasks if provided
    if sub_tasks:
        new_task.sub_tasks = [
            SubTask(title=st.get("title", "").strip(), description=st.get("description"))
            for st in sub_tasks
            if st.get("title")
        ]
    
    # Commit to database
    db.session.add(new_task)
    db.session.commit()
    
    # Update BN with this observation
    try:
        record_observation(_task_to_obs(new_task))
    except Exception as e:
        print(f"[BN] record_observation failed: {e}")
    
    return new_task


# ---------- routes ----------

@tasks_bp.route("", methods=["GET"])
@auth_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=g.user.id).all()
    return jsonify({"tasks": [t.to_json() for t in tasks]}), 200


@tasks_bp.route("", methods=["POST"])
@auth_required
def create_task():
    """
    Manual task creation endpoint (CASE 1).
    
    User provides structured data from the "Add new task" form.
    Creates task directly with exact parameters provided.
    """
    # Check if BN is initialized (with lazy init for existing users)
    from Ai.network.inference import ensure_bn_initialized
    if not ensure_bn_initialized(g.user.id):
        return jsonify({
            "message": "Please complete your preferences setup first",
            "action_required": "set_preferences"
        }), 403
    
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

    # FIX: If no explicit schedule provided, derive from dueDate/dueTime for conflict detection
    # When user provides a due date/time, they're implicitly scheduling the task
    if not scheduled_start and not scheduled_end:
        if due_dt:
            # If due_time is provided separately, use it; otherwise extract from due_dt
            if due_time:
                scheduled_start = datetime.combine(due_dt.date(), due_time)
            elif due_dt.time() != dtime(0, 0):  # due_dt has time component (not just midnight)
                scheduled_start = due_dt
            else:
                scheduled_start = None  # Only date provided, no time - can't schedule
            
            if scheduled_start:
                # Calculate scheduled_end based on duration
                scheduled_end = scheduled_start + timedelta(minutes=duration_minutes)
                print(f"[DEBUG] Derived schedule from dueDate/dueTime: {scheduled_start} to {scheduled_end}")

    # subtasks
    sub_tasks = data.get("subTasks") or []

    # Use shared helper for creation + BN update
    try:
        new_task = create_task_with_bn_update(
            user_id=g.user.id,
            title=title,
            task_type=task_type,
            priority=priority,
            status=status,
            description=description,
            due_date=due_dt,
            due_time=due_time,
            duration_minutes=duration_minutes,
            scheduled_start=scheduled_start,
            scheduled_end=scheduled_end,
            sub_tasks=sub_tasks
        )
        
        # Check for conflicts (Stage 1: detection only, doesn't block creation)
        from services.conflict_detection import check_time_conflicts
        conflict_info = {"hasConflict": False, "conflicts": []}
        if scheduled_start and scheduled_end:
            conflict_info = check_time_conflicts(g.user.id, scheduled_start, scheduled_end)
        
        return jsonify({
            "message": "Task created!",
            "id": new_task.id,
            "task": new_task.to_json(),
            "conflict": conflict_info
        }), 201
    except TimeConflictError as e:
        return jsonify({"status": "conflict", "message": str(e)}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


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
