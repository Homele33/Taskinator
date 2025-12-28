"""
Persistence layer for Bayesian Networks.

Handles saving and loading BN state to/from JSON files.
Each user has a separate BN file stored in the data directory.

File format:
    {
        "user_id": 123,
        "network_structure": {...},
        "evidence": {...},
        "observations": [...],
        "metadata": {...}
    }
"""

from __future__ import annotations
from typing import Dict, Any, Optional
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime, date, time


# Data directory for BN files
DATA_DIR = Path(__file__).parent.parent / "data"


def get_bn_file_path(user_id: int) -> Path:
    """
    Get the file path for a user's BN state.
    
    Args:
        user_id: User ID
    
    Returns:
        Path object for the BN JSON file
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"bn_user_{user_id}.json"


def _serialize_datetime(obj):
    """Helper to serialize datetime objects to ISO format strings."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, time):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def save_bn_state(
    user_id: int,
    network_dict: Dict[str, Any],
    observations: list,
    metadata: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save BN state to disk atomically.
    
    Uses atomic write (write to temp file, then rename) to prevent
    corruption if the process crashes mid-write.
    
    Args:
        user_id: User ID
        network_dict: Serialized network structure (from network.to_dict())
        observations: List of all task observations used for training
        metadata: Optional metadata (e.g., last_updated, version)
    
    Returns:
        File path where state was saved
    
    Raises:
        IOError: If write fails
    """
    file_path = get_bn_file_path(user_id)
    
    # Prepare data structure
    data = {
        "user_id": user_id,
        "network_structure": network_dict,
        "observations": observations,
        "metadata": metadata or {}
    }
    
    # Atomic write: write to temp file, then rename
    temp_fd = None
    temp_path = None
    
    try:
        # Create temp file in same directory (ensures same filesystem)
        temp_fd, temp_path = tempfile.mkstemp(
            prefix=".bn_tmp_",
            suffix=".json",
            dir=file_path.parent
        )
        
        # Write JSON to temp file
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_serialize_datetime)
            temp_fd = None  # Closed by context manager
        
        # Atomic rename
        os.replace(temp_path, file_path)
        temp_path = None  # Successfully moved
        
        return str(file_path)
    
    finally:
        # Clean up temp file if something went wrong
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except Exception:
                pass
        
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


def _deserialize_observation(obs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert ISO string datetimes back to datetime objects in an observation.
    
    Args:
        obs: Observation dict with ISO string datetimes
    
    Returns:
        Observation dict with datetime objects
    """
    obs = obs.copy()
    
    # Convert datetime strings back to datetime objects
    for field in ['scheduled_start', 'scheduled_end']:
        if field in obs and obs[field] and isinstance(obs[field], str):
            try:
                obs[field] = datetime.fromisoformat(obs[field])
            except (ValueError, TypeError):
                obs[field] = None
    
    return obs


def load_bn_state(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Load BN state from disk.
    
    Args:
        user_id: User ID
    
    Returns:
        Dictionary with keys:
            - "user_id": int
            - "network_structure": dict
            - "observations": list
            - "metadata": dict
        Or None if file doesn't exist or is corrupted
    """
    file_path = get_bn_file_path(user_id)
    
    if not file_path.exists():
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validate structure
        if not isinstance(data, dict):
            return None
        
        if data.get("user_id") != user_id:
            # Mismatched user ID
            return None
        
        # Deserialize observations (convert ISO strings back to datetime objects)
        if "observations" in data and isinstance(data["observations"], list):
            data["observations"] = [
                _deserialize_observation(obs) 
                for obs in data["observations"]
            ]
        
        return data
    
    except (json.JSONDecodeError, IOError, OSError) as e:
        # Corrupted or unreadable file
        print(f"[BN Persistence] Failed to load BN for user {user_id}: {e}")
        return None


def bn_exists(user_id: int) -> bool:
    """
    Check if a BN file exists for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        True if BN file exists, False otherwise
    """
    return get_bn_file_path(user_id).exists()


def delete_bn_state(user_id: int) -> bool:
    """
    Delete a user's BN state file.
    
    Args:
        user_id: User ID
    
    Returns:
        True if deleted successfully, False if file didn't exist
    
    Raises:
        IOError: If deletion fails
    """
    file_path = get_bn_file_path(user_id)
    
    if not file_path.exists():
        return False
    
    try:
        file_path.unlink()
        return True
    except OSError as e:
        raise IOError(f"Failed to delete BN file: {e}")


def get_bn_metadata(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Load just the metadata from a BN file without loading the full network.
    
    Args:
        user_id: User ID
    
    Returns:
        Metadata dictionary or None if file doesn't exist
    """
    data = load_bn_state(user_id)
    if not data:
        return None
    
    return data.get("metadata", {})


def update_bn_metadata(user_id: int, metadata_updates: Dict[str, Any]) -> bool:
    """
    Update metadata fields without rewriting the entire BN.
    
    Args:
        user_id: User ID
        metadata_updates: Dictionary of metadata fields to update
    
    Returns:
        True if updated successfully, False if BN doesn't exist
    
    Raises:
        IOError: If read/write fails
    """
    data = load_bn_state(user_id)
    if not data:
        return False
    
    # Update metadata
    metadata = data.get("metadata", {})
    metadata.update(metadata_updates)
    data["metadata"] = metadata
    
    # Save back
    save_bn_state(
        user_id=user_id,
        network_dict=data["network_structure"],
        observations=data["observations"],
        metadata=metadata
    )
    
    return True
