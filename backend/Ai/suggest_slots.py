from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional

from models import Task, UserPreferences, db
# NEW: Bayesian Network scoring (replaces old statistical bonus)
from Ai.network.bayesian import UserBayesianNetwork


# ---------- internal helpers ----------

def _overlaps(a_start: datetime, a_end: datetime,
              b_start: datetime, b_end: datetime) -> bool:
    """
    Check if two time intervals overlap.
    Returns True if they overlap, False if they don't.
    
    Logic: Two intervals DON'T overlap if:
    - a ends before or when b starts (a_end <= b_start)
    - OR b ends before or when a starts (b_end <= a_start)
    
    So they DO overlap if neither of those conditions is true.
    """
    no_overlap = (a_end <= b_start or b_end <= a_start)
    result = not no_overlap
    return result


def _within(t: time, start: Optional[time], end: Optional[time]) -> bool:
    if not start or not end:
        return True
    return start <= t <= end


def _is_day_off(dt: datetime, days_off: List[int]) -> bool:
    # Python weekday(): Mon=0..Sun=6 ; our convention: Sun=0..Sat=6
    py = dt.weekday()         # 0..6  (Mon..Sun)
    our = (py + 1) % 7        # 0..6  (Sun..Sat)
    return our in days_off


def _load_busy_intervals(user_id: int) -> List[tuple[datetime, datetime]]:
    """Collect existing scheduled intervals from tasks."""
    busy: List[tuple[datetime, datetime]] = []
    q = db.session.query(Task).filter(Task.user_id == user_id)
    task_count = 0
    for t in q:
        task_count += 1
        start: Optional[datetime] = getattr(t, "scheduled_start", None)
        end: Optional[datetime] = getattr(t, "scheduled_end", None)

        # Fallbacks: if only due_date exists (legacy)
        if not start and getattr(t, "due_date", None):
            dd = t.due_date
            if isinstance(dd, datetime):
                start = dd
                dur = getattr(t, "duration_minutes", None) or 60
                end = start + timedelta(minutes=int(dur))

        if start and end:
            busy.append((start, end))
            print(f"[BUSY INTERVALS] Task {task_count} (ID={t.id}): {start} to {end}")
        else:
            print(f"[BUSY INTERVALS] Task {task_count} (ID={t.id}): No schedule (skipped)")
    
    print(f"[BUSY INTERVALS] Total: {len(busy)} scheduled intervals found")
    return busy


def _slot_is_free(start: datetime, end: datetime,
                  busy: List[tuple[datetime, datetime]]) -> bool:
    for (b_start, b_end) in busy:
        overlaps = _overlaps(start, end, b_start, b_end)
        if overlaps:
            print(f"[OVERLAP CHECK] ❌ Overlap detected: [{start} to {end}] vs [{b_start} to {b_end}]")
            return False
    return True


def _score_slot(
    dt_start: datetime,
    dt_end: datetime,
    user_id: int,
    task_type: str,
    prefs: Optional[UserPreferences]
) -> float:
    """
    Score a time slot using Bayesian Network predictions.
    
    This replaces the old heuristic scoring with pure BN inference.
    The BN learns from stated preferences and observed task patterns.
    
    Args:
        dt_start: Slot start datetime
        dt_end: Slot end datetime
        user_id: User ID for BN lookup
        task_type: Type of task (Meeting/Training/Studies)
        prefs: UserPreferences (kept for compatibility, not used)
    
    Returns:
        Score in [0..10] where higher is better
    """
    try:
        # Load user's BN
        bn = UserBayesianNetwork(user_id)
        
        if not bn.is_trained():
            # Fallback: return neutral score if BN not trained
            return 5.0
        
        # Get BN prediction for this slot
        score = bn.predict_slot_score(task_type, dt_start, dt_end)
        
        return score
    
    except Exception as e:
        print(f"[BN Scoring] Error: {e}")
        # Fallback: neutral score
        return 5.0


# ---------- public API ----------

