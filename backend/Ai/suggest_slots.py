# backend/Ai/suggest_slots.py
from __future__ import annotations
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from flask import g

from models import Task, UserPreferences, db

# Internal helpers
def _overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return not (a_end <= b_start or b_end <= a_start)

def _within(t: time, start: Optional[time], end: Optional[time]) -> bool:
    if not start or not end:
        return True
    return start <= t <= end

def _is_day_off(dt: datetime, days_off: List[int]) -> bool:
    py = dt.weekday()         # 0..6  (Mon..Sun)
    our = (py + 1) % 7        # 0..6  (Sun..Sat)
    return our in days_off

def _load_busy_intervals(user_id: int) -> List[tuple[datetime, datetime]]:
    """Collect existing scheduled intervals from tasks."""
    busy: List[tuple[datetime, datetime]] = []
    q = db.session.query(Task).filter(Task.user_id == user_id)
    for t in q:
        start: Optional[datetime] = getattr(t, "scheduled_start", None)
        end: Optional[datetime] = getattr(t, "scheduled_end", None)

        # Fallbacks: if only due_date exists (legacy)
        if not start and getattr(t, "due_date", None):
            dd = t.due_date
            if isinstance(dd, datetime):
                start = dd
                # use duration if exists, else 1h
                dur = getattr(t, "duration_minutes", None) or 60
                end = start + timedelta(minutes=int(dur))

        if start and end:
            busy.append((start, end))
    return busy

def _slot_is_free(start: datetime, end: datetime, busy: List[tuple[datetime, datetime]]) -> bool:
    for (b_start, b_end) in busy:
        if _overlaps(start, end, b_start, b_end):
            return False
    return True

def _score_slot(dt_start: datetime,
                dt_end: datetime,
                prefs: UserPreferences | None) -> int:
    """Score slot 0..10. Higher is better."""
    score = 5

    if prefs:
        # Prefer focus peak window
        fs, fe = prefs.focus_peak_start, prefs.focus_peak_end
        if fs and fe and _within(dt_start.time(), fs, fe):
            score += 2

        # Respect workday window
        ws, we = prefs.workday_pref_start, prefs.workday_pref_end
        if ws and we and _within(dt_start.time(), ws, we):
            score += 2

        # Flexibility nudges
        if prefs.flexibility == "LOW":
            # penalize off-hours
            if not (ws and we and _within(dt_start.time(), ws, we)):
                score -= 1
        elif prefs.flexibility == "HIGH":
            score += 1

    # Prefer near future (but not too soon)
    mins_ahead = (dt_start - datetime.now()).total_seconds() / 60.0
    if 60 <= mins_ahead <= 7*24*60:
        score += 1

    return max(0, min(10, score))


def suggest_slots_for_user(
    *,
    user_id: int,
    duration_minutes: int,
    page: int = 1,
    page_size: int = 3,
    horizon_days: int = 21,
    step_minutes: int = 30,
) -> List[Dict]:
    # Load preferences (if any)
    prefs: Optional[UserPreferences] = (
        db.session.query(UserPreferences)
        .filter(UserPreferences.user_id == user_id)
        .first()
    )

    raw_days_off = (prefs.days_off if prefs else []) or []
    try:
        days_off: List[int] = [int(x) for x in raw_days_off]
    except Exception:
        days_off = []

    work_start: Optional[time] = prefs.workday_pref_start if prefs else None
    work_end: Optional[time]   = prefs.workday_pref_end   if prefs else None

    now = datetime.now()
    start_scan = now + timedelta(minutes=30)  
    end_scan   = now + timedelta(days=horizon_days)

    busy = _load_busy_intervals(user_id)

  
    BUFFER_FACTOR = 8  
    target_pool   = max(page * page_size * BUFFER_FACTOR, page_size * 8)

    candidates: List[Dict] = []
    cursor = start_scan
    step = timedelta(minutes=step_minutes)

    while cursor < end_scan and len(candidates) < target_pool:

        if _is_day_off(cursor, days_off):
            cursor += step
            continue

     
        if work_start and work_end:
            if not _within(cursor.time(), work_start, work_end):
                cursor += step
                continue

        slot_start = cursor
        slot_end = slot_start + timedelta(minutes=duration_minutes)

        if work_start and work_end and not _within(slot_end.time(), work_start, work_end):
            cursor += step
            continue

        if _slot_is_free(slot_start, slot_end, busy):
            score = _score_slot(slot_start, slot_end, prefs)
            candidates.append(
                {
                    "scheduledStart": slot_start.replace(second=0, microsecond=0).isoformat(),
                    "scheduledEnd":   slot_end.replace(second=0, microsecond=0).isoformat(),
                    "score": int(score),
                }
            )

        cursor += step


    candidates.sort(key=lambda s: (-s["score"], s["scheduledStart"]))

   
    start_idx = (page - 1) * page_size
    end_idx   = start_idx + page_size
    return candidates[start_idx:end_idx]

