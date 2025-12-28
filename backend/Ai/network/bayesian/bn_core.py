"""
Core Bayesian Network primitives.

This module provides the foundational classes for building and manipulating
Bayesian Networks: nodes, conditional probability tables (CPTs), and the
network structure itself.

Classes:
    BNNode: Represents a random variable in the network
    CPT: Conditional Probability Table for computing P(node | parents)
    BayesianNetwork: Complete network with nodes and inference capabilities
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Callable, Tuple
from collections import defaultdict
import copy


class BNNode:
    """
    Represents a node (random variable) in a Bayesian Network.
    
    A node has:
    - A unique name
    - A list of possible states (discrete values)
    - References to parent nodes
    - A CPT defining P(this node | parents)
    
    Attributes:
        name: Unique identifier for this node
        states: List of possible discrete values this node can take
        parents: List of parent BNNode objects
        cpt: Conditional Probability Table
    """
    
    def __init__(
        self,
        name: str,
        states: List[str],
        parents: Optional[List[BNNode]] = None
    ):
        """
        Initialize a Bayesian Network node.
        
        Args:
            name: Unique node identifier
            states: Possible discrete values (e.g., ["LOW", "MEDIUM", "HIGH"])
            parents: Parent nodes that this node depends on
        """
        self.name = name
        self.states = states
        self.parents = parents or []
        self.cpt: Optional[CPT] = None
    
    def set_cpt(self, cpt: CPT) -> None:
        """Attach a CPT to this node."""
        self.cpt = cpt
    
    def __repr__(self) -> str:
        parent_names = [p.name for p in self.parents]
        return f"BNNode({self.name}, states={self.states}, parents={parent_names})"


class CPT:
    """
    Conditional Probability Table for a Bayesian Network node.
    
    Stores P(node=state | parent_values) for all combinations of node states
    and parent configurations. Supports both:
    - Explicit tables (dict-based lookup)
    - Functional CPTs (computed on-the-fly via a function)
    
    Attributes:
        node: The BNNode this CPT belongs to
        table: Explicit probability table (if not using a function)
        func: Optional function to compute probabilities dynamically
    """
    
    def __init__(
        self,
        node: BNNode,
        table: Optional[Dict[Tuple, Dict[str, float]]] = None,
        func: Optional[Callable[[str, Dict[str, str]], float]] = None
    ):
        """
        Initialize a CPT.
        
        Args:
            node: The node this CPT describes
            table: Explicit probability table:
                   {(parent1_val, parent2_val, ...): {node_state: probability}}
            func: Function that computes P(node_state | parent_values)
                  Signature: func(node_state: str, parent_vals: Dict[str, str]) -> float
        
        Note: Either table or func must be provided, not both.
        """
        self.node = node
        self.table = table or {}
        self.func = func
        
        if not table and not func:
            # Initialize uniform distribution if nothing provided
            self._initialize_uniform()
    
    def _initialize_uniform(self) -> None:
        """Initialize CPT with uniform probabilities over all states."""
        num_states = len(self.node.states)
        uniform_prob = 1.0 / num_states if num_states > 0 else 0.0
        
        if not self.node.parents:
            # No parents: simple prior
            self.table[()] = {state: uniform_prob for state in self.node.states}
        else:
            # Has parents: generate all parent combinations
            parent_combos = self._generate_parent_combinations()
            for combo in parent_combos:
                self.table[combo] = {state: uniform_prob for state in self.node.states}
    
    def _generate_parent_combinations(self) -> List[Tuple[str, ...]]:
        """Generate all possible combinations of parent states."""
        if not self.node.parents:
            return [()]
        
        # Recursive generation of all combinations
        def _recurse(parent_idx: int) -> List[Tuple[str, ...]]:
            if parent_idx >= len(self.node.parents):
                return [()]
            
            parent = self.node.parents[parent_idx]
            sub_combos = _recurse(parent_idx + 1)
            result = []
            for state in parent.states:
                for sub in sub_combos:
                    result.append((state,) + sub)
            return result
        
        return _recurse(0)
    
    def get_probability(
        self,
        node_state: str,
        parent_values: Dict[str, str]
    ) -> float:
        """
        Get P(node=node_state | parent_values).
        
        Args:
            node_state: The value of this node to query
            parent_values: Dictionary mapping parent names to their values
        
        Returns:
            Probability in [0, 1]
        
        Raises:
            KeyError: If configuration not found in table
        """
        if self.func:
            # Use functional CPT
            return self.func(node_state, parent_values)
        
        # Build parent configuration tuple in same order as self.node.parents
        parent_config = tuple(
            parent_values.get(p.name, self.node.parents[0].states[0])
            for p in self.node.parents
        )
        
        # Lookup in table
        if parent_config not in self.table:
            # Fallback: uniform
            return 1.0 / len(self.node.states)
        
        return self.table[parent_config].get(node_state, 0.0)
    
    def set_probability(
        self,
        node_state: str,
        parent_values: Dict[str, str],
        probability: float
    ) -> None:
        """
        Set P(node=node_state | parent_values) = probability.
        
        Args:
            node_state: The node state to set
            parent_values: Parent configuration
            probability: New probability value
        
        Note: Only works for table-based CPTs, not functional ones.
        """
        if self.func:
            raise ValueError("Cannot set probabilities on functional CPTs")
        
        parent_config = tuple(
            parent_values.get(p.name, self.node.parents[0].states[0])
            for p in self.node.parents
        )
        
        if parent_config not in self.table:
            self.table[parent_config] = {}
        
        self.table[parent_config][node_state] = probability
    
    def normalize(self, parent_values: Dict[str, str]) -> None:
        """
        Normalize probabilities for a given parent configuration to sum to 1.0.
        
        Args:
            parent_values: Parent configuration to normalize
        """
        if self.func:
            return  # Can't normalize functional CPTs
        
        parent_config = tuple(
            parent_values.get(p.name, self.node.parents[0].states[0])
            for p in self.node.parents
        )
        
        if parent_config not in self.table:
            return
        
        total = sum(self.table[parent_config].values())
        if total > 0:
            for state in self.table[parent_config]:
                self.table[parent_config][state] /= total
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize CPT to dictionary for persistence."""
        return {
            "node_name": self.node.name,
            "table": {
                str(k): v for k, v in self.table.items()
            } if not self.func else {},
            "is_functional": self.func is not None
        }