def suggest_slots_for_user(
    *,
    user_id: int,
    duration_minutes: int,
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 3,
    horizon_days: int = 21,
    step_minutes: int = 15,  # FIX: Changed default from 30 to 15 for finer granularity
    preferred_start: Optional[datetime] = None,  
    window_start: Optional[datetime] = None,     
    window_end: Optional[datetime] = None,       
    day_start: Optional[time] = None,            
    day_end: Optional[time] = None,
    explicit_date_requested: bool = False,
    preferred_time_of_day: Optional[Tuple[int, int]] = None,
    explicit_datetime_given: bool = False,
    fixed_time_search: bool = False,  # CASE 2: Only suggest slots at exact time
) -> List[Dict]:
    prefs: Optional[UserPreferences] = (
        db.session.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .first()
    )
    
    print(f"\n[WORK HOURS DEBUG] ============================================")
    print(f"[WORK HOURS DEBUG] Fetching preferences for user_id: {user_id}")
    if prefs:
        print(f"[WORK HOURS DEBUG] Found preferences (ID: {prefs.id}):")
        print(f"[WORK HOURS DEBUG]   - workday_pref_start: {prefs.workday_pref_start} (type: {type(prefs.workday_pref_start)})")
        print(f"[WORK HOURS DEBUG]   - workday_pref_end: {prefs.workday_pref_end} (type: {type(prefs.workday_pref_end)})")
        print(f"[WORK HOURS DEBUG]   - days_off: {prefs.days_off}")
        print(f"[WORK HOURS DEBUG]   - created_at: {prefs.created_at}")
        print(f"[WORK HOURS DEBUG]   - updated_at: {prefs.updated_at}")
        print(f"[WORK HOURS DEBUG] NOTE: These are the ACTUAL values from database, not defaults!")
    else:
        print(f"[WORK HOURS DEBUG] ❌ NO PREFERENCES FOUND FOR USER {user_id}!")
        print(f"[WORK HOURS DEBUG] This user needs to complete preferences setup!")
    print(f"[WORK HOURS DEBUG] ============================================\n")

    raw_days_off = (prefs.days_off if prefs else []) or []
    try:
        days_off: List[int] = [int(x) for x in raw_days_off]
    except Exception:
        days_off = []

    work_start: Optional[time] = prefs.workday_pref_start if prefs else None
    work_end: Optional[time] = prefs.workday_pref_end if prefs else None

    now = datetime.now()
    print(f"\n[SLOT SEARCH DEBUG] ============================================")
    print(f"[SLOT SEARCH DEBUG] Function called with:")
    print(f"[SLOT SEARCH DEBUG]   - duration_minutes: {duration_minutes}")
    print(f"[SLOT SEARCH DEBUG]   - page: {page}")
    print(f"[SLOT SEARCH DEBUG]   - page_size: {page_size}")
    print(f"[SLOT SEARCH DEBUG]   - window_start: {window_start}")
    print(f"[SLOT SEARCH DEBUG]   - window_end: {window_end}")
    print(f"[SLOT SEARCH DEBUG]   - work_start: {work_start}")
    print(f"[SLOT SEARCH DEBUG]   - work_end: {work_end}")
    print(f"[SLOT SEARCH DEBUG]   - explicit_date_requested: {explicit_date_requested}")
    print(f"[SLOT SEARCH DEBUG]   - ACTUAL current time (now): {now}")
    print(f"[SLOT SEARCH DEBUG] ============================================\n")

    # CASE 2.D: User provided explicit date+time but NO duration
    # Generate multiple duration suggestions at the EXACT same date+time
    if explicit_datetime_given and preferred_start:
        tt = task_type if task_type in ("Meeting", "Training", "Studies") else "Meeting"
        
        # Fixed date and time from user input
        fixed_datetime = preferred_start
        
        # If the datetime is in the past, skip
        if fixed_datetime < now + timedelta(minutes=30):
            return []
        
        # Check if this is a rest day
        is_rest_day = _is_day_off(fixed_datetime, days_off)
        # Skip rest days ONLY if user did NOT explicitly request this date
        # In CASE 2.D, user explicitly provides date+time, so explicit_date_requested should be True
        if is_rest_day and not explicit_date_requested:
            return []
        
        busy = _load_busy_intervals(user_id)
        
        # Generate duration candidates: 30, 45, 60, 90, 120 minutes
        duration_candidates = [30, 45, 60, 90, 120]
        
        candidates: List[Dict] = []
        
        for dur in duration_candidates:
            slot_start = fixed_datetime
            slot_end = slot_start + timedelta(minutes=dur)
            
            # Check if slot fits within work hours (if defined)
            if work_start and work_end:
                if not (_within(slot_start.time(), work_start, work_end) and 
                        _within(slot_end.time(), work_start, work_end)):
                    continue
            
            # Check if slot is free
            if _slot_is_free(slot_start, slot_end, busy):
                # Score with BN
                bn_score = _score_slot(
                    dt_start=slot_start,
                    dt_end=slot_end,
                    user_id=user_id,
                    task_type=tt,
                    prefs=prefs
                )
                
                final_score = max(0.0, min(10.0, float(bn_score)))
                
                # Check if slot exceeds work hours
                exceeds_work_hours = False
                if work_start and work_end:
                    if not (_within(slot_start.time(), work_start, work_end) and 
                            _within(slot_end.time(), work_start, work_end)):
                        exceeds_work_hours = True
                
                candidates.append({
                    "scheduledStart": slot_start.replace(
                        second=0, microsecond=0
                    ).isoformat(),
                    "scheduledEnd": slot_end.replace(
                        second=0, microsecond=0
                    ).isoformat(),
                    "score": int(round(final_score)),
                    "exceedsWorkHours": exceeds_work_hours,
                })
        
        # Sort by BN score (highest first)
        candidates.sort(key=lambda s: (-s["score"], s["scheduledEnd"]))
        
        # Return paginated results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return candidates[start_idx:end_idx]
    
    # CASE 2.G: User provided ONLY a time (no date, no duration)
    # Fixed TIME + Flexible DATE + Flexible DURATION
    # Examples: "schedule a task at 15:00", "add a meeting at 7 in the morning"
    if preferred_time_of_day and not window_start and not preferred_start:
        tt = task_type if task_type in ("Meeting", "Training", "Studies") else "Meeting"
        pref_hour, pref_minute = preferred_time_of_day
        
        # Use default horizon since no date constraint
        start_scan = now + timedelta(minutes=30)
        end_scan = now + timedelta(days=horizon_days)
        
        busy = _load_busy_intervals(user_id)
        
        # Duration candidates to try at the fixed time
        duration_candidates = [30, 45, 60, 90, 120]
        
        candidates: List[Dict] = []
        
        # Scan day-by-day through the horizon
        # CRITICAL: Use actual current time for filtering past slots
        actual_now = datetime.now()
        current_date = start_scan.date()
        end_date = end_scan.date()
        
        while current_date <= end_date:
            # Construct datetime at the fixed time on this date
            slot_time = datetime(
                current_date.year, current_date.month, current_date.day,
                pref_hour, pref_minute, 0
            )
            
            # CRITICAL FIX: Filter past times using ACTUAL current time
            # This prevents suggesting times that have already passed
            if slot_time < actual_now + timedelta(minutes=30):
                current_date += timedelta(days=1)
                continue
            
            # Skip rest days (no explicit date = filter rest days)
            if _is_day_off(slot_time, days_off) and not explicit_date_requested:
                current_date += timedelta(days=1)
                continue
            
            # Try each duration at this fixed time
            for dur in duration_candidates:
                slot_start = slot_time
                slot_end = slot_start + timedelta(minutes=dur)
                
                # Check if slot fits within work hours
                if work_start and work_end:
                    if not (_within(slot_start.time(), work_start, work_end) and 
                            _within(slot_end.time(), work_start, work_end)):
                        continue
                
                # Check if slot is free
                if _slot_is_free(slot_start, slot_end, busy):
                    # Score with BN
                    bn_score = _score_slot(
                        dt_start=slot_start,
                        dt_end=slot_end,
                        user_id=user_id,
                        task_type=tt,
                        prefs=prefs
                    )
                    
                    final_score = max(0.0, min(10.0, float(bn_score)))
                    
                    # Check if slot exceeds work hours
                    exceeds_work_hours = False
                    if work_start and work_end:
                        if not (_within(slot_start.time(), work_start, work_end) and 
                                _within(slot_end.time(), work_start, work_end)):
                            exceeds_work_hours = True
                    
                    candidates.append({
                        "scheduledStart": slot_start.replace(
                            second=0, microsecond=0
                        ).isoformat(),
                        "scheduledEnd": slot_end.replace(
                            second=0, microsecond=0
                        ).isoformat(),
                        "score": int(round(final_score)),
                        "exceedsWorkHours": exceeds_work_hours,
                    })
            
            # Move to next day
            current_date += timedelta(days=1)
        
        # Sort by BN score (highest first), then by start time
        candidates.sort(key=lambda s: (-s["score"], s["scheduledStart"]))
        
        # Return paginated results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        return candidates[start_idx:end_idx]

    # CASE 1: Specific date window provided by NLP (e.g., "next Tuesday", "November 25th 2025")
    # Use that window directly, don't clamp to default horizon
    if window_start and window_end:
        start_scan = window_start
        end_scan = window_end
        print(f"[SLOT SEARCH DEBUG] CASE 1: Using provided window")
        print(f"[SLOT SEARCH DEBUG]   - Initial start_scan: {start_scan}")
        print(f"[SLOT SEARCH DEBUG]   - Initial end_scan: {end_scan}")
        
        # CRITICAL FIX: Only apply "30 minutes in future" filter if start_scan is TODAY
        # For future dates, start from the beginning of that day
        if start_scan.date() == now.date():
            # Same day - ensure start is at least 30 minutes in the future
            if start_scan < now + timedelta(minutes=30):
                print(f"[SLOT SEARCH DEBUG]   - Adjusting start_scan for TODAY (from {start_scan} to {now + timedelta(minutes=30)})")
                start_scan = now + timedelta(minutes=30)
                # If the entire window is in the past, return empty
                if start_scan >= end_scan:
                    print(f"[SLOT SEARCH DEBUG]   - Entire window is in the past, returning empty")
                    return []
        else:
            print(f"[SLOT SEARCH DEBUG]   - Future date ({start_scan.date()}), keeping start_scan at beginning of day")
        
        print(f"[SLOT SEARCH DEBUG]   - Final start_scan: {start_scan}")
        print(f"[SLOT SEARCH DEBUG]   - Final end_scan: {end_scan}")
    
    # CASE 2: Preferred start time provided (date+time specified)
    elif preferred_start:
        anchor = preferred_start
        if anchor < now + timedelta(minutes=30):
            anchor = now + timedelta(minutes=30)
        start_scan = anchor - timedelta(hours=2)
        end_scan = anchor + timedelta(days=7)
        
        # Intersect with window if provided (should rarely happen in this case)
        if window_start and start_scan < window_start:
            start_scan = window_start
        if window_end and end_scan > window_end:
            end_scan = window_end
    
    # CASE 3: No date constraint at all - use default horizon from today
    else:
        start_scan = now + timedelta(minutes=30)
        end_scan = now + timedelta(days=horizon_days)
        
        # Intersect with window if provided
        if window_start and start_scan < window_start:
            start_scan = window_start
        if window_end and end_scan > window_end:
            end_scan = window_end

    if start_scan >= end_scan:
        return []

    busy = _load_busy_intervals(user_id)

    # FIX: Increase buffer to find more candidates with finer granularity
    BUFFER_FACTOR = 20  # Increased from 8 to allow ~60 candidates per page
    target_pool = max(page * page_size * BUFFER_FACTOR, 50)  # Minimum 50 candidates
    
    print(f"[CANDIDATE POOL DEBUG] target_pool set to: {target_pool}")

    candidates: List[Dict] = []
    tt = task_type if task_type in ("Meeting", "Training", "Studies") else "Meeting"

    # SPECIAL CASE: If preferred_time_of_day is provided with a window,
    # scan day-by-day and generate ONE slot per day at the preferred time
    # This handles cases like "sometime this week at 10am"
    if preferred_time_of_day and window_start and window_end:
        pref_hour, pref_minute = preferred_time_of_day
        current_date = start_scan.date()
        end_date = end_scan.date()
        
        # DEBUG: Counter to limit log spam
        debug_counter = 0
        max_debug_logs = 10
        print(f"[DEBUG SCAN] Starting preferred time scan: {pref_hour}:{pref_minute}, window: {start_scan} to {end_scan}")
        
        while current_date <= end_date and len(candidates) < target_pool:
            # CRITICAL FIX: If window is date-locked (same day), don't scan multiple days
            if window_start.date() == window_end.date():
                # Date-locked: only scan this one specific day
                if current_date != window_start.date():
                    print(f"[DATE LOCK] Stopped scanning at {current_date} (locked to {window_start.date()})")
                    break
            
            # Construct slot at preferred time on this date
            slot_start = datetime(
                current_date.year, current_date.month, current_date.day,
                pref_hour, pref_minute, 0
            )
            
            # DEBUG: Log first few attempts
            should_debug = debug_counter < max_debug_logs
            
            # Skip if slot is in the past
            if slot_start < now + timedelta(minutes=30):
                if should_debug:
                    print(f"[DEBUG SCAN {debug_counter}] {slot_start} - REJECTED: In the past (now+30min: {now + timedelta(minutes=30)})")
                    debug_counter += 1
                current_date += timedelta(days=1)
                continue
            
            # Skip rest days ONLY if user did NOT explicitly request a date
            # For CASE 2.C (vague ranges like "sometime this week"), explicit_date_requested=False
            # FIX: Skip this check entirely if explicit_date_requested is True (conflict resolution "Same Day")
            if not explicit_date_requested:
                if _is_day_off(slot_start, days_off):
                    if should_debug:
                        print(f"[DEBUG SCAN {debug_counter}] {slot_start} - REJECTED: Day off (days_off: {days_off})")
                        debug_counter += 1
                    current_date += timedelta(days=1)
                    continue
            elif should_debug:
                print(f"[DEBUG SCAN {debug_counter}] {slot_start} - Explicit date requested, skipping day_off check")
            
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            
            # Check if slot fits within work hours (if no day_start/day_end override)
            # FIX: Skip work hours check if explicit_date_requested is True
            if not explicit_date_requested and not (day_start and day_end) and work_start and work_end:
                within_work = _within(slot_start.time(), work_start, work_end) and _within(slot_end.time(), work_start, work_end)
                if not within_work:
                    if should_debug:
                        print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - REJECTED: Outside work hours ({work_start}-{work_end})")
                        debug_counter += 1
                    current_date += timedelta(days=1)
                    continue
            elif explicit_date_requested and should_debug:
                print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - Explicit date requested, skipping work hours check")
            
            # Check if slot is free
            is_free = _slot_is_free(slot_start, slot_end, busy)
            if should_debug:
                print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - Free? {is_free} (busy intervals: {len(busy)})")
                debug_counter += 1
            
            if is_free:
                bn_score = _score_slot(
                    dt_start=slot_start,
                    dt_end=slot_end,
                    user_id=user_id,
                    task_type=tt,
                    prefs=prefs
                )
                
                final_score = max(0.0, min(10.0, float(bn_score)))
                
                # Check if slot exceeds work hours
                exceeds_work_hours = False
                if work_start and work_end:
                    if not (_within(slot_start.time(), work_start, work_end) and 
                            _within(slot_end.time(), work_start, work_end)):
                        exceeds_work_hours = True
                
                candidates.append({
                    "scheduledStart": slot_start.replace(
                        second=0, microsecond=0
                    ).isoformat(),
                    "scheduledEnd": slot_end.replace(
                        second=0, microsecond=0
                    ).isoformat(),
                    "score": int(round(final_score)),
                    "exceedsWorkHours": exceeds_work_hours,
                })
            
            current_date += timedelta(days=1)
    
    # NORMAL CASE: No preferred time, scan with 30-minute steps
    # For "Duration Only" case (no date, no time), use day-distribution strategy
    # to ensure suggestions span multiple days rather than clustering on today
    else:
        # Detect "Duration Only" case: no window, no preferred_start, no preferred_time
        is_duration_only = not window_start and not preferred_start and not preferred_time_of_day
        
        if is_duration_only:
            # DAY-DISTRIBUTION STRATEGY for Duration Only
            # Scan day-by-day and collect best slots from each day
            # This ensures suggestions span the entire horizon rather than clustering on today
            current_date = start_scan.date()
            end_date = end_scan.date()
            
            # Collect multiple slots per day to ensure good coverage
            slots_per_day = 8  # Collect up to 8 good slots per day
            
            # DEBUG: Counter to limit log spam
            debug_counter = 0
            max_debug_logs = 10
            
            while current_date <= end_date and len(candidates) < target_pool:
                # CRITICAL FIX: If window is date-locked (same day), don't scan multiple days
                if window_start and window_end:
                    if window_start.date() == window_end.date():
                        # Date-locked: only scan this one specific day
                        if current_date != window_start.date():
                            print(f"[DATE LOCK] Stopped scanning at {current_date} (locked to {window_start.date()})")
                            break
                
                # Skip rest days UNLESS explicit date requested
                day_start_dt = datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0)
                # FIX: Skip day_off check if explicit_date_requested is True
                if not explicit_date_requested and _is_day_off(day_start_dt, days_off):
                    current_date += timedelta(days=1)
                    continue
                
                # Scan this day with 30-minute steps
                day_cursor = datetime(
                    current_date.year, current_date.month, current_date.day,
                    start_scan.hour if current_date == start_scan.date() else 0,
                    start_scan.minute if current_date == start_scan.date() else 0,
                    0
                )
                day_end_time = datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59)
                day_slots = []
                
                while day_cursor < day_end_time and len(day_slots) < slots_per_day:
                    # DEBUG: Log first few attempts
                    should_debug = debug_counter < max_debug_logs
                    
                    # Check work hours - FIX: Skip if explicit_date_requested
                    if not explicit_date_requested and work_start and work_end:
                        if not _within(day_cursor.time(), work_start, work_end):
                            if should_debug:
                                print(f"[DEBUG SCAN {debug_counter}] {day_cursor} - REJECTED: Outside work hours ({work_start}-{work_end})")
                                debug_counter += 1
                            day_cursor += timedelta(minutes=step_minutes)
                            continue
                    
                    # Enforce part-of-day window if defined - FIX: Skip if explicit_date_requested
                    if not explicit_date_requested and day_start and day_end:
                        if not _within(day_cursor.time(), day_start, day_end):
                            if should_debug:
                                print(f"[DEBUG SCAN {debug_counter}] {day_cursor} - REJECTED: Outside day window ({day_start}-{day_end})")
                                debug_counter += 1
                            day_cursor += timedelta(minutes=step_minutes)
                            continue
                    
                    slot_start = day_cursor
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Check if slot end is still within bounds - FIX: Skip if explicit_date_requested
                    if not explicit_date_requested and work_start and work_end:
                        if not _within(slot_end.time(), work_start, work_end):
                            if should_debug:
                                print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - REJECTED: End time outside work hours")
                                debug_counter += 1
                            day_cursor += timedelta(minutes=step_minutes)
                            continue
                    
                    if not explicit_date_requested and day_start and day_end:
                        if not _within(slot_end.time(), day_start, day_end):
                            if should_debug:
                                print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - REJECTED: End time outside day window")
                                debug_counter += 1
                            day_cursor += timedelta(minutes=step_minutes)
                            continue
                    
                    # Check if slot is free
                    is_free = _slot_is_free(slot_start, slot_end, busy)
                    if should_debug:
                        print(f"[DEBUG SCAN {debug_counter}] {slot_start}-{slot_end} - Free? {is_free}, Work: {work_start}-{work_end}")
                        debug_counter += 1
                    
                    if is_free:
                        bn_score = _score_slot(
                            dt_start=slot_start,
                            dt_end=slot_end,
                            user_id=user_id,
                            task_type=tt,
                            prefs=prefs
                        )
                        
                        final_score = max(0.0, min(10.0, float(bn_score)))
                        
                        # Check if slot exceeds work hours
                        exceeds_work_hours = False
                        if work_start and work_end:
                            if not (_within(slot_start.time(), work_start, work_end) and 
                                    _within(slot_end.time(), work_start, work_end)):
                                exceeds_work_hours = True
                        
                        day_slots.append({
                            "scheduledStart": slot_start.replace(second=0, microsecond=0).isoformat(),
                            "scheduledEnd": slot_end.replace(second=0, microsecond=0).isoformat(),
                            "score": int(round(final_score)),
                            "exceedsWorkHours": exceeds_work_hours,
                        })
                    
                    day_cursor += timedelta(minutes=step_minutes)
                
                # Add all slots from this day to candidates
                candidates.extend(day_slots)
                
                # Move to next day
                current_date += timedelta(days=1)
        
        else:
            # PRECISION SCANNING: Start at exact workday_pref_start, then 15-min intervals
            # Example: workday_pref_start = 08:25
            # Scan order: 08:25 (exact), 08:30 (next 15-min), 08:45, 09:00, etc.
            
            # CRITICAL: Initialize step variable for 15-minute intervals
            step = timedelta(minutes=15)
            
            cursor = start_scan
            
            # If we have workday_pref_start and start_scan is aligned to it, start there
            # Otherwise start from start_scan
            if work_start and not (day_start and day_end):
                # Check if start_scan time matches workday_pref_start
                # If so, great! If not, we still start from start_scan
                cursor_time = cursor.time()
                if cursor_time == work_start:
                    print(f"[PRECISION SCAN] Starting at exact workday_pref_start: {cursor}")
                elif cursor_time < work_start:
                    # Advance to workday_pref_start on same day
                    cursor = cursor.replace(hour=work_start.hour, minute=work_start.minute, second=0, microsecond=0)
                    print(f"[PRECISION SCAN] Advanced to workday_pref_start: {cursor}")
                else:
                    print(f"[PRECISION SCAN] Starting from: {cursor}")
            
            print(f"[SLOT SEARCH DEBUG] Starting precision scanning:")
            print(f"[SLOT SEARCH DEBUG]   - start_scan: {start_scan}")
            print(f"[SLOT SEARCH DEBUG]   - cursor (precision start): {cursor}")
            print(f"[SLOT SEARCH DEBUG]   - end_scan: {end_scan}")
            print(f"[SLOT SEARCH DEBUG]   - work_start: {work_start}")
            print(f"[SLOT SEARCH DEBUG]   - target_pool: {target_pool}")
            print(f"[SLOT SEARCH DEBUG]   - step: 15 minutes")
            
            # Track whether we've scanned the exact workday_pref_start
            scanned_workday_start = False
            
            scan_count = 0
            max_debug_scans = 20

            while cursor < end_scan and len(candidates) < target_pool:
                scan_count += 1
                should_log = scan_count <= max_debug_scans
                
                # CRITICAL FIX: If window is date-locked (start and end on same day), 
                # ensure cursor stays within that day
                if window_start and window_end:
                    if window_start.date() == window_end.date():
                        # Date-locked window: Don't scan beyond the locked date
                        if cursor.date() != window_start.date():
                            if should_log:
                                print(f"[DATE LOCK] Scan {scan_count}: {cursor} - STOPPED (crossed date boundary from {window_start.date()})")
                            break  # Stop scanning completely
                
                # Skip rest days ONLY if user did NOT explicitly request a specific date
                if _is_day_off(cursor, days_off) and not explicit_date_requested:
                    if should_log:
                        print(f"[SLOT SEARCH DEBUG] Scan {scan_count}: {cursor} - SKIPPED (day off)")
                    cursor += step
                    continue

                if not (day_start and day_end) and work_start and work_end:
                    if not _within(cursor.time(), work_start, work_end):
                        if should_log:
                            print(f"[SLOT SEARCH DEBUG] Scan {scan_count}: {cursor} - SKIPPED (outside work hours {work_start}-{work_end})")
                        cursor += step
                        continue

                # Enforce part-of-day window if defined
                if day_start and day_end:
                    if not _within(cursor.time(), day_start, day_end):
                        cursor += step
                        continue

                slot_start = cursor
                slot_end = slot_start + timedelta(minutes=duration_minutes)

            
                if not (day_start and day_end) and work_start and work_end:
                    if not _within(slot_end.time(), work_start, work_end):
                        if should_log:
                            print(f"[SLOT SEARCH DEBUG] Scan {scan_count}: {slot_start}-{slot_end} - REJECTED (end time outside work hours)")
                        cursor += step
                        continue

            
                if day_start and day_end and not _within(slot_end.time(), day_start, day_end):
                    if should_log:
                        print(f"[SLOT SEARCH DEBUG] Scan {scan_count}: {slot_start}-{slot_end} - REJECTED (end time outside day window)")
                    cursor += step
                    continue

                is_free = _slot_is_free(slot_start, slot_end, busy)
                if should_log:
                    print(f"[SLOT SEARCH DEBUG] Scan {scan_count}: {slot_start}-{slot_end} - Free: {is_free}")
                
                if is_free:
                    # CASE 2: Fixed-Time Search - Only accept slots at exact requested time
                    if fixed_time_search and preferred_time_of_day:
                        required_hour, required_minute = preferred_time_of_day
                        if slot_start.hour != required_hour or slot_start.minute != required_minute:
                            if should_log:
                                print(f"[FIXED-TIME FILTER] Scan {scan_count}: {slot_start} - REJECTED (time {slot_start.hour:02d}:{slot_start.minute:02d} != required {required_hour:02d}:{required_minute:02d})")
                            cursor += step
                            continue
                        else:
                            if should_log:
                                print(f"[FIXED-TIME FILTER] Scan {scan_count}: {slot_start} - ACCEPTED (exact time match: {required_hour:02d}:{required_minute:02d})")
                    
                    bn_score = _score_slot(
                        dt_start=slot_start,
                        dt_end=slot_end,
                        user_id=user_id,
                        task_type=tt,
                        prefs=prefs
                    )
                    
                    final_score = max(0.0, min(10.0, float(bn_score)))

                    # Check if slot exceeds work hours
                    exceeds_work_hours = False
                    if work_start and work_end:
                        if not (_within(slot_start.time(), work_start, work_end) and 
                                _within(slot_end.time(), work_start, work_end)):
                            exceeds_work_hours = True

                    candidates.append(
                        {
                            "scheduledStart": slot_start.replace(
                                second=0, microsecond=0
                            ).isoformat(),
                            "scheduledEnd": slot_end.replace(
                                second=0, microsecond=0
                            ).isoformat(),
                            "score": int(round(final_score)),
                            "exceedsWorkHours": exceeds_work_hours,
                        }
                    )

                # PRECISION INCREMENT: After scanning workday_pref_start (e.g., 08:25),
                # jump to next 15-min mark (e.g., 08:30), then continue with 15-min intervals
                if not scanned_workday_start and work_start and cursor.time() == work_start:
                    scanned_workday_start = True
                    # Find next 15-minute mark
                    minutes = cursor.minute
                    remainder = minutes % 15
                    if remainder != 0:
                        # Round up to next 15-min mark
                        cursor = cursor.replace(minute=minutes - remainder, second=0, microsecond=0)
                        cursor += timedelta(minutes=15)
                    else:
                        # Already on 15-min mark, just advance by 15
                        cursor += timedelta(minutes=15)
                    if should_log:
                        print(f"[PRECISION SCAN] After workday_pref_start, jumped to next 15-min mark: {cursor}")
                else:
                    # Normal 15-minute increment
                    cursor += timedelta(minutes=15)
            
            # Log first 5 candidates generated (before scoring/sorting)
            print(f"\n[CANDIDATE DEBUG] ============================================")
            print(f"[CANDIDATE DEBUG] First 5 candidates generated (raw, before sorting):")
            for i, c in enumerate(candidates[:5]):
                print(f"[CANDIDATE DEBUG]   #{i+1}: {c['scheduledStart']} (score: {c['score']})")
            print(f"[CANDIDATE DEBUG] ============================================\n")

    # EMERGENCY: If we got 0 candidates with 15-min scan, fall back to 30-min scan
    if len(candidates) == 0 and step_minutes == 15:
        print(f"\n[FALLBACK WARNING] ============================================")
        print(f"[FALLBACK WARNING] 15-minute scan returned 0 candidates!")
        print(f"[FALLBACK WARNING] Attempting fallback to 30-minute scan...")
        print(f"[FALLBACK WARNING] ============================================\n")
        
        # Retry with 30-minute step
        cursor = start_scan
        step = timedelta(minutes=30)
        scan_count = 0
        
        while cursor < end_scan and len(candidates) < target_pool:
            scan_count += 1
            should_log = scan_count <= 5
            
            # CRITICAL FIX: If window is date-locked, ensure cursor stays within that day
            if window_start and window_end:
                if window_start.date() == window_end.date():
                    if cursor.date() != window_start.date():
                        if should_log:
                            print(f"[FALLBACK DATE LOCK] Stopped at {cursor} (locked to {window_start.date()})")
                        break
            
            if _is_day_off(cursor, days_off) and not explicit_date_requested:
                cursor += step
                continue
            
            if not (day_start and day_end) and work_start and work_end:
                if not _within(cursor.time(), work_start, work_end):
                    if should_log:
                        print(f"[FALLBACK] Scan {scan_count}: {cursor} - SKIPPED (outside work hours)")
                    cursor += step
                    continue
            
            slot_start = cursor
            slot_end = slot_start + timedelta(minutes=duration_minutes)
            
            if not (day_start and day_end) and work_start and work_end:
                if not _within(slot_end.time(), work_start, work_end):
                    cursor += step
                    continue
            
            is_free = _slot_is_free(slot_start, slot_end, busy)
            
            if is_free:
                if should_log:
                    print(f"[FALLBACK] Scan {scan_count}: {slot_start} - FREE")
                
                bn_score = _score_slot(
                    dt_start=slot_start,
                    dt_end=slot_end,
                    user_id=user_id,
                    task_type=tt,
                    prefs=prefs
                )
                final_score = max(0.0, min(10.0, float(bn_score)))
                
                exceeds_work_hours = False
                if work_start and work_end:
                    if not (_within(slot_start.time(), work_start, work_end) and 
                            _within(slot_end.time(), work_start, work_end)):
                        exceeds_work_hours = True
                
                candidates.append({
                    "scheduledStart": slot_start.replace(second=0, microsecond=0).isoformat(),
                    "scheduledEnd": slot_end.replace(second=0, microsecond=0).isoformat(),
                    "score": int(round(final_score)),
                    "exceedsWorkHours": exceeds_work_hours,
                })
            
            cursor += step
        
        print(f"[FALLBACK] Found {len(candidates)} candidates with 30-minute scan\n")

    # CRITICAL: Sort by SCORE (descending), then by time
    # This ensures the BEST suggestions appear first, regardless of time
    # Workday start (e.g., 08:25) will find its natural position based on Bayesian score
    
    # Global Search Debug Logging
    if len(candidates) > 0:
        top_score = max(c["score"] for c in candidates)
        top_slot = next(c for c in candidates if c["score"] == top_score)
        avg_score = sum(c["score"] for c in candidates) / len(candidates)
        
        print(f"\n[GLOBAL SEARCH] ============================================")
        print(f"[GLOBAL SEARCH] Scanned {len(candidates)} total slots across entire window")
        print(f"[REAL-TIME SEARCH] Found top slot at {top_slot['scheduledStart']} with score {top_score:.2f}")
        print(f"[GLOBAL SEARCH] Average score: {avg_score:.2f}")
        print(f"[GLOBAL SEARCH] Score range: [{min(c['score'] for c in candidates):.2f} - {max(c['score'] for c in candidates):.2f}]")
        print(f"[GLOBAL SEARCH] Now sorting by quality (score descending)...")
        print(f"[GLOBAL SEARCH] ============================================\n")
    
    print(f"\n[SORTING DEBUG] ============================================")
    print(f"[SORTING DEBUG] Sorting {len(candidates)} candidates by score (descending)...")
    candidates.sort(key=lambda s: (-s["score"], s["scheduledStart"]))
    
    if len(candidates) > 0:
        print(f"[SORTING DEBUG] Top 5 candidates after sort:")
        for i, c in enumerate(candidates[:5]):
            print(f"[SORTING DEBUG]   #{i+1}: {c['scheduledStart']} (score: {c['score']})")
    print(f"[SORTING DEBUG] ============================================\n")

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    print(f"\n[PAGINATION DEBUG] ============================================")
    print(f"[PAGINATION DEBUG] Slicing candidates from {start_idx} to {end_idx} for page {page}")
    print(f"[PAGINATION DEBUG] page={page}, page_size={page_size}")
    print(f"[PAGINATION DEBUG] Total candidates before slicing: {len(candidates)}")
    print(f"[PAGINATION DEBUG] ============================================\n")
    
    result = candidates[start_idx:end_idx]
    
    print(f"\n[SLOT SEARCH DEBUG] ============================================")
    print(f"[SLOT SEARCH DEBUG] SEARCH COMPLETE")
    print(f"[SLOT SEARCH DEBUG]   - Total raw candidates found: {len(candidates)}")
    print(f"[SLOT SEARCH DEBUG]   - Requested page: {page} (size: {page_size})")
    print(f"[SLOT SEARCH DEBUG]   - Pagination slice: [{start_idx}:{end_idx}]")
    print(f"[SLOT SEARCH DEBUG]   - Returning {len(result)} suggestions")
    if len(candidates) > 0:
        print(f"[SLOT SEARCH DEBUG]   - Top candidate (before pagination): {candidates[0]['scheduledStart']} (score: {candidates[0]['score']})")
    if len(result) > 0:
        print(f"[SLOT SEARCH DEBUG]   - First suggestion on this page: {result[0]['scheduledStart']} (score: {result[0]['score']})")
        print(f"[SLOT SEARCH DEBUG]   - Last suggestion on this page: {result[-1]['scheduledStart']} (score: {result[-1]['score']})")
    else:
        print(f"[SLOT SEARCH DEBUG]   - NO SUGGESTIONS ON THIS PAGE (check if page > total pages)")
    print(f"[SLOT SEARCH DEBUG] ============================================\n")
    
    return result
