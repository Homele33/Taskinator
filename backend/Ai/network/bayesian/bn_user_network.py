"""
User-specific Bayesian Network wrapper.

This module provides the main UserBayesianNetwork class, which is the primary
interface for working with the BN learning system. Each user has their own
independent BN that learns from their preferences and task history.

Main Class:
    UserBayesianNetwork: Complete BN system for a single user

Usage Example:
    # Initialize BN for user
    bn = UserBayesianNetwork(user_id=1)
    bn.initialize_from_preferences(user_prefs)
    
    # Update from task
    bn.update_from_task(task_observation)
    
    # Get predictions
    score = bn.predict_slot_score("Meeting", datetime.now(), datetime.now() + timedelta(hours=1))
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, time as Time
from models import UserPreferences

from .bn_core import BayesianNetwork, BNNode, CPT
from .bn_nodes import (
    # Layer 1 states
    WorkdayWindowState, FocusPeakState, DaysOffPattern,
    FlexibilityLevel, DeadlineBehaviorType, DurationPreference,
    # Layer 2 states
    UserPersona, EnergyPattern, TaskBatchingPreference, PlanningHorizon,
    # Layer 3 states
    PreferredTimeOfDay, PreferredDayType,
    # CPT functions
    cpt_user_persona, cpt_energy_pattern, cpt_task_batching_pref,
    cpt_planning_horizon, cpt_preferred_time_of_day, cpt_preferred_day_type,
    # Helper functions
    extract_workday_window_state, extract_focus_peak_state,
    extract_days_off_pattern, extract_duration_preference
)
from .bn_inference import (
    infer_most_likely_state, compute_node_distribution,
    infer_all_latent_nodes, compute_map_assignment
)
from .bn_learning import (
    HistoricalStatistics, update_network_from_statistics,
    recompute_all_cpts_from_observations, map_hour_to_time_of_day
)
from .bn_persistence import (
    save_bn_state, load_bn_state, bn_exists, get_bn_file_path
)


class UserBayesianNetwork:
    """
    Complete Bayesian Network system for a single user.
    
    This class manages:
    - Network structure (nodes and CPTs)
    - Evidence from UserPreferences
    - Learning from task observations
    - Predictions for scheduling
    - Persistence to/from disk
    
    Attributes:
        user_id: User identifier
        network: The underlying BayesianNetwork
        observations: List of all task observations used for training
        statistics: Aggregated statistics for learning
        is_initialized: Whether network has been set up
    """
    
    def __init__(self, user_id: int):
        """
        Initialize user's BN (loads from disk if exists).
        
        Args:
            user_id: User identifier
        """
        self.user_id = user_id
        self.network: Optional[BayesianNetwork] = None
        self.observations: List[Dict] = []
        self.statistics: HistoricalStatistics = HistoricalStatistics()
        self.is_initialized = False
        
        # Try to load existing BN
        self._load_from_disk()
    
    def _load_from_disk(self) -> bool:
        """
        Load BN state from disk if it exists.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not bn_exists(self.user_id):
            return False
        
        data = load_bn_state(self.user_id)
        if not data:
            return False
        
        try:
            # Load observations
            self.observations = data.get("observations", [])
            
            # Rebuild statistics from observations
            self.statistics = HistoricalStatistics()
            for obs in self.observations:
                self.statistics.add_observation(obs)
            
            # CRITICAL FIX: Rebuild the network structure
            # The network structure must exist for is_trained() to return True
            self.network = self._build_network_structure()
            
            # Restore evidence from saved state
            saved_evidence = data.get("network_structure", {}).get("evidence", {})
            for node_name, value in saved_evidence.items():
                try:
                    self.network.set_evidence(node_name, value)
                except Exception as e:
                    print(f"[BN] Warning: Could not restore evidence for {node_name}: {e}")
            
            # Recompute learned CPTs from observations
            if self.observations:
                from .bn_learning import recompute_all_cpts_from_observations
                recompute_all_cpts_from_observations(self.network, self.observations)
            
            self.is_initialized = True
            return True
        
        except Exception as e:
            print(f"[BN] Failed to load network for user {self.user_id}: {e}")
            return False
    
    def initialize_from_preferences(self, prefs: UserPreferences) -> None:
        """
        Initialize the BN from user preferences.
        
        This sets up the network structure, sets Layer 1 evidence,
        and saves the initial state to disk.
        
        Args:
            prefs: UserPreferences model instance
        
        Raises:
            ValueError: If initialization fails
        """
        # Build network structure
        self.network = self._build_network_structure()
        
        # Set evidence from preferences
        self._set_evidence_from_preferences(prefs)
        
        # Mark as initialized
        self.is_initialized = True
        
        # Save to disk
        self._save_to_disk()
    
    def _build_network_structure(self) -> BayesianNetwork:
        """
        Build the complete BN structure with all nodes and CPTs.
        
        Returns:
            Initialized BayesianNetwork
        """
        network = BayesianNetwork()
        
        # =================================================================
        # LAYER 1: Evidence nodes (from UserPreferences)
        # =================================================================
        
        workday_node = BNNode(
            "WorkdayWindow",
            [s.value for s in WorkdayWindowState],
            parents=[]
        )
        network.add_node(workday_node)
        
        focus_node = BNNode(
            "FocusPeakState",
            [s.value for s in FocusPeakState],
            parents=[]
        )
        network.add_node(focus_node)
        
        days_off_node = BNNode(
            "DaysOffPattern",
            [s.value for s in DaysOffPattern],
            parents=[]
        )
        network.add_node(days_off_node)
        
        flexibility_node = BNNode(
            "FlexibilityLevel",
            [s.value for s in FlexibilityLevel],
            parents=[]
        )
        network.add_node(flexibility_node)
        
        deadline_node = BNNode(
            "DeadlineBehavior",
            [s.value for s in DeadlineBehaviorType],
            parents=[]
        )
        network.add_node(deadline_node)
        
        duration_pref_node = BNNode(
            "DurationPreference",
            [s.value for s in DurationPreference],
            parents=[]
        )
        network.add_node(duration_pref_node)
        
        # =================================================================
        # LAYER 2: Latent trait nodes
        # =================================================================
        
        persona_node = BNNode(
            "UserPersona",
            [s.value for s in UserPersona],
            parents=[flexibility_node, workday_node, days_off_node]
        )
        persona_node.set_cpt(CPT(persona_node, func=cpt_user_persona))
        network.add_node(persona_node)
        
        energy_node = BNNode(
            "EnergyPattern",
            [s.value for s in EnergyPattern],
            parents=[focus_node, workday_node]
        )
        energy_node.set_cpt(CPT(energy_node, func=cpt_energy_pattern))
        network.add_node(energy_node)
        
        batching_node = BNNode(
            "TaskBatchingPreference",
            [s.value for s in TaskBatchingPreference],
            parents=[duration_pref_node, flexibility_node]
        )
        batching_node.set_cpt(CPT(batching_node, func=cpt_task_batching_pref))
        network.add_node(batching_node)
        
        horizon_node = BNNode(
            "PlanningHorizon",
            [s.value for s in PlanningHorizon],
            parents=[deadline_node, flexibility_node]
        )
        horizon_node.set_cpt(CPT(horizon_node, func=cpt_planning_horizon))
        network.add_node(horizon_node)
        
        # =================================================================
        # LAYER 3: Task prediction nodes (one set per task type)
        # =================================================================
        
        for task_type in ["Meeting", "Training", "Studies"]:
            # PreferredTimeOfDay for this task type
            time_node = BNNode(
                f"PreferredTimeOfDay_{task_type}",
                [s.value for s in PreferredTimeOfDay],
                parents=[energy_node, persona_node]
            )
            # CPT will be set with historical data later
            time_node.set_cpt(CPT(time_node, func=lambda state, parents, tt=task_type: 
                self._time_cpt_with_history(state, parents, tt)))
            network.add_node(time_node)
            
            # PreferredDayType for this task type
            day_node = BNNode(
                f"PreferredDayType_{task_type}",
                [s.value for s in PreferredDayType],
                parents=[days_off_node]
            )
            day_node.set_cpt(CPT(day_node, func=lambda state, parents, tt=task_type:
                self._day_cpt_with_history(state, parents, tt)))
            network.add_node(day_node)
        
        return network
    
    def _time_cpt_with_history(
        self,
        state: str,
        parent_values: Dict[str, str],
        task_type: str
    ) -> float:
        """
        CPT function for PreferredTimeOfDay that incorporates historical data.
        
        Args:
            state: PreferredTimeOfDay state
            parent_values: Parent node values
            task_type: Task type
        
        Returns:
            Probability
        """
        # Get historical distribution if available
        hist_dist = None
        if self.network:
            node = self.network.get_node(f"PreferredTimeOfDay_{task_type}")
            if node and hasattr(node, 'historical_data'):
                hist_dist = node.historical_data.get('time_dist')
        
        return cpt_preferred_time_of_day(state, parent_values, hist_dist)
    
    def _day_cpt_with_history(
        self,
        state: str,
        parent_values: Dict[str, str],
        task_type: str
    ) -> float:
        """
        CPT function for PreferredDayType that incorporates historical data.
        
        Args:
            state: PreferredDayType state
            parent_values: Parent node values
            task_type: Task type
        
        Returns:
            Probability
        """
        hist_dist = None
        if self.network:
            node = self.network.get_node(f"PreferredDayType_{task_type}")
            if node and hasattr(node, 'historical_data'):
                hist_dist = node.historical_data.get('day_dist')
        
        return cpt_preferred_day_type(state, parent_values, hist_dist)
    
    def _set_evidence_from_preferences(self, prefs: UserPreferences) -> None:
        """
        Extract evidence from UserPreferences and set in network.
        
        Args:
            prefs: UserPreferences model instance
        """
        if not self.network:
            return
        
        # WorkdayWindow
        workday_state = extract_workday_window_state(
            prefs.workday_pref_start,
            prefs.workday_pref_end
        )
        self.network.set_evidence("WorkdayWindow", workday_state.value)
        
        # FocusPeakState
        focus_state = extract_focus_peak_state(
            prefs.focus_peak_start,
            prefs.focus_peak_end
        )
        self.network.set_evidence("FocusPeakState", focus_state.value)
        
        # DaysOffPattern
        days_off_pattern = extract_days_off_pattern(prefs.days_off or [])
        self.network.set_evidence("DaysOffPattern", days_off_pattern.value)
        
        # FlexibilityLevel
        flexibility = prefs.flexibility or "UNKNOWN"
        self.network.set_evidence("FlexibilityLevel", flexibility)
        
        # DeadlineBehavior
        deadline = prefs.deadline_behavior or "UNKNOWN"
        self.network.set_evidence("DeadlineBehavior", deadline)
        
        # DurationPreference
        duration_pref = extract_duration_preference(prefs.default_duration_minutes)
        self.network.set_evidence("DurationPreference", duration_pref.value)
    
    def is_trained(self) -> bool:
        """
        Check if the BN is initialized and ready to use.
        
        Returns:
            True if BN is trained, False otherwise
        """
        return self.is_initialized and self.network is not None
    
    def update_from_task(self, task_obs: Dict) -> None:
        """
        Update BN from a task observation (create/update).
        
        This adds the observation to history, updates statistics,
        and recomputes Layer 3 CPTs.
        
        Args:
            task_obs: Task observation dict with keys:
                - user_id: int
                - task_type: str
                - priority: str
                - scheduled_start: datetime
                - scheduled_end: datetime
                - duration_minutes: int
        """
        if not self.is_trained():
            # Initialize network on-the-fly if needed
            # (This shouldn't happen if enforcement is correct, but handle gracefully)
            return
        
        # Add to observations
        self.observations.append(task_obs)
        
        # Update statistics
        self.statistics.add_observation(task_obs)
        
        # Update Layer 3 CPTs
        task_type = task_obs.get("task_type", "Meeting")
        update_network_from_statistics(self.network, self.statistics, task_type)
        
        # Save to disk
        self._save_to_disk()
    
    def remove_task(self, task_obs: Dict) -> None:
        """
        Remove a task observation (for deletions).
        
        Args:
            task_obs: Task observation dict (same format as update_from_task)
        """
        if not self.is_trained():
            return
        
        # Remove from statistics
        self.statistics.remove_observation(task_obs)
        
        # Rebuild from remaining observations
        # (Simpler than trying to selectively update)
        self.observations = [obs for obs in self.observations if obs != task_obs]
        
        # Recompute CPTs from scratch
        recompute_all_cpts_from_observations(self.network, self.observations)
        
        # Save
        self._save_to_disk()
    
    def predict_slot_score(
        self,
        task_type: str,
        slot_start: datetime,
        slot_end: datetime
    ) -> float:
        """
        Predict how good a time slot is for scheduling a task.
        
        This is the main prediction interface used by suggest_slots.
        Returns a score in [0..10] where higher is better.
        
        Args:
            task_type: Type of task (Meeting/Training/Studies)
            slot_start: Start datetime of the slot
            slot_end: End datetime of the slot
        
        Returns:
            Score in [0, 10]
        """
        if not self.is_trained():
            # Return neutral score if not trained
            return 5.0
        
        # Infer latent traits first (Layer 2)
        latent_states = infer_all_latent_nodes(self.network)
        
        # Query PreferredTimeOfDay for this task type
        time_node_name = f"PreferredTimeOfDay_{task_type}"
        time_dist = compute_node_distribution(self.network, time_node_name)
        
        # Map slot time to PreferredTimeOfDay state
        slot_time_state = map_hour_to_time_of_day(slot_start.hour)
        
        # Get probability for this time
        time_prob = time_dist.get(slot_time_state, 0.2)
        
        # Query PreferredDayType
        day_node_name = f"PreferredDayType_{task_type}"
        day_dist = compute_node_distribution(self.network, day_node_name)
        
        # Map slot weekday to PreferredDayType
        from .bn_learning import map_weekday_to_day_type
        slot_day_state = map_weekday_to_day_type(slot_start.weekday())
        day_prob = day_dist.get(slot_day_state, 0.33)
        
        # Combine probabilities into score [0..10]
        # Weight: 60% time-of-day, 40% day-type
        combined_prob = 0.6 * time_prob + 0.4 * day_prob
        
        # Scale to [0, 10]
        score = combined_prob * 10.0
        
        # Clamp to valid range
        return max(0.0, min(10.0, score))
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current BN status and metadata.
        
        Returns:
            Dictionary with keys:
                - user_id: int
                - is_trained: bool
                - num_observations: int
                - has_preferences: bool
                - latent_traits: dict (if trained)
        """
        status = {
            "user_id": self.user_id,
            "is_trained": self.is_trained(),
            "num_observations": len(self.observations),
            "has_preferences": bool(self.network and self.network.evidence)
        }
        
        if self.is_trained():
            # Infer current latent traits
            latent = infer_all_latent_nodes(self.network)
            status["latent_traits"] = {
                node: state for node, (state, prob) in latent.items()
                if node in ["UserPersona", "EnergyPattern", "TaskBatchingPreference", "PlanningHorizon"]
            }
        
        return status
    
    def _save_to_disk(self) -> None:
        """Save current BN state to disk."""
        if not self.network:
            return
        
        try:
            network_dict = self.network.to_dict()
            save_bn_state(
                user_id=self.user_id,
                network_dict=network_dict,
                observations=self.observations,
                metadata={
                    "num_observations": len(self.observations),
                    "is_initialized": self.is_initialized
                }
            )
        except Exception as e:
            print(f"[BN] Failed to save network for user {self.user_id}: {e}")
