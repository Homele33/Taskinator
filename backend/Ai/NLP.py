import re
import sqlite3
import os
from suggest_slots import suggest_slots
from Ai.feature_engineering import time_to_index

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'mydatabase.db'))

# Parse task info from free-text

def parse_free_text(text: str):
    text = text.lower()
    task_type = "Meeting"  # Default fallback
    priority = "Medium"    # Default
    date = None
    time = None

    # Task type detection with broader keyword support
    if any(word in text for word in ["meeting", "meet", "call", "appointment"]):
        task_type = "Meeting"
    elif any(word in text for word in ["train", "workout", "exercise", "session"]):
        task_type = "Training"
    elif any(word in text for word in ["study", "homework", "reading", "research"]):
        task_type = "Studies"

    # Priority detection with broader keywords
    if any(word in text for word in ["high", "urgent", "critical", "important"]):
        priority = "High"
    elif any(word in text for word in ["low", "optional", "not important"]):
        priority = "Low"

    # Time detection
    time_match = re.search(r"(?:at|around)?\s*(\d{1,2})([:.]?(\d{2}))?\s*(am|pm)?", text)
    if time_match:
        hour = int(time_match.group(1))
        minute = time_match.group(3) or "00"
        ampm = time_match.group(4)
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        time = f"{hour:02}:{minute}"

    # Date detection
    if "tomorrow" in text:
        date = "tomorrow"
    elif "next week" in text:
        date = "next week"
    else:
        weekdays = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
        for day in weekdays:
            if day in text:
                date = day
                break

    return {
        "task_type": task_type,
        "priority": priority,
        "date": date,
        "time": time
    }

# Fetch real busy slots from task table

def get_busy_slots():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT due_date FROM task")
    rows = cursor.fetchall()
    conn.close()

    busy = []
    for (due_date_str,) in rows:
        if due_date_str:
            try:
                time_part = due_date_str.split(" ")[1]
                h, m, *_ = time_part.split(":")
                tstr = f"{int(h):02d}:{int(m):02d}"
                busy.append(time_to_index(tstr))
            except Exception:
                continue
    return busy

# Main handling function

def handle_free_text_input(text: str):
    parsed = parse_free_text(text)
    print("Parsed:", parsed)

    if parsed["time"] and parsed["date"]:
        print("✅ Full date and time provided – task can be scheduled directly.")
        return

    busy = get_busy_slots()
    suggestions = suggest_slots(parsed["task_type"], parsed["priority"], busy)
    print("Suggested slots:", suggestions)

if __name__ == "__main__":
    text = "Plan something important next week"
    handle_free_text_input(text)
