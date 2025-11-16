from __future__ import annotations
import json, os, tempfile
from typing import Dict, Any, Optional
from collections import defaultdict
from Ai.network.data.data_schemas import ObservedTask, Priority, TaskType


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def _model_path(user_id: int) -> str:
    _ensure_dir(DATA_DIR)
    return os.path.join(DATA_DIR, f"user_{user_id}.json")

def _atomic_write(path: str, payload: Dict[str, Any]) -> None:
    _ensure_dir(os.path.dirname(path))
    tmp_fd, tmp_path = tempfile.mkstemp(prefix=".tmp", dir=os.path.dirname(path))
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass

class UserPreferenceModel:
    """
    Lightweight, file-backed statistics model per user.
    Schema (example):
    {
      "by_type": {
         "Meeting": {
            "hour": {"9": 12, "10": 5, ...},
            "weekday": {"0": 3, "1": 7, ...},
            "priority": {"LOW": 2, "MEDIUM": 9, "HIGH": 6},
            "duration": {"30": 1, "60": 8, "90": 3, "long": 1}
         },
         "Training": { ... },
         "Studies": { ... }
      },
      "global": {
         "hour": {...}, "weekday": {...}, "priority": {...}, "duration": {...}
      },
      "meta": {"total_events": 123}
    }
    """

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.state: Dict[str, Any] = {
            "by_type": {},
            "global": {"hour": {}, "weekday": {}, "priority": {}, "duration": {}},
            "meta": {"total_events": 0},
        }
        self._load()

    # ---------- IO ----------
    def _load(self) -> None:
        path = _model_path(self.user_id)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.state = json.load(f)
            except Exception:
                # Corrupted file? start fresh
                self.state = {
                    "by_type": {},
                    "global": {"hour": {}, "weekday": {}, "priority": {}, "duration": {}},
                    "meta": {"total_events": 0},
                }

    def _save(self) -> None:
        _atomic_write(_model_path(self.user_id), self.state)

    # ---------- helpers ----------
    def _inc(self, d: Dict[str, Any], key: str, delta: int = 1) -> None:
        cur = int(d.get(key, 0))
        new = cur + delta
        if new <= 0:
            if key in d:
                del d[key]
        else:
            d[key] = new


    def _type_bucket(self, t: TaskType) -> Dict[str, Dict[str, int]]:
        by_type = self.state.setdefault("by_type", {})
        bucket = by_type.setdefault(t, {"hour": {}, "weekday": {}, "priority": {}, "duration": {}})
        return bucket

    # ---------- public API ----------
    def update_from_observation(self, obs: ObservedTask, sign: int = +1) -> None:
        """
        Apply an observation (sign=+1 for add / sign=-1 for remove).
        """
        b = self._type_bucket(obs.task_type)

        self._inc(b["hour"], str(obs.hour), sign)
        self._inc(b["weekday"], str(obs.weekday), sign)
        self._inc(b["priority"], obs.priority, sign)
        self._inc(b["duration"], obs.duration_bin, sign)

        self._inc(self.state["global"]["hour"], str(obs.hour), sign)
        self._inc(self.state["global"]["weekday"], str(obs.weekday), sign)
        self._inc(self.state["global"]["priority"], obs.priority, sign)
        self._inc(self.state["global"]["duration"], obs.duration_bin, sign)

        self.state["meta"]["total_events"] = max(0, int(self.state["meta"].get("total_events", 0)) + sign)
        self._save()

    def mode_priority(self, task_type: TaskType) -> Optional[Priority]:
        bucket = self._type_bucket(task_type)["priority"]
        if not bucket:
            bucket = self.state["global"]["priority"]
        if not bucket:
            return None
        # argmax
        return max(bucket.items(), key=lambda kv: kv[1])[0]  # type: ignore[return-value]

    def mode_duration_minutes(self, task_type: TaskType) -> Optional[int]:
        bucket = self._type_bucket(task_type)["duration"] or self.state["global"]["duration"]
        if not bucket:
            return None
        # choose most frequent bucket midpoint
        key, _ = max(bucket.items(), key=lambda kv: kv[1])
        return 120 if key == "long" else int(key)

    def score_bonus(self, task_type: TaskType, hour: int, weekday: int) -> float:
        """
        Return a small, smoothed bonus based on historical preferences.
        """
        t_bucket = self._type_bucket(task_type)
        g = self.state["global"]

        def rel_freq(d: Dict[str, int], k: str) -> float:
            s = sum(max(0, int(v)) for v in d.values()) or 1
            return max(0, int(d.get(k, 0))) / s

        # Simple mix of type-specific and global distributions
        h = 0.6 * rel_freq(t_bucket["hour"], str(hour)) + 0.4 * rel_freq(g["hour"], str(hour))
        w = 0.6 * rel_freq(t_bucket["weekday"], str(weekday)) + 0.4 * rel_freq(g["weekday"], str(weekday))

        # Map [0..1] to a small score boost [0..2]
        return 2.0 * (0.5 * h + 0.5 * w)
