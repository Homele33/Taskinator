import sqlite3
import os
from datetime import datetime
from Ai.preferences_loader import get_user_preferences
from Ai.feature_engineering import encode_row, time_to_index
import numpy as np
import pickle
from pymc.data import set_data

MODEL_DIR = os.path.abspath("model_store")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'mydatabase.db'))

def fetch_latest_task():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT id, task_type, priority, due_date
    FROM task
    ORDER BY id DESC
    LIMIT 1
    """
    row = cursor.execute(query).fetchone()
    conn.close()

    if not row:
        raise ValueError("No new task found in DB")
    due_date_str = row["due_date"]
    try:
        time_part = due_date_str.split(" ")[1]  # "14:30:00.000000"
        h, m, *_ = time_part.split(":")
        due_time = f"{int(h):02d}:{int(m):02d}"
    except Exception as e:
        raise ValueError(f'Error in decomposition due_date: {e}')

    return {
        "task_type": row["task_type"],
        "priority": row["priority"],
        "due_time": due_time
    }

def update_model_with_task(task_row):
    with open(os.path.join(MODEL_DIR, "approx.pkl"), "rb") as f:
        approx = pickle.load(f)

    X = np.load(os.path.join(MODEL_DIR, "X.npy"))
    y = np.load(os.path.join(MODEL_DIR, "y.npy"))

    prefs = get_user_preferences()
    features = encode_row(task_row, prefs)
    label = time_to_index(task_row["due_time"])

    X = np.vstack([X, features])
    y = np.append(y, label)

    np.save(os.path.join(MODEL_DIR, "X.npy"), X)
    np.save(os.path.join(MODEL_DIR, "y.npy"), y)

    set_data("X", X)
    set_data("y", y)
    approx = approx.fit(n=1000)

    with open(os.path.join(MODEL_DIR, "approx.pkl"), "wb") as f:
        pickle.dump(approx, f)

    print("The model has been successfully updated")

if __name__ == "__main__":
    task = fetch_latest_task()
    update_model_with_task(task)
