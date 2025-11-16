from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal

TaskType = Literal["Meeting", "Training", "Studies"]
Priority = Literal["LOW", "MEDIUM", "HIGH"]

def hour_bucket(dt: datetime) -> int:
    """Return hour-of-day bucket [0..23]."""
    return int(dt.hour)

def weekday_idx(dt: datetime) -> int:
    """
    Return weekday as 0..6 (Mon=0..Sun=6) to align with Python's datetime.weekday().
    We will keep all internal stats in this convention.
    """
    return int(dt.weekday())

def duration_bucket(minutes: int) -> str:
    """Bucket durations to control sparsity."""
    bins = [15, 30, 45, 60, 90, 120, 180]
    for b in bins:
        if minutes <= b:
            return str(b)
    return "long"

@dataclass
class ObservedTask:
    """Normalized observation for training."""
    user_id: int
    task_type: TaskType
    priority: Priority
    scheduled_start: datetime
    scheduled_end: datetime
    duration_minutes: int

    @property
    def hour(self) -> int:
        return hour_bucket(self.scheduled_start)

    @property
    def weekday(self) -> int:
        return weekday_idx(self.scheduled_start)

    @property
    def duration_bin(self) -> str:
        return duration_bucket(self.duration_minutes)

def normalize_priority(value: Optional[str]) -> Priority:
    v = (value or "MEDIUM").upper()
    return "HIGH" if v == "HIGH" else "LOW" if v == "LOW" else "MEDIUM"

def normalize_task_type(value: Optional[str]) -> TaskType:
    v = (value or "Meeting")
    return v if v in ("Meeting", "Training", "Studies") else "Meeting"
