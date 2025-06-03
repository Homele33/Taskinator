import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.abspath(os.path.join(BASE_DIR, '..', 'instance', 'mydatabase.db'))

CACHED_USER_PREFS = None

def get_user_preferences():
    global CACHED_USER_PREFS
    if CACHED_USER_PREFS is not None:
        return CACHED_USER_PREFS

    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM user_preferences WHERE id = 1"
    row = conn.execute(query).fetchone()
    conn.close()

    if row is None:
        raise ValueError("User preferences not found in database")

    columns = [
        "id", "answers", "preference_time", "preferred_days", "preferred_days_by_task"
    ]
    pref_dict = dict(zip(columns, row))

    pref_dict["answers"] = json.loads(pref_dict["answers"])
    pref_dict["preferred_days"] = json.loads(pref_dict["preferred_days"])
    pref_dict["preferred_days_by_task"] = json.loads(pref_dict["preferred_days_by_task"])

    CACHED_USER_PREFS = pref_dict
    return pref_dict


