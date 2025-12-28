from flask import Blueprint, request, jsonify, g
from datetime import datetime, timedelta, time as dtime
import calendar
from flask_cors import cross_origin
from services.auth_middleware import auth_required
from models import Task, db
from Ai.NLP import handle_free_text_input, parse_free_text
from Ai.suggest_slots import suggest_slots_for_user
from routes.tasks import TimeConflictError  

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


# ------------ helper: get user's default duration ------------

def _get_user_default_duration(user_id: int) -> int:
    """
    Fetch the user's default_duration_minutes from preferences.
    
    Args:
        user_id: The ID of the user
    
    Returns:
        int: The user's default duration in minutes (fallback to 60 if not set)
    """
    from models import UserPreferences
    prefs = db.session.query(UserPreferences).filter_by(user_id=user_id).first()
    default_duration = prefs.default_duration_minutes if prefs else 60
    
    print(f"[DURATION DEBUG] User {user_id} default_duration_minutes: {default_duration}")
    
    return default_duration


# ------------ /api/ai/parseTask ------------

@ai_bp.route("/parseTask", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def parse_task():
    """
    Parse free text and determine whether to create task directly (CASE 2.A)
    or generate suggestions (CASE 2.B).
    
    Returns:
        - shouldCreateDirectly: true if all D/T/L present (CASE 2.A)
        - shouldCreateDirectly: false if at least one missing (CASE 2.B)
        - suggestions: empty if shouldCreateDirectly=true, populated otherwise
    """
    # Check if BN is initialized (with lazy init for existing users)
    from Ai.network.inference import ensure_bn_initialized
    if not ensure_bn_initialized(g.user.id):
        return jsonify({
            "message": "Please complete your preferences setup first",
            "action_required": "set_preferences"
        }), 403
    
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"message": "text is required"}), 400

    # Parse free text to extract structured fields
    result = parse_free_text(text)
    parsed = result.get("parsed", {}) or {}
    critical = result.get("critical_fields", {})

    # CASE 4: Date + Time but NO Duration → Use default_duration_minutes and create directly
    has_date = critical.get("has_date", False)
    has_time = critical.get("has_time", False)
    has_duration = critical.get("has_duration", False)
    
    if has_date and has_time and not has_duration:
        print(f"\n[CASE 4: DATE+TIME, NO DURATION] ============================================")
        print(f"[CASE 4] User provided Date + Time but NO Duration")
        print(f"[CASE 4] Fetching user's default_duration_minutes...")
        
        # Fetch user's default duration from preferences
        default_duration = _get_user_default_duration(g.user.id)
        
        print(f"[DURATION DEBUG] No duration in NLP, using User Preference: {default_duration} minutes")
        print(f"[CASE 4] Setting duration to {default_duration} and creating task directly")
        
        # Add duration to parsed data
        parsed["durationMinutes"] = default_duration
        
        # Extract datetime and check for conflicts
        if parsed.get("dueDateTime"):
            try:
                start_dt = datetime.fromisoformat(parsed["dueDateTime"])
                end_dt = start_dt + timedelta(minutes=default_duration)
                
                print(f"[CASE 4] Task details:")
                print(f"[CASE 4]   - Start: {start_dt}")
                print(f"[CASE 4]   - End: {end_dt}")
                print(f"[CASE 4]   - Duration: {default_duration} minutes")
                print(f"[CASE 4] Checking for conflicts...")
                
                # Check for overlaps
                from Ai.suggest_slots import _load_busy_intervals, _slot_is_free
                busy_intervals = _load_busy_intervals(g.user.id)
                is_free = _slot_is_free(start_dt, end_dt, busy_intervals)
                
                print(f"[CASE 4] Slot is FREE? {is_free}")
                
                if not is_free:
                    print(f"[CASE 4] ❌ CONFLICT! Returning 409 with parsed data")
                    print(f"[CASE 4] ============================================\n")
                    return jsonify({
                        "status": "conflict",
                        "message": "TimeConflict: Proposed time slot is already busy.",
                        "parsed": parsed,
                        "result": result,
                        "scheduledStart": start_dt.isoformat(),
                        "scheduledEnd": end_dt.isoformat(),
                        "dueDate": start_dt.isoformat(),
                        "durationMinutes": default_duration,
                        "task_type": parsed.get("task_type") or "Meeting",
                        "title": parsed.get("title") or "New task",
                        "priority": parsed.get("priority") or "MEDIUM"
                    }), 409
                
                # No conflict → create task directly
                print(f"[CASE 4] ✅ No conflict! Creating task directly...")
                from routes.tasks import create_task_with_bn_update
                
                task_type = parsed.get("task_type") or "Meeting"
                priority = parsed.get("priority") or "MEDIUM"
                title = parsed.get("title") or "New task"
                
                new_task = create_task_with_bn_update(
                    user_id=g.user.id,
                    title=title,
                    task_type=task_type,
                    priority=priority,
                    status="TODO",
                    description="",
                    scheduled_start=start_dt,
                    scheduled_end=end_dt,
                    duration_minutes=default_duration,
                )
                
                print(f"[CASE 4] ✅ Task created successfully with ID: {new_task.id}")
                print(f"[CASE 4] ============================================\n")
                
                result["shouldCreateDirectly"] = True
                result["suggestions"] = []
                result["task"] = new_task.to_json()
                result["case"] = "CASE_4_DATE_TIME_NO_DURATION"
                return jsonify(result), 200
                
            except (ValueError, KeyError) as e:
                print(f"[CASE 4] ❌ Error: {e}")
                print(f"[CASE 4] Falling back to suggestion generation")
                print(f"[CASE 4] ============================================\n")
                # Continue with normal suggestion flow if parsing fails
    
    # Check if all three critical fields (D/T/L) are present
    if critical.get("all_present", False):
        # CASE 2.A: All D/T/L present → BUT check for overlaps first!
        # CRITICAL FIX: Check for conflicts BEFORE returning shouldCreateDirectly
        
        # Extract datetime and duration for overlap check
        if parsed.get("dueDateTime"):
            try:
                start_dt = datetime.fromisoformat(parsed["dueDateTime"])
                # Use user preference if duration not in NLP
                duration = parsed.get("durationMinutes")
                if not duration:
                    duration = _get_user_default_duration(g.user.id)
                    print(f"[DURATION DEBUG] No duration in NLP, using User Preference: {duration} minutes")
                else:
                    duration = int(duration)
                end_dt = start_dt + timedelta(minutes=duration)
                
                print(f"\n[PARSE TASK OVERLAP CHECK] ============================================")
                print(f"[PARSE TASK OVERLAP CHECK] Checking for overlaps:")
                print(f"[PARSE TASK OVERLAP CHECK]   - Start: {start_dt}")
                print(f"[PARSE TASK OVERLAP CHECK]   - End: {end_dt}")
                print(f"[PARSE TASK OVERLAP CHECK]   - Duration: {duration} minutes")
                
                # Load busy intervals and check for overlap
                from Ai.suggest_slots import _load_busy_intervals, _slot_is_free
                busy_intervals = _load_busy_intervals(g.user.id)
                is_free = _slot_is_free(start_dt, end_dt, busy_intervals)
                
                print(f"[PARSE TASK OVERLAP CHECK] Slot is FREE? {is_free}")
                print(f"[PARSE TASK OVERLAP CHECK] ============================================\n")
                
                if not is_free:
                    # CONFLICT DETECTED! Return 409 with task data
                    print(f"[PARSE TASK 409] ❌ CONFLICT! Returning 409 with parsed data")
                    return jsonify({
                        "status": "conflict",
                        "message": "TimeConflict: Proposed time slot is already busy.",
                        # Include parsed data for frontend
                        "parsed": parsed,
                        "result": result,
                        "scheduledStart": start_dt.isoformat(),
                        "scheduledEnd": end_dt.isoformat(),
                        "dueDate": start_dt.isoformat(),
                        "durationMinutes": duration,
                        "task_type": parsed.get("task_type") or "Meeting",
                        "title": parsed.get("title") or "New task",
                        "priority": parsed.get("priority") or "MEDIUM"
                    }), 409
            except (ValueError, KeyError) as e:
                print(f"[PARSE TASK OVERLAP CHECK] Failed to parse datetime: {e}")
                # Continue with normal flow if parsing fails
        
        # No conflict or couldn't check → proceed with direct creation
        result["shouldCreateDirectly"] = True
        result["suggestions"] = []
        return jsonify(result), 200

    # CASE 2.B: At least one critical field missing → generate suggestions
    # Extract known constraints for suggestion generation
    # IMPORTANT: Only default duration if it's actually missing, don't override parsed value
    duration = parsed.get("durationMinutes")
    if not duration:
        # CRITICAL FIX: Use user preference instead of hardcoded 60
        duration = _get_user_default_duration(g.user.id)
        print(f"[DURATION DEBUG] No duration in NLP, using User Preference: {duration} minutes")
    task_type = parsed.get("task_type") or "Meeting"

    try:
        page = int(request.args.get("page", "1"))
    except ValueError:
        page = 1
    if page < 1:
        page = 1

    # Use preferred_start if exact datetime is known (date+time fixed)
    preferred_start = None
    if parsed.get("dueDateTime"):
        try:
            preferred_start = datetime.fromisoformat(parsed["dueDateTime"])
        except ValueError:
            preferred_start = None

    # Use window constraints if date range is known (but not exact time)
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

    # Infer part-of-day window from text (e.g., "morning", "afternoon")
    day_start, day_end = _infer_day_window(text)

    # Extract explicitDateRequested flag to override rest day filtering
    # This is TRUE when user specifies a concrete date (absolute or relative)
    # and FALSE for vague ranges like "sometime this week"
    explicit_date_requested = parsed.get("explicitDateRequested", False)

    # Extract explicitDateTimeGiven flag for CASE 2.D (date+time but no duration)
    explicit_datetime_given = parsed.get("explicitDateTimeGiven", False)

    # Extract preferred time of day (for cases like "sometime this week at 10am")
    preferred_time_str = parsed.get("preferredTimeOfDay")
    preferred_time_tuple = None
    if preferred_time_str:
        try:
            parts = preferred_time_str.split(":")
            if len(parts) == 2:
                preferred_time_tuple = (int(parts[0]), int(parts[1]))
        except (ValueError, AttributeError):
            preferred_time_tuple = None
    
    # CASE 2: Fixed-Time Search (Time + Duration but NO Date)
    # Detect when user specifies time and duration but not a specific date
    # Example: "at 16:00 for 60 minutes" → scan next 30 days, only show slots at 16:00
    fixed_time_search = False
    if not has_date and has_duration and preferred_time_tuple:
        fixed_time_search = True
        print(f"\n[CASE 2: FIXED-TIME SEARCH] ============================================")
        print(f"[CASE 2] User provided Time + Duration but NO Date")
        print(f"[CASE 2] Fixed time: {preferred_time_tuple[0]:02d}:{preferred_time_tuple[1]:02d}")
        print(f"[CASE 2] Duration: {duration} minutes")
        print(f"[CASE 2] Will scan next 30 days for slots at this exact time")
        print(f"[CASE 2] ============================================\n")

    # Generate suggestions based on known constraints
    # BN will fill in missing fields (date, time, or duration)
    suggestions = suggest_slots_for_user(
        user_id=g.user.id,
        duration_minutes=int(duration),
        task_type=task_type,
        page=page,
        page_size=3,
        horizon_days=30 if fixed_time_search else 21,  # Wider horizon for fixed-time search
        step_minutes=30,
        preferred_start=preferred_start,
        window_start=window_start,
        window_end=window_end,
        day_start=day_start,
        day_end=day_end,
        explicit_date_requested=explicit_date_requested,
        preferred_time_of_day=preferred_time_tuple,
        explicit_datetime_given=explicit_datetime_given,
        fixed_time_search=fixed_time_search,  # CASE 2: Strict time filtering
    )

    result["shouldCreateDirectly"] = False
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
    """
    NLP direct creation endpoint (CASE 2.A).
    
    Called when all three critical fields (D/T/L) are present in the text.
    Creates task directly with parsed parameters.
    """
    # Check if BN is initialized (with lazy init for existing users)
    from Ai.network.inference import ensure_bn_initialized
    from routes.tasks import create_task_with_bn_update
    
    if not ensure_bn_initialized(g.user.id):
        return jsonify({
            "message": "Please complete your preferences setup first",
            "action_required": "set_preferences"
        }), 403
    
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()
    if not text:
        return jsonify({"message": "text is required"}), 400

    result = handle_free_text_input(text)
    if result.get("status") != "complete":
        return jsonify({"message": "parse not complete", "result": result}), 400

    parsed = result["parsed"]
    start_dt = datetime.fromisoformat(parsed["dueDateTime"])
    # Use user preference if duration not in NLP
    duration = parsed.get("durationMinutes")
    if not duration:
        duration = _get_user_default_duration(g.user.id)
        print(f"[DURATION DEBUG] No duration in NLP, using User Preference: {duration} minutes")
    else:
        duration = int(duration)
    end_dt = start_dt + timedelta(minutes=duration)

    task_type = parsed.get("task_type") or "Meeting"
    priority = parsed.get("priority") or "MEDIUM"
    title = parsed.get("title") or "New task"

    # Use shared helper for creation + BN update
    try:
        new_task = create_task_with_bn_update(
            user_id=g.user.id,
            title=title,
            task_type=task_type,
            priority=priority,
            status="TODO",
            description="",
            due_date=start_dt,
            due_time=start_dt.time(),
            duration_minutes=duration,
            scheduled_start=start_dt,
            scheduled_end=end_dt,
            sub_tasks=[]
        )
        
        # Check for conflicts (Stage 1: detection only, doesn't block creation)
        from services.conflict_detection import check_time_conflicts
        conflict_info = check_time_conflicts(g.user.id, start_dt, end_dt)
        
        return jsonify({
            "message": "Task created",
            "source": "complete-parse",
            "scheduledStart": start_dt.isoformat(),
            "scheduledEnd": end_dt.isoformat(),
            "task": new_task.to_json() if hasattr(new_task, "to_json") else {"id": new_task.id},
            "conflict": conflict_info
        }), 201
    except TimeConflictError as e:
        # CRITICAL FIX: Return parsed date/time data with 409 so frontend can pass to suggest endpoint
        print(f"[CONFLICT FIX] Returning 409 with parsed task data:")
        print(f"[CONFLICT FIX]   - scheduledStart: {start_dt.isoformat()}")
        print(f"[CONFLICT FIX]   - scheduledEnd: {end_dt.isoformat()}")
        print(f"[CONFLICT FIX]   - durationMinutes: {duration}")
        print(f"[CONFLICT FIX]   - task_type: {task_type}")
        
        return jsonify({
            "status": "conflict", 
            "message": str(e),
            # Include task data so frontend can pass to suggest endpoint
            "scheduledStart": start_dt.isoformat(),
            "scheduledEnd": end_dt.isoformat(),
            "dueDate": start_dt.isoformat(),  # For backward compatibility
            "durationMinutes": duration,
            "task_type": task_type,
            "title": title,
            "priority": priority
        }), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


