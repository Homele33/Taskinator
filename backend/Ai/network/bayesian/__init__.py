"""
Bayesian Network learning system for Taskinator.

This package provides a complete Bayesian Network implementation for learning
user task preferences and predicting optimal scheduling times.

Main entry point: UserBayesianNetwork class from bn_user_network module.
"""

from .bn_user_network import UserBayesianNetwork

__all__ = ["UserBayesianNetwork"]
