# backend/Ai/network/inference.py
"""
Inference layer for Bayesian Network learning system.

This module provides the interface between route handlers and the BN system.
It maintains backward compatibility with the old UserPreferenceModel API
while using the new Bayesian Network internally.

Functions:
    - initialize_bn_for_user: Create BN from UserPreferences
    - is_bn_trained: Check if user's BN is ready
    - ensure_bn_initialized: Check BN readiness with lazy initialization for existing users
    - record_observation: Update BN from task creation
    - remove_observation: Update BN from task deletion
    - update_observation: Update BN from task modification
    - score_bonus_for_slot: Get BN prediction for a time slot
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict
from models import UserPreferences, db

# NEW: Bayesian Network system
from .bayesian import UserBayesianNetwork



# =============================================================================
# NEW: BN Initialization and Status Functions
# =============================================================================

def initialize_bn_for_user(user_id: int) -> bool:
    """
    Initialize Bayesian Network from UserPreferences.
    
    This should be called immediately after a user creates their preferences
    via PUT /api/preferences. It builds the BN structure and sets initial
    evidence from their stated preferences.
    
    Args:
        user_id: User ID
    
    Returns:
        True if initialization succeeded, False otherwise
    
    Raises:
        ValueError: If UserPreferences don't exist for this user
    """
    # Load user's preferences from DB
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        raise ValueError(f"No preferences found for user {user_id}")
    
    # Create BN instance
    bn = UserBayesianNetwork(user_id)
    
    # Initialize from preferences
    try:
        bn.initialize_from_preferences(prefs)
        return True
    except Exception as e:
        print(f"[BN] Failed to initialize BN for user {user_id}: {e}")
        return False


def is_bn_trained(user_id: int) -> bool:
    """
    Check if user's Bayesian Network is trained and ready to use.
    
    Args:
        user_id: User ID
    
    Returns:
        True if BN exists and is trained, False otherwise
    """
    try:
        bn = UserBayesianNetwork(user_id)
        return bn.is_trained()
    except Exception:
        return False


def ensure_bn_initialized(user_id: int) -> bool:
    """
    Ensure user's BN is initialized, with lazy initialization for existing users.
    
    This function handles the migration case where users created preferences
    before the BN system was added. It provides "lazy initialization":
    - If BN already exists → return True immediately
    - If no BN but UserPreferences exist → auto-initialize BN → return True
    - If no UserPreferences → return False (user must complete onboarding)
    
    This maintains the guard that new users without preferences are blocked,
    while allowing existing users to continue working after BN migration.
    
    Args:
        user_id: User ID
    
    Returns:
        True if BN is ready (exists or was just initialized), False if no preferences
    """
    # Fast path: BN already exists
    if is_bn_trained(user_id):
        return True
    
    # Check if user has preferences but no BN (migration case)
    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        # No preferences → user needs to complete onboarding
        return False
    
    # User has preferences but no BN → lazy initialization
    print(f"[BN] Lazy initialization for user {user_id} (preferences exist, BN missing)")
    try:
        success = initialize_bn_for_user(user_id)
        if success:
            print(f"[BN] Lazy initialization successful for user {user_id}")
            return True
        else:
            print(f"[BN] Lazy initialization failed for user {user_id}")
            return False
    except Exception as e:
        print(f"[BN] Lazy initialization error for user {user_id}: {e}")
        return False


def get_bn_status(user_id: int) -> Dict:
    """
    Get detailed status of user's BN.
    
    Args:
        user_id: User ID
    
    Returns:
        Status dictionary with training info and metadata
    """
    try:
        bn = UserBayesianNetwork(user_id)
        return bn.get_status()
    except Exception as e:
        return {
            "user_id": user_id,
            "is_trained": False,
            "error": str(e)
        }


# =============================================================================
# Predictions / Scoring (using BN)
# =============================================================================

def score_bonus_for_slot(
    user_id: int,
    task_type: str,
    slot_start: datetime,
    slot_end: datetime,
) -> float:
    """
    Get BN-based score for a time slot.
    
    This replaces the old statistical bonus with a full BN prediction.
    Returns a score representing how well this slot matches the user's
    learned preferences.
    
    Args:
        user_id: User ID
        task_type: Type of task (Meeting/Training/Studies)
        slot_start: Start datetime of slot
        slot_end: End datetime of slot
    
    Returns:
        Score bonus in [0..3] range (to match old scoring scale)
    """
    try:
        bn = UserBayesianNetwork(user_id)
        if not bn.is_trained():
            return 0.0
        
        # Get BN prediction [0..10]
        bn_score = bn.predict_slot_score(task_type, slot_start, slot_end)
        
        # Normalize to [0..3] bonus range
        # BN score 0-10 maps to bonus -1 to +2
        bonus = (bn_score - 5.0) / 5.0 * 1.5
        
        return max(-1.0, min(2.0, bonus))
    
    except Exception as e:
        print(f"[BN] score_bonus_for_slot failed: {e}")
        return 0.0



# =============================================================================
# Observation Management (BN Learning)
# =============================================================================

def record_observation(obs_dict: Dict) -> None:
    """
    Add a task observation to user's BN (called on task create).
    
    This updates the BN's learned parameters based on the user's
    actual scheduling choices.
    
    Args:
        obs_dict: Task observation dict with keys:
            - user_id: int
            - task_type: str
            - priority: str
            - scheduled_start: datetime
            - scheduled_end: datetime
            - duration_minutes: int
    """
    try:
        user_id = obs_dict.get("user_id")
        if not user_id:
            return
        
        bn = UserBayesianNetwork(user_id)
        if not bn.is_trained():
            print(f"[BN] Cannot record observation: BN not trained for user {user_id}")
            return
        
        bn.update_from_task(obs_dict)
    
    except Exception as e:
        print(f"[BN] record_observation failed: {e}")


def remove_observation(obs_dict: Dict) -> None:
    """
    Remove a task observation from user's BN (called on task delete).
    
    This decrements the BN's learned statistics to reflect the deletion.
    
    Args:
        obs_dict: Task observation dict (same format as record_observation)
    """
    try:
        user_id = obs_dict.get("user_id")
        if not user_id:
            return
        
        bn = UserBayesianNetwork(user_id)
        if not bn.is_trained():
            return
        
        bn.remove_task(obs_dict)
    
    except Exception as e:
        print(f"[BN] remove_observation failed: {e}")


def update_observation(before_dict: Dict, after_dict: Dict) -> None:
    """
    Update BN when a task is modified (called on task PATCH/PUT).
    
    This removes the old observation and adds the new one.
    
    Args:
        before_dict: Task state before update
        after_dict: Task state after update
    """
    try:
        user_id = before_dict.get("user_id")
        if not user_id:
            return
        
        bn = UserBayesianNetwork(user_id)
        if not bn.is_trained():
            return
        
        # Remove old observation
        bn.remove_task(before_dict)
        
        # Add new observation
        bn.update_from_task(after_dict)
    
    except Exception as e:
        print(f"[BN] update_observation failed: {e}")

