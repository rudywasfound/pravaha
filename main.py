"""
Main entry point for Pravaha causal inference framework.

This module orchestrates the entire satellite anomaly diagnosis workflow:
1. Initialize realistic simulators for power and thermal subsystems
2. Generate nominal (healthy) and degraded (faulty) telemetry data
3. Analyze deviations to quantify fault severity
4. Build causal graph representing failure mechanisms
5. Rank root causes using Bayesian causal inference
6. Generate visualizations and detailed reports

The workflow demonstrates how Pravaha can diagnose multi-fault scenarios
that would confuse simpler approaches (correlation, threshold checks, etc).
For example, when solar panels degrade, it affects not just solar input
but also battery temperature (secondary effect) due to power coupling.
Causal reasoning explicitly models these relationships.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulator.power import PowerSimulator
from simulator.thermal import ThermalSimulator
from visualization.plotter import TelemetryPlotter
from analysis.residual_analyzer import ResidualAnalyzer
from causal_graph.graph_definition import CausalGraph
from causal_graph.root_cause_ranking import RootCauseRanker


class CombinedTelemetry:
    """
    Container for unified power and thermal telemetry.
    
    Why combine them: In real operations, an operator sees all sensor readings
    simultaneously. By combining power and thermal data into a single object,
    we can:
    1. Reason about cross-subsystem failures (solar loss -> battery overtemp)
    2. Detect confounding effects (one fault masks another)
    3. Model realistic failure cascades
    
    The causal graph can then trace how a root cause propagates through both
    subsystems, producing observable deviations in multiple sensors.
    """
    
    def __init__(self, power_telem, thermal_telem):
        """
        Initialize combined telemetry from power and thermal sources.
        
        We align the time bases and assume both simulators were run with
        the same duration and sampling rate, so indices are directly comparable.
        """
        
        # Time axis in seconds (same for both subsystems)
        self.time = power_telem.time
        
        # Power subsystem observables
        self.solar_input = power_telem.solar_input
        self.battery_voltage = power_telem.battery_voltage
        self.battery_charge = power_telem.battery_charge
        self.bus_voltage = power_telem.bus_voltage
        
        # Thermal subsystem observables
        self.battery_temp = thermal_telem.battery_temp
        self.solar_panel_temp = thermal_telem.solar_panel_temp
        self.payload_temp = thermal_telem.payload_temp
        self.bus_current = thermal_telem.bus_current
        
        # Timestamp index for alignment with causal graph node indices
        self.timestamp = power_telem.timestamp


def main():
    """
    Execute the full Pravaha workflow.
    
    The workflow consists of three main phases that build on each other:
    Phase 1: Data generation (simulators produce realistic telemetry)
    Phase 2: Analysis (quantify what changed and by how much)
    Phase 3: Inference (determine which root causes explain the changes)
    """
    
    print("=" * 70)
    print("Causal Inference for Satellite Fault Diagnosis")
    print("=" * 70)

    # Create output directory to store generated plots and reports
    # This ensures clean separation of input code from generated artifacts
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    # PHASE 1: DATA GENERATION
    # We create realistic telemetry by running simulators that model actual
    # satellite physics. Using simulators instead of real data lets us:
    # 1. Know ground truth (which fault was actually present)
    # 2. Control fault parameters (severity, timing, type)
    # 3. Run repeatable experiments
    # 4. Build a diverse dataset quickly
    
    print("\n[1] Initializing simulators...")
    power_sim = PowerSimulator(duration_hours=24, sampling_rate_hz=0.1)
    thermal_sim = ThermalSimulator(duration_hours=24, sampling_rate_hz=0.1)

    # Generate nominal scenario: satellite operating perfectly
    # This baseline is essential because diagnosis works by comparing
    # degraded behavior to nominal behavior. We can only detect anomalies
    # by noting deviations from normal operation.
    print("[2] Running nominal scenario...")
    power_nom = power_sim.run_nominal()
    thermal_nom = thermal_sim.run_nominal(
        power_nom.solar_input,
        power_nom.battery_charge,
        power_nom.battery_voltage,
    )
    nominal = CombinedTelemetry(power_nom, thermal_nom)

    # Generate degraded scenario: satellite with multiple simultaneous faults
    # Multi-fault testing is critical because:
    # 1. Real failures often cascade (solar loss -> reduced charging -> battery stress)
    # 2. Simple approaches fail when one fault causes secondary deviations
    # 3. Causal reasoning explicitly models these interactions
    print("[3] Running degraded scenario (multi-fault)...")
    power_deg = power_sim.run_degraded(
        solar_degradation_hour=6.0,   # Solar panels degrade 6 hours into mission
        solar_factor=0.7,             # Panels operate at 70% efficiency (30% loss)
        battery_degradation_hour=8.0, # Battery aging starts at 8 hours
        battery_factor=0.8,           # Battery efficiency drops to 80%
    )
    thermal_deg = thermal_sim.run_degraded(
        power_deg.solar_input,
        power_deg.battery_charge,
        power_deg.battery_voltage,
        battery_cooling_hour=8.0,    # Cooling system degrades at 8 hours
        battery_cooling_factor=0.5,  # Cooling becomes 50% effective
    )
    degraded = CombinedTelemetry(power_deg, thermal_deg)

    # PHASE 2: ANALYSIS
    # Quantify what changed between nominal and degraded scenarios
    # The residual analyzer computes deviations and identifies anomalies
    
    print("[4] Analyzing deviations...")
    analyzer = ResidualAnalyzer(deviation_threshold=0.15)
    # Threshold=0.15 means we flag a deviation as significant only if it's
    # >15% of the nominal mean. This filters out small fluctuations from
    # normal sensor noise, focusing on real anomalies.
    stats = analyzer.analyze(nominal, degraded)
    analyzer.print_report(stats)

    # PHASE 3: VISUALIZATION
    # Generate plots showing nominal vs degraded behavior
    # Visualizations help operators quickly understand what went wrong
    
    print("[5] Generating plots...")
    plotter = TelemetryPlotter()
    # Plot 1: Side-by-side comparison of nominal and degraded telemetry
    # This shows the raw timeseries and makes deviations visually obvious
    plotter.plot_comparison(
        nominal,
        degraded,
        degradation_hours=(6, 24),  # Highlight the period when faults were active
        save_path=f"{output_dir}/comparison.png",
    )
    # Plot 2: Residuals showing the actual deviations
    # Residuals (difference from nominal) highlight anomalies more clearly
    plotter.plot_residuals(nominal, degraded, save_path=f"{output_dir}/residuals.png")

    # PHASE 4: CAUSAL INFERENCE
    # This is the core innovation of Pravaha
    # Instead of just finding deviations, we trace them back to root causes
    
    print("[6] Building causal graph...")
    graph = CausalGraph()
    # The graph encodes domain knowledge:
    # - 7 root causes (solar degradation, battery aging, thermal failures, etc)
    # - 23 nodes total (root causes + intermediates + observables)
    # - 29 edges representing causal mechanisms
    print(f"    {len(graph.nodes)} nodes, {len(graph.edges)} edges")

    # PHASE 5: ROOT CAUSE RANKING
    # Given the observed deviations, use Bayesian inference to rank causes
    # The algorithm:
    # 1. For each root cause, check if it could explain the observed deviations
    # 2. Score by how well the explanation fits (via graph consistency checking)
    # 3. Normalize scores to probabilities
    # 4. Return ranked list with confidence intervals
    
    print("[7] Ranking root causes...")
    ranker = RootCauseRanker(graph)
    hypotheses = ranker.analyze(nominal, degraded, deviation_threshold=0.15)
    # The analyze method returns Hypothesis objects with:
    # - name: root cause name
    # - probability: posterior probability (sums to 1.0 across all hypotheses)
    # - confidence: how certain we are about this hypothesis (depends on evidence quality)
    # - mechanisms: explanation of how this cause produced the observed deviations
    ranker.print_report(hypotheses)

    # Confirm completion
    print(f"\nOutputs saved to '{output_dir}/'")
    print("Workflow complete. Review plots and report for diagnosis.")


if __name__ == "__main__":
    main()
