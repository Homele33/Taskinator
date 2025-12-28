"""
Unified Conflict Detection Layer (Stage 1)

This module provides conflict detection for task scheduling.
It detects overlapping tasks but does NOT prevent task creation.

Stage 1: Detection only - returns conflict information in API responses
Stage 2 (future): Frontend conflict resolution UI
Stage 3 (future): Automatic rescheduling capabilities
"""

from datetime import datetime
from typing import List, Dict, Optional
from models import Task, db


def check_time_conflicts(user_id: int, start_dt: datetime, end_dt: datetime) -> Dict:
    """
    Check if a new task would overlap with existing tasks for the given user.
    
    Overlap condition: new_start < existing_end AND new_end > existing_start
    
    Args:
        user_id: ID of the user whose tasks to check
        start_dt: Scheduled start datetime of the new task
        end_dt: Scheduled end datetime of the new task
    
    Returns:
        Dictionary with conflict information:
        {
            "hasConflict": bool,
            "conflicts": [
                {
                    "id": int,
                    "title": str,
                    "start": str (ISO format),
                    "end": str (ISO format),
                    "taskType": str
                },
                ...
            ]
        }
    
    Notes:
        - Only checks tasks with scheduled_start and scheduled_end set
        - Ignores tasks with status "COMPLETED" (considered done)
        - Uses timezone-aware comparison if datetimes are timezone-aware
        - Returns empty conflicts list if no overlaps found
    """
    # Validate inputs
    if not start_dt or not end_dt:
        return {
            "hasConflict": False,
            "conflicts": []
        }
    
    if start_dt >= end_dt:
        # Invalid time range - no conflict check possible
        return {
            "hasConflict": False,
            "conflicts": []
        }
    
    # Query all tasks for this user that have scheduled times
    # Exclude completed tasks as they are done and won't cause conflicts
    existing_tasks = Task.query.filter(
        Task.user_id == user_id,
        Task.scheduled_start.isnot(None),
        Task.scheduled_end.isnot(None),
        Task.status != "COMPLETED"
    ).all()
    
    conflicts: List[Dict] = []
    
    for task in existing_tasks:
        # Check for overlap:
        # Two time ranges overlap if: start1 < end2 AND start2 < end1
        # In our case: new_start < existing_end AND new_end > existing_start
        if start_dt < task.scheduled_end and end_dt > task.scheduled_start:
            conflicts.append({
                "id": task.id,
                "title": task.title,
                "start": task.scheduled_start.isoformat(),
                "end": task.scheduled_end.isoformat(),
                "taskType": task.task_type or "Meeting"
            })
    
    return {
        "hasConflict": len(conflicts) > 0,
        "conflicts": conflicts
    }


def get_conflict_info_for_task(task: Task) -> Dict:
    """
    Check conflicts for an existing task object.
    
    Convenience wrapper around check_time_conflicts that extracts
    the necessary fields from a Task object.
    
    Args:
        task: Task object to check for conflicts
    
    Returns:
        Same format as check_time_conflicts()
    """
    if not task.scheduled_start or not task.scheduled_end:
        return {
            "hasConflict": False,
            "conflicts": []
        }
    
    return check_time_conflicts(
        user_id=task.user_id,
        start_dt=task.scheduled_start,
        end_dt=task.scheduled_end
    )
