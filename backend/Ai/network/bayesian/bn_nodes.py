"""
Node definitions for user preference Bayesian Network.

This module defines all nodes (random variables) in the user preference BN,
including their possible states and CPT logic. The network has three layers:

Layer 1 (Evidence): Observable preferences from UserPreferences table
Layer 2 (Latent): Inferred user traits and patterns
Layer 3 (Predictions): Task-specific scheduling preferences

Type Definitions:
    All node state enums and CPT functions for the user preference network
"""

from __future__ import annotations
from typing import Dict, Optional, Tuple
from datetime import time as Time
from enum import Enum


# =============================================================================
# LAYER 1: Evidence Nodes (from UserPreferences table)
# =============================================================================

class WorkdayWindowState(str, Enum):
    """Discretized work hour preferences."""
    NONE = "NONE"  # No preference specified
    EARLY_BIRD = "EARLY_BIRD"  # Starts before 8 AM
    STANDARD = "STANDARD"  # 8-10 AM start
    NIGHT_OWL = "NIGHT_OWL"  # Starts after 10 AM or ends after 8 PM
    FLEXIBLE = "FLEXIBLE"  # Very wide window (>12 hours)


class FocusPeakState(str, Enum):
    """When user reports peak focus hours."""
    MORNING = "MORNING"  # Before noon
    AFTERNOON = "AFTERNOON"  # 12-5 PM
    EVENING = "EVENING"  # After 5 PM
    NONE = "NONE"  # No preference


class DaysOffPattern(str, Enum):
    """Pattern of days user takes off."""
    NO_DAYS_OFF = "NO_DAYS_OFF"  # Empty list
    WEEKEND_ONLY = "WEEKEND_ONLY"  # Saturday/Sunday
    MIXED = "MIXED"  # 1-2 non-weekend days
    HEAVY = "HEAVY"  # 3+ days off


