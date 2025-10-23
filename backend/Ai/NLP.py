import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List

WEEKDAYS = {
    "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
    "friday": 4, "saturday": 5, "sunday": 6,
}
MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

def _parse_time_str(text: str) -> Optional[Tuple[int, int]]:
    m = re.search(r'\b(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\b', text.lower())
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2)) if m.group(2) else 0
    ampm = (m.group(3) or "").lower()
    if ampm == "pm" and hour < 12:
        hour += 12
    if ampm == "am" and hour == 12:
        hour = 0
    if 0 <= hour <= 23 and 0 <= minute <= 59:
        return hour, minute
    return None

def _next_weekday(base: datetime, target_wd: int) -> datetime:
    days_ahead = (target_wd - base.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (base + timedelta(days=days_ahead)).replace(hour=0, minute=0, second=0, microsecond=0)

def _upcoming_weekday(base: datetime, target_wd: int) -> datetime:
    return _next_weekday(base, target_wd)

def _parse_priority(text: str) -> str:
    t = text.lower()
    if re.search(r'\b(high|urgent|critical)\b(?:\s*priority)?', t):
        return "HIGH"
    if re.search(r'\blow\b(?:\s*priority)?', t):
        return "LOW"
    if re.search(r'\bmedium\b(?:\s*priority)?', t):
        return "MEDIUM"
    return "MEDIUM"

def _parse_task_type(text: str) -> str:
    t = text.lower()
    if re.search(r'\b(meeting|meet|call|appointment)\b', t):
        return "Meeting"
    if re.search(r'\b(train|training|workout|exercise|session)\b', t):
        return "Training"
    if re.search(r'\b(study|studies|homework|reading|research)\b', t):
        return "Studies"
    return "Meeting"

def _parse_duration_minutes(text: str) -> Optional[int]:
    t = text.lower()
    m = re.search(r'\bfor\s+(\d{1,3})\s*(minutes?|mins?|m)\b', t)
    if m:
        return int(m.group(1))
    m = re.search(r'\bfor\s+(\d{1,2})\s*(hours?|hrs?|h)\b', t)
    if m:
        return int(m.group(1)) * 60
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
    m = re.search(r'\bfor\s+(one|two|three|four|five|six|seven|eight)\s+hours?\b', t)
    if m:
        return words[m.group(1)] * 60
    return None

def _parse_absolute_month_day(text: str, now: datetime, hm: Tuple[int, int]) -> Optional[datetime]:
    t = text.lower()
    m = re.search(r'\bon\s+(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
                  r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+(\d{1,2})\b', t)
    if not m: return None
    month = MONTHS[m.group(1)]
    day = int(m.group(2))
    cand = datetime(now.year, month, day, hm[0], hm[1], 0)
    if cand <= now:
        cand = datetime(now.year + 1, month, day, hm[0], hm[1], 0)
    return cand

def _parse_relative_datetime(text: str, now: Optional[datetime] = None) -> Optional[datetime]:
    if now is None:
        now = datetime.now()
    t = text.lower()
    hm = _parse_time_str(t)
    if not hm:
        return None
    if re.search(r'\btomorrow\b', t):
        return (now + timedelta(days=1)).replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
    m = re.search(r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t)
    if m:
        wd = WEEKDAYS[m.group(1)]
        base = _next_weekday(now, wd)
        return base.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
    m = re.search(r'\bnext\s+week\b.*?\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t)
    if m:
        next_monday = _next_weekday(now, WEEKDAYS["monday"])
        target_wd = WEEKDAYS[m.group(1)]
        delta = (target_wd - WEEKDAYS["monday"]) % 7
        base = (next_monday + timedelta(days=delta)).replace(hour=0, minute=0, second=0, microsecond=0)
        return base.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
    m = re.search(r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t)
    if m:
        wd = WEEKDAYS[m.group(1)]
        base = _upcoming_weekday(now, wd)
        return base.replace(hour=hm[0], minute=hm[1], second=0, microsecond=0)
    abs_dt = _parse_absolute_month_day(t, now, hm)
    if abs_dt: return abs_dt
    return None

def parse_free_text(text: str) -> Dict[str, Any]:
    raw = text
    title = text.strip()
    task_type = _parse_task_type(text)
    priority = _parse_priority(text)
    duration = _parse_duration_minutes(text)
    dt = _parse_relative_datetime(text)

    debug = {
        "raw": raw,
        "matchedDateTime": dt.isoformat(timespec="seconds") if isinstance(dt, datetime) else None,
        "matchedDuration": duration,
        "matchedTaskType": task_type,
    }

    parsed = {
        "title": title.lower(),
        "task_type": task_type,
        "dueDateTime": dt.isoformat(timespec="seconds") if isinstance(dt, datetime) else None,
        "durationMinutes": duration,
        "priority": priority,
    }

    full = bool(parsed["dueDateTime"]) and bool(parsed["durationMinutes"])
    return {
        "status": "complete" if full else "partial",
        "parsed": parsed,
        "missing": [k for k in ("dueDateTime", "durationMinutes") if not parsed.get(k)],
        "debug": debug,
    }

def handle_free_text_input(text: str) -> Dict[str, Any]:
    return parse_free_text(text)
