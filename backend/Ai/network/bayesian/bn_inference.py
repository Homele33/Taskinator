"""
Inference engine for Bayesian Networks.

Provides algorithms for querying probabilities in a Bayesian Network:
- Forward inference: computing node states given evidence
- Maximum a posteriori (MAP): finding most likely state for a node
- Probability queries: computing P(node | evidence)

This implementation uses simplified forward sampling and enumeration,
suitable for small networks with discrete variables.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple
from .bn_core import BayesianNetwork, BNNode
import random


def infer_most_likely_state(
    network: BayesianNetwork,
    node_name: str,
    evidence: Optional[Dict[str, str]] = None
) -> Tuple[str, float]:
    """
    Find the most likely state for a node given evidence.
    
    Uses exact enumeration over all possible states of the query node,
    computing P(node=state | evidence) for each and returning the max.
    
    Args:
        network: The Bayesian Network
        node_name: Name of the node to query
        evidence: Dictionary of observed node values (merged with network.evidence)
    
    Returns:
        Tuple of (most_likely_state, probability)
    
    Raises:
        ValueError: If node doesn't exist
    """
    node = network.get_node(node_name)
    if not node:
        raise ValueError(f"Node {node_name} not found")
    
    # Merge evidence
    full_evidence = {**network.evidence, **(evidence or {})}
    
    # If this node is already in evidence, return that
    if node_name in full_evidence:
        return full_evidence[node_name], 1.0
    
    # Compute probability for each possible state
    state_probs = {}
    for state in node.states:
        prob = compute_posterior_probability(
            network, node_name, state, full_evidence
        )
        state_probs[state] = prob
    
    # Return state with highest probability
    if not state_probs:
        return node.states[0], 0.0
    
    best_state = max(state_probs.items(), key=lambda x: x[1])
    return best_state[0], best_state[1]


def compute_posterior_probability(
    network: BayesianNetwork,
    node_name: str,
    node_state: str,
    evidence: Optional[Dict[str, str]] = None
) -> float:
    """
    Compute P(node=node_state | evidence).
    
    For nodes with parents, this queries the CPT.
    For nodes without parents, returns the prior probability.
    
    Args:
        network: The Bayesian Network
        node_name: Name of the node
        node_state: Specific state to query
        evidence: Observed values for other nodes
    
    Returns:
        Probability in [0, 1]
    
    Raises:
        ValueError: If node doesn't exist
    """
    node = network.get_node(node_name)
    if not node:
        raise ValueError(f"Node {node_name} not found")
    
    if not node.cpt:
        # No CPT: uniform distribution
        return 1.0 / len(node.states) if node.states else 0.0
    
    # Merge evidence
    full_evidence = {**network.evidence, **(evidence or {})}
    
    # Build parent values from evidence or infer them
    parent_values = {}
    for parent in node.parents:
        if parent.name in full_evidence:
            parent_values[parent.name] = full_evidence[parent.name]
        else:
            # Parent not observed: use most likely state
            parent_state, _ = infer_most_likely_state(network, parent.name, full_evidence)
            parent_values[parent.name] = parent_state
    
    # Query CPT
    return node.cpt.get_probability(node_state, parent_values)


def infer_all_latent_nodes(
    network: BayesianNetwork,
    evidence: Optional[Dict[str, str]] = None
) -> Dict[str, Tuple[str, float]]:
    """
    Infer most likely states for all nodes not in evidence.
    
    Processes nodes in topological order to ensure parents are
    inferred before children.
    
    Args:
        network: The Bayesian Network
        evidence: Observed node values
    
    Returns:
        Dictionary mapping node_name -> (most_likely_state, probability)
    """
    full_evidence = {**network.evidence, **(evidence or {})}
    results = {}
    
    try:
        ordered_nodes = network.topological_sort()
    except ValueError:
        # Fallback if network has issues
        ordered_nodes = list(network.nodes.keys())
    
    for node_name in ordered_nodes:
        if node_name not in full_evidence:
            state, prob = infer_most_likely_state(network, node_name, full_evidence)
            results[node_name] = (state, prob)
            # Add to evidence for downstream nodes
            full_evidence[node_name] = state
    
    return results


def compute_node_distribution(
    network: BayesianNetwork,
    node_name: str,
    evidence: Optional[Dict[str, str]] = None
) -> Dict[str, float]:
    """
    Compute full probability distribution P(node | evidence).
    
    Returns probabilities for all possible states of the node.
    
    Args:
        network: The Bayesian Network
        node_name: Name of the node to query
        evidence: Observed values
    
    Returns:
        Dictionary mapping state -> probability
    
    Raises:
        ValueError: If node doesn't exist
    """
    node = network.get_node(node_name)
    if not node:
        raise ValueError(f"Node {node_name} not found")
    
    full_evidence = {**network.evidence, **(evidence or {})}
    
    # If node is in evidence, return delta distribution
    if node_name in full_evidence:
        return {
            state: (1.0 if state == full_evidence[node_name] else 0.0)
            for state in node.states
        }
    
    # Compute probability for each state
    distribution = {}
    for state in node.states:
        prob = compute_posterior_probability(network, node_name, state, full_evidence)
        distribution[state] = prob
    
    # Normalize
    total = sum(distribution.values())
    if total > 0:
        distribution = {s: p / total for s, p in distribution.items()}
    
    return distribution


def sample_network(
    network: BayesianNetwork,
    evidence: Optional[Dict[str, str]] = None,
    num_samples: int = 100
) -> List[Dict[str, str]]:
    """
    Generate samples from the network using forward sampling.
    
    Useful for approximate inference and debugging.
    
    Args:
        network: The Bayesian Network
        evidence: Fixed observed values
        num_samples: Number of samples to generate
    
    Returns:
        List of dictionaries, each representing one complete assignment
    """
    samples = []
    full_evidence = {**network.evidence, **(evidence or {})}
    
    try:
        ordered_nodes = network.topological_sort()
    except ValueError:
        ordered_nodes = list(network.nodes.keys())
    
    for _ in range(num_samples):
        sample = full_evidence.copy()
        
        for node_name in ordered_nodes:
            if node_name in sample:
                continue  # Already have evidence
            
            node = network.nodes[node_name]
            if not node.cpt:
                # No CPT: sample uniformly
                sample[node_name] = random.choice(node.states)
                continue
            
            # Get parent values from current sample
            parent_values = {p.name: sample[p.name] for p in node.parents if p.name in sample}
            
            # Compute distribution for this node
            dist = {
                state: node.cpt.get_probability(state, parent_values)
                for state in node.states
            }
            
            # Normalize
            total = sum(dist.values())
            if total > 0:
                dist = {s: p / total for s, p in dist.items()}
            else:
                dist = {s: 1.0 / len(node.states) for s in node.states}
            
            # Sample
            r = random.random()
            cumsum = 0.0
            for state, prob in dist.items():
                cumsum += prob
                if r <= cumsum:
                    sample[node_name] = state
                    break
        
        samples.append(sample)
    
    return samples


def compute_map_assignment(
    network: BayesianNetwork,
    evidence: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Find the maximum a posteriori (MAP) assignment.
    
    Returns the most likely complete assignment to all nodes
    given the evidence.
    
    Args:
        network: The Bayesian Network
        evidence: Observed values
    
    Returns:
        Dictionary mapping all node names to their MAP states
    """
    full_evidence = {**network.evidence, **(evidence or {})}
    assignment = full_evidence.copy()
    
    # Infer remaining nodes in topological order
    inferred = infer_all_latent_nodes(network, full_evidence)
    for node_name, (state, _) in inferred.items():
        assignment[node_name] = state
    
    return assignment
