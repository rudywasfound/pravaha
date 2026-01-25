#!/usr/bin/env python3
"""
d-Separation Analysis for Causal Graph

This module implements Pearl's d-separation criterion to:
1. Verify conditional independence assumptions
2. Prove that Pravaha can ignore noise in some measurements
3. Show why certain root causes are distinguishable
4. Demonstrate causal isolation between subsystems

d-Separation (directional separation):
- Two variables X and Z are d-separated given S if all paths from X to Z
  are blocked by S
- A path is blocked if it passes through:
  * A non-collider node in S (conditioning blocks it)
  * A collider node whose descendants are not in S
  
Key insight: d-separation justifies ignoring certain variables or noise
sources when diagnosing failures.
"""

import sys
import os
from typing import Set, List, Tuple, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from causal_graph.graph_definition import CausalGraph


class DSeparationAnalyzer:
    """
    Analyzes d-separation properties of the causal graph.
    
    This provides formal verification that:
    1. Solar noise doesn't propagate when battery is stable
    2. Thermal failures don't affect power measurements (except via battery temp)
    3. Payload and power systems are causally isolated
    4. Sensor bias can be distinguished from real degradation
    """
    
    def __init__(self, graph: CausalGraph):
        """Initialize analyzer with causal graph."""
        self.graph = graph
        self.parents_cache = {}  # Cache parent relationships
        self.children_cache = {}  # Cache children relationships
    
    def are_d_separated(
        self,
        x: str,
        z: str,
        conditioning_set: Set[str] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Check if X and Z are d-separated given conditioning set S.
        
        Returns:
            (is_separated, blocking_nodes) - whether separated and which nodes block
            
        Algorithm:
        1. Find all paths from X to Z
        2. For each path, check if it's blocked
        3. If ALL paths are blocked, X and Z are d-separated
        """
        
        if conditioning_set is None:
            conditioning_set = set()
        
        # Find all paths from X to Z
        paths = self._find_all_paths(x, z, max_length=10)
        
        if not paths:
            # No paths means d-separated (and causal independence)
            return True, ["NO_PATHS"]
        
        # Check if each path is blocked
        blocking_nodes = []
        all_paths_blocked = True
        
        for path in paths:
            is_blocked = self._is_path_blocked(path, conditioning_set)
            if not is_blocked:
                all_paths_blocked = False
            else:
                # Track which nodes block this path
                blocking_nodes.extend(self._get_blocking_nodes(path, conditioning_set))
        
        return all_paths_blocked, list(set(blocking_nodes))
    
    def _find_all_paths(
        self,
        start: str,
        end: str,
        max_length: int = 10,
        visited: Set[str] = None,
        current_path: List[str] = None,
    ) -> List[List[str]]:
        """
        Find all paths from start to end (BFS, respecting DAG structure).
        
        Args:
            start: Starting node
            end: Ending node
            max_length: Maximum path length to prevent infinite recursion
            visited: Nodes already visited in this path
            current_path: Current path being built
        
        Returns:
            List of paths (each path is a list of nodes from start to end)
        """
        
        if visited is None:
            visited = set()
        if current_path is None:
            current_path = []
        
        # Base case: found the end
        if start == end:
            return [current_path + [start]]
        
        # Base case: max depth or cycle
        if len(current_path) >= max_length or start in visited:
            return []
        
        # Recursive case: explore children
        visited.add(start)
        current_path.append(start)
        
        all_paths = []
        children = self.graph.get_children(start)
        
        for child in children:
            new_visited = visited.copy()
            paths = self._find_all_paths(
                child, end, max_length,
                visited=new_visited,
                current_path=current_path.copy()
            )
            all_paths.extend(paths)
        
        return all_paths
    
    def _is_path_blocked(self, path: List[str], conditioning_set: Set[str]) -> bool:
        """
        Check if a path is blocked by the conditioning set.
        
        A path is blocked if it contains a non-collider in conditioning set
        OR a collider whose descendants are not in the conditioning set.
        
        Args:
            path: List of nodes forming a path
            conditioning_set: The set we're conditioning on
        
        Returns:
            True if path is blocked (cannot transmit information)
        """
        
        if len(path) < 2:
            return True  # Single node or empty path
        
        # Check each node in the path (except endpoints)
        for i in range(1, len(path) - 1):
            node = path[i]
            prev_node = path[i - 1]
            next_node = path[i + 1]
            
            # Check if this node is a collider (receives from both sides)
            is_collider = self._is_collider(node, prev_node, next_node, path)
            
            if is_collider:
                # Collider blocks unless its descendants are in conditioning set
                descendants = self._get_descendants(node)
                if not descendants.intersection(conditioning_set):
                    # No descendants in conditioning set -> path is blocked
                    return True
            else:
                # Non-collider blocks if it's in conditioning set
                if node in conditioning_set:
                    return True
        
        # All blocks found (path is blocked)
        return False
    
    def _is_collider(self, node: str, prev_node: str, next_node: str, path: List[str]) -> bool:
        """
        Check if node is a collider (receives arrows from both neighbors in path).
        
        In the path prev_node → node ← next_node, node is a collider.
        """
        
        # Get parents of this node
        parents = self.graph.get_parents(node)
        
        # Node is collider if BOTH prev and next are parents
        return (prev_node in parents) and (next_node in parents)
    
    def _get_descendants(self, node: str, visited: Set[str] = None) -> Set[str]:
        """
        Find all descendants of a node (nodes reachable via outgoing edges).
        
        Args:
            node: Starting node
            visited: Nodes already visited
        
        Returns:
            Set of all descendant nodes
        """
        
        if visited is None:
            visited = set()
        
        if node in visited:
            return set()
        
        visited.add(node)
        descendants = set()
        
        children = self.graph.get_children(node)
        for child in children:
            descendants.add(child)
            descendants.update(self._get_descendants(child, visited))
        
        return descendants
    
    def _get_blocking_nodes(self, path: List[str], conditioning_set: Set[str]) -> List[str]:
        """Get the nodes that block a path."""
        blocking = []
        
        for i in range(1, len(path) - 1):
            node = path[i]
            if node in conditioning_set:
                blocking.append(node)
        
        return blocking
    
    def print_d_separation_report(self):
        """
        Print comprehensive d-separation analysis for key variable pairs.
        
        This validates our critical causal assumptions.
        """
        
        print("\n" + "=" * 80)
        print("d-SEPARATION ANALYSIS: VALIDATING CAUSAL STRUCTURE")
        print("=" * 80)
        
        # Key variable pairs to test
        test_cases = [
            # (X, Z, conditioning_set, description)
            ("solar_degradation", "bus_voltage_measured", {"battery_state"},
             "Solar noise ignored when battery stable"),
            
            ("battery_aging", "battery_temp_measured", {"battery_efficiency"},
             "Aging doesn't cause overheating directly"),
            
            ("payload_radiator_degradation", "bus_voltage_measured", set(),
             "Payload isolated from power system"),
            
            ("solar_degradation", "payload_temp_measured", set(),
             "Solar and payload are independent"),
            
            ("sensor_bias", "battery_state", set(),
             "Sensor bias doesn't change physical state"),
            
            ("battery_thermal", "bus_voltage_measured", set(),
             "Thermal affects power only via battery"),
            
            ("panel_insulation_degradation", "battery_voltage_measured", set(),
             "Panel insulation doesn't affect battery voltage directly"),
        ]
        
        print("\nKEY d-SEPARATION TESTS:")
        print("-" * 80)
        
        for x, z, cond_set, description in test_cases:
            is_sep, blocking = self.are_d_separated(x, z, cond_set)
            
            cond_str = f"given {{{', '.join(cond_set)}}}" if cond_set else "unconditional"
            
            print(f"\n{description}")
            print(f"  X: {x}")
            print(f"  Z: {z}")
            print(f"  Condition: {cond_str}")
            print(f"  d-Separated: {'✓ YES' if is_sep else '✗ NO'}")
            if blocking:
                print(f"  Blocking nodes: {', '.join(blocking)}")
        
        print("\n" + "=" * 80)
    
    def validate_causal_assumptions(self) -> Dict[str, bool]:
        """
        Validate all critical causal assumptions for Pravaha.
        
        Returns:
            Dictionary mapping assumption name to validity (True = correct)
        """
        
        assumptions = {}
        
        # Assumption 1: Solar doesn't directly affect bus voltage
        sep, _ = self.are_d_separated(
            "solar_degradation", "bus_voltage_measured",
            {"battery_state"}
        )
        assumptions["solar_mediated_by_battery"] = sep
        
        # Assumption 2: Battery aging and thermal are distinguishable
        sep_age_temp, _ = self.are_d_separated(
            "battery_aging", "battery_temp_measured",
            {"battery_efficiency"}
        )
        assumptions["aging_distinct_from_thermal"] = sep_age_temp
        
        # Assumption 3: Payload is isolated
        sep_payload, _ = self.are_d_separated(
            "payload_radiator_degradation", "bus_voltage_measured",
            set()
        )
        assumptions["payload_isolated"] = sep_payload
        
        # Assumption 4: Sensor bias is distinguishable
        sep_bias, _ = self.are_d_separated(
            "sensor_bias", "battery_state",
            set()
        )
        assumptions["sensor_bias_identifiable"] = sep_bias
        
        return assumptions


def main():
    """Run d-separation analysis."""
    graph = CausalGraph()
    analyzer = DSeparationAnalyzer(graph)
    
    # Print analysis
    analyzer.print_d_separation_report()
    
    # Validate assumptions
    print("\n" + "=" * 80)
    print("ASSUMPTION VALIDATION")
    print("=" * 80)
    
    assumptions = analyzer.validate_causal_assumptions()
    
    all_valid = True
    for assumption, is_valid in assumptions.items():
        status = "✓ VALID" if is_valid else "✗ INVALID"
        print(f"  {assumption:40s} {status}")
        all_valid = all_valid and is_valid
    
    print()
    if all_valid:
        print("✓ All causal assumptions validated!")
        print("  Pravaha can safely use d-separation for inference.")
    else:
        print("✗ Some assumptions failed validation.")
        print("  Review causal graph structure.")
    
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
