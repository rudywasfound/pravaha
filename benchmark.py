"""
Extended Benchmark: causal inference vs correlation baseline.

This module evaluates the performance of Pravaha's causal inference approach
against a simpler correlation-based baseline. We test across multiple dimensions:
- 12 diverse scenarios (fault severity, type, timing)
- Fault severity robustness (how well each approach handles minor vs major faults)
- Noise tolerance (realistic sensor noise from 0% to 20%)

The goal is to demonstrate that explicit causal reasoning outperforms simple
correlation, especially in multi-fault scenarios where one fault can cause
secondary deviations in unrelated sensors (confounding effects).
"""

import numpy as np
from simulator.power import PowerSimulator
from simulator.thermal import ThermalSimulator
from causal_graph.graph_definition import CausalGraph
from causal_graph.root_cause_ranking import RootCauseRanker


class CorrelationBaseline:
    """
    Correlation-based root cause ranking (baseline approach).
    
    This is a simple heuristic baseline that ranks root causes by how many
    "expected observable deviations" match the actual deviations observed
    in telemetry. We use this to show that causal reasoning adds value
    beyond simple pattern matching.
    """
    
    def __init__(self):
        pass
    
    def rank_causes(self, nominal, degraded):
        """
        Rank root causes using correlation analysis.
        
        The baseline works by:
        1. Computing which telemetry metrics deviated significantly
        2. For each known cause, checking how many of its "expected observables" are deviated
        3. Scoring causes by the fraction of expected observables that match reality
        
        This approach is fast and intuitive, but fails when:
        - One fault causes secondary effects in unrelated sensors (solar loss affects battery temp)
        - Multiple faults interact (confounding: reduced power limits cooling capability)
        - The causal graph is more complex than simple 1-to-1 mappings
        """
        
        # Define expected patterns for each cause. These are hand-coded heuristics
        # that map each root cause to the observables we expect to see affected.
        # In reality, a satellite domain expert would define these patterns.
        patterns = {
            "solar_degradation": ["solar_input", "battery_charge", "bus_voltage"],
            "battery_aging": ["battery_voltage", "battery_charge"],
            "battery_heatsink_failure": ["battery_temp", "bus_current"],
        }
        
        # Step 1: Identify which observables deviated significantly from nominal
        # We use a 15% threshold based on the mean value, below which we ignore the deviation
        # (small fluctuations are normal and don't indicate a real fault)
        deviations = {}
        for attr in ["solar_input", "battery_voltage", "battery_charge", "bus_voltage",
                    "battery_temp", "solar_panel_temp", "payload_temp", "bus_current"]:
            if hasattr(nominal, attr):
                nom_vals = getattr(nominal, attr)
                deg_vals = getattr(degraded, attr)
                # Compute mean absolute deviation (how far off each reading is on average)
                dev = np.abs(deg_vals - nom_vals).mean()
                # Only flag this as a "real deviation" if it's > 15% of the nominal mean
                if dev > np.mean(nom_vals) * 0.15:
                    deviations[attr] = dev
        
        # Step 2: For each known root cause, score it by how well its expected pattern matches
        # the actual deviations we observed. The score is: (matches / total expected)
        scores = {}
        for cause, expected_obs in patterns.items():
            # Count how many expected observables actually deviated
            matches = sum(1 for obs in expected_obs if obs in deviations)
            # Score is the fraction of expected observables that match
            if len(expected_obs) > 0:
                scores[cause] = matches / len(expected_obs)
            else:
                scores[cause] = 0
        
        # Step 3: Return causes ranked by score (highest first), filtering out zeros
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [cause for cause, _ in ranked if _ > 0]


