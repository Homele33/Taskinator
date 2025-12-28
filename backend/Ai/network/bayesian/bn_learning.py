"""
Learning module for Bayesian Networks.

Handles incremental CPT parameter updates from task observations.
As users create, update, and delete tasks, the BN learns their actual
preferences and adjusts prediction accuracy.

Learning Strategy:
    - Layer 1 (Evidence): Fixed from UserPreferences, never learned
    - Layer 2 (Latent): Updated based on consistency with observations
    - Layer 3 (Predictions): Directly learned from task scheduling patterns
"""

from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

from .bn_core import BayesianNetwork, BNNode, CPT
from .bn_nodes import PreferredTimeOfDay, PreferredDayType


def map_hour_to_time_of_day(hour: int) -> str:
    """
    Map hour [0-23] to PreferredTimeOfDay state.
    
    Args:
        hour: Hour of day (0-23)
    
    Returns:
        PreferredTimeOfDay state string
    """
    if 6 <= hour < 12:
        return PreferredTimeOfDay.MORNING.value
    elif 12 <= hour < 14:
        return PreferredTimeOfDay.MIDDAY.value
    elif 14 <= hour < 17:
        return PreferredTimeOfDay.AFTERNOON.value
    elif 17 <= hour < 21:
        return PreferredTimeOfDay.EVENING.value
    else:
        return PreferredTimeOfDay.NIGHT.value


def map_weekday_to_day_type(weekday: int) -> str:
    """
    Map weekday [0-6] to PreferredDayType state.
    
    Args:
        weekday: Day of week (0=Monday, 6=Sunday per Python convention)
    
    Returns:
        PreferredDayType state string
    """
    # 0-4 = Mon-Fri (weekday), 5-6 = Sat-Sun (weekend)
    if weekday < 5:
        return PreferredDayType.WEEKDAY.value
    else:
        return PreferredDayType.WEEKEND.value


