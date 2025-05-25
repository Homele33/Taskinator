import os
import numpy as np
import pickle
from pymc import Model, Normal, Categorical, fit
from pymc.math import dot, tanh, softmax
from pymc.data import Data

from Ai.preferences_loader import get_user_preferences
from Ai.feature_engineering import encode_row, time_to_index

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model_store")
os.makedirs(MODEL_DIR, exist_ok=True)

def get_middle_index(start_str, end_str):
    h1, m1 = map(int, start_str.split(":"))
    h2, m2 = map(int, end_str.split(":"))
    t1 = h1 * 60 + m1
    t2 = h2 * 60 + m2
    mid = (t1 + t2) // 2
    mid_h = mid // 60
    mid_m = mid % 60
    return time_to_index(f"{mid_h:02}:{mid_m:02}")

def init_model():
    prefs = get_user_preferences()
    answers = prefs["answers"]

    X = []
    y = []

    for key, time_range in answers.items():
        if "_" not in key:
            continue

        task_type, priority = key.split("_")
        task = {"task_type": task_type, "priority": priority}
        features = encode_row(task, prefs)
        label = get_middle_index(time_range["start"], time_range["end"])
        X.append(features)
        y.append(label)

    X = np.array(X)
    y = np.array(y)

    np.save(os.path.join(MODEL_DIR, "X.npy"), X)
    np.save(os.path.join(MODEL_DIR, "y.npy"), y)

    with Model() as model:
        X_data = Data("X", X)
        y_data = Data("y", y)

        w1 = Normal("w1", mu=0, sigma=1, shape=(X.shape[1], 16))
        b1 = Normal("b1", mu=0, sigma=1, shape=(16,))
        hidden = tanh(dot(X_data, w1) + b1)

        w2 = Normal("w2", mu=0, sigma=1, shape=(16, 48))
        b2 = Normal("b2", mu=0, sigma=1, shape=(48,))
        logits = dot(hidden, w2) + b2

        theta = softmax(logits)
        yl = Categorical("yl", p=theta, observed=y_data)

        approx = fit(n=3000, method="advi")

        with open(os.path.join(MODEL_DIR, "approx.pkl"), "wb") as f:
            pickle.dump(approx, f)

    print("train working")

if __name__ == "__main__":
    init_model()