class FlexibilityLevel(str, Enum):
    """How flexible user is with scheduling."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class DeadlineBehaviorType(str, Enum):
    """How user approaches deadlines."""
    EARLY = "EARLY"
    ON_TIME = "ON_TIME"
    LAST_MINUTE = "LAST_MINUTE"
    UNKNOWN = "UNKNOWN"


class DurationPreference(str, Enum):
    """Preferred task duration."""
    SHORT = "SHORT"  # ≤45 min
    MEDIUM = "MEDIUM"  # 45-90 min
    LONG = "LONG"  # >90 min


# =============================================================================
# LAYER 2: Latent Trait Nodes (inferred from evidence)
# =============================================================================

class UserPersona(str, Enum):
    """High-level user work style."""
    STRUCTURED = "STRUCTURED"  # Rigid schedule, low flexibility
    ADAPTIVE = "ADAPTIVE"  # Medium flexibility, balanced
    SPONTANEOUS = "SPONTANEOUS"  # High flexibility, loose schedule
    WORKAHOLIC = "WORKAHOLIC"  # Works all hours, no clear boundaries


class EnergyPattern(str, Enum):
    """When user is most productive."""
    FRONT_LOADED = "FRONT_LOADED"  # Morning person
    BALANCED = "BALANCED"  # Consistent throughout day
    BACK_LOADED = "BACK_LOADED"  # Evening person


class TaskBatchingPreference(str, Enum):
    """Preference for task block sizes."""
    PREFERS_SINGLE = "PREFERS_SINGLE"  # Short, discrete tasks
    PREFERS_BATCHING = "PREFERS_BATCHING"  # Long focused blocks


class PlanningHorizon(str, Enum):
    """How far ahead user plans."""
    SHORT_TERM = "SHORT_TERM"  # Last minute
    MEDIUM_TERM = "MEDIUM_TERM"  # Few days ahead
    LONG_TERM = "LONG_TERM"  # Week+ ahead


# =============================================================================
# LAYER 3: Task Prediction Nodes (what we want to infer)
# =============================================================================

class PreferredTimeOfDay(str, Enum):
    """Preferred time for scheduling a task."""
    MORNING = "MORNING"  # 6-12
    MIDDAY = "MIDDAY"  # 12-2
    AFTERNOON = "AFTERNOON"  # 2-5
    EVENING = "EVENING"  # 5-9
    NIGHT = "NIGHT"  # After 9


class PreferredDayType(str, Enum):
    """Preferred day type for task."""
    WEEKDAY = "WEEKDAY"
    WEEKEND = "WEEKEND"
    ANY = "ANY"


# =============================================================================
# CPT Functions (Conditional Probability Tables)
# =============================================================================

def cpt_user_persona(
    persona: str,
    parent_values: Dict[str, str]
) -> float:
    """
    P(UserPersona | FlexibilityLevel, WorkdayWindow, DaysOffPattern).
    
    Logic:
    - STRUCTURED: LOW flexibility + STANDARD window + WEEKEND_ONLY days
    - ADAPTIVE: MEDIUM flexibility + any window
    - SPONTANEOUS: HIGH flexibility + FLEXIBLE window
    - WORKAHOLIC: FLEXIBLE window + NO_DAYS_OFF
    
    Args:
        persona: UserPersona state to query
        parent_values: Dict with keys "FlexibilityLevel", "WorkdayWindow", "DaysOffPattern"
    
    Returns:
        Probability in [0, 1]
    """
    flexibility = parent_values.get("FlexibilityLevel", "UNKNOWN")
    workday = parent_values.get("WorkdayWindow", "NONE")
    days_off = parent_values.get("DaysOffPattern", "NO_DAYS_OFF")
    
    # Default uniform
    probs = {p.value: 0.25 for p in UserPersona}
    
    # STRUCTURED: low flex, standard hours, weekend off
    if flexibility == "LOW" and workday == "STANDARD" and days_off == "WEEKEND_ONLY":
        probs["STRUCTURED"] = 0.7
        probs["ADAPTIVE"] = 0.2
        probs["SPONTANEOUS"] = 0.05
        probs["WORKAHOLIC"] = 0.05
    
    # ADAPTIVE: medium flex
    elif flexibility == "MEDIUM":
        probs["STRUCTURED"] = 0.2
        probs["ADAPTIVE"] = 0.6
        probs["SPONTANEOUS"] = 0.15
        probs["WORKAHOLIC"] = 0.05
    
    # SPONTANEOUS: high flex, flexible window
    elif flexibility == "HIGH" and workday in ("FLEXIBLE", "NONE"):
        probs["STRUCTURED"] = 0.05
        probs["ADAPTIVE"] = 0.2
        probs["SPONTANEOUS"] = 0.7
        probs["WORKAHOLIC"] = 0.05
    
    # WORKAHOLIC: flexible + no days off
    elif workday == "FLEXIBLE" and days_off == "NO_DAYS_OFF":
        probs["STRUCTURED"] = 0.1
        probs["ADAPTIVE"] = 0.15
        probs["SPONTANEOUS"] = 0.15
        probs["WORKAHOLIC"] = 0.6
    
    return probs.get(persona, 0.25)


def cpt_energy_pattern(
    energy: str,
    parent_values: Dict[str, str]
) -> float:
    """
    P(EnergyPattern | FocusPeakState, WorkdayWindow).
    
    Logic:
    - FRONT_LOADED: MORNING focus + EARLY_BIRD workday
    - BALANCED: AFTERNOON focus or NONE
    - BACK_LOADED: EVENING focus + NIGHT_OWL workday
    
    Args:
        energy: EnergyPattern state
        parent_values: Dict with "FocusPeakState", "WorkdayWindow"
    
    Returns:
        Probability in [0, 1]
    """
    focus = parent_values.get("FocusPeakState", "NONE")
    workday = parent_values.get("WorkdayWindow", "NONE")
    
    probs = {e.value: 0.33 for e in EnergyPattern}
    
    if focus == "MORNING" and workday == "EARLY_BIRD":
        probs["FRONT_LOADED"] = 0.7
        probs["BALANCED"] = 0.2
        probs["BACK_LOADED"] = 0.1
    elif focus == "EVENING" or workday == "NIGHT_OWL":
        probs["FRONT_LOADED"] = 0.1
        probs["BALANCED"] = 0.2
        probs["BACK_LOADED"] = 0.7
    elif focus == "AFTERNOON" or focus == "NONE":
        probs["FRONT_LOADED"] = 0.25
        probs["BALANCED"] = 0.5
        probs["BACK_LOADED"] = 0.25
    
    return probs.get(energy, 0.33)


def cpt_task_batching_pref(
    batching: str,
    parent_values: Dict[str, str]
) -> float:
    """
    P(TaskBatchingPreference | DurationPreference, FlexibilityLevel).
    
    Logic:
    - PREFERS_BATCHING: LONG duration + LOW flexibility (wants focus time)
    - PREFERS_SINGLE: SHORT/MEDIUM + HIGH flexibility
    
    Args:
        batching: TaskBatchingPreference state
        parent_values: Dict with "DurationPreference", "FlexibilityLevel"
    
    Returns:
        Probability in [0, 1]
    """
    duration = parent_values.get("DurationPreference", "MEDIUM")
    flexibility = parent_values.get("FlexibilityLevel", "UNKNOWN")
    
    probs = {"PREFERS_SINGLE": 0.5, "PREFERS_BATCHING": 0.5}
    
    if duration == "LONG" and flexibility == "LOW":
        probs["PREFERS_BATCHING"] = 0.8
        probs["PREFERS_SINGLE"] = 0.2
    elif duration == "SHORT" and flexibility == "HIGH":
        probs["PREFERS_SINGLE"] = 0.8
        probs["PREFERS_BATCHING"] = 0.2
    elif duration == "MEDIUM":
        probs["PREFERS_SINGLE"] = 0.55
        probs["PREFERS_BATCHING"] = 0.45
    
    return probs.get(batching, 0.5)


def cpt_planning_horizon(
    horizon: str,
    parent_values: Dict[str, str]
) -> float:
    """
    P(PlanningHorizon | DeadlineBehavior, FlexibilityLevel).
    
    Logic:
    - SHORT_TERM: LAST_MINUTE + HIGH flexibility
    - MEDIUM_TERM: ON_TIME + MEDIUM flexibility
    - LONG_TERM: EARLY + LOW flexibility
    
    Args:
        horizon: PlanningHorizon state
        parent_values: Dict with "DeadlineBehavior", "FlexibilityLevel"
    
    Returns:
        Probability in [0, 1]
    """
    deadline = parent_values.get("DeadlineBehavior", "UNKNOWN")
    flexibility = parent_values.get("FlexibilityLevel", "UNKNOWN")
    
    probs = {h.value: 0.33 for h in PlanningHorizon}
    
    if deadline == "LAST_MINUTE" or flexibility == "HIGH":
        probs["SHORT_TERM"] = 0.6
        probs["MEDIUM_TERM"] = 0.3
        probs["LONG_TERM"] = 0.1
    elif deadline == "EARLY" or flexibility == "LOW":
        probs["SHORT_TERM"] = 0.1
        probs["MEDIUM_TERM"] = 0.3
        probs["LONG_TERM"] = 0.6
    else:  # ON_TIME or MEDIUM
        probs["SHORT_TERM"] = 0.2
        probs["MEDIUM_TERM"] = 0.6
        probs["LONG_TERM"] = 0.2
    
    return probs.get(horizon, 0.33)


def cpt_preferred_time_of_day(
    time_of_day: str,
    parent_values: Dict[str, str],
    historical_dist: Optional[Dict[str, float]] = None
) -> float:
    """
    P(PreferredTimeOfDay | EnergyPattern, UserPersona, HistoricalData).
    
    Combines energy pattern (40%), historical hour distribution (50%),
    and persona defaults (10%).
    
    Args:
        time_of_day: PreferredTimeOfDay state
        parent_values: Dict with "EnergyPattern", "UserPersona"
        historical_dist: Optional dict mapping time_of_day -> frequency
    
    Returns:
        Probability in [0, 1]
    """
    energy = parent_values.get("EnergyPattern", "BALANCED")
    persona = parent_values.get("UserPersona", "ADAPTIVE")
    
    # Base distribution from energy pattern
    if energy == "FRONT_LOADED":
        energy_probs = {
            "MORNING": 0.5, "MIDDAY": 0.2, "AFTERNOON": 0.2,
            "EVENING": 0.05, "NIGHT": 0.05
        }
    elif energy == "BACK_LOADED":
        energy_probs = {
            "MORNING": 0.1, "MIDDAY": 0.15, "AFTERNOON": 0.25,
            "EVENING": 0.4, "NIGHT": 0.1
        }
    else:  # BALANCED
        energy_probs = {
            "MORNING": 0.25, "MIDDAY": 0.2, "AFTERNOON": 0.3,
            "EVENING": 0.2, "NIGHT": 0.05
        }
    
    # Persona adjustment
    persona_weight = 0.1
    if persona == "WORKAHOLIC":
        persona_probs = {
            "MORNING": 0.25, "MIDDAY": 0.2, "AFTERNOON": 0.25,
            "EVENING": 0.2, "NIGHT": 0.1
        }
    else:
        persona_probs = energy_probs  # Use energy as default
    
    # Historical data (if available)
    hist_weight = 0.5 if historical_dist else 0.0
    energy_weight = 0.4 + (0.5 if not historical_dist else 0.0)
    
    # Combine
    prob = energy_weight * energy_probs.get(time_of_day, 0.2)
    prob += persona_weight * persona_probs.get(time_of_day, 0.2)
    
    if historical_dist:
        prob += hist_weight * historical_dist.get(time_of_day, 0.0)
    
    return prob


def cpt_preferred_day_type(
    day_type: str,
    parent_values: Dict[str, str],
    historical_dist: Optional[Dict[str, float]] = None
) -> float:
    """
    P(PreferredDayType | DaysOffPattern, HistoricalData).
    
    Args:
        day_type: PreferredDayType state
        parent_values: Dict with "DaysOffPattern"
        historical_dist: Optional dict mapping day_type -> frequency
    
    Returns:
        Probability in [0, 1]
    """
    days_off = parent_values.get("DaysOffPattern", "NO_DAYS_OFF")
    
    # Base priors
    if days_off == "WEEKEND_ONLY":
        probs = {"WEEKDAY": 0.8, "WEEKEND": 0.05, "ANY": 0.15}
    elif days_off == "NO_DAYS_OFF":
        probs = {"WEEKDAY": 0.45, "WEEKEND": 0.45, "ANY": 0.1}
    else:
        probs = {"WEEKDAY": 0.6, "WEEKEND": 0.3, "ANY": 0.1}
    
    # Mix with historical if available
    if historical_dist:
        for dt in probs:
            probs[dt] = 0.4 * probs[dt] + 0.6 * historical_dist.get(dt, 0.33)
    
    return probs.get(day_type, 0.33)


# =============================================================================
# Helper Functions
# =============================================================================

def extract_workday_window_state(
    start: Optional[Time],
    end: Optional[Time]
) -> WorkdayWindowState:
    """
    Convert workday time range to discrete state.
    
    Args:
        start: workday_pref_start from UserPreferences
        end: workday_pref_end from UserPreferences
    
    Returns:
        WorkdayWindowState enum value
    """
    if not start or not end:
        return WorkdayWindowState.NONE
    
    # Calculate span in hours
    start_hour = start.hour + start.minute / 60.0
    end_hour = end.hour + end.minute / 60.0
    span = end_hour - start_hour
    
    if span > 12:
        return WorkdayWindowState.FLEXIBLE
    elif start_hour < 8:
        return WorkdayWindowState.EARLY_BIRD
    elif start_hour > 10 or end_hour > 20:
        return WorkdayWindowState.NIGHT_OWL
    else:
        return WorkdayWindowState.STANDARD


def extract_focus_peak_state(
    start: Optional[Time],
    end: Optional[Time]
) -> FocusPeakState:
    """
    Convert focus peak time range to discrete state.
    
    Args:
        start: focus_peak_start from UserPreferences
        end: focus_peak_end from UserPreferences
    
    Returns:
        FocusPeakState enum value
    """
    if not start:
        return FocusPeakState.NONE
    
    hour = start.hour
    if hour < 12:
        return FocusPeakState.MORNING
    elif hour < 17:
        return FocusPeakState.AFTERNOON
    else:
        return FocusPeakState.EVENING


def extract_days_off_pattern(days_off: list) -> DaysOffPattern:
    """
    Convert days_off list to discrete pattern.
    
    Args:
        days_off: List of integers 0-6 (Sun-Sat)
    
    Returns:
        DaysOffPattern enum value
    """
    if not days_off:
        return DaysOffPattern.NO_DAYS_OFF
    
    # Check for weekend (Sun=0, Sat=6)
    is_weekend_only = set(days_off).issubset({0, 6})
    
    if len(days_off) >= 3:
        return DaysOffPattern.HEAVY
    elif is_weekend_only:
        return DaysOffPattern.WEEKEND_ONLY
    else:
        return DaysOffPattern.MIXED


def extract_duration_preference(default_duration: int) -> DurationPreference:
    """
    Convert default_duration_minutes to discrete preference.
    
    Args:
        default_duration: default_duration_minutes from UserPreferences
    
    Returns:
        DurationPreference enum value
    """
    if default_duration <= 45:
        return DurationPreference.SHORT
    elif default_duration <= 90:
        return DurationPreference.MEDIUM
    else:
        return DurationPreference.LONG
