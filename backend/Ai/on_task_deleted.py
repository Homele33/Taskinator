import sqlite3
import os
import numpy as np
import pickle
from pymc.data import set_data
from Ai.feature_engineering import build_dataset
from Ai.preferences_loader import get_user_preferences

MODEL_DIR = os.path.abspath("model_store")
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'instance', 'mydatabase.db'))

def fetch_all_tasks():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    query = """
    SELECT task_type, priority, due_date
    FROM task
    """
    rows = cursor.execute(query).fetchall()
    conn.close()

    return [dict(row) for row in rows]

def rebuild_model_from_tasks():
    task_rows = fetch_all_tasks()
    prefs = get_user_preferences()
    
    X, y = build_dataset(task_rows, prefs)

    if len(X) == 0:
        print("⚠ No tasks remaining. Model not updated.")
        return

    np.save(os.path.join(MODEL_DIR, "X.npy"), X)
    np.save(os.path.join(MODEL_DIR, "y.npy"), y)

    with open(os.path.join(MODEL_DIR, "approx.pkl"), "rb") as f:
        approx = pickle.load(f)

    set_data("X", X)
    set_data("y", y)
    approx = approx.fit(n=1000)

    with open(os.path.join(MODEL_DIR, "approx.pkl"), "wb") as f:
        pickle.dump(approx, f)

    print("✓ Model was updated after task deletion")

if __name__ == "__main__":
    rebuild_model_from_tasks()
