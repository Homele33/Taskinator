import numpy as np

TASK_TYPES = ["Meeting", "Training", "Studies"]
PRIORITIES = ["Low", "Medium", "High"]
TIMES_OF_DAY = ["Morning", "Afternoon", "Evening", "No preference"]
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def time_to_index(tstr: str) -> int:
    tstr = tstr.strip()
    h, m = map(int, tstr.split(":")[:2])
    return h * 2 + (1 if m >= 30 else 0)

def one_hot(value, options):
    return [1 if value == opt else 0 for opt in options]

def encode_row(task_row: dict, user_prefs: dict) -> list:
    features = []

   
    features += one_hot(task_row["task_type"], TASK_TYPES)
    features += one_hot(task_row["priority"], PRIORITIES)
    features += one_hot(user_prefs["preference_time"], TIMES_OF_DAY)

  
    features += [1 if day in user_prefs["preferred_days"] else 0 for day in DAYS]

  
    task_days = user_prefs["preferred_days_by_task"].get(task_row["task_type"], [])
    features += [1 if day in task_days else 0 for day in DAYS]

  
    focus = user_prefs["answers"]["focusHours"]
    avoid = user_prefs["answers"]["avoidTimes"]
    features += [time_to_index(focus["start"]) / 48, time_to_index(focus["end"]) / 48]
    features += [time_to_index(avoid["start"]) / 48, time_to_index(avoid["end"]) / 48]


    key = f"{task_row['task_type']}_{task_row['priority']}"
    time_range = user_prefs["answers"].get(key, {"start": "00:00", "end": "00:30"})
    features += [time_to_index(time_range["start"]) / 48, time_to_index(time_range["end"]) / 48]

    return features

def extract_label_from_due_date(due_date_str: str) -> int:
    time_part = due_date_str.split(" ")[1]  # "12:00:00.000000"
    h, m, *_ = time_part.split(":")
    hour_str = f"{int(h):02d}:{int(m):02d}"
    return time_to_index(hour_str)

def build_dataset(task_rows: list, user_prefs: dict):
    X = []
    y = []

    for row in task_rows:
        due_date_str = row.get("due_date")
        if not due_date_str:
            continue

        try:
            label = extract_label_from_due_date(due_date_str)
        except:
            continue

        features = encode_row(row, user_prefs)
        X.append(features)
        y.append(label)

    return np.array(X), np.array(y)
