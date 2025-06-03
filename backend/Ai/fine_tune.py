import os
import pickle
import numpy as np
from pymc.data import set_data
from Ai.feature_engineering import encode_row, time_to_index
from Ai.preferences_loader import get_user_preferences

MODEL_DIR = os.path.abspath("model_store")

# Load the existing trained model (approx)
with open(os.path.join(MODEL_DIR, "approx.pkl"), "rb") as f:
    approx = pickle.load(f)

# Load the existing features and tags
X = np.load(os.path.join(MODEL_DIR, "X.npy"))
y = np.load(os.path.join(MODEL_DIR, "y.npy"))

# New task to add
new_task = {
    "task_type": "Meeting",
    "priority": "High",
    "due_time": "16:30"
}

# Coding the task
prefs = get_user_preferences()
features = encode_row(new_task, prefs)
label = time_to_index(new_task["due_time"])

# Add to data
X = np.vstack([X, features])
y = np.append(y, label)

# Updating files
np.save(os.path.join(MODEL_DIR, "X.npy"), X)
np.save(os.path.join(MODEL_DIR, "y.npy"), y)

# Updating data in the existing model
set_data("X", X)
set_data("y", y)

# Continue training with the new task
approx = approx.fit(n=1000)

# Re-save
with open(os.path.join(MODEL_DIR, "approx.pkl"), "wb") as f:
    pickle.dump(approx, f)

print("fine_tune working")