class Benchmark:
    """
    Benchmark framework for comprehensive evaluation.
    
    This class orchestrates the testing process:
    - Creates realistic satellite failure scenarios with known ground truth
    - Runs both causal and baseline approaches on the same data
    - Measures which approach correctly identifies the root cause
    - Tests robustness to fault severity and measurement noise
    
    By comparing both approaches on identical data, we get a fair assessment
    of the value added by explicit causal reasoning.
    """
    
    def __init__(self):
        # Initialize simulators for power and thermal subsystems
        # We use the same simulators as production code to ensure realistic test data
        self.power_sim = PowerSimulator(duration_hours=24, sampling_rate_hz=0.1)
        self.thermal_sim = ThermalSimulator(duration_hours=24, sampling_rate_hz=0.1)
        
        # Initialize the causal inference engine
        # This is the "smart" approach we're testing
        self.graph = CausalGraph()
        self.causal_ranker = RootCauseRanker(self.graph)
        
        # Initialize the correlation baseline
        # This is the "naive" approach we're comparing against
        self.baseline_ranker = CorrelationBaseline()
    
    def create_scenario(self, true_cause, **kwargs):
        """
        Create a test scenario with known ground truth.
        
        Why we do this: Testing requires knowing the actual root cause (ground truth).
        We create scenarios by:
        1. Running the simulator in healthy mode to get nominal baseline
        2. Running the simulator in degraded mode with a specific injected fault
        3. Comparing the two to see what changed
        
        The "true_cause" parameter tells us which fault we injected, so we can
        later check if our inference engine identified it correctly.
        """
        
        # Step 1: Generate nominal (healthy) telemetry for both power and thermal
        # This represents what the satellite looks like when everything is working correctly
        power_nom = self.power_sim.run_nominal()
        thermal_nom = self.thermal_sim.run_nominal(
            power_nom.solar_input,
            power_nom.battery_charge,
            power_nom.battery_voltage,
        )
        
        # Step 2: Generate degraded (faulty) telemetry with specific faults injected
        # The kwargs contain parameters like "solar_hour=6.0, solar_factor=0.7"
        # which tell the simulator when to start the fault and how severe it is
        power_deg = self.power_sim.run_degraded(
            solar_degradation_hour=kwargs.get("solar_hour", 999),  # 999 means no degradation
            solar_factor=kwargs.get("solar_factor", 0.7),
            battery_degradation_hour=kwargs.get("battery_hour", 999),
            battery_factor=kwargs.get("battery_factor", 0.8),
        )
        thermal_deg = self.thermal_sim.run_degraded(
            power_deg.solar_input,
            power_deg.battery_charge,
            power_deg.battery_voltage,
            panel_degradation_hour=kwargs.get("panel_hour", 999),
            panel_drift_rate=kwargs.get("panel_drift", 0.5),
            battery_cooling_hour=kwargs.get("cooling_hour", 999),
            battery_cooling_factor=kwargs.get("cooling_factor", 0.5),
        )
        
        # Step 3: Combine power and thermal telemetry into a single unified object
        # This mirrors how an operator would see all subsystem data together
        from main import CombinedTelemetry
        nominal = CombinedTelemetry(power_nom, thermal_nom)
        degraded = CombinedTelemetry(power_deg, thermal_deg)
        
        return nominal, degraded, true_cause
    
    def run_scenario(self, nominal, degraded, true_cause):
        """
        Test both approaches on a scenario and return their ranks.
        
        Why we measure "rank": If an approach correctly identifies the root cause
        as the #1 most likely cause, we call that a "hit" (rank=1). If it ranks
        it #2, rank=2, etc. A lower rank is better. This metric is more nuanced
        than just binary correct/incorrect because ranking matters operationally:
        if an operator sees root cause A ranked first and true cause ranked second,
        they'll likely check A first (which is still useful even if not perfect).
        
        Returns (causal_rank, baseline_rank) where rank 1 is best (most likely).
        """
        
        # Step 1: Run causal approach
        # This uses the explicit causal graph to trace deviations back to root causes
        causal_hyps = self.causal_ranker.analyze(nominal, degraded, deviation_threshold=0.15)
        # Extract just the cause names in rank order
        causal_causes = [h.name for h in causal_hyps]
        
        # Step 2: Run baseline approach
        # This uses simple pattern matching on observables
        baseline_causes = self.baseline_ranker.rank_causes(nominal, degraded)
        
        # Step 3: Find where each approach ranked the true cause
        # If the true cause is in the ranked list, find its position (1-indexed)
        # If it's not in the list, assign it rank = number_of_causes + 1 (worst possible)
        causal_rank = causal_causes.index(true_cause) + 1 if true_cause in causal_causes else len(causal_causes) + 1
        baseline_rank = baseline_causes.index(true_cause) + 1 if true_cause in baseline_causes else len(baseline_causes) + 1
        
        return causal_rank, baseline_rank
    
    def add_noise(self, array, noise_level=0.05):
        """
        Add Gaussian noise to an array to simulate realistic sensor noise.
        
        Why this matters: Real satellites have noisy sensors. A robust diagnosis
        system must work even when sensor readings are imperfect. By testing at
        different noise levels (0%, 5%, 10%, 20%), we can see if causal reasoning
        is more robust to noise than simple correlation.
        
        We scale noise proportionally to the signal mean so that a high-value
        signal (e.g., solar_input=500W) gets proportionally more noise than a
        low-value signal (e.g., battery_temp=30C). This is realistic: a 5% error
        on a 500W signal is 25W, while 5% error on 30C is 1.5C.
        """
        
        # If no noise requested, return the original array unchanged
        if noise_level == 0:
            return array
        
        # Generate Gaussian noise with standard deviation = noise_level * mean_signal
        # This ensures noise scales with signal magnitude (proportional noise model)
        noise = np.random.normal(0, noise_level * np.abs(array).mean(), len(array))
        
        # Return original signal plus noise
        return array + noise
    
    def benchmark_fault_severity(self):
        """
        Test how each approach handles faults of varying severity.
        
        Why test severity: In real operations, faults can be subtle (1% loss)
        or catastrophic (50% loss). An effective diagnosis system should work
        across this range. This test specifically looks at solar degradation
        at 4 different severity levels and measures ranking accuracy at each.
        
        The hypothesis: Causal reasoning should maintain accuracy across
        severity levels because it reasons about cause-effect relationships.
        Correlation-based approaches might fail on subtle faults (not enough
        signal) or misidentify causes when the fault is so severe that secondary
        effects dominate (confounding).
        """
        
        print("\n" + "="*70)
        print("FAULT SEVERITY ANALYSIS: Solar Degradation")
        print("="*70)
        
        # Test at 4 severity levels: 10% loss, 30% loss, 50% loss, 70% loss
        # We test 70% loss as the "severe" case because beyond that, the system
        # is essentially non-functional and diagnosis becomes trivial
        severities = [0.3, 0.5, 0.7, 0.9]
        results = {severity: {"causal": [], "baseline": []} for severity in severities}
        
        for severity in severities:
            print(f"\nTesting at {(1-severity)*100:.0f}% loss...")
            
            # Run each severity level twice to get a more stable average
            # (one trial is noisy due to random initialization in simulators)
            for trial in range(2):
                nominal, degraded, _ = self.create_scenario(
                    "solar_degradation",
                    solar_hour=6.0,  # Fault starts at 6 hours
                    solar_factor=severity  # How much power remains (0.3 = 70% loss)
                )
                causal_rank, baseline_rank = self.run_scenario(nominal, degraded, "solar_degradation")
                results[severity]["causal"].append(causal_rank)
                results[severity]["baseline"].append(baseline_rank)
        
        # Print results in a table format for easy comparison
        print(f"\n{'Loss':<12} {'Causal Rank':<15} {'Baseline Rank':<15}")
        print(" " * 42)
        for sev in severities:
            causal_mean = np.mean(results[sev]["causal"])
            baseline_mean = np.mean(results[sev]["baseline"])
            print(f"{(1-sev)*100:>6.0f}%     {causal_mean:>6.2f}           {baseline_mean:>6.2f}")
    
    def benchmark_noise_robustness(self):
        """
        Test robustness to measurement noise from imperfect sensors.
        
        Why test noise: In production, satellite sensors are not perfect.
        They have noise from electronics, quantization, calibration drift, etc.
        A practical diagnosis system must tolerate this noise and still identify
        root causes correctly.
        
        We test at 4 noise levels (0%, 5%, 10%, 20%) on battery heatsink failure.
        The hypothesis: Causal reasoning uses the entire graph structure and
        consistency checks, so it might be MORE robust to noise than simple
        correlation which relies on exact pattern matching.
        """
        
        print("\n" + "="*70)
        print("NOISE ROBUSTNESS ANALYSIS: Battery Heatsink Failure")
        print("="*70)
        
        # Test at 4 noise levels, from perfectly clean (0%) to quite noisy (20%)
        # Beyond 20%, data becomes essentially useless for diagnosis anyway
        noise_levels = [0.0, 0.05, 0.10, 0.20]
        results = {nl: {"causal": [], "baseline": []} for nl in noise_levels}
        
        for noise_level in noise_levels:
            print(f"\nTesting with {noise_level*100:.0f}% noise...")
            
            # Run twice per noise level to average out randomness
            for trial in range(2):
                nominal, degraded, _ = self.create_scenario(
                    "battery_heatsink_failure",
                    cooling_hour=8.0,  # Cooling failure starts at 8 hours
                    cooling_factor=0.5  # Cooling effectiveness drops to 50%
                )
                
                # Add noise to key telemetry signals
                # We add noise to the signals most affected by the heatsink failure
                degraded.battery_temp = self.add_noise(degraded.battery_temp, noise_level)
                degraded.bus_current = self.add_noise(degraded.bus_current, noise_level)
                degraded.battery_voltage = self.add_noise(degraded.battery_voltage, noise_level)
                
                causal_rank, baseline_rank = self.run_scenario(nominal, degraded, "battery_heatsink_failure")
                results[noise_level]["causal"].append(causal_rank)
                results[noise_level]["baseline"].append(baseline_rank)
        
        # Print results in table format
        print(f"\n{'Noise':<12} {'Causal Rank':<15} {'Baseline Rank':<15}")
        print(" " * 42)
        for nl in noise_levels:
            causal_mean = np.mean(results[nl]["causal"])
            baseline_mean = np.mean(results[nl]["baseline"])
            print(f"{nl*100:>6.1f}%     {causal_mean:>6.2f}           {baseline_mean:>6.2f}")
    
    def benchmark(self):
        """
        Run comprehensive benchmark suite across 12 diverse scenarios.
        
        Why 12 scenarios: We want to test across multiple dimensions:
        - Fault type: power (solar) vs thermal (cooling) vs multi-fault
        - Fault severity: mild (20% loss) vs moderate (30% loss) vs severe (60% loss)
        - Fault timing: early (6 hours) vs late (18 hours)
        
        This breadth of scenarios gives confidence that results generalize
        and aren't just lucky on a few specific cases.
        """
        
        print("=" * 70)
        print("BENCHMARK: Causal Inference vs Correlation Baseline (12 Scenarios)")
        print("=" * 70)
        
        # Define 12 test scenarios covering different fault modes
        # Each scenario specifies which root cause was injected and when/how severe
        scenarios = [
            # Mild severity single faults (20% loss or less)
            # These represent early-stage degradation in production
            ("solar_degradation", {"solar_hour": 6.0, "solar_factor": 0.8}),
            ("battery_aging", {"battery_hour": 8.0, "battery_factor": 0.85}),
            ("battery_heatsink_failure", {"cooling_hour": 8.0, "cooling_factor": 0.6}),
            
            # Moderate severity single faults (30% loss)
            # These represent mid-stage degradation
            ("solar_degradation", {"solar_hour": 6.0, "solar_factor": 0.7}),
            ("battery_heatsink_failure", {"cooling_hour": 8.0, "cooling_factor": 0.5}),
            
            # Severe single faults (60%+ loss)
            # These represent advanced degradation
            ("solar_degradation", {"solar_hour": 6.0, "solar_factor": 0.4}),
            ("battery_heatsink_failure", {"cooling_hour": 6.0, "cooling_factor": 0.2}),
            
            # Multi-fault scenarios (where causal reasoning should shine)
            # Solar degradation + thermal degradation simultaneously
            ("solar_degradation", {"solar_hour": 6.0, "solar_factor": 0.7, "cooling_hour": 8.0, "cooling_factor": 0.5}),
            # Thermal degradation + solar degradation (same fault, different perspective)
            ("battery_heatsink_failure", {"cooling_hour": 8.0, "cooling_factor": 0.5, "solar_hour": 6.0, "solar_factor": 0.7}),
            # Solar degradation + battery aging (two independent power subsystem faults)
            ("solar_degradation", {"solar_hour": 5.0, "solar_factor": 0.6, "battery_hour": 8.0, "battery_factor": 0.8}),
            
            # Late-onset faults (fault appears 18 hours into 24-hour observation window)
            # These test if approaches can diagnose faults that appear near the end
            ("solar_degradation", {"solar_hour": 18.0, "solar_factor": 0.7}),
            ("battery_heatsink_failure", {"cooling_hour": 18.0, "cooling_factor": 0.5}),
        ]
        
        # Storage for results from all scenarios
        causal_ranks = []
        baseline_ranks = []
        
        print(f"\nRunning {len(scenarios)} scenarios...\n")
        
        # Run each scenario and record how each approach ranked the true root cause
        for idx, (true_cause, kwargs) in enumerate(scenarios, 1):
            # Create scenario with known ground truth
            nominal, degraded, _ = self.create_scenario(true_cause, **kwargs)
            # Test both approaches
            causal_rank, baseline_rank = self.run_scenario(nominal, degraded, true_cause)
            
            # Store results
            causal_ranks.append(causal_rank)
            baseline_ranks.append(baseline_rank)
            
            # Format results for readable output
            # "HIT" means rank 1 (correct), otherwise show actual rank
            status_causal = "HIT" if causal_rank == 1 else f"RANK{causal_rank}"
            status_baseline = "HIT" if baseline_rank == 1 else f"RANK{baseline_rank}"
            
            # Determine scenario characteristics for the output label
            fault_count = ("cooling_hour" in kwargs) + ("solar_hour" in kwargs) + ("battery_hour" in kwargs)
            if fault_count >= 2:
                scenario_type = "multi-fault"
            elif "cooling_hour" in kwargs:
                scenario_type = "thermal"
            else:
                scenario_type = "power"
            
            # Infer severity from the degradation factor
            # 0.8+ means mild, 0.5-0.8 means moderate, <0.5 means severe
            severity = "mild" if kwargs.get("solar_factor", 1.0) >= 0.8 else "severe" if kwargs.get("solar_factor", 1.0) <= 0.5 else "moderate"
            
            # Print result line with scenario details and outcomes
            print(f"[{idx:2d}] {true_cause:25s} ({scenario_type:10s}/{severity:8s}) | Causal: {status_causal:8s} | Baseline: {status_baseline:8s}")
        
        # Compute and display aggregate metrics
        print("\n" + "=" * 70)
        print("RESULTS SUMMARY")
        print("=" * 70)
        
        # Top-1 accuracy: how often did each approach rank the true cause first?
        # This is the strictest metric but also operationally most important
        causal_acc = sum(1 for r in causal_ranks if r == 1) / len(causal_ranks)
        baseline_acc = sum(1 for r in baseline_ranks if r == 1) / len(baseline_ranks)
        
        # Mean rank: on average, where did each approach rank the true cause?
        # Lower is better. A mean rank of 1.0 means always correct.
        causal_mean_rank = np.mean(causal_ranks)
        baseline_mean_rank = np.mean(baseline_ranks)
        
        # Top-3 accuracy: how often was the true cause in the top 3 ranked causes?
        # This is more lenient (gives an operator a few guesses) but more achievable
        causal_top3 = sum(1 for r in causal_ranks if r <= 3) / len(causal_ranks)
        baseline_top3 = sum(1 for r in baseline_ranks if r <= 3) / len(baseline_ranks)
        
        # Display metrics with improvements (positive = causal is better)
        print(f"\nTop-1 Accuracy:")
        print(f"  Causal:      {causal_acc:.1%}")
        print(f"  Baseline:    {baseline_acc:.1%}")
        print(f"  Improvement: {(causal_acc - baseline_acc):+.1%}")
        
        print(f"\nTop-3 Accuracy:")
        print(f"  Causal:      {causal_top3:.1%}")
        print(f"  Baseline:    {baseline_top3:.1%}")
        print(f"  Improvement: {(causal_top3 - baseline_top3):+.1%}")
        
        print(f"\nMean Rank (lower is better):")
        print(f"  Causal:      {causal_mean_rank:.2f}")
        print(f"  Baseline:    {baseline_mean_rank:.2f}")
        print(f"  Improvement: {(baseline_mean_rank - causal_mean_rank):+.2f}")
        
        # Break down performance by scenario type to identify where causal reasoning helps most
        print(f"\n" + "=" * 70)
        print("DETAILED ANALYSIS BY SCENARIO TYPE")
        print("=" * 70)
        
        # Mild single-fault scenarios (indices 0, 1, 2)
        # These should be easy for both approaches since the fault is obvious
        print("\nSingle Fault (mild):")
        print("  Causal top-1:", sum(1 for i in [0,1,2] if causal_ranks[i] == 1), "/3")
        print("  Baseline top-1:", sum(1 for i in [0,1,2] if baseline_ranks[i] == 1), "/3")
        
        # Moderate single-fault scenarios (indices 3, 4)
        # Medium difficulty
        print("\nSingle Fault (moderate):")
        print("  Causal top-1:", sum(1 for i in [3,4] if causal_ranks[i] == 1), "/2")
        print("  Baseline top-1:", sum(1 for i in [3,4] if baseline_ranks[i] == 1), "/2")
        
        # Severe single-fault scenarios (indices 5, 6)
        # Hard because multiple secondary effects dominate
        print("\nSingle Fault (severe):")
        print("  Causal top-1:", sum(1 for i in [5,6] if causal_ranks[i] == 1), "/2")
        print("  Baseline top-1:", sum(1 for i in [5,6] if baseline_ranks[i] == 1), "/2")
        
        # Multi-fault scenarios (indices 7, 8, 9)
        # This is where causal reasoning should have the biggest advantage
        # because multiple causes create confounding effects that correlation misses
        print("\nMulti-Fault Scenarios:")
        print("  Causal top-1:", sum(1 for i in [7,8,9] if causal_ranks[i] == 1), "/3")
        print("  Baseline top-1:", sum(1 for i in [7,8,9] if baseline_ranks[i] == 1), "/3")
        
        print("\n" + "=" * 70)


if __name__ == "__main__":
    # Create a single benchmark instance
    benchmark = Benchmark()
    
    # Step 1: Run the main 12-scenario benchmark
    # This gives overall performance metrics across diverse scenarios
    benchmark.benchmark()
    
    # Step 2: Run fault severity analysis
    # This tests how each approach scales with fault magnitude
    print("\n\n")
    benchmark.benchmark_fault_severity()
    
    # Step 3: Run noise robustness analysis
    # This tests how well each approach tolerates sensor noise
    print("\n\n")
    benchmark.benchmark_noise_robustness()