# ------------ /api/ai/createFromSuggestion ------------

@ai_bp.route("/createFromSuggestion", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def create_from_suggestion():
    """
    NLP suggestion-based creation endpoint (CASE 2.B).
    
    Called when user selects a suggestion from the list.
    Creates task with the chosen time slot.
    """
    # Check if BN is initialized (with lazy init for existing users)
    from Ai.network.inference import ensure_bn_initialized
    from routes.tasks import create_task_with_bn_update
    
    if not ensure_bn_initialized(g.user.id):
        return jsonify({
            "message": "Please complete your preferences setup first",
            "action_required": "set_preferences"
        }), 403
    
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

    # Use shared helper for creation + BN update
    try:
        new_task = create_task_with_bn_update(
            user_id=g.user.id,
            title=title,
            task_type=task_type,
            priority=priority,
            status="TODO",
            description="",
            due_date=start_dt,
            due_time=start_dt.time(),
            duration_minutes=duration,
            scheduled_start=start_dt,
            scheduled_end=end_dt,
            sub_tasks=[]
        )
        
        # Check for conflicts (Stage 1: detection only, doesn't block creation)
        from services.conflict_detection import check_time_conflicts
        conflict_info = check_time_conflicts(g.user.id, start_dt, end_dt)
        
        return jsonify({
            "message": "Task created from suggestion",
            "source": "suggestion",
            "scheduledStart": start_dt.isoformat(),
            "scheduledEnd": end_dt.isoformat(),
            "task": new_task.to_json() if hasattr(new_task, "to_json") else {"id": new_task.id},
            "conflict": conflict_info
        }), 201
    except TimeConflictError as e:
        return jsonify({"status": "conflict", "message": str(e)}), 409
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


# ------------ /api/ai/suggest ------------

@ai_bp.route("/suggest", methods=["POST", "OPTIONS"])
@cross_origin(
    origins=CORS_ORIGINS,
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin"],
)
@auth_required
def get_manual_suggestions():
    """
    Fetch time slot suggestions based on structured input and search strategy.
    
    This endpoint is used for conflict resolution - when a user's requested
    time slot conflicts with existing tasks, the frontend calls this to get
    alternative suggestions based on their chosen strategy (day/week/month/auto).
    
    Request Body:
        - durationMinutes (int, optional): Task duration in minutes (uses user preference if not provided)
        - task_type (str): Type of task - Meeting/Training/Studies (default: "Meeting")
        - strategy (str): Search strategy - 'day'/'week'/'month'/'auto' (default: "auto")
        - referenceDate (str, optional): ISO format datetime to use as starting point
    
    Returns:
        JSON with suggestions array containing time slots with scores
    """
    import traceback
    print(f"\n[DEBUG] Suggest Endpoint Hit. Data: {request.get_json()}")
    
    # Check if BN is initialized
    from Ai.network.inference import ensure_bn_initialized
    if not ensure_bn_initialized(g.user.id):
        return jsonify({
            "message": "Please complete your preferences setup first",
            "action_required": "set_preferences"
        }), 403
    
    data = request.get_json(silent=True) or {}
    
    # CRITICAL FIX: Extract page and page_size FIRST, before any logic that uses them
    # Pagination support - must be at the very beginning
    try:
        page = int(data.get("page", 1))
    except (ValueError, TypeError):
        page = 1
    if page < 1:
        page = 1
    
    # UX: Allow customizable page size, default to 3 for optimal chunks
    try:
        page_size = int(data.get("pageSize", 3))
    except (ValueError, TypeError):
        page_size = 3
    # Cap at reasonable maximum
    if page_size < 1:
        page_size = 3
    if page_size > 20:
        page_size = 20
    
    # Parse input parameters
    # CRITICAL FIX: Use user preference instead of hardcoded 60
    duration = data.get("durationMinutes")
    if duration is not None:
        duration = int(duration)
    else:
        duration = _get_user_default_duration(g.user.id)
        print(f"[DURATION DEBUG] No duration in request, using User Preference: {duration} minutes")
    
    task_type = data.get("task_type", "Meeting")
    if task_type not in ("Meeting", "Training", "Studies"):
        task_type = "Meeting"
    
    strategy = data.get("strategy", None)
    
    # CRITICAL FIX: Extract target task date from multiple possible sources
    # Priority order: scheduledStart > scheduledEnd > dueDate > referenceDate > now
    target_task_date = None
    
    print(f"\n[DATE EXTRACTION] ============================================")
    print(f"[DATE EXTRACTION] Received data keys: {list(data.keys())}")
    print(f"[DATE EXTRACTION]   - scheduledStart: {data.get('scheduledStart')}")
    print(f"[DATE EXTRACTION]   - scheduledEnd: {data.get('scheduledEnd')}")
    print(f"[DATE EXTRACTION]   - dueDate: {data.get('dueDate')}")
    print(f"[DATE EXTRACTION]   - referenceDate: {data.get('referenceDate')}")
    
    # Try scheduledStart first (most specific)
    if data.get("scheduledStart"):
        try:
            target_task_date = datetime.fromisoformat(data["scheduledStart"].replace('Z', '+00:00'))
            print(f"[DATE EXTRACTION] ✅ Using scheduledStart as target date: {target_task_date}")
        except (ValueError, AttributeError) as e:
            print(f"[DATE EXTRACTION] ❌ Failed to parse scheduledStart: {e}")
    
    # Try scheduledEnd if scheduledStart not available
    if not target_task_date and data.get("scheduledEnd"):
        try:
            target_task_date = datetime.fromisoformat(data["scheduledEnd"].replace('Z', '+00:00'))
            print(f"[DEBUG] Using scheduledEnd as target date: {target_task_date}")
        except (ValueError, AttributeError):
            pass
    
    # Try dueDate if neither scheduled field available
    if not target_task_date and data.get("dueDate"):
        try:
            target_task_date = datetime.fromisoformat(data["dueDate"].replace('Z', '+00:00'))
            print(f"[DEBUG] Using dueDate as target date: {target_task_date}")
        except (ValueError, AttributeError):
            pass
    
    # Parse reference date or use now
    ref_date_str = data.get("referenceDate")
    if ref_date_str:
        try:
            # Handle ISO format with 'Z' suffix (UTC timezone)
            if ref_date_str.endswith('Z'):
                ref_date_str = ref_date_str[:-1] + '+00:00'
            now = datetime.fromisoformat(ref_date_str)
            print(f"[DEBUG] Using reference date from request (UTC): {now}")
            
            # FIX: Convert to local system time FIRST, then make naive
            # This prevents early morning UTC shift (06:15 UTC becomes local time, not 06:15 local)
            if now.tzinfo is not None:
                now = now.astimezone(None).replace(tzinfo=None)
                print(f"[DEBUG] Converted to Local Naive Time: {now}")
            else:
                print(f"[DEBUG] Already offset-naive: {now}")
        except (ValueError, AttributeError) as e:
            print(f"[DEBUG] Failed to parse referenceDate '{ref_date_str}': {e}")
            now = datetime.now()
            print(f"[DEBUG] Falling back to current time: {now}")
    else:
        now = datetime.now()
        print(f"[DEBUG] No referenceDate provided, using current time: {now}")
    
    # Smart strategy defaulting: If scheduledStart is provided but no strategy, default to 'day'
    # This ensures date locking for NLP inputs like "Jan 5th for 60 minutes"
    if strategy is None:
        if data.get("scheduledStart") or data.get("dueDate"):
            strategy = "day"
            print(f"[STRATEGY DEFAULT] ✅ scheduledStart/dueDate provided, defaulting to 'day' strategy")
        else:
            strategy = "auto"
            print(f"[STRATEGY DEFAULT] ✅ No date provided, defaulting to 'auto' strategy")
    
    # Validate strategy
    if strategy not in ("day", "week", "month", "auto"):
        strategy = "auto"
        print(f"[STRATEGY DEFAULT] ⚠️ Invalid strategy, falling back to 'auto'")
    
    print(f"[DATE EXTRACTION] Final strategy: {strategy}")
    print(f"[DATE EXTRACTION] ============================================\n")
    
    # Calculate time window based on strategy
    # CRITICAL FIX: For "Same Day" conflict resolution, use the TARGET TASK'S date
    # extracted from payload fields (scheduledStart/End, dueDate) or referenceDate
    window_start = now
    window_end = None  # Default for 'auto'
    
    # CRITICAL FIX: Check if windowStart/windowEnd are provided in request (e.g., "next week")
    # If present, they override strategy-based calculation
    request_window_start = data.get("windowStart")
    request_window_end = data.get("windowEnd")
    
    if request_window_start and request_window_end:
        try:
            window_start = datetime.fromisoformat(request_window_start.replace('Z', '+00:00'))
            window_end = datetime.fromisoformat(request_window_end.replace('Z', '+00:00'))
            
            # Convert to local time if timezone-aware
            if window_start.tzinfo is not None:
                window_start = window_start.astimezone(None).replace(tzinfo=None)
            if window_end.tzinfo is not None:
                window_end = window_end.astimezone(None).replace(tzinfo=None)
            
            print(f"\n[WINDOW CONSTRAINT] ============================================")
            print(f"[WINDOW CONSTRAINT] ✅ Using window from request (e.g., 'next week')")
            print(f"[WINDOW CONSTRAINT] windowStart: {window_start}")
            print(f"[WINDOW CONSTRAINT] windowEnd: {window_end}")
            print(f"[WINDOW CONSTRAINT] Duration: {(window_end - window_start).days + 1} days")
            print(f"[WINDOW CONSTRAINT] This overrides strategy-based calculation")
            print(f"[WINDOW CONSTRAINT] ============================================\n")
            
            # Skip strategy-based calculation, window is already set
        except (ValueError, AttributeError) as e:
            print(f"[WINDOW CONSTRAINT] ❌ Failed to parse window constraints: {e}")
            print(f"[WINDOW CONSTRAINT] Falling back to strategy-based calculation")
            # Continue with strategy-based calculation below
    
    if not (request_window_start and request_window_end):
        # No explicit window provided, calculate based on strategy
        print(f"[WINDOW CONSTRAINT] ⚪ No window constraint in request, using strategy: {strategy}")
    
    if strategy == "day" and not (request_window_start and request_window_end):
        # Same day: Use the FULL day of the target task (00:00 to 23:59:59)
        # Priority: Use target_task_date if available, otherwise fall back to referenceDate (now)
        print(f"\n[WINDOW CALCULATION] ============================================")
        print(f"[WINDOW CALCULATION] Strategy: 'day' (Same Day)")
        print(f"[WINDOW CALCULATION] target_task_date: {target_task_date}")
        print(f"[WINDOW CALCULATION] now (referenceDate): {now}")
        
        if target_task_date:
            # Convert to local time if timezone-aware
            if target_task_date.tzinfo is not None:
                target_task_date = target_task_date.astimezone(None).replace(tzinfo=None)
            target_date = target_task_date.date()
            print(f"[WINDOW CALCULATION] ✅ Using extracted task date: {target_date}")
        else:
            target_date = now.date()
            print(f"[WINDOW CALCULATION] ⚠️ Falling back to referenceDate: {target_date}")
        
        window_start = datetime.combine(target_date, dtime(0, 0, 0))  # Start of day
        window_end = datetime.combine(target_date, dtime(23, 59, 59, 999999))  # End of day
        
        # CRITICAL SAFETY CHECK: If paginating (page > 1) with a locked date,
        # ENFORCE the window boundaries to prevent date leakage
        if page > 1 and data.get("scheduledStart"):
            print(f"[PAGINATION SAFETY CHECK] Page {page} with scheduledStart - ENFORCING date lock")
            print(f"[PAGINATION SAFETY CHECK] Window LOCKED to: {window_start.date()} to {window_end.date()}")
            # Window is already set correctly above, just logging for safety
        
        print(f"[WINDOW CALCULATION] ✅ Final window_start: {window_start}")
        print(f"[WINDOW CALCULATION] ✅ Final window_end: {window_end}")
        print(f"[WINDOW CALCULATION] ============================================\n")
    elif strategy == "week" and not (request_window_start and request_window_end):
        # This week: from now until end of current calendar week (Saturday 23:59:59)
        # weekday() returns: 0=Monday, 1=Tuesday, ..., 5=Saturday, 6=Sunday
        current_weekday = now.weekday()
        
        # Calculate days until Saturday (5)
        if current_weekday <= 5:  # Monday-Saturday
            days_until_saturday = 5 - current_weekday
        else:  # Sunday (6)
            days_until_saturday = 6  # Next Saturday is 6 days away
        
        # Set window_end to Saturday 23:59:59
        saturday = now.date() + timedelta(days=days_until_saturday)
        window_end = datetime.combine(saturday, dtime(23, 59, 59, 999999))
        
        print(f"[WINDOW CALCULATION] ============================================")
        print(f"[WINDOW CALCULATION] Strategy: This Week")
        print(f"[WINDOW CALCULATION] Current date: {now.date()} ({['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][current_weekday]})")
        print(f"[WINDOW CALCULATION] Days until Saturday: {days_until_saturday}")
        print(f"[WINDOW CALCULATION] ✅ window_end set to: {window_end} (Saturday)")
        print(f"[WINDOW CALCULATION] ============================================\n")
    elif strategy == "month" and not (request_window_start and request_window_end):
        # This month: from start of next week (Sunday) until last day of current month
        # Calculate current week's Saturday
        current_weekday = now.weekday()  # 0=Mon, 5=Sat, 6=Sun
        
        # Calculate days until Saturday
        if current_weekday <= 5:  # Monday-Saturday
            days_until_saturday = 5 - current_weekday
        else:  # Sunday (6)
            days_until_saturday = 6  # Next Saturday
        
        # Get Saturday of current week
        saturday = now.date() + timedelta(days=days_until_saturday)
        
        # window_start: Next Sunday (day after Saturday) at 00:00:00
        sunday = saturday + timedelta(days=1)
        window_start = datetime.combine(sunday, dtime(0, 0, 0))
        
        # window_end: Last day of the month at 23:59:59
        # Get the last day of the current month
        year = now.year
        month = now.month
        last_day_of_month = calendar.monthrange(year, month)[1]
        month_end = datetime(year, month, last_day_of_month, 23, 59, 59, 999999)
        window_end = month_end
        
        print(f"[WINDOW CALCULATION] ============================================")
        print(f"[WINDOW CALCULATION] Strategy: This Month")
        print(f"[MONTH STRATEGY] Conflict Date: {now.date()}")
        print(f"[WINDOW CALCULATION] Current weekday: {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][current_weekday]}")
        print(f"[WINDOW CALCULATION] Current week ends: Saturday {saturday}")
        print(f"[WINDOW CALCULATION] ✅ window_start set to: {window_start} (Next Sunday)")
        print(f"[MONTH STRATEGY] Window: {window_start} to {window_end}")
        print(f"[WINDOW CALCULATION] ✅ window_end set to: {window_end} (Last day of month)")
        print(f"[WINDOW CALCULATION] ============================================\n")
    elif strategy == "auto" and not (request_window_start and request_window_end):
        # Next Best Slot: Global quality search starting from CURRENT TIME
        # CRITICAL: Search starts from NOW (datetime.now()), not from conflict date
        # This allows the system to find best slots in the user's calendar from today onwards
        
        # Get current system time
        current_time = datetime.now()
        
        # Set search window: from now to 30 days ahead
        window_start = current_time
        window_end = current_time + timedelta(days=30)
        
        # Extract conflict info for logging (but don't use it for window)
        conflict_info = "Unknown"
        if target_task_date:
            if target_task_date.tzinfo is not None:
                target_task_date = target_task_date.astimezone(None).replace(tzinfo=None)
            conflict_info = str(target_task_date)
        
        print(f"[WINDOW CALCULATION] ============================================")
        print(f"[WINDOW CALCULATION] Strategy: Next Best Slot (Global Quality Search)")
        print(f"[REAL-TIME SEARCH] Current time is {current_time}")
        print(f"[REAL-TIME SEARCH] Conflicted task was at: {conflict_info}")
        print(f"[REAL-TIME SEARCH] Scanning for best slots from TODAY onwards")
        print(f"[WINDOW CALCULATION] ✅ window_start: {window_start} (NOW)")
        print(f"[WINDOW CALCULATION] ✅ window_end: {window_end} (30 days from now)")
        print(f"[WINDOW CALCULATION] Will rank all candidates by Bayesian score (quality-first)")
        print(f"[WINDOW CALCULATION] ============================================\n")
    # Any other strategy leaves window_end as None for default horizon
    
    # CRITICAL PAGINATION CHECK: Validate that date lock is maintained on page 2+
    # NOTE: page and page_size are already extracted at the beginning of the function
    print(f"\n[PAGINATION CHECK] ============================================")
    print(f"[PAGINATION CHECK] Page: {page}")
    print(f"[PAGINATION CHECK] scheduledStart present: {data.get('scheduledStart') is not None}")
    print(f"[PAGINATION CHECK] scheduledStart value: {data.get('scheduledStart')}")
    print(f"[PAGINATION CHECK] Strategy: {strategy}")
    
    # SURGICAL FIX: Only warn about missing scheduledStart, don't fail hard
    # This allows conflict resolution to work while still detecting issues
    if page > 1 and strategy == "day" and not data.get("scheduledStart"):
        print(f"[PAGINATION CHECK] ⚠️  WARNING: Page {page} with 'day' strategy but NO scheduledStart!")
        print(f"[PAGINATION CHECK] ⚠️  This may cause date lock to be lost.")
        print(f"[PAGINATION CHECK] ⚠️  Allowing for now to prevent breaking conflict resolution flow.")
        print(f"[PAGINATION CHECK] ⚠️  Frontend should include scheduledStart in pagination requests.")
        # DO NOT return 400 - allow the request to proceed
    
    if page > 1:
        if data.get("scheduledStart"):
            print(f"[PAGINATION CHECK] ✅ Page {page} validation passed - Date lock maintained: {data.get('scheduledStart')}")
        else:
            print(f"[PAGINATION CHECK] ⚪ Page {page} proceeding without date lock (flexible date search)")
    
    print(f"[PAGINATION CHECK] ============================================\n")
    
    # CONSTRAINT SUMMARY: Show all active constraints for this request
    # CRITICAL: This must come AFTER page and page_size are extracted
    print(f"\n{'='*80}")
    print(f"CONSTRAINT SUMMARY - What Must Stay Locked")
    print(f"{'='*80}")
    print(f"📋 Request Type: {'PAGINATION (page > 1)' if page > 1 else 'INITIAL REQUEST (page 1)'}")
    print(f"📄 Page: {page} | Page Size: {page_size}")
    print(f"🎯 Strategy: {strategy}")
    print(f"")
    print(f"🔒 LOCKED CONSTRAINTS:")
    if target_task_date:
        locked_date = target_task_date.date()
        print(f"   ✅ LOCKED DATE: {locked_date}")
        print(f"      Source: scheduledStart/dueDate")
        print(f"      Impact: Window MUST stay within this specific date")
    else:
        print(f"   ⚪ No date locked (flexible date search)")
    
    if data.get("preferredTimeOfDay"):
        print(f"   ✅ LOCKED TIME: {data.get('preferredTimeOfDay')}")
        print(f"      Impact: Only suggest slots at this exact time")
    else:
        print(f"   ⚪ No time locked (flexible time search)")
    
    print(f"")
    print(f"📊 Task Details:")
    print(f"   - Duration: {duration} minutes")
    print(f"   - Task Type: {task_type}")
    print(f"")
    if page > 1 and target_task_date:
        print(f"⚠️  CRITICAL: This is page {page} with a locked date!")
        print(f"   The window MUST NOT cross into another day.")
        print(f"   If no more slots exist on {target_task_date.date()}, return empty list.")
    print(f"{'='*80}\n")
    
    # PAGINATION DEBUG: Show if date is locked
    if target_task_date and strategy == "day":
        locked_date = target_task_date.date()
        print(f"\n[PAGINATION DEBUG] ============================================")
        print(f"[PAGINATION DEBUG] Requesting Page {page} for Locked Date: {locked_date}")
        print(f"[PAGINATION DEBUG] Page Size: {page_size}")
        print(f"[PAGINATION DEBUG] Window: {window_start.date()} to {window_end.date()}")
        print(f"[PAGINATION DEBUG] Strategy: {strategy} (date-locked)")
        print(f"[PAGINATION DEBUG] ============================================\n")
    
    # Call suggestion service
    try:
        # FIX: If strategy is "day", treat as explicit user request to relax constraints
        # This allows suggestions even outside work hours or on days off
        explicit_date_requested = (strategy == "day")
        
        print(f"[DEBUG] Calling suggest_slots_for_user with:")
        print(f"  - user_id={g.user.id}")
        print(f"  - duration={duration}")
        print(f"  - task_type={task_type}")
        print(f"  - strategy={strategy}")
        print(f"  - page={page}")  # CRITICAL: Verify page parameter
        print(f"  - page_size={page_size}")
        print(f"  - window_start={window_start}")
        print(f"  - window_end={window_end}")
        print(f"  - explicit_date_requested={explicit_date_requested}")
        
        suggestions = suggest_slots_for_user(
            user_id=g.user.id,
            duration_minutes=duration,
            task_type=task_type,
            page=page,
            page_size=page_size,
            horizon_days=21,  # Default horizon for 'auto'
            step_minutes=15,  # FIX: Changed from 30 to 15 for finer granularity
            window_start=window_start,
            window_end=window_end,
            explicit_date_requested=explicit_date_requested,
        )
        
        print(f"[DEBUG] Suggestions found: {len(suggestions)}")
        
        # VALIDATION: If date-locked, verify all suggestions are on the locked date
        if target_task_date and strategy == "day" and len(suggestions) > 0:
            locked_date = target_task_date.date()
            print(f"\n[DATE LOCK VALIDATION] ============================================")
            print(f"[DATE LOCK VALIDATION] Verifying suggestions for locked date: {locked_date}")
            for i, sugg in enumerate(suggestions, 1):
                try:
                    sugg_start = datetime.fromisoformat(sugg["scheduledStart"])
                    sugg_date = sugg_start.date()
                    if sugg_date == locked_date:
                        print(f"[DATE LOCK VALIDATION]   ✅ Suggestion {i}: {sugg_start} (correct date)")
                    else:
                        print(f"[DATE LOCK VALIDATION]   ❌ Suggestion {i}: {sugg_start} (WRONG DATE! Expected {locked_date})")
                except:
                    print(f"[DATE LOCK VALIDATION]   ⚠️ Suggestion {i}: Failed to parse")
            print(f"[DATE LOCK VALIDATION] ============================================\n")
        
        print(f"[DEBUG] Suggestions: {suggestions}")
        
        # FINAL CONSTRAINT VERIFICATION SUMMARY
        print(f"\n{'='*80}")
        print(f"FINAL VERIFICATION - Constraints Maintained?")
        print(f"{'='*80}")
        print(f"📋 Returning {len(suggestions)} suggestions for page {page}")
        
        if len(suggestions) == 0:
            print(f"⚠️  EMPTY RESULT")
            if target_task_date:
                print(f"   Reason: No more slots available on locked date {target_task_date.date()}")
            else:
                print(f"   Reason: No slots found in search window")
        else:
            print(f"✅ Found {len(suggestions)} suggestions")
            
            if target_task_date:
                all_correct = all(
                    datetime.fromisoformat(s["scheduledStart"]).date() == target_task_date.date()
                    for s in suggestions
                )
                if all_correct:
                    print(f"   ✅ All suggestions on locked date: {target_task_date.date()}")
                else:
                    print(f"   ❌ CONSTRAINT VIOLATION: Some suggestions on wrong date!")
            
            print(f"")
            print(f"📅 Date Range:")
            if len(suggestions) > 0:
                dates = [datetime.fromisoformat(s["scheduledStart"]).date() for s in suggestions]
                unique_dates = sorted(set(dates))
                print(f"   {', '.join(str(d) for d in unique_dates)}")
                if len(unique_dates) > 1 and target_task_date:
                    print(f"   ⚠️  WARNING: Multiple dates found but date is locked to {target_task_date.date()}!")
        
        print(f"{'='*80}\n")
        
        return jsonify({
            "suggestions": suggestions,
            "strategy": strategy,
            "duration": duration,
            "task_type": task_type
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Suggestion failed: {e}")
        print(traceback.format_exc())
        return jsonify({
            "message": f"Failed to generate suggestions: {str(e)}"
        }), 500