class BayesianNetwork:
    """
    Complete Bayesian Network with nodes and structure.
    
    Represents a directed acyclic graph (DAG) of BNNodes with CPTs.
    Provides methods for:
    - Building the network structure
    - Setting evidence (observed values)
    - Running inference queries
    
    Attributes:
        nodes: Dictionary mapping node names to BNNode objects
        evidence: Currently observed values for some nodes
    """
    
    def __init__(self):
        """Initialize an empty Bayesian Network."""
        self.nodes: Dict[str, BNNode] = {}
        self.evidence: Dict[str, str] = {}
    
    def add_node(self, node: BNNode) -> None:
        """
        Add a node to the network.
        
        Args:
            node: BNNode to add
        
        Raises:
            ValueError: If node name already exists
        """
        if node.name in self.nodes:
            raise ValueError(f"Node {node.name} already exists in network")
        self.nodes[node.name] = node
    
    def get_node(self, name: str) -> Optional[BNNode]:
        """Get a node by name."""
        return self.nodes.get(name)
    
    def set_evidence(self, node_name: str, value: str) -> None:
        """
        Set evidence (observed value) for a node.
        
        Args:
            node_name: Name of the node
            value: Observed value (must be in node's states)
        
        Raises:
            ValueError: If node doesn't exist or value is invalid
        """
        node = self.nodes.get(node_name)
        if not node:
            raise ValueError(f"Node {node_name} not found")
        if value not in node.states:
            raise ValueError(f"Value {value} not in states for {node_name}")
        self.evidence[node_name] = value
    
    def clear_evidence(self, node_name: Optional[str] = None) -> None:
        """
        Clear evidence for a specific node or all nodes.
        
        Args:
            node_name: Node to clear evidence for, or None to clear all
        """
        if node_name:
            self.evidence.pop(node_name, None)
        else:
            self.evidence.clear()
    
    def get_children(self, node_name: str) -> List[BNNode]:
        """
        Get all child nodes (nodes that have this node as a parent).
        
        Args:
            node_name: Name of the parent node
        
        Returns:
            List of child BNNode objects
        """
        children = []
        for node in self.nodes.values():
            if any(p.name == node_name for p in node.parents):
                children.append(node)
        return children
    
    def topological_sort(self) -> List[str]:
        """
        Return nodes in topological order (parents before children).
        
        Returns:
            List of node names in topological order
        
        Raises:
            ValueError: If network contains cycles
        """
        in_degree = {name: len(node.parents) for name, node in self.nodes.items()}
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for child in self.get_children(current):
                in_degree[child.name] -= 1
                if in_degree[child.name] == 0:
                    queue.append(child.name)
        
        if len(result) != len(self.nodes):
            raise ValueError("Network contains cycles")
        
        return result
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize network to dictionary for persistence.
        
        Returns:
            Dictionary representation of the network
        """
        return {
            "nodes": {
                name: {
                    "states": node.states,
                    "parents": [p.name for p in node.parents],
                    "cpt": node.cpt.to_dict() if node.cpt else None
                }
                for name, node in self.nodes.items()
            },
            "evidence": self.evidence.copy()
        }
    
    def __repr__(self) -> str:
        return f"BayesianNetwork(nodes={len(self.nodes)}, evidence={self.evidence})"
