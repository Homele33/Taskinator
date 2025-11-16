# backend/Ai/network/inference.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict
from .model import UserPreferenceModel
from .data.data_schemas import (
    ObservedTask,
    Priority,
    TaskType,
    normalize_priority,
    normalize_task_type,
)

# ---------- Predictions / scoring ----------

def predict_missing_priority(user_id: int, task_type: TaskType) -> Optional[Priority]:
    return UserPreferenceModel(user_id).mode_priority(task_type)

def predict_missing_duration(user_id: int, task_type: TaskType) -> Optional[int]:
    return UserPreferenceModel(user_id).mode_duration_minutes(task_type)

def score_bonus_for_slot(
    user_id: int,
    task_type: TaskType,
    slot_start: datetime,
    slot_end: datetime,
) -> float:
    return UserPreferenceModel(user_id).score_bonus(
        task_type, hour=slot_start.hour, weekday=slot_start.weekday()
    )

# ---------- Observation helpers used by routes ----------

def _dict_to_obs(d: Dict) -> ObservedTask:
    """
    Expecting a dict with:
      user_id, task_type, priority, scheduled_start, scheduled_end, duration_minutes
    """
    return ObservedTask(
        user_id=int(d["user_id"]),
        task_type=normalize_task_type(d.get("task_type")),
        priority=normalize_priority(d.get("priority")),
        scheduled_start=d["scheduled_start"],   # datetime
        scheduled_end=d["scheduled_end"],       # datetime
        duration_minutes=int(d["duration_minutes"]),
    )

def record_observation(obs_dict: Dict) -> None:
    """Add one observation (called on task create/choose-suggestion)."""
    obs = _dict_to_obs(obs_dict)
    UserPreferenceModel(obs.user_id).update_from_observation(obs, sign=+1)

def remove_observation(obs_dict: Dict) -> None:
    """Remove one observation (called on task delete)."""
    obs = _dict_to_obs(obs_dict)
    UserPreferenceModel(obs.user_id).update_from_observation(obs, sign=-1)

def update_observation(before_dict: Dict, after_dict: Dict) -> None:
    """
    Update stats by subtracting the 'before' snapshot and adding the 'after' snapshot.
    Used on task PATCH/PUT.
    """
    before = _dict_to_obs(before_dict)
    after  = _dict_to_obs(after_dict)
    m = UserPreferenceModel(before.user_id)
    m.update_from_observation(before, sign=-1)
    m.update_from_observation(after,  sign=+1)
