#backend/Ai/network/training.py
from __future__ import annotations
from datetime import datetime
from typing import Optional
from Ai.network.data.data_schemas import ObservedTask, normalize_priority, normalize_task_type
from Ai.network.model import UserPreferenceModel

def record_task_created(
    *,
    user_id: int,
    title: str,
    task_type: Optional[str],
    priority: Optional[str],
    scheduled_start: datetime,
    scheduled_end: datetime,
    duration_minutes: int,
) -> None:
    """Record creation event into the user model."""
    obs = ObservedTask(
        user_id=user_id,
        task_type=normalize_task_type(task_type),
        priority=normalize_priority(priority),
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        duration_minutes=int(duration_minutes),
    )
    UserPreferenceModel(user_id).update_from_observation(obs, sign=+1)

def record_task_deleted(
    *,
    user_id: int,
    title: str,
    task_type: Optional[str],
    priority: Optional[str],
    scheduled_start: datetime,
    scheduled_end: datetime,
    duration_minutes: int,
) -> None:
    """Remove the observation if task is deleted (keeps stats consistent)."""
    obs = ObservedTask(
        user_id=user_id,
        task_type=normalize_task_type(task_type),
        priority=normalize_priority(priority),
        scheduled_start=scheduled_start,
        scheduled_end=scheduled_end,
        duration_minutes=int(duration_minutes),
    )
    UserPreferenceModel(user_id).update_from_observation(obs, sign=-1)

def record_task_updated(
    *,
    user_id: int,
    old_start: datetime,
    old_end: datetime,
    old_duration: int,
    old_task_type: Optional[str],
    old_priority: Optional[str],
    new_start: datetime,
    new_end: datetime,
    new_duration: int,
    new_task_type: Optional[str],
    new_priority: Optional[str],
) -> None:
    """Update stats by subtracting old and adding new observation."""
    record_task_deleted(
        user_id=user_id,
        title="",
        task_type=old_task_type,
        priority=old_priority,
        scheduled_start=old_start,
        scheduled_end=old_end,
        duration_minutes=old_duration,
    )
    record_task_created(
        user_id=user_id,
        title="",
        task_type=new_task_type,
        priority=new_priority,
        scheduled_start=new_start,
        scheduled_end=new_end,
        duration_minutes=new_duration,
    )