class HistoricalStatistics:
    """
    Tracks aggregated task statistics for learning.
    
    Maintains counts of observed task properties to build empirical
    distributions for CPT updates.
    
    Attributes:
        task_type_counts: Count of tasks by type
        hour_counts_by_type: Count of tasks scheduled at each hour, per type
        weekday_counts_by_type: Count of tasks on each weekday, per type
        duration_counts_by_type: Count of task durations, per type
        priority_counts_by_type: Count of priority levels, per type
    """
    
    def __init__(self):
        """Initialize empty statistics."""
        self.task_type_counts: Dict[str, int] = defaultdict(int)
        
        # hour -> count
        self.hour_counts_by_type: Dict[str, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        
        # weekday -> count
        self.weekday_counts_by_type: Dict[str, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        
        # duration_minutes -> count
        self.duration_counts_by_type: Dict[str, Dict[int, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        
        # priority -> count
        self.priority_counts_by_type: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
    
    def add_observation(self, obs: Dict) -> None:
        """
        Add a task observation to statistics.
        
        Args:
            obs: Task observation dict with keys:
                - task_type: str
                - scheduled_start: datetime
                - scheduled_end: datetime
                - duration_minutes: int
                - priority: str
        """
        task_type = obs.get("task_type", "Meeting")
        start = obs.get("scheduled_start")
        duration = obs.get("duration_minutes", 60)
        priority = obs.get("priority", "MEDIUM")
        
        if not start or not isinstance(start, datetime):
            return
        
        self.task_type_counts[task_type] += 1
        self.hour_counts_by_type[task_type][start.hour] += 1
        self.weekday_counts_by_type[task_type][start.weekday()] += 1
        self.duration_counts_by_type[task_type][duration] += 1
        self.priority_counts_by_type[task_type][priority] += 1
    
    def remove_observation(self, obs: Dict) -> None:
        """
        Remove a task observation from statistics (for deletes).
        
        Args:
            obs: Task observation dict (same format as add_observation)
        """
        task_type = obs.get("task_type", "Meeting")
        start = obs.get("scheduled_start")
        duration = obs.get("duration_minutes", 60)
        priority = obs.get("priority", "MEDIUM")
        
        if not start or not isinstance(start, datetime):
            return
        
        # Decrement counts (don't go below 0)
        self.task_type_counts[task_type] = max(0, self.task_type_counts[task_type] - 1)
        self.hour_counts_by_type[task_type][start.hour] = max(
            0, self.hour_counts_by_type[task_type][start.hour] - 1
        )
        self.weekday_counts_by_type[task_type][start.weekday()] = max(
            0, self.weekday_counts_by_type[task_type][start.weekday()] - 1
        )
        self.duration_counts_by_type[task_type][duration] = max(
            0, self.duration_counts_by_type[task_type][duration] - 1
        )
        self.priority_counts_by_type[task_type][priority] = max(
            0, self.priority_counts_by_type[task_type][priority] - 1
        )
    
    def get_time_of_day_distribution(self, task_type: str) -> Dict[str, float]:
        """
        Get empirical distribution of PreferredTimeOfDay for a task type.
        
        Args:
            task_type: Task type (Meeting, Training, Studies)
        
        Returns:
            Dictionary mapping PreferredTimeOfDay states to frequencies
        """
        hour_counts = self.hour_counts_by_type.get(task_type, {})
        
        # Aggregate hours into time-of-day bins
        time_counts = defaultdict(int)
        for hour, count in hour_counts.items():
            time_of_day = map_hour_to_time_of_day(hour)
            time_counts[time_of_day] += count
        
        # Convert to distribution
        total = sum(time_counts.values())
        if total == 0:
            return {}
        
        return {state: count / total for state, count in time_counts.items()}
    
    def get_day_type_distribution(self, task_type: str) -> Dict[str, float]:
        """
        Get empirical distribution of PreferredDayType for a task type.
        
        Args:
            task_type: Task type
        
        Returns:
            Dictionary mapping PreferredDayType states to frequencies
        """
        weekday_counts = self.weekday_counts_by_type.get(task_type, {})
        
        # Aggregate weekdays into day types
        day_type_counts = defaultdict(int)
        for weekday, count in weekday_counts.items():
            day_type = map_weekday_to_day_type(weekday)
            day_type_counts[day_type] += count
        
        # Convert to distribution
        total = sum(day_type_counts.values())
        if total == 0:
            return {}
        
        return {state: count / total for state, count in day_type_counts.items()}
    
    def get_average_duration(self, task_type: str) -> Optional[int]:
        """
        Get average task duration for a task type.
        
        Args:
            task_type: Task type
        
        Returns:
            Average duration in minutes, or None if no data
        """
        duration_counts = self.duration_counts_by_type.get(task_type, {})
        
        if not duration_counts:
            return None
        
        total_minutes = sum(duration * count for duration, count in duration_counts.items())
        total_tasks = sum(duration_counts.values())
        
        return int(total_minutes / total_tasks) if total_tasks > 0 else None
    
    def get_most_common_priority(self, task_type: str) -> Optional[str]:
        """
        Get most frequently used priority for a task type.
        
        Args:
            task_type: Task type
        
        Returns:
            Priority string (LOW/MEDIUM/HIGH) or None if no data
        """
        priority_counts = self.priority_counts_by_type.get(task_type, {})
        
        if not priority_counts:
            return None
        
        return max(priority_counts.items(), key=lambda x: x[1])[0]


def update_network_from_statistics(
    network: BayesianNetwork,
    stats: HistoricalStatistics,
    task_type: str
) -> None:
    """
    Update CPT parameters for Layer 3 prediction nodes based on statistics.
    
    This modifies the CPTs to incorporate learned distributions from
    observed tasks, blending with the priors from Layer 1/2.
    
    Args:
        network: The Bayesian Network to update
        stats: Accumulated statistics from observations
        task_type: Specific task type to update (Meeting/Training/Studies)
    
    Note:
        This function modifies the network in-place. It only updates
        Layer 3 nodes (PreferredTimeOfDay, PreferredDayType, etc.)
    """
    # Update PreferredTimeOfDay distribution
    time_dist = stats.get_time_of_day_distribution(task_type)
    if time_dist:
        # Store as auxiliary data that CPT function can access
        # (The CPT function in bn_nodes.py can use this via historical_dist parameter)
        node_name = f"PreferredTimeOfDay_{task_type}"
        node = network.get_node(node_name)
        if node and node.cpt:
            # Store historical distribution as metadata on the node
            if not hasattr(node, 'historical_data'):
                node.historical_data = {}
            node.historical_data['time_dist'] = time_dist
    
    # Update PreferredDayType distribution
    day_dist = stats.get_day_type_distribution(task_type)
    if day_dist:
        node_name = f"PreferredDayType_{task_type}"
        node = network.get_node(node_name)
        if node and node.cpt:
            if not hasattr(node, 'historical_data'):
                node.historical_data = {}
            node.historical_data['day_dist'] = day_dist
    
    # Update ExpectedDuration
    avg_duration = stats.get_average_duration(task_type)
    if avg_duration:
        node_name = f"ExpectedDuration_{task_type}"
        node = network.get_node(node_name)
        if node:
            if not hasattr(node, 'historical_data'):
                node.historical_data = {}
            node.historical_data['avg_duration'] = avg_duration
    
    # Update ExpectedPriority
    common_priority = stats.get_most_common_priority(task_type)
    if common_priority:
        node_name = f"ExpectedPriority_{task_type}"
        node = network.get_node(node_name)
        if node:
            if not hasattr(node, 'historical_data'):
                node.historical_data = {}
            node.historical_data['common_priority'] = common_priority


def recompute_all_cpts_from_observations(
    network: BayesianNetwork,
    observations: List[Dict]
) -> None:
    """
    Recompute all CPT parameters from scratch given all observations.
    
    Used when initializing a BN from existing tasks or when rebuilding
    after structural changes.
    
    Args:
        network: The Bayesian Network
        observations: List of all task observation dicts
    """
    # Build statistics from all observations
    stats = HistoricalStatistics()
    for obs in observations:
        stats.add_observation(obs)
    
    # Update network for each task type
    for task_type in ["Meeting", "Training", "Studies"]:
        update_network_from_statistics(network, stats, task_type)
