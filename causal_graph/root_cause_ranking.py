"""
Root cause ranking algorithms for multi-fault diagnosis.

This module implements the core inference engine of Pravaha: given observed
telemetry deviations, rank which root causes best explain the observations.

The algorithm works in three steps:
1. ANOMALY DETECTION: Which observables deviated significantly?
2. BACKWARD TRACING: Which root causes could have caused these deviations?
3. RANKING: Which root causes best fit the pattern of observed anomalies?

Why this approach:
- Explicit reasoning: We trace from observations back to causes (transparent)
- Multi-fault capable: Can handle multiple simultaneous root causes
- Confounding-aware: Recognizes when one fault causes secondary deviations
- Explainable: Can show users WHY we ranked a hypothesis (mechanisms, paths, evidence)

The algorithm is rule-based Bayesian inference, not statistical learning:
- Rules encode domain knowledge (causal mechanisms)
- Bayesian: score hypotheses by how well they explain evidence
- No training data required: knowledge comes from expert elicitation
- Deterministic: same input always produces same output (reproducible)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple
from simulator.power import PowerTelemetry
from causal_graph.graph_definition import CausalGraph


@dataclass
class RootCauseHypothesis:
    """
    A ranked hypothesis for root cause.
    
    This represents a potential diagnosis: "I think the root cause is X,
    with probability P, based on evidence E, with confidence C".
    
    Operators use this information to:
    1. Know which fault is most likely (probability)
    2. Understand why (mechanism, evidence)
    3. Know how confident to be (confidence score)
    """
    
    name: str                   # Root cause name (e.g., "solar_degradation")
    probability: float          # Posterior probability this is the cause (0-1, sums to 1.0)
    evidence: List[str]         # Observable deviations supporting this hypothesis
    mechanism: str              # Explanation of causal mechanism
    confidence: float           # Confidence in this hypothesis (0-1, independent of probability)


class RootCauseRanker:
    """
    Infer and rank root causes using causal graph.
    
    This is the main diagnosis engine. It takes two telemetry datasets
    (nominal and degraded) and produces a ranked list of hypotheses
    about what went wrong.
    
    The algorithm:
    1. Compare nominal vs degraded to find deviations in each observable
    2. For each deviation, trace backward through causal graph to root causes
    3. Score root causes by path strength, deviation severity, and consistency
    4. Normalize scores to probabilities and rank
    5. Compute confidence based on evidence quality
    """

    def __init__(self, graph: CausalGraph):
        """
        Initialize ranker with causal graph.
        
        Args:
            graph: CausalGraph instance containing domain knowledge
        """
        
        self.graph = graph
        
        # Mapping from physical quantity names to observable node names
        # This allows us to handle different naming conventions in telemetry
        self.observables_map = {
            # Power subsystem physical quantities -> graph node names
            "solar_input": "solar_input_measured",
            "battery_voltage": "battery_voltage_measured",
            "battery_charge": "battery_charge_measured",
            "bus_voltage": "bus_voltage_measured",
            # Thermal subsystem physical quantities -> graph node names
            "solar_panel_temp": "solar_panel_temp_measured",
            "battery_temp": "battery_temp_measured",
            "payload_temp": "payload_temp_measured",
            "bus_current": "bus_current_measured",
        }

    def analyze(
        self,
        nominal: PowerTelemetry,
        degraded: PowerTelemetry,
        deviation_threshold: float = 0.15,
    ) -> List[RootCauseHypothesis]:
        """
        Analyze deviations and rank root causes.

        This is the main entry point. It orchestrates the three-step inference process:
        1. Detect anomalies (which observables deviated significantly?)
        2. Trace back to roots (which root causes could cause these anomalies?)
        3. Score and rank (which root cause best explains the pattern?)

        Args:
            nominal: Healthy telemetry (baseline for comparison)
            degraded: Faulty telemetry (what we're diagnosing)
            deviation_threshold: Fractional threshold for flagging an anomaly.
                For example, 0.15 means we only flag a deviation if it's >15% of
                the nominal mean. This filters out sensor noise and normal fluctuations.

        Returns:
            Sorted list of root cause hypotheses, ranked by probability (highest first)
        """
        
        # STEP 1: ANOMALY DETECTION
        # Compare nominal vs degraded to find which observables deviated significantly
        anomalies = self._detect_anomalies(nominal, degraded, deviation_threshold)

        # STEP 2: BACKWARD TRACING
        # For each observable deviation, trace back through the causal graph
        # to find which root causes could have caused it
        root_cause_scores = {}  # Accumulates scores for each root cause
        root_cause_evidence = {}  # Tracks which observations support each hypothesis

        for observable, severity in anomalies.items():
            # Trace from this observable back to root causes
            # Returns dict mapping root_cause_name -> score contribution
            contributing_causes = self._trace_back_to_roots(
                observable, severity, anomalies
            )

            # Accumulate scores and evidence for each root cause
            for cause_name, cause_score in contributing_causes.items():
                if cause_name not in root_cause_scores:
                    root_cause_scores[cause_name] = 0.0
                    root_cause_evidence[cause_name] = []

                root_cause_scores[cause_name] += cause_score
                root_cause_evidence[cause_name].append(f"{observable} deviation")

        # STEP 3: RANKING
        # Normalize scores to probabilities and create hypothesis objects

        # If no scores, no root causes were found
        total_score = sum(root_cause_scores.values())
        if total_score == 0:
            return []

        hypotheses = []
        for cause_name in root_cause_scores:
            # Probability: this root cause's score as a fraction of total
            # (ensures all probabilities sum to 1.0)
            probability = root_cause_scores[cause_name] / total_score
            
            # Mechanism: plain-text explanation of how this fault would cause symptoms
            mechanism = self._explain_mechanism(
                cause_name, root_cause_evidence[cause_name], anomalies
            )
            
            # Confidence: how sure are we about this hypothesis?
            # (independent of probability; can have high probability but low confidence
            # if evidence is weak, or low probability but high confidence if it's a clear cause)
            confidence = self._compute_confidence(
                cause_name, root_cause_evidence[cause_name], anomalies
            )

            hypotheses.append(
                RootCauseHypothesis(
                    name=cause_name,
                    probability=probability,
                    evidence=root_cause_evidence[cause_name],
                    mechanism=mechanism,
                    confidence=confidence,
                )
            )

        # Sort by probability (highest first) for easy ranking
        hypotheses.sort(key=lambda h: h.probability, reverse=True)
        return hypotheses

    def _detect_anomalies(
        self,
        nominal,  # PowerTelemetry or combined telemetry object
        degraded,  # PowerTelemetry or combined telemetry object
        threshold: float,
    ) -> Dict[str, float]:
        """
        Detect which observables deviate from nominal.

        This is the first step: identify what changed between nominal and degraded.
        We compute residuals (absolute differences) and flag anything larger than
        threshold * mean as an "anomaly".

        Why threshold?
        - Real sensors have noise, so small deviations don't indicate faults
        - 15% threshold is typical for satellite telemetry (1-5% noise +  buffer)
        - Prevents false positives while catching real degradation

        Supports both power-only and power+thermal telemetry by checking
        which fields exist and analyzing those.

        Returns:
            Dict mapping observable name string -> severity (0-1)
        """
        
        anomalies = {}

        # Define which observables to check
        # Start with power subsystem (always present)
        telemetry_pairs = [
            ("solar_input", nominal.solar_input, degraded.solar_input),
            ("battery_voltage", nominal.battery_voltage, degraded.battery_voltage),
            ("battery_charge", nominal.battery_charge, degraded.battery_charge),
            ("bus_voltage", nominal.bus_voltage, degraded.bus_voltage),
        ]

        # Add thermal subsystem if available (combined telemetry)
        if hasattr(nominal, "battery_temp"):
            telemetry_pairs.extend([
                ("battery_temp", nominal.battery_temp, degraded.battery_temp),
                ("solar_panel_temp", nominal.solar_panel_temp, degraded.solar_panel_temp),
                ("payload_temp", nominal.payload_temp, degraded.payload_temp),
                ("bus_current", nominal.bus_current, degraded.bus_current),
            ])

        # For each observable, compute residual and check if it exceeds threshold
        for name, nom_values, deg_values in telemetry_pairs:
            # Residual: absolute magnitude of change
            residual = np.abs(deg_values - nom_values)
            mean_deviation = np.mean(residual)
            baseline = np.mean(nom_values)

            # Fractional deviation: deviation relative to nominal mean
            # E.g., if solar_input normally averages 250W and now deviates 50W on average,
            # fractional_dev = 50 / 250 = 0.2 (20% deviation)
            if baseline > 0:
                fractional_dev = mean_deviation / baseline
            else:
                fractional_dev = 0

            # Flag as anomaly if exceeds threshold
            if fractional_dev > threshold:
                # Severity on scale 0-1 (where 0.5 = 50% deviation = severity 1.0)
                # This is used for scoring: larger deviations get higher severity
                severity = np.clip(fractional_dev / 0.5, 0, 1)
                anomalies[name] = severity

        return anomalies

    def _trace_back_to_roots(
        self,
        observable: str,
        severity: float,
        anomalies: Dict[str, float],
    ) -> Dict[str, float]:
        """
        Trace from observable back to root causes.

        Core algorithm: for a given observable deviation, find all causal paths
        back to root causes, then score each root cause by:
        1. Path strength: How strong is the causal chain? (product of edge weights)
        2. Deviation severity: How big is the deviation? (bigger = stronger evidence)
        3. Consistency: Do other observed anomalies match this root cause pattern?

        Example:
        Observable: battery_voltage_measured deviated
        Path 1: battery_voltage_measured ← battery_state ← solar_input ← solar_degradation
        Path 2: battery_voltage_measured ← battery_state ← battery_efficiency ← battery_aging
        
        We score each path and root cause, then return the scores.

        Args:
            observable: Name of observable that deviated (e.g., "battery_voltage")
            severity: Severity of deviation (0-1)
            anomalies: All detected anomalies (used for consistency checking)

        Returns:
            Dict mapping root_cause_name -> score contribution (higher = stronger evidence)
        """
        
        # Convert observable name to graph node name
        observable_node = self.observables_map.get(observable, observable)
        
        # Find all paths from this observable back to root causes
        # Each path is a sequence of nodes from observable to root
        paths = self.graph.get_paths_to_root(observable_node)

        root_scores = {}

        # Score each path and attribute to its root cause
        for path in paths:
            # First element in path (when traversing backward) is the root cause
            root_cause = path[0]

            if root_cause not in root_scores:
                root_scores[root_cause] = 0.0

            # STEP 1: Compute path strength
            # Product of all edge weights along the path
            # E.g., if path has edges with weights 0.9 and 0.8, path_strength = 0.9 * 0.8 = 0.72
            # Stronger causal chains (higher weights) = higher path strength
            path_strength = 1.0
            for i in range(len(path) - 1):
                source, target = path[i], path[i + 1]
                parents = self.graph.get_parents(target)
                if source in parents:
                    path_strength *= parents[source]

            # STEP 2: Check consistency
            # Are other observed anomalies consistent with this root cause?
            # E.g., if we hypothesize "solar degradation", do we also see the expected
            # effects on battery charge and voltage? Consistency 0-1 (higher is better)
            consistency = self._check_consistency(root_cause, anomalies)
            
            # STEP 3: Compute overall score
            # Combine path strength, severity, and consistency
            # The formula: score = path_strength * severity * (baseline + consistency_boost)
            # This means:
            # - Strong paths get higher scores
            # - Severe deviations are stronger evidence than minor ones
            # - Consistent patterns get boosted, inconsistent get discount
            score = path_strength * severity * (0.5 + 0.5 * consistency)

            root_scores[root_cause] += score

        return root_scores

    def _check_consistency(self, root_cause: str, anomalies: Dict[str, float]) -> float:
        """
        Check if other observed anomalies are consistent with this root cause.

        The idea: if we hypothesize root cause X, what secondary effects do we expect
        to see in telemetry? If we see them, consistency is high. If we don't, it's lower.

        Example:
        Hypothesis: "solar_degradation"
        Expected anomalies: solar_input (direct), battery_charge (can't charge fully), bus_voltage (power limited)
        If we observe all three: consistency = 3/3 = 1.0 (perfect match)
        If we observe two: consistency = 2/3 = 0.67
        If we observe one: consistency = 1/3 = 0.33

        Returns:
            Consistency score (0-1), higher if observed matches expected
        """
        
        # Domain knowledge: for each root cause, what observables do we expect to deviate?
        # This comes from the system design and causal understanding
        expected_anomalies = {
            # Power subsystem causes
            "solar_degradation": ["solar_input", "battery_charge", "bus_voltage"],
            "battery_aging": ["battery_voltage", "battery_charge", "bus_voltage"],
            "battery_thermal": ["battery_voltage", "battery_charge"],
            "sensor_bias": ["battery_voltage", "battery_charge"],
            # Thermal subsystem causes
            "panel_insulation_degradation": ["solar_panel_temp", "battery_temp"],
            "battery_heatsink_failure": ["battery_temp", "bus_current"],
            "payload_radiator_degradation": ["payload_temp"],
        }

        if root_cause not in expected_anomalies:
            return 0.5  # Unknown cause - neutral consistency (neither matches nor mismatches)

        # Count how many expected anomalies we actually observed
        expected = set(expected_anomalies[root_cause])
        observed = set(anomalies.keys())
        intersection = expected & observed  # Which expected were observed?

        if len(expected) == 0:
            return 0.5  # Degenerate case

        # Consistency: fraction of expected anomalies that were observed
        consistency = len(intersection) / len(expected)
        return consistency

    def _explain_mechanism(
        self,
        root_cause: str,
        evidence: List[str],
        anomalies: Dict[str, float],
    ) -> str:
        """
        Generate plain-text explanation of mechanism.

        This is crucial for explainability. When we rank a hypothesis, we should
        tell the operator WHY we think it's the root cause, not just that it has
        high probability.

        Each root cause has a templated explanation that describes the physical
        mechanism and the evidence supporting it.

        Returns:
            Multi-sentence explanation suitable for display to operators
        """
        
        # Template explanations for each root cause
        explanations = {
            # Power subsystem mechanisms
            "solar_degradation": (
                "Reduced solar input is propagating through the power subsystem. "
                "This suggests solar panel degradation or shadowing, which reduces "
                "available power for charging the battery."
            ),
            "battery_aging": (
                "Battery voltage and charge deviations indicate internal degradation. "
                "This suggests increased internal resistance or cell aging, reducing "
                "charging efficiency and available capacity."
            ),
            "battery_thermal": (
                "Battery voltage droop under nominal load suggests thermal stress. "
                "Elevated temperature is degrading electrochemical performance "
                "and increasing internal losses."
            ),
            "sensor_bias": (
                "Anomalies in voltage and charge measurements may be due to sensor "
                "calibration drift rather than actual physical degradation. "
                "Cross-check with other subsystems before taking action."
            ),
            # Thermal subsystem mechanisms
            "panel_insulation_degradation": (
                "Elevated solar panel temperature indicates loss of thermal insulation "
                "or radiator fouling. This reduces panel efficiency and increases "
                "heat-induced stress on power electronics."
            ),
            "battery_heatsink_failure": (
                "High battery temperature with elevated current draw indicates the "
                "primary thermal management system has failed. This accelerates battery "
                "aging and risks thermal runaway if not corrected."
            ),
            "payload_radiator_degradation": (
                "Elevated payload temperature indicates radiator coating degradation "
                "or micrometeorite damage. Payload must operate at reduced power to "
                "avoid thermal shutdown."
            ),
        }

        # Get base explanation for this root cause
        base_explanation = explanations.get(
            root_cause, "Unknown root cause mechanism."
        )

        # Append evidence if available
        if evidence:
            evidence_str = "; ".join(evidence)
            return f"{base_explanation}\nEvidence: {evidence_str}"
        return base_explanation

    def _compute_confidence(
        self,
        root_cause: str,
        evidence: List[str],
        anomalies: Dict[str, float],
    ) -> float:
        """
        Compute confidence in this root cause hypothesis.

        Confidence measures how sure we are about this diagnosis, independent
        of probability. For example:
        - High probability + high confidence: We're very sure about this diagnosis
        - High probability + low confidence: It's the best guess, but evidence is weak
        - Low probability + high confidence: Small chance but if it's true, we'd be certain

        Higher confidence if:
        - Multiple observations support it (redundancy)
        - Other anomalies match the expected pattern (consistency)

        Returns:
            Confidence score (0-1)
        """
        
        # Base confidence: 50% (neutral)
        base_confidence = 0.5
        
        # Number of independent observations supporting this hypothesis
        # Each piece of evidence boosts confidence (diminishing returns, capped at 3)
        num_evidence = len(evidence)
        
        # Consistency: how well do OTHER anomalies match the pattern expected from this cause?
        consistency = self._check_consistency(root_cause, anomalies)

        # Compute final confidence:
        # base (0.5) + evidence_boost (up to 0.45) + consistency_boost (up to 0.2)
        # This formula ensures confidence stays in [0, 1]
        confidence = base_confidence + 0.15 * min(num_evidence, 3) + 0.2 * consistency
        return np.clip(confidence, 0, 1)

    def print_report(self, hypotheses: List[RootCauseHypothesis]):
        """
        Pretty-print root cause analysis report for operators.
        
        Format:
        1. Summary ranking (most likely first)
        2. Detailed explanation for each hypothesis (evidence and mechanism)
        
        This is the main output shown to satellite operators for decision-making.
        """
        
        print("\n" + "=" * 70)
        print("ROOT CAUSE RANKING ANALYSIS")
        print("=" * 70)

        if not hypotheses:
            print("\nNo significant root causes detected.")
            return

        # SECTION 1: Ranked summary (operators see this first)
        print("\nMost Likely Root Causes (by posterior probability):\n")
        for rank, hyp in enumerate(hypotheses, 1):
            print(
                f"{rank}. {hyp.name:25s} "
                f"P={hyp.probability:6.1%}  "
                f"Confidence={hyp.confidence:5.1%}"
            )

        # SECTION 2: Detailed explanations (for deeper investigation)
        print("\n" + "-" * 70)
        print("DETAILED EXPLANATIONS:\n")

        for hyp in hypotheses:
            print(f"• {hyp.name} (P={hyp.probability:.1%})")
            print(f"  Evidence: {', '.join(hyp.evidence)}")
            print(f"  Mechanism: {hyp.mechanism}")
            print()

        print("=" * 70 + "\n")


if __name__ == "__main__":
    # Quick test of root cause ranking
    from simulator.power import PowerSimulator

    sim = PowerSimulator(duration_hours=24)
    nominal = sim.run_nominal()
    degraded = sim.run_degraded(
        solar_degradation_hour=6.0,
        battery_degradation_hour=8.0,
    )

    graph = CausalGraph()
    ranker = RootCauseRanker(graph)

    hypotheses = ranker.analyze(nominal, degraded, deviation_threshold=0.15)
    ranker.print_report(hypotheses)
