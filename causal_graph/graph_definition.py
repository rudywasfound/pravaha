"""
Causal graph definition for satellite power and thermal subsystems.

This module encodes engineering domain knowledge as a directed acyclic graph (DAG).
The graph represents how failures propagate through satellites:

Root Causes (faults) --> Intermediate Effects --> Observable Deviations

Example path:
solar_degradation --> reduced solar_input --> battery can't charge properly --> 
lower battery_charge measured in telemetry

Why a causal graph:
1. Explicit representation of failure mechanisms (transparent to domain experts)
2. Enables path tracing from observables back to root causes
3. Supports multi-fault diagnosis (traces multiple causes simultaneously)
4. Domain experts (ISRO engineers) can validate and refine the structure
5. Handles confounding effects (one fault causing secondary deviations)

The graph structure:
- 7 ROOT CAUSES (primary faults we want to identify)
- 8 INTERMEDIATE nodes (effects that propagate between subsystems)
- 8 OBSERVABLE nodes (measured telemetry we can see)
- 29 directed edges with weights and mechanisms

This encoding enables Bayesian causal inference to rank hypotheses about
which root causes best explain observed deviations in telemetry.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set
from enum import Enum


class NodeType(Enum):
    """
    Types of nodes in causal graph.
    
    Each type represents a different role in the failure propagation chain:
    - ROOT_CAUSE: Primary faults (what we want to diagnose)
    - INTERMEDIATE: Effects propagating through subsystems
    - OBSERVABLE: Measured telemetry we can actually see
    """
    
    ROOT_CAUSE = "root_cause"  # Primary fault sources (the diagnosis targets)
    INTERMEDIATE = "intermediate"  # Propagation nodes (unobservable state)
    OBSERVABLE = "observable"  # Measured telemetry (what we observe)


@dataclass
class Node:
    """
    A node in the causal graph.
    
    Each node represents some aspect of the satellite:
    - A root cause (fault) that needs diagnosis
    - An intermediate physical effect (unobservable but inferred)
    - An observable measurement from telemetry
    
    The description and degradation_modes help domain experts understand
    what each node represents and how it can fail.
    """
    
    name: str                           # Unique identifier
    node_type: NodeType                 # Is this a cause, intermediate, or observable?
    description: str                    # Natural language explanation for operators
    degradation_modes: List[str] = field(default_factory=list)  # How can this node fail?


@dataclass
class Edge:
    """
    A directed causal edge (parent → child).
    
    An edge from A to B means "failures in A cause effects in B".
    The weight quantifies strength: 0.9 means strong causal effect,
    0.5 means weak effect.
    
    The mechanism is crucial for explainability: when we rank a hypothesis,
    we can show the user "Solar degradation likely because: reduced input power
    cannot recharge battery (mechanism) -> battery charge drops (observable)".
    """
    
    source: str             # Source node name (cause)
    target: str             # Target node name (effect)
    weight: float = 1.0     # Strength of causal relationship (0-1, higher = stronger)
    mechanism: str = ""     # How source affects target (for explanation)


class CausalGraph:
    """
    DAG representing causal relationships in power and thermal subsystems.
    
    This is the knowledge base that enables causal inference. It encodes
    engineering understanding of how satellites work and how they fail.
    
    Structure:
    - 23 nodes total (7 root causes, 8 intermediate, 8 observable)
    - 29 edges with weights and mechanisms
    - Supports path tracing: observable -> intermediate -> root cause
    - Enables hypothesis ranking based on path strength and consistency
    
    How it's used:
    1. Operator sees deviations in telemetry (observables)
    2. Inference engine traces paths backward to root causes
    3. Hypotheses ranked by how well they explain observed deviations
    4. Top-ranked hypothesis is the diagnosis
    
    Example: If we see low battery voltage and low battery charge both deviating,
    the inference engine will:
    - Find paths from these observables backward to root causes
    - Solar degradation path: solar_degradation -> solar_input -> battery_state -> battery_voltage_measured (matches!)
    - Battery aging path: battery_aging -> battery_efficiency -> battery_state -> battery_charge_measured (matches!)
    - Score both hypotheses by path strength and consistency
    - Rank the better-fitting hypothesis first
    """

    def __init__(self):
        """
        Initialize graph and build the power subsystem structure.
        
        We build the graph in __init__ rather than loading from a file
        because the structure is relatively small (23 nodes) and fits
        naturally as Python code. This makes it easy to:
        1. See the full structure at a glance
        2. Add/remove nodes or edges for experimentation
        3. Version control changes to the graph structure
        4. Validate that node dependencies are satisfied (e.g., target nodes exist)
        """
        
        self.nodes: Dict[str, Node] = {}  # name -> Node object
        self.edges: List[Edge] = []        # List of causal edges
        
        # Build the complete graph structure
        self._build_power_subsystem_graph()

    def _build_power_subsystem_graph(self):
        """
        Build initial power and thermal subsystem causal graph.
        
        The graph is built in layers:
        1. Define all ROOT CAUSE nodes (faults we want to diagnose)
        2. Define INTERMEDIATE nodes (physical effects)
        3. Define OBSERVABLE nodes (measured telemetry)
        4. Connect them with edges (failure propagation paths)
        5. Add POWER-THERMAL COUPLING edges (cross-subsystem effects)
        
        This structure represents about 20 years of accumulated knowledge
        from satellite operations, supplemented with domain expert input.
        The mechanisms on each edge explain why the connection exists
        (important for operators to understand recommendations).
        """

        # ========== ROOT CAUSES (LAYER 1) ==========
        # These are the faults we want to diagnose. Each represents a failure mode.
        
        # Power subsystem root causes
        self.add_node(
            "solar_degradation",
            NodeType.ROOT_CAUSE,
            "Solar panel efficiency loss or shadowing",
            degradation_modes=["panel_aging", "dust_accumulation", "partial_shadowing"],
        )
        # Why solar degradation: Panels accumulate dust, micrometeorite damage, thermal cycling
        # causes adhesive degradation and contact loss
        
        self.add_node(
            "battery_aging",
            NodeType.ROOT_CAUSE,
            "Battery cell degradation and capacity loss",
            degradation_modes=["cell_aging", "internal_resistance_rise"],
        )
        # Why battery aging: Satellites have limited thermal control, cycling causes
        # stress, and calendar aging occurs even with limited use (can be 20+ year missions)
        
        self.add_node(
            "battery_thermal",
            NodeType.ROOT_CAUSE,
            "Excessive battery temperature stress",
            degradation_modes=["thermal_runaway_risk", "efficiency_loss"],
        )
        # Why battery thermal: If cooling fails or dissipation exceeds capability,
        # battery can overheat, further degrading electrochemistry
        
        self.add_node(
            "sensor_bias",
            NodeType.ROOT_CAUSE,
            "Measurement bias or sensor drift",
            degradation_modes=["calibration_drift", "electronic_aging"],
        )
        # Why sensor bias: Electronics age in vacuum/radiation, causing slight calibration
        # drift that can mimic real faults

        # Thermal subsystem root causes
        self.add_node(
            "panel_insulation_degradation",
            NodeType.ROOT_CAUSE,
            "Solar panel insulation or radiator fouling",
            degradation_modes=["insulation_loss", "radiator_fouling"],
        )
        # Why insulation fails: Multi-layer insulation (MLI) can tear from micrometeorites,
        # contaminants can accumulate, coatings degrade in UV

        self.add_node(
            "battery_heatsink_failure",
            NodeType.ROOT_CAUSE,
            "Battery thermal management system failure",
            degradation_modes=["heatsink_blockage", "coolant_loss"],
        )
        # Why heatsinks fail: Coolant can leak, interfaces can degrade, radiator
        # can get contaminated or damaged

        self.add_node(
            "payload_radiator_degradation",
            NodeType.ROOT_CAUSE,
            "Payload electronics radiator degradation",
            degradation_modes=["radiator_coating_loss", "micrometeorite_damage"],
        )
        # Why payload radiators fail: Similar to panel insulation, radiator coatings
        # degrade in vacuum/radiation environment

        # ========== INTERMEDIATE NODES (LAYER 2) ==========
        # These represent physical effects that propagate between subsystems.
        # We don't measure them directly, but infer them from observables.

        # Power subsystem intermediates
        self.add_node(
            "solar_input",
            NodeType.INTERMEDIATE,
            "Available solar power from panels",
        )
        # This is the power produced by the solar array after degradation

        self.add_node(
            "battery_efficiency",
            NodeType.INTERMEDIATE,
            "Battery charge/discharge efficiency",
        )
        # This represents how much of the input power actually gets stored (vs lost as heat)

        self.add_node(
            "battery_state",
            NodeType.INTERMEDIATE,
            "Battery charge capacity and health",
        )
        # This is the actual state of charge and degradation of the battery

        self.add_node(
            "bus_regulation",
            NodeType.INTERMEDIATE,
            "Bus voltage regulation quality",
        )
        # This represents how well the power conditioning maintains stable output voltage

        # Thermal subsystem intermediates
        self.add_node(
            "solar_panel_temp",
            NodeType.INTERMEDIATE,
            "Solar panel temperature",
        )

        self.add_node(
            "battery_temp",
            NodeType.INTERMEDIATE,
            "Battery cell temperature",
        )

        self.add_node(
            "payload_temp",
            NodeType.INTERMEDIATE,
            "Payload electronics temperature",
        )

        self.add_node(
            "thermal_stress",
            NodeType.INTERMEDIATE,
            "Overall system thermal stress level",
        )
        # Aggregates thermal stress from multiple sources

        # ========== OBSERVABLE NODES (LAYER 3) ==========
        # These are measured telemetry that operators and inference engines can see.

        # Power observables
        self.add_node(
            "solar_input_measured",
            NodeType.OBSERVABLE,
            "Measured solar input power",
        )

        self.add_node(
            "battery_voltage_measured",
            NodeType.OBSERVABLE,
            "Measured battery voltage",
        )

        self.add_node(
            "battery_charge_measured",
            NodeType.OBSERVABLE,
            "Measured battery charge state percentage",
        )

        self.add_node(
            "bus_voltage_measured",
            NodeType.OBSERVABLE,
            "Measured bus output voltage",
        )

        # Thermal observables
        self.add_node(
            "solar_panel_temp_measured",
            NodeType.OBSERVABLE,
            "Measured solar panel temperature",
        )

        self.add_node(
            "battery_temp_measured",
            NodeType.OBSERVABLE,
            "Measured battery temperature",
        )

        self.add_node(
            "payload_temp_measured",
            NodeType.OBSERVABLE,
            "Measured payload temperature",
        )

        self.add_node(
            "bus_current_measured",
            NodeType.OBSERVABLE,
            "Measured bus current (power dissipation proxy)",
        )

        # ========== CAUSAL EDGES: POWER SUBSYSTEM ==========
        # These edges represent how power faults propagate

        # Solar degradation directly affects available solar input
        self.add_edge(
            "solar_degradation",
            "solar_input",
            weight=0.95,  # Strong effect (degradation directly reduces output)
            mechanism="Reduced panel output due to physical degradation or shadowing",
        )

        # Battery aging reduces charging efficiency
        self.add_edge(
            "battery_aging",
            "battery_efficiency",
            weight=0.85,  # Strong effect
            mechanism="Increased internal resistance reduces charge/discharge efficiency",
        )

        # Battery thermal stress reduces efficiency (temperature effects on electrochemistry)
        self.add_edge(
            "battery_thermal",
            "battery_efficiency",
            weight=0.75,  # Moderate effect (temperature is one of several factors)
            mechanism="High temperature degrades battery electrochemistry and increases losses",
        )

        # Reduced solar input means battery can't recharge properly
        self.add_edge(
            "solar_input",
            "battery_state",
            weight=0.9,  # Strong effect
            mechanism="Reduced input power cannot recharge battery to nominal capacity",
        )

        # Lower efficiency means less power stored per unit input
        self.add_edge(
            "battery_efficiency",
            "battery_state",
            weight=0.85,  # Strong effect
            mechanism="Lower efficiency means less power actually stored per unit of solar input",
        )

        # Degraded battery makes voltage regulation harder
        self.add_edge(
            "battery_state",
            "bus_regulation",
            weight=0.8,  # Moderate effect
            mechanism="Degraded battery supply makes regulation harder and less stable",
        )

        # ========== MEASUREMENT EDGES: POWER SYSTEM ==========
        # These connect physical quantities to measured telemetry

        # Solar input is directly measured
        self.add_edge(
            "solar_input",
            "solar_input_measured",
            weight=1.0,  # Nearly perfect measurement of physical quantity
            mechanism="Direct measurement of solar power via sensor",
        )

        # Battery state is reflected in measured voltage
        self.add_edge(
            "battery_state",
            "battery_voltage_measured",
            weight=0.95,  # Strong correlation (voltage sags with low charge)
            mechanism="Battery voltage reflects state of charge via electrochemical potential",
        )

        # Efficiency degradation causes voltage droop
        self.add_edge(
            "battery_efficiency",
            "battery_voltage_measured",
            weight=0.7,  # Moderate effect (efficiency affects voltage under load)
            mechanism="Efficiency degradation causes voltage droop due to increased internal resistance",
        )

        # Charge capacity is directly measured
        self.add_edge(
            "battery_state",
            "battery_charge_measured",
            weight=0.9,  # Strong measurement of physical quantity
            mechanism="Charge sensor reports actual state of charge of battery",
        )

        # Bus regulation quality affects measured bus voltage
        self.add_edge(
            "bus_regulation",
            "bus_voltage_measured",
            weight=0.95,  # Strong effect (regulator directly controls output)
            mechanism="Bus voltage sensor directly measures regulator output",
        )

        # Battery state affects available regulated power
        self.add_edge(
            "battery_state",
            "bus_voltage_measured",
            weight=0.75,  # Moderate effect (battery is source of regulated power)
            mechanism="Battery state affects available power for regulation",
        )

        # Sensor bias adds error to voltage measurements
        self.add_edge(
            "sensor_bias",
            "battery_voltage_measured",
            weight=0.5,  # Weak but consistent effect (bias is constant or slow-varying)
            mechanism="Sensor drift and calibration error add bias to voltage readings",
        )

        # Sensor bias affects charge estimation
        self.add_edge(
            "sensor_bias",
            "battery_charge_measured",
            weight=0.5,  # Weak effect (charge estimation also depends on other factors)
            mechanism="Sensor drift affects charge state estimation algorithms",
        )

        # ========== CAUSAL EDGES: THERMAL SUBSYSTEM ==========
        # These represent thermal failure propagation

        # Battery state affects battery temperature (through discharge current)
        self.add_edge(
            "battery_state",
            "battery_temp",
            weight=0.8,  # Moderate effect (discharge current is one heat source)
            mechanism="Low battery state forces higher discharge current, generating more I²R heat",
        )

        # Solar input affects panel temperature (more sun = more heating)
        self.add_edge(
            "solar_input",
            "solar_panel_temp",
            weight=0.85,  # Strong effect (solar radiation is primary heat source)
            mechanism="Increased solar radiation heats panel (albedo and thermal effects)",
        )

        # Regulated power enables payload operation and heat generation
        self.add_edge(
            "bus_regulation",
            "payload_temp",
            weight=0.7,  # Moderate effect (heat from payload electronics)
            mechanism="Available regulated power enables payload operation, generating heat",
        )

        # Insulation degradation prevents cooling, raising panel temperature
        self.add_edge(
            "panel_insulation_degradation",
            "solar_panel_temp",
            weight=0.9,  # Strong effect (insulation is primary temperature control)
            mechanism="Poor insulation/radiator coating prevents radiative cooling to space",
        )

        # Heatsink failure raises battery temperature
        self.add_edge(
            "battery_heatsink_failure",
            "battery_temp",
            weight=0.95,  # Very strong effect (heatsink is primary cooling path)
            mechanism="Failed heatsink eliminates primary cooling path for battery heat dissipation",
        )

        # Radiator degradation prevents payload cooling
        self.add_edge(
            "payload_radiator_degradation",
            "payload_temp",
            weight=0.9,  # Strong effect (radiator is primary cooling)
            mechanism="Degraded radiator reduces heat dissipation to space",
        )

        # Battery temperature contributes to overall thermal stress
        self.add_edge(
            "battery_temp",
            "thermal_stress",
            weight=0.7,  # Significant contributor
            mechanism="High battery temperature is critical thermal stress indicator (risk of runaway)",
        )

        # Payload temperature contributes to thermal stress
        self.add_edge(
            "payload_temp",
            "thermal_stress",
            weight=0.6,  # Moderate contributor
            mechanism="High payload temperature increases mission risk (reduced margins)",
        )

        # Panel temperature contributes to thermal stress
        self.add_edge(
            "solar_panel_temp",
            "thermal_stress",
            weight=0.5,  # Lower priority contributor
            mechanism="High panel temperature indicates reduced thermal margin",
        )

        # ========== POWER-THERMAL COUPLING ==========
        # These edges represent cross-subsystem effects

        # High battery temperature reduces efficiency (feedback loop)
        self.add_edge(
            "battery_temp",
            "battery_efficiency",
            weight=0.7,  # Moderate feedback effect
            mechanism="Elevated temperature increases internal resistance and electrochemical losses",
        )

        # ========== MEASUREMENT EDGES: THERMAL SYSTEM ==========
        # Connect thermal quantities to measurements

        # Panel temperature is directly measured
        self.add_edge(
            "solar_panel_temp",
            "solar_panel_temp_measured",
            weight=0.98,  # Nearly perfect measurement
            mechanism="Direct temperature sensor measurement via thermistor",
        )

        # Battery temperature is directly measured
        self.add_edge(
            "battery_temp",
            "battery_temp_measured",
            weight=0.95,  # High fidelity measurement
            mechanism="Battery thermistor directly measures cell temperature",
        )

        # Payload temperature is directly measured
        self.add_edge(
            "payload_temp",
            "payload_temp_measured",
            weight=0.96,  # High fidelity measurement
            mechanism="Payload thermal sensor provides local temperature measurement",
        )

        # Battery state affects current draw (regulation effort)
        self.add_edge(
            "battery_state",
            "bus_current_measured",
            weight=0.8,  # Moderate effect
            mechanism="Low battery state increases regulation effort and current draw",
        )

        # Reduced efficiency requires higher current
        self.add_edge(
            "battery_efficiency",
            "bus_current_measured",
            weight=0.7,  # Moderate effect
            mechanism="Reduced efficiency requires higher current to deliver same power",
        )

    def add_node(
        self,
        name: str,
        node_type: NodeType,
        description: str,
        degradation_modes: List[str] = None,
    ):
        """
        Add a node to the graph.
        
        Args:
            name: Unique identifier for the node
            node_type: Whether this is a root cause, intermediate, or observable
            description: Human-readable explanation for operators
            degradation_modes: List of specific ways this node can fail
        """
        
        if degradation_modes is None:
            degradation_modes = []
        self.nodes[name] = Node(name, node_type, description, degradation_modes)

    def add_edge(
        self,
        source: str,
        target: str,
        weight: float = 1.0,
        mechanism: str = "",
    ):
        """
        Add a directed causal edge to the graph.
        
        Args:
            source: Source node name (cause)
            target: Target node name (effect)
            weight: Strength of causal relationship (0-1, higher = stronger)
            mechanism: Explanation of how source causes target (for user interpretation)
            
        We validate that both nodes exist before adding the edge, preventing
        accidental dangling references that would cause inference to fail.
        """
        
        if source not in self.nodes:
            raise ValueError(f"Source node '{source}' not in graph")
        if target not in self.nodes:
            raise ValueError(f"Target node '{target}' not in graph")

        self.edges.append(Edge(source, target, weight, mechanism))

    def get_children(self, node_name: str) -> Dict[str, float]:
        """
        Get all children of a node (nodes it points to).
        
        This is used for forward inference: given a root cause, what effects propagate?
        
        Args:
            node_name: Node to query
            
        Returns:
            Dictionary mapping child node names to edge weights
        """
        
        children = {}
        for edge in self.edges:
            if edge.source == node_name:
                children[edge.target] = edge.weight
        return children

    def get_parents(self, node_name: str) -> Dict[str, float]:
        """
        Get all parents of a node (nodes pointing to it).
        
        This is used for backward inference: given an observable, what causes it?
        
        Args:
            node_name: Node to query
            
        Returns:
            Dictionary mapping parent node names to edge weights
        """
        
        parents = {}
        for edge in self.edges:
            if edge.target == node_name:
                parents[edge.source] = edge.weight
        return parents

    def get_root_causes(self) -> List[str]:
        """
        Get all root cause nodes.
        
        Returns:
            List of root cause node names (these are the diagnosis targets)
        """
        
        return [
            name
            for name, node in self.nodes.items()
            if node.node_type == NodeType.ROOT_CAUSE
        ]

    def get_observables(self) -> List[str]:
        """
        Get all observable (telemetry) nodes.
        
        Returns:
            List of observable node names (the measured quantities)
        """
        
        return [
            name
            for name, node in self.nodes.items()
            if node.node_type == NodeType.OBSERVABLE
        ]

    def get_paths_to_root(self, node_name: str, max_depth: int = 10) -> List[List[str]]:
        """
        Find all paths from a node back to root causes (upstream).
        
        This is the core algorithm for causal inference. Starting from an
        observable (measured telemetry), we trace backward through intermediate
        effects to find which root causes could have caused the observation.
        
        Example:
        Starting from "battery_voltage_measured", we find paths like:
        - battery_voltage_measured ← battery_state ← solar_input ← solar_degradation
        - battery_voltage_measured ← battery_state ← battery_efficiency ← battery_aging
        
        These paths are then scored based on how consistent they are with
        all observed deviations.
        
        Args:
            node_name: Starting node (typically an observable)
            max_depth: Maximum path length to prevent infinite recursion
            
        Returns:
            List of paths, where each path is a list of node names from observable to root
        """
        
        if max_depth == 0:
            return []

        parents = self.get_parents(node_name)
        if not parents:
            # No parents means this is a root cause (or isolated node)
            return [[node_name]]

        all_paths = []
        for parent in parents:
            parent_paths = self.get_paths_to_root(parent, max_depth - 1)
            for path in parent_paths:
                all_paths.append(path + [node_name])

        return all_paths

    def print_structure(self):
        """
        Pretty-print graph structure for inspection.
        
        Useful for:
        1. Verifying graph was built correctly
        2. Understanding the causal structure at a glance
        3. Finding nodes by name or type
        4. Reviewing causal mechanisms
        """
        
        print("\n" + "=" * 70)
        print("CAUSAL GRAPH STRUCTURE")
        print("=" * 70)

        # Print nodes grouped by type
        for node_type in [NodeType.ROOT_CAUSE, NodeType.INTERMEDIATE, NodeType.OBSERVABLE]:
            nodes = [
                (name, node)
                for name, node in self.nodes.items()
                if node.node_type == node_type
            ]
            if nodes:
                print(f"\n{node_type.value.upper()}:")
                for name, node in sorted(nodes):
                    print(f"  • {name:25s} - {node.description}")
                    if node.degradation_modes:
                        modes_str = ", ".join(node.degradation_modes)
                        print(f"    Modes: {modes_str}")

        # Print all edges with weights and mechanisms
        print("\nCAUSAL EDGES:")
        for edge in sorted(self.edges, key=lambda e: e.source):
            print(
                f"  {edge.source:25s} → {edge.target:25s} "
                f"(weight={edge.weight:.2f})"
            )
            if edge.mechanism:
                print(f"    Mechanism: {edge.mechanism}")

        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Quick test of graph structure
    graph = CausalGraph()
    graph.print_structure()

    # Example: Find all causal paths from a measurement back to root causes
    print("\nExample: Paths from battery_voltage_measured back to root causes:")
    paths = graph.get_paths_to_root("battery_voltage_measured")
    for i, path in enumerate(paths, 1):
        print(f"  Path {i}: {' ← '.join(reversed(path))}")
