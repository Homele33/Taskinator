import re
from datetime import datetime, timedelta, time
from typing import Optional, Tuple, Dict, Any

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

TEXT_NUMBERS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


# --------- basic helpers ---------


def _parse_time_str(text: str) -> Optional[Tuple[int, int]]:
    t = text.lower()
    
    # Try "X in the afternoon/evening/morning" patterns first
    # "3 in the afternoon" -> 15:00, "7 in the evening" -> 19:00, "9 in the morning" -> 09:00
    m = re.search(r'\b(\d{1,2})(?::(\d{2}))?\s+in\s+the\s+(afternoon|evening|morning)\b', t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        period = m.group(3)
        
        if period == "afternoon":
            # Afternoon: 12pm-5pm. If hour < 12, add 12
            if hour < 12:
                hour += 12
        elif period == "evening":
            # Evening: 5pm-9pm. If hour < 12, add 12
            if hour < 12:
                hour += 12
        elif period == "morning":
            # Morning: 6am-12pm. Keep as is, unless it's 12 (12am = 0)
            if hour == 12:
                hour = 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (afternoon/evening/morning pattern)")
            return hour, minute
    
    # PRIORITY 1: "at H:MM am/pm" or "at HH:MM am/pm" (explicit "at" with colon AND am/pm)
    m = re.search(r'\bat\s+(\d{1,2}):(\d{2})\s*(am|pm)\b', t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = m.group(3).lower()
        
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "pm" and hour == 12:
            pass  # 12 PM stays as 12
        elif ampm == "am" and hour == 12:
            hour = 0  # 12 AM becomes 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (at HH:MM am/pm pattern)")
            return hour, minute
    
    # PRIORITY 2: "H:MM am/pm" or "HH:MM am/pm" (standalone time with colon AND am/pm)
    m = re.search(r'\b(\d{1,2}):(\d{2})\s*(am|pm)\b', t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        ampm = m.group(3).lower()
        
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "pm" and hour == 12:
            pass  # 12 PM stays as 12
        elif ampm == "am" and hour == 12:
            hour = 0  # 12 AM becomes 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (HH:MM am/pm pattern)")
            return hour, minute
    
    # PRIORITY 3: "at H am/pm" or "at HH am/pm" (explicit "at" with am/pm, no colon)
    m = re.search(r'\bat\s+(\d{1,2})\s*(am|pm)\b', t)
    if m:
        hour = int(m.group(1))
        minute = 0
        ampm = m.group(2).lower()
        
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "pm" and hour == 12:
            pass  # 12 PM stays as 12
        elif ampm == "am" and hour == 12:
            hour = 0  # 12 AM becomes 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (at H am/pm pattern)")
            return hour, minute
    
    # PRIORITY 4: "H am/pm" or "HH am/pm" (standalone with am/pm, no colon)
    m = re.search(r'\b(\d{1,2})\s*(am|pm)\b', t)
    if m:
        hour = int(m.group(1))
        minute = 0
        ampm = m.group(2).lower()
        
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "pm" and hour == 12:
            pass  # 12 PM stays as 12
        elif ampm == "am" and hour == 12:
            hour = 0  # 12 AM becomes 0
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (H am/pm pattern)")
            return hour, minute
    
    # PRIORITY 5: "at HH:MM" or "at H:MM" (explicit "at" with colon, NO am/pm)
    # Only match if there's NO am/pm after it
    m = re.search(r'\bat\s+(\d{1,2}):(\d{2})(?!\s*(?:am|pm))\b', t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (at HH:MM 24h pattern)")
            return hour, minute
    
    # PRIORITY 6: Standalone time with colon "HH:MM" (without "at" and without am/pm)
    # This avoids matching dates like "12/10" or day numbers like "5"
    m = re.search(r'\b(\d{1,2}):(\d{2})(?!\s*(?:am|pm))\b', t)
    if m:
        hour = int(m.group(1))
        minute = int(m.group(2))
        
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            print(f"DEBUG NLP: Time string '{text}' parsed as {hour:02d}:{minute:02d} (HH:MM 24h pattern)")
            return hour, minute
    
    return None


def _parse_time_range(text: str) -> Optional[Tuple[Tuple[int, int], int]]:
    """
    Parse time range patterns like "9:00 - 11:00" or "9:00 to 11:00".
    Returns ((start_hour, start_minute), duration_minutes) if a range is found.
    Returns None if no time range is detected.
    
    Supported patterns:
    - "HH:MM - HH:MM" (e.g., "9:00 - 11:00", "14:00-15:30")
    - "HH:MM to HH:MM" (e.g., "9:00 to 11:00")
    - "HH:MM until HH:MM" (e.g., "9:00 until 11:00")
    - With AM/PM: "9:00 am - 11:00 am", "2:00 pm to 3:30 pm"
    """
    t = text.lower()
    
    # Pattern 1: HH:MM (am/pm) - HH:MM (am/pm)
    # Matches: "9:00 - 11:00", "9:00 am - 11:00 am", "14:00-15:30"
    m = re.search(
        r'\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\s*[-–—]\s*(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b',
        t
    )
    if m:
        start_hour = int(m.group(1))
        start_minute = int(m.group(2))
        start_ampm = (m.group(3) or "").lower()
        end_hour = int(m.group(4))
        end_minute = int(m.group(5))
        end_ampm = (m.group(6) or "").lower()
        
        # Apply AM/PM conversion for start time
        if start_ampm == "pm" and start_hour < 12:
            start_hour += 12
        elif start_ampm == "am" and start_hour == 12:
            start_hour = 0
        
        # Apply AM/PM conversion for end time
        if end_ampm == "pm" and end_hour < 12:
            end_hour += 12
        elif end_ampm == "am" and end_hour == 12:
            end_hour = 0
        
        # Validate hours and minutes
        if 0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_hour <= 23 and 0 <= end_minute <= 59:
            # Calculate duration in minutes
            start_total_minutes = start_hour * 60 + start_minute
            end_total_minutes = end_hour * 60 + end_minute
            
            # Handle case where end time is earlier than start time (next day)
            if end_total_minutes <= start_total_minutes:
                # Assume end time is next day
                end_total_minutes += 24 * 60
            
            duration = end_total_minutes - start_total_minutes
            
            # Sanity check: duration should be reasonable (1 min to 24 hours)
            if 1 <= duration <= 1440:
                return ((start_hour, start_minute), duration)
    
    # Pattern 2: HH:MM (am/pm) to/until HH:MM (am/pm)
    # Matches: "9:00 to 11:00", "9:00 am until 11:00 am"
    m = re.search(
        r'\b(\d{1,2}):(\d{2})(?:\s*(am|pm))?\s+(?:to|until)\s+(\d{1,2}):(\d{2})(?:\s*(am|pm))?\b',
        t
    )
    if m:
        start_hour = int(m.group(1))
        start_minute = int(m.group(2))
        start_ampm = (m.group(3) or "").lower()
        end_hour = int(m.group(4))
        end_minute = int(m.group(5))
        end_ampm = (m.group(6) or "").lower()
        
        # Apply AM/PM conversion for start time
        if start_ampm == "pm" and start_hour < 12:
            start_hour += 12
        elif start_ampm == "am" and start_hour == 12:
            start_hour = 0
        
        # Apply AM/PM conversion for end time
        if end_ampm == "pm" and end_hour < 12:
            end_hour += 12
        elif end_ampm == "am" and end_hour == 12:
            end_hour = 0
        
        # Validate hours and minutes
        if 0 <= start_hour <= 23 and 0 <= start_minute <= 59 and 0 <= end_hour <= 23 and 0 <= end_minute <= 59:
            # Calculate duration in minutes
            start_total_minutes = start_hour * 60 + start_minute
            end_total_minutes = end_hour * 60 + end_minute
            
            # Handle case where end time is earlier than start time (next day)
            if end_total_minutes <= start_total_minutes:
                # Assume end time is next day
                end_total_minutes += 24 * 60
            
            duration = end_total_minutes - start_total_minutes
            
            # Sanity check: duration should be reasonable (1 min to 24 hours)
            if 1 <= duration <= 1440:
                return ((start_hour, start_minute), duration)
    
    return None


def _next_weekday(base: datetime, target_wd: int) -> datetime:
    """Get next occurrence of target weekday, excluding today."""
    days_ahead = (target_wd - base.weekday() + 7) % 7
    if days_ahead == 0:
        days_ahead = 7
    return (base + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _upcoming_weekday(base: datetime, target_wd: int) -> datetime:
    """Get upcoming occurrence of target weekday (always in future, never today)."""
    days_ahead = (target_wd - base.weekday() + 7) % 7
    if days_ahead == 0:
        # If today is the target weekday, skip to next week
        days_ahead = 7
    return (base + timedelta(days=days_ahead)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def _next_week_weekday(base: datetime, target_wd: int) -> datetime:
    """
    Get target weekday in 'next week' using Sunday-Saturday week semantics.
    
    - Current week = Sunday to Saturday containing 'base'
    - Next week = the full week (Sunday-Saturday) after current week
    - Returns the target weekday within that next week
    """
    # Find Sunday of current week (going backwards from base)
    days_since_sunday = (base.weekday() + 1) % 7  # Monday=0 in Python, so Sunday=(0+1)%7=1 days back
    current_week_sunday = base - timedelta(days=days_since_sunday)
    
    # Next week starts 7 days after current week's Sunday
    next_week_sunday = current_week_sunday + timedelta(days=7)
    
    # Find target weekday in next week
    # target_wd: Monday=0, Tuesday=1, ..., Sunday=6
    # Convert to days from Sunday: Sunday=0, Monday=1, ..., Saturday=6
    days_from_sunday = (target_wd + 1) % 7
    
    result = next_week_sunday + timedelta(days=days_from_sunday)
    return result.replace(hour=0, minute=0, second=0, microsecond=0)


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

    # Studies: academic, learning, projects
    if re.search(
        r'\b(study|studies|homework|reading|research|exam|test|lecture|class|course|presentation|project|brainstorming|review)\b',
        t,
    ):
        return "Studies"

    # Training: physical activities, exercise
    # Added "running" to catch "running session"
    if re.search(r'\b(workout|exercise|gym|run|running|jogging|training)\b', t):
        return "Training"

    # Meeting: professional interactions
    if re.search(r'\b(meeting|meet|call|appointment)\b', t):
        return "Meeting"

    return "Meeting"


def _parse_duration_minutes(text: str) -> Optional[int]:
    t = text.lower()

    # "two and a half hours" -> 150 minutes, "three and a half hours" -> 210, etc.
    m = re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+and\s+a\s+half\s+hours?\b', t)
    if m:
        base_hours = TEXT_NUMBERS[m.group(1)]
        return int((base_hours + 0.5) * 60)
    
    # "an hour and a half" / "one and a half hours" -> 90 minutes
    if re.search(r'\b(an|one)\s+hour\s+and\s+a\s+half\b', t):
        return 90
    if re.search(r'\b(an|one)\s+and\s+a\s+half\s+hours?\b', t):
        return 90
    
    # "one hour and fifteen minutes" -> 75, "two hours and thirty minutes" -> 150
    m = re.search(r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\s+hours?\s+and\s+(\d{1,2}|fifteen|thirty|forty-five)\s+minutes?\b', t)
    if m:
        hours = TEXT_NUMBERS[m.group(1)]
        minutes_str = m.group(2)
        if minutes_str.isdigit():
            minutes = int(minutes_str)
        elif minutes_str == "fifteen":
            minutes = 15
        elif minutes_str == "thirty":
            minutes = 30
        elif minutes_str == "forty-five":
            minutes = 45
        else:
            minutes = 0
        return hours * 60 + minutes
    
    # Numeric "X hour(s) and Y minutes" -> e.g., "2 hours and 30 minutes" -> 150
    m = re.search(r'\b(\d{1,2})\s+hours?\s+and\s+(\d{1,2})\s+minutes?\b', t)
    if m:
        hours = int(m.group(1))
        minutes = int(m.group(2))
        return hours * 60 + minutes
    
    # Fractional hours: "1.5 hours", "2.5 hours"
    m = re.search(r'\b(\d+\.\d+)\s*(hours?|hrs?|h)\b', t)
    if m:
        return int(float(m.group(1)) * 60)
    
    # "for/lasting/about X minutes" - with optional "about" keyword
    m = re.search(r'\b(?:for|lasting|about)\s+(?:about\s+)?(\d{1,3})\s*(minutes?|mins?|m)\b', t)
    if m:
        return int(m.group(1))
    
    # "for/lasting/about X hours" - with optional "about" keyword
    m = re.search(r'\b(?:for|lasting|about)\s+(?:about\s+)?(\d{1,2})\s*(hours?|hrs?|h)\b', t)
    if m:
        return int(m.group(1)) * 60
    
    # "for/lasting one/two/three hours" (text numbers)
    m = re.search(
        r'\b(?:for|lasting)\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+hours?\b', t
    )
    if m:
        return TEXT_NUMBERS[m.group(1)] * 60
    
    # "lasting one hour" / "about an hour" (special case)
    if re.search(r'\b(?:lasting|about|for)\s+(an|one)\s+hour\b', t):
        return 60
    
    # Fallback: just "X minutes" or "X hours" without preposition
    m = re.search(r'\b(\d{1,3})\s*(minutes?|mins?)\b', t)
    if m:
        return int(m.group(1))
    
    m = re.search(r'\b(\d{1,2})\s*(hours?|hrs?)\b', t)
    if m:
        return int(m.group(1)) * 60

    return None


def _parse_absolute_datetime(text: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse absolute date/time formats:
    - ISO: 2025-12-20 at 08:45
    - Numeric: 12/10/2025 at 09:15, 20.12.2025 at 18:00
    - Written: November 25th 2025 at 10:00, December 5, 2025 at 13:00
    - Day Month Year: 10 Dec 2025 at 16:00
    - Month Day (no year): December 10th at 11:00
    """
    if now is None:
        now = datetime.now()
    
    t = text.lower()
    
    # First, try to extract time using dedicated time parser
    hm = _parse_time_str(t)
    if not hm:
        return None  # No time found, can't create absolute datetime
    
    hour, minute = hm
    
    # Pattern 1: ISO date format YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', t)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        try:
            return datetime(year, month, day, hour, minute, 0)
        except ValueError:
            pass
    
    # Pattern 2: DD.MM.YYYY (European format with dots)
    m = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        try:
            return datetime(year, month, day, hour, minute, 0)
        except ValueError:
            pass
    
    # Pattern 3: Month name + day + year (November 25th 2025, Dec 3rd 2025)
    # Support with or without ordinal suffixes (st, nd, rd, th)
    m = re.search(
        r'\b('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})\b',
        t
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3))
        try:
            return datetime(year, month, day, hour, minute, 0)
        except ValueError:
            pass
    
    # Pattern 4: Day + Month name + Year (10 Dec 2025, 25 November 2025)
    m = re.search(
        r'\b(\d{1,2})\s+('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{4})\b',
        t
    )
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2)]
        year = int(m.group(3))
        try:
            return datetime(year, month, day, hour, minute, 0)
        except ValueError:
            pass
    
    # Pattern 5: Numeric dates DD/MM/YYYY ONLY (strict enforcement)
    # ALWAYS interpret as Day/Month/Year - no fallback to MM/DD/YYYY
    m = re.search(r'\b(\d{1,2})[/\-\.]?(\d{1,2})[/\-\.]?(\d{4})\b', t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        
        print(f"DEBUG NLP: Input '{text}' - Numeric date found: Day={day}, Month={month}, Year={year}")
        
        # STRICT DD/MM/YYYY interpretation
        if 1 <= day <= 31 and 1 <= month <= 12:
            try:
                result = datetime(year, month, day, hour, minute, 0)
                print(f"DEBUG NLP: Successfully parsed as {result.strftime('%d/%m/%Y')}")
                return result
            except ValueError as e:
                print(f"DEBUG NLP: Failed to parse - {e}")
                pass
    
    # Pattern 6: Month name + day without year (December 10th, Nov 25)
    # Infer year: use current year if date is in future, otherwise next year
    m = re.search(
        r'\b('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})(?:st|nd|rd|th)?\b',
        t
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        month_name = m.group(1).capitalize()
        
        print(f"[NLP PARSER] Original string: \"{text}\" (with time)")
        print(f"[NLP PARSER] Extracted: {month_name} {day} at {hour:02d}:{minute:02d} (no year specified)")
        print(f"[NLP PARSER] Current datetime: {now}")
        
        # Try current year first
        try:
            cand = datetime(now.year, month, day, hour, minute, 0)
            print(f"[NLP PARSER] Candidate with current year: {cand} ({now.year})")
            
            if cand > now:
                print(f"[NLP PARSER] ✅ DateTime is in future, using year: {now.year}")
                print(f"[NLP PARSER] Final DateTime: {cand}")
                return cand
            
            # Date has passed, use next year
            next_year_dt = datetime(now.year + 1, month, day, hour, minute, 0)
            print(f"[NLP PARSER] ⚠️ DateTime is in the past, incrementing year")
            print(f"[NLP PARSER] Inferred Year: {now.year + 1}")
            print(f"[NLP PARSER] Final DateTime: {next_year_dt}")
            return next_year_dt
        except ValueError as e:
            print(f"[NLP PARSER] ❌ ValueError: {e}")
            pass
    
    # Pattern 7: "on Month Day" + time
    m = re.search(
        r'\bon\s+('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})\b',
        t,
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        month_name = m.group(1).capitalize()
        
        print(f"[NLP PARSER] Original string: \"{text}\" (with time)")
        print(f"[NLP PARSER] Extracted: on {month_name} {day} at {hour:02d}:{minute:02d} (no year specified)")
        print(f"[NLP PARSER] Current datetime: {now}")
        
        try:
            cand = datetime(now.year, month, day, hour, minute, 0)
            print(f"[NLP PARSER] Candidate with current year: {cand} ({now.year})")
            
            if cand > now:
                print(f"[NLP PARSER] DateTime is in future, using year: {now.year}")
                print(f"[NLP PARSER] Final DateTime: {cand}")
                return cand
            
            next_year_dt = datetime(now.year + 1, month, day, hour, minute, 0)
            print(f"[NLP PARSER] DateTime is in the past, incrementing year")
            print(f"[NLP PARSER] Inferred Year: {now.year + 1}")
            print(f"[NLP PARSER] Final DateTime: {next_year_dt}")
            return next_year_dt
        except ValueError as e:
            print(f"[NLP PARSER] ❌ ValueError: {e}")
            pass
    
    return None


def _add_months(base: datetime, months: int) -> datetime:
    year = base.year + (base.month - 1 + months) // 12
    month = (base.month - 1 + months) % 12 + 1
    return datetime(year, month, 1, 0, 0, 0)


def _parse_date_only_absolute(text: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse absolute dates WITHOUT requiring time.
    Returns datetime at start of day (00:00:00) if date is found.
    
    Supports:
    - ISO: 2025-12-20
    - European: 20.12.2025
    - Written: November 25th 2025, December 5, 2025
    - Day first: 10 Dec 2025
    - Numeric: 12/10/2025
    - Month without year: December 10th
    """
    if now is None:
        now = datetime.now()
    
    t = text.lower()
    
    # Pattern 1: ISO date format YYYY-MM-DD or YYYY/MM/DD
    m = re.search(r'\b(\d{4})[-/](\d{1,2})[-/](\d{1,2})\b', t)
    if m:
        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        try:
            return datetime(year, month, day, 0, 0, 0)
        except ValueError:
            pass
    
    # Pattern 2: DD.MM.YYYY (European format with dots)
    m = re.search(r'\b(\d{1,2})\.(\d{1,2})\.(\d{4})\b', t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        try:
            return datetime(year, month, day, 0, 0, 0)
        except ValueError:
            pass
    
    # Pattern 3: Month name + day + year (November 25th 2025, Dec 3rd 2025)
    m = re.search(
        r'\b('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})(?:st|nd|rd|th)?[,\s]+(\d{4})\b',
        t
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        year = int(m.group(3))
        try:
            return datetime(year, month, day, 0, 0, 0)
        except ValueError:
            pass
    
    # Pattern 4: Day + Month name + Year (10 Dec 2025, 25 November 2025)
    m = re.search(
        r'\b(\d{1,2})\s+('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{4})\b',
        t
    )
    if m:
        day = int(m.group(1))
        month = MONTHS[m.group(2)]
        year = int(m.group(3))
        try:
            return datetime(year, month, day, 0, 0, 0)
        except ValueError:
            pass
    
    # Pattern 5: Numeric dates DD/MM/YYYY ONLY (strict enforcement)
    # ALWAYS interpret as Day/Month/Year - no fallback to MM/DD/YYYY
    m = re.search(r'\b(\d{1,2})[/\-\.]?(\d{1,2})[/\-\.]?(\d{4})\b', t)
    if m:
        day = int(m.group(1))
        month = int(m.group(2))
        year = int(m.group(3))
        
        print(f"DEBUG NLP: Input '{text}' - Numeric date found: Day={day}, Month={month}, Year={year}")
        
        # STRICT DD/MM/YYYY interpretation
        if 1 <= day <= 31 and 1 <= month <= 12:
            try:
                result = datetime(year, month, day, 0, 0, 0)
                print(f"DEBUG NLP: Successfully parsed as {result.strftime('%d/%m/%Y')}")
                return result
            except ValueError as e:
                print(f"DEBUG NLP: Failed to parse - {e}")
                pass
    
    # Pattern 6: Month name + day without year (December 10th, Nov 25)
    m = re.search(
        r'\b('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})(?:st|nd|rd|th)?\b',
        t
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        month_name = m.group(1).capitalize()
        
        print(f"[NLP PARSER] Original string: \"{text}\"")
        print(f"[NLP PARSER] Extracted: {month_name} {day} (no year specified)")
        print(f"[NLP PARSER] Current date: {now.date()} ({now.year})")
        
        # Try current year first
        try:
            cand = datetime(now.year, month, day, 0, 0, 0)
            print(f"[NLP PARSER] Candidate with current year: {cand.date()} ({now.year})")
            
            if cand.date() >= now.date():
                print(f"[NLP PARSER] ✅ Date is today or in future, using year: {now.year}")
                print(f"[NLP PARSER] Final Date: {cand.date()}")
                return cand
            
            # Date has passed, use next year
            next_year_date = datetime(now.year + 1, month, day, 0, 0, 0)
            print(f"[NLP PARSER] ⚠️ Date is in the past, incrementing year")
            print(f"[NLP PARSER] Inferred Year: {now.year + 1}")
            print(f"[NLP PARSER] Final Date: {next_year_date.date()}")
            return next_year_date
        except ValueError as e:
            print(f"[NLP PARSER] ❌ ValueError: {e}")
            pass
    
    # Pattern 7: "on Month Day"
    m = re.search(
        r'\bon\s+('
        r'jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|'
        r'aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)'
        r'\s+(\d{1,2})\b',
        t,
    )
    if m:
        month = MONTHS[m.group(1)]
        day = int(m.group(2))
        month_name = m.group(1).capitalize()
        
        print(f"[NLP PARSER] Original string: \"{text}\"")
        print(f"[NLP PARSER] Extracted: on {month_name} {day} (no year specified)")
        print(f"[NLP PARSER] Current date: {now.date()} ({now.year})")
        
        try:
            cand = datetime(now.year, month, day, 0, 0, 0)
            print(f"[NLP PARSER] Candidate with current year: {cand.date()} ({now.year})")
            
            if cand.date() >= now.date():
                print(f"[NLP PARSER] ✅ Date is today or in future, using year: {now.year}")
                print(f"[NLP PARSER] Final Date: {cand.date()}")
                return cand
            
            next_year_date = datetime(now.year + 1, month, day, 0, 0, 0)
            print(f"[NLP PARSER] ⚠️ Date is in the past, incrementing year")
            print(f"[NLP PARSER] Inferred Year: {now.year + 1}")
            print(f"[NLP PARSER] Final Date: {next_year_date.date()}")
            return next_year_date
        except ValueError as e:
            print(f"[NLP PARSER] ❌ ValueError: {e}")
            pass
    
    return None


def _parse_date_only_relative(text: str, now: Optional[datetime] = None) -> Optional[datetime]:
    """
    Parse relative dates WITHOUT requiring time.
    Returns datetime at start of day (00:00:00) if date is found.
    
    Supports:
    - tomorrow
    - next Tuesday, upcoming Monday, etc.
    - next week Tuesday
    - second Friday of next month
    - in X days
    """
    if now is None:
        now = datetime.now()
    t = text.lower()
    
    # tomorrow
    if re.search(r'\btomorrow\b', t):
        return (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # in X days
    m = re.search(r'\bin\s+(\d{1,3})\s+days?\b', t)
    if m:
        days = int(m.group(1))
        return (now + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    m = re.search(
        r'\bin\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\b', t
    )
    if m:
        days = TEXT_NUMBERS[m.group(1)]
        return (now + timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # upcoming <weekday>
    m = re.search(
        r'\bupcoming\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        return _upcoming_weekday(now, wd)
    
    # next week <weekday>
    m = re.search(
        r'\bnext\s+week\b.*?\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        t,
    )
    if m:
        target_wd = WEEKDAYS[m.group(1)]
        return _next_week_weekday(now, target_wd)
    
    # next <weekday>
    m = re.search(
        r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        return _next_weekday(now, wd)
    
    # Ordinal weekday of next month
    m = re.search(
        r'\b(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+of\s+next\s+month\b',
        t
    )
    if not m:
        m = re.search(
            r'\bnext\s+month\s+(?:on\s+)?(?:the\s+)?(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            t
        )
    
    if m:
        ordinal = m.group(1)
        weekday_name = m.group(2)
        target_wd = WEEKDAYS[weekday_name]
        
        # Get first day of next month
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        next_month_start = _add_months(current_month_start, 1)
        
        if ordinal == "last":
            month_after = _add_months(next_month_start, 1)
            last_day = month_after - timedelta(days=1)
            days_back = (last_day.weekday() - target_wd) % 7
            result_date = last_day - timedelta(days=days_back)
        else:
            occurrence_map = {"first": 1, "second": 2, "third": 3, "fourth": 4}
            occurrence = occurrence_map.get(ordinal, 1)
            
            first_wd = next_month_start.weekday()
            days_to_target = (target_wd - first_wd) % 7
            first_occurrence = next_month_start + timedelta(days=days_to_target)
            result_date = first_occurrence + timedelta(weeks=occurrence - 1)
        
        return result_date.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # on <weekday>
    m = re.search(
        r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        return _upcoming_weekday(now, wd)
    
    return None


# --------- relative date parsing ---------


def _parse_relative_exact_datetime(
    text: str, now: Optional[datetime] = None
) -> Optional[datetime]:
    if now is None:
        now = datetime.now()
    t = text.lower()

    hm = _parse_time_str(t)
    if not hm:
        return None

    # tomorrow at <time>
    if re.search(r'\btomorrow\b', t):
        return (now + timedelta(days=1)).replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )

   
    m = re.search(r'\bin\s+(\d{1,3})\s+days?\b', t)
    if m:
        days = int(m.group(1))
        return (now + timedelta(days=days)).replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )
    m = re.search(
        r'\bin\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\b', t
    )
    if m:
        days = TEXT_NUMBERS[m.group(1)]
        return (now + timedelta(days=days)).replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )

    # "upcoming <weekday>" at <time> - always future, never today
    m = re.search(
        r'\bupcoming\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        base = _upcoming_weekday(now, wd)
        return base.replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )

    # "next week <weekday>" at <time> - using Sunday-Saturday week semantics
    m = re.search(
        r'\bnext\s+week\b.*?\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
        t,
    )
    if m:
        target_wd = WEEKDAYS[m.group(1)]
        base = _next_week_weekday(now, target_wd)
        return base.replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )
    
    # "next <weekday>" at <time> - simple next occurrence
    m = re.search(
        r'\bnext\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        base = _next_weekday(now, wd)
        return base.replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )

    # "next month on the second <weekday>" or "the second <weekday> of next month"
    # Try both word orders
    m = re.search(
        r'\b(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+of\s+next\s+month\b',
        t
    )
    if not m:
        m = re.search(
            r'\bnext\s+month\s+(?:on\s+)?(?:the\s+)?(first|second|third|fourth|last)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
            t
        )
    
    if m:
        ordinal = m.group(1)
        weekday_name = m.group(2)
        target_wd = WEEKDAYS[weekday_name]
        
        # Get first day of next month
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        next_month_start = _add_months(current_month_start, 1)
        
        # Find the Nth occurrence of target weekday
        if ordinal == "last":
            # Find last occurrence: go to last day of month and work backwards
            month_after = _add_months(next_month_start, 1)
            last_day = month_after - timedelta(days=1)
            # Find the last target weekday
            days_back = (last_day.weekday() - target_wd) % 7
            result_date = last_day - timedelta(days=days_back)
        else:
            # Find first occurrence of target weekday in next month
            occurrence_map = {"first": 1, "second": 2, "third": 3, "fourth": 4}
            occurrence = occurrence_map.get(ordinal, 1)
            
            # Find first target weekday in month
            first_wd = next_month_start.weekday()
            days_to_target = (target_wd - first_wd) % 7
            first_occurrence = next_month_start + timedelta(days=days_to_target)
            
            # Add weeks for 2nd, 3rd, 4th occurrence
            result_date = first_occurrence + timedelta(weeks=occurrence - 1)
        
        return result_date.replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )
    
    # on <weekday> at <time>
    m = re.search(
        r'\bon\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', t
    )
    if m:
        wd = WEEKDAYS[m.group(1)]
        base = _upcoming_weekday(now, wd)
        return base.replace(
            hour=hm[0], minute=hm[1], second=0, microsecond=0
        )

    return None


def _parse_relative_window(
    text: str, now: Optional[datetime] = None
) -> Tuple[Optional[datetime], Optional[datetime]]:
    if now is None:
        now = datetime.now()
    t = text.lower()

    # "this week" or "sometime this week"
    if re.search(r'\b(sometime\s+)?this\s+week\b', t):
        # Current week: from today to end of Saturday
        today = now.date()
        # Calculate days until Saturday (weekday 5)
        days_until_saturday = (5 - today.weekday()) % 7
        if days_until_saturday == 0 and today.weekday() == 5:
            # Today is Saturday, include it
            days_until_saturday = 0
        saturday = today + timedelta(days=days_until_saturday)
        start = datetime(today.year, today.month, today.day, 0, 0, 0)
        end = datetime(saturday.year, saturday.month, saturday.day, 23, 59, 59)
        return start, end

   
    if re.search(r'\btomorrow\b', t):
        day = (now + timedelta(days=1)).date()
        start = datetime(day.year, day.month, day.day, 0, 0, 0)
        end = start + timedelta(days=1)
        return start, end

  
    m = re.search(r'\bin\s+(\d{1,3})\s+days?\b', t)
    if m:
        days = int(m.group(1))
        day = (now + timedelta(days=days)).date()
        start = datetime(day.year, day.month, day.day, 0, 0, 0)
        end = start + timedelta(days=1)
        return start, end

    m = re.search(
        r'\bin\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+days?\b', t
    )
    if m:
        days = TEXT_NUMBERS[m.group(1)]
        day = (now + timedelta(days=days)).date()
        start = datetime(day.year, day.month, day.day, 0, 0, 0)
        end = start + timedelta(days=1)
        return start, end


    def _next_sunday_strict(base: datetime) -> datetime:
        # Monday=0..Sunday=6
        days_ahead = (6 - base.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        target = base + timedelta(days=days_ahead)
        return datetime(target.year, target.month, target.day, 0, 0, 0)

 
    if re.search(r'\b(sometime\s+)?next\s+week\b', t):
        n_weeks = 1
        first_sunday = _next_sunday_strict(now)
        week_start = first_sunday + timedelta(days=7 * (n_weeks - 1))
        week_end = week_start + timedelta(days=7)
        return week_start, week_end

    m = re.search(r'\bin\s+(\d{1,2})\s+weeks?\b', t)
    if m:
        n_weeks = int(m.group(1))
        if n_weeks < 1:
            n_weeks = 1
        first_sunday = _next_sunday_strict(now)
        week_start = first_sunday + timedelta(days=7 * (n_weeks - 1))
        week_end = week_start + timedelta(days=7)
        return week_start, week_end

    m = re.search(
        r'\bin\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+weeks?\b', t
    )
    if m:
        n_weeks = TEXT_NUMBERS[m.group(1)]
        if n_weeks < 1:
            n_weeks = 1
        first_sunday = _next_sunday_strict(now)
        week_start = first_sunday + timedelta(days=7 * (n_weeks - 1))
        week_end = week_start + timedelta(days=7)
        return week_start, week_end

    # "later this month"
    if re.search(r'\blater\s+this\s+month\b', t):
        # Last 10 days of current month
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        next_month_start = _add_months(current_month_start, 1)
        current_month_end = next_month_start - timedelta(days=1)
        # Start from 10 days before end of month
        later_start = current_month_end - timedelta(days=9)
        # But not before today
        if later_start.date() < now.date():
            later_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        return later_start, current_month_end

    # "this month" or "sometime this month"
    if re.search(r'\b(sometime\s+)?this\s+month\b', t):
        # From today to end of current month
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        next_month_start = _add_months(current_month_start, 1)
        current_month_end = next_month_start - timedelta(days=1)
        today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
        return today_start, current_month_end

  
    if re.search(r'\b(sometime\s+)?next\s+month\b', t):
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        month_start = _add_months(current_month_start, 1)
        month_end = _add_months(month_start, 1)
        return month_start, month_end

    m = re.search(r'\bin\s+(\d{1,2})\s+months?\b', t)
    if m:
        n_months = int(m.group(1))
        if n_months < 1:
            n_months = 1
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        month_start = _add_months(current_month_start, n_months)
        month_end = _add_months(month_start, 1)
        return month_start, month_end

    m = re.search(
        r'\bin\s+(one|two|three|four|five|six|seven|eight|nine|ten)\s+months?\b', t
    )
    if m:
        n_months = TEXT_NUMBERS[m.group(1)]
        if n_months < 1:
            n_months = 1
        current_month_start = datetime(now.year, now.month, 1, 0, 0, 0)
        month_start = _add_months(current_month_start, n_months)
        month_end = _add_months(month_start, 1)
        return month_start, month_end

    # Specific month names: "sometime in January", "in February", etc.
    month_pattern = r'\b(sometime\s+)?in\s+(january|february|march|april|may|june|july|august|september|october|november|december)\b'
    m = re.search(month_pattern, t)
    if m:
        target_month_name = m.group(2)
        target_month = MONTHS.get(target_month_name[:3])  # Use first 3 chars
        if target_month:
            # Determine year: if month is in past, use next year
            target_year = now.year
            if target_month < now.month or (target_month == now.month and now.day > 1):
                target_year = now.year + 1
            month_start = datetime(target_year, target_month, 1, 0, 0, 0)
            month_end = _add_months(month_start, 1)
            return month_start, month_end

    return None, None


# --------- main public functions ---------


def parse_free_text(text: str) -> Dict[str, Any]:
    raw = text
    title = text.strip()
    task_type = _parse_task_type(text)
    priority = _parse_priority(text)
    
    # Parse explicit duration first (e.g., "for 2 hours")
    duration = _parse_duration_minutes(text)
    
    # Try to parse time range (e.g., "9:00 - 11:00")
    # Only use it if no explicit duration was found
    time_range_result = _parse_time_range(text)
    time_range_start = None
    time_range_duration = None
    
    if time_range_result:
        time_range_start, time_range_duration = time_range_result
        # If no explicit duration was found, use the time range duration
        if duration is None:
            duration = time_range_duration

    # Try relative date/time parsing first (upcoming Monday, next week, etc.)
    exact_dt = _parse_relative_exact_datetime(text)
    
    # If relative parsing failed, try absolute date/time parsing
    # (November 25th 2025 at 10:00, 2025-12-20 at 08:45, etc.)
    if exact_dt is None:
        exact_dt = _parse_absolute_datetime(text)

    # Try to parse date-only (without time) for CASE 2.B
    # This preserves the date constraint even when time is missing
    parsed_date_only: Optional[datetime] = None
    if exact_dt is None:
        # Try relative date-only (next Tuesday, upcoming Monday, etc.)
        parsed_date_only = _parse_date_only_relative(text)
        
        # If that failed, try absolute date-only (November 25th 2025, 2025-12-20, etc.)
        if parsed_date_only is None:
            parsed_date_only = _parse_date_only_absolute(text)

    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    preferred_time: Optional[Tuple[int, int]] = None  # (hour, minute)
    
    if exact_dt is None and parsed_date_only is None:
        # No date found at all, try window-based parsing
        window_start, window_end = _parse_relative_window(text)
        # If we have a window, try to extract preferred time separately
        # This handles cases like "sometime this week at 10am"
        if window_start is not None:
            preferred_time = _parse_time_str(text)
        # CASE 2.G: If no window either, still try to extract time
        # This handles "schedule a task at 15:00" (time only, no date)
        elif preferred_time is None:
            preferred_time = _parse_time_str(text)
    elif exact_dt is None and parsed_date_only is not None:
        # Date found but no time → convert to day-window for suggestions
        # This ensures suggestions stay on the parsed date
        window_start = parsed_date_only.replace(hour=0, minute=0, second=0, microsecond=0)
        window_end = parsed_date_only.replace(hour=23, minute=59, second=59, microsecond=0)

    debug: Dict[str, Any] = {
        "raw": raw,
        "matchedDateTime": exact_dt.isoformat(timespec="seconds")
        if isinstance(exact_dt, datetime)
        else None,
        "matchedWindowStart": window_start.isoformat(timespec="seconds")
        if isinstance(window_start, datetime)
        else None,
        "matchedWindowEnd": window_end.isoformat(timespec="seconds")
        if isinstance(window_end, datetime)
        else None,
        "matchedDuration": duration,
        "matchedTaskType": task_type,
    }

    parsed: Dict[str, Any] = {
        "title": title.lower(),
        "task_type": task_type,
        "dueDateTime": exact_dt.isoformat(timespec="seconds")
        if isinstance(exact_dt, datetime)
        else None,
        "durationMinutes": duration,
        "priority": priority,
        "windowStart": window_start.isoformat(timespec="seconds")
        if isinstance(window_start, datetime)
        else None,
        "windowEnd": window_end.isoformat(timespec="seconds")
        if isinstance(window_end, datetime)
        else None,
        "preferredTimeOfDay": f"{preferred_time[0]:02d}:{preferred_time[1]:02d}"
        if preferred_time
        else None,
    }

    full = bool(parsed["dueDateTime"]) and bool(parsed["durationMinutes"])
    
    # Detect presence of critical fields (D/T/L) separately
    # D (Date) present if: exact datetime exists OR parsed_date_only exists OR window exists
    has_date = bool(parsed["dueDateTime"]) or bool(parsed_date_only) or bool(parsed.get("windowStart"))
    
    # T (Time) present if: exact datetime exists (full datetime with time component)
    # If only window or date-only exists, time is NOT specified for has_time purposes
    # Note: preferredTimeOfDay is a separate constraint, not counted as "has_time"
    has_time = bool(parsed["dueDateTime"])
    
    # L (Duration) present if: durationMinutes is specified
    has_duration = bool(parsed["durationMinutes"])
    
    # All three critical fields present
    all_critical_present = has_date and has_time and has_duration
    
    # Flag to indicate if user explicitly requested a specific date
    # TRUE = user provided specific date (absolute or relative):
    #   - "November 25th 2025", "December 5th"
    #   - "next Tuesday", "this Friday", "upcoming Monday"
    #   - "third Friday of next month", "first Monday of next month"
    # FALSE = no date provided OR only vague range:
    #   - "schedule a task" (no date at all)
    #   - "sometime this week", "later this month", "sometime next month"
    #   - "this month", "sometime in January"
    # This flag is used to override rest-day filtering:
    #   If TRUE, suggestions MUST appear even on rest days
    #   If FALSE, rest days are filtered out
    explicit_date_requested = bool(exact_dt) or bool(parsed_date_only)
    
    parsed["explicitDateRequested"] = explicit_date_requested
    
    # Legacy flag for backward compatibility (will be deprecated)
    parsed["userExplicitDate"] = explicit_date_requested
    
    # Flag for CASE 2.D: User provided date+time but NO duration
    # This triggers fixed datetime mode in suggestion engine
    explicit_datetime_given = bool(exact_dt) and not bool(duration)
    parsed["explicitDateTimeGiven"] = explicit_datetime_given
    
    return {
        "status": "complete" if full else "partial",
        "parsed": parsed,
        "missing": [
            k for k in ("dueDateTime", "durationMinutes") if not parsed.get(k)
        ],
        "critical_fields": {
            "has_date": has_date,
            "has_time": has_time,
            "has_duration": has_duration,
            "all_present": all_critical_present
        },
        "debug": debug,
    }


def handle_free_text_input(text: str) -> Dict[str, Any]:
    return parse_free_text(text)
