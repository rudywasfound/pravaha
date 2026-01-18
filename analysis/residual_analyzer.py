"""
Residual and anomaly analysis for satellite telemetry.

This module quantifies what changed between nominal and degraded scenarios.
This is the bridge between raw data and causal inference:

Data flow:
Nominal telemetry --> Compute residuals --> Find deviations --> Feed to causal inference

Why residual analysis:
1. Anomaly detection: Flag significant deviations from baseline
2. Severity quantification: Measure how bad the fault is
3. Onset detection: When did the fault start?
4. Input to causal engine: Causal graph uses deviations to rank root causes

The residual analyzer uses simple statistics (mean, max, threshold) because:
1. Satellites have well-understood sensor noise characteristics
2. Domain experts can interpret simple metrics (voltage dropped by 2V)
3. Statistical approaches are more robust than complex ML models
4. We want explainability: why did we flag this deviation?
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict
from simulator.power import PowerTelemetry


@dataclass
class ResidualStats:
    """
    Container for residual analysis results.
    
    Each field represents a different view of the same underlying deviations:
    - mean_deviation: How much did each signal deviate on average?
    - max_deviation: What was the worst-case deviation?
    - onset_time: When did the fault first become detectable?
    - severity_score: How bad is the overall degradation (0-1 scale)?
    
    These metrics feed into the causal inference engine to identify root causes.
    """
    
    mean_deviation: Dict[str, float]  # Mean absolute deviation per metric
    max_deviation: Dict[str, float]   # Maximum deviation encountered
    onset_time: Dict[str, float]      # Time (hours) when deviation exceeds threshold
    severity_score: float             # Overall degradation severity (0-1)


class ResidualAnalyzer:
    """
    Analyze deviations between nominal and degraded telemetry.
    
    This class computes residuals (differences from baseline) and identifies
    which signals deviated significantly. These deviations are the observable
    evidence that the causal inference engine uses to identify root causes.
    
    Key insight: A deviation in a sensor is only meaningful if it's significantly
    larger than normal sensor noise. The deviation_threshold parameter defines
    what "significant" means. Setting it too low produces false positives
    (normal fluctuations flagged as anomalies). Setting it too high misses
    real faults (subtle degradation not detected).
    """

    def __init__(self, deviation_threshold: float = 0.1):
        """
        Initialize analyzer with sensitivity threshold.
        
        Args:
            deviation_threshold: Fractional threshold (0.1 = 10% deviation) to flag anomaly
            
        Why this threshold: Satellites have sensor noise of order 1-5%. If we set
        threshold to 0.05 (5%), we correctly flag 10-20% faults but also get false
        positives from noise. Setting to 0.15 (15%) eliminates false positives but
        might miss early-stage degradation. The 0.1-0.15 range is typical for
        real satellite operations.
        """
        
        self.deviation_threshold = deviation_threshold

    def analyze(
        self, nominal: PowerTelemetry, degraded: PowerTelemetry
    ) -> ResidualStats:
        """
        Compute residual statistics between nominal and degraded scenarios.

        Process:
        1. For each observable (voltage, current, etc), compute absolute deviation
        2. Find mean and max deviations
        3. Detect onset time (when deviation exceeds threshold)
        4. Compute overall severity score
        
        The output serves as input to the causal inference engine, which will
        interpret these deviations as evidence for or against each root cause.

        Args:
            nominal: PowerTelemetry from healthy scenario (baseline)
            degraded: PowerTelemetry from faulty scenario (what we're analyzing)

        Returns:
            ResidualStats with deviation metrics
        """
        
        # Define which metrics to analyze
        # We use power subsystem metrics here, but thermal could be added
        metrics = {
            "solar_input": (nominal.solar_input, degraded.solar_input),
            "battery_voltage": (nominal.battery_voltage, degraded.battery_voltage),
            "battery_charge": (nominal.battery_charge, degraded.battery_charge),
            "bus_voltage": (nominal.bus_voltage, degraded.bus_voltage),
        }

        # Storage for computed statistics
        mean_dev = {}
        max_dev = {}
        onset = {}

        # Compute statistics for each metric
        for name, (nom, deg) in metrics.items():
            # Residual: absolute difference between degraded and nominal
            # We use absolute value because we care about magnitude, not direction
            residual = np.abs(deg - nom)
            
            # Mean deviation: average magnitude of difference across all time samples
            mean_dev[name] = float(np.mean(residual))
            
            # Max deviation: worst-case difference encountered
            max_dev[name] = float(np.max(residual))

            # Onset time: when did the deviation first become significant?
            # Threshold is set relative to the nominal mean value
            # E.g., if solar input averages 250W, threshold at 15% = 37.5W
            # So we flag the first sample where solar deviation > 37.5W
            threshold = self.deviation_threshold * np.mean(nom)
            exceeds = np.where(residual > threshold)[0]
            
            if len(exceeds) > 0:
                # Convert sample index to time in hours
                # (nominal.time is in seconds, so divide by 3600)
                onset[name] = float(nominal.time[exceeds[0]] / 3600)
            else:
                # No deviation exceeded threshold, use infinity to indicate "never"
                onset[name] = float("inf")

        # Aggregate severity: normalize deviations and compute weighted score
        # This produces a single number (0-1) representing overall fault magnitude
        severity = self._compute_severity(mean_dev, max_dev, nominal)

        return ResidualStats(
            mean_deviation=mean_dev,
            max_deviation=max_dev,
            onset_time=onset,
            severity_score=severity,
        )

    def _compute_severity(
        self,
        mean_dev: Dict[str, float],
        max_dev: Dict[str, float],
        nominal: PowerTelemetry,
    ) -> float:
        """
        Compute overall degradation severity score (0-1).

        Why aggregate into one score:
        1. Operators need a quick overall assessment
        2. Different metrics have different scales (voltage vs charge percent)
        3. By normalizing each metric to a fraction, we can average them fairly
        
        The score helps prioritize urgency: 0.1 (minor) vs 0.5 (major) vs 0.9 (critical)
        
        Simple approach: For each metric, compute fractional deviation (actual_dev / baseline),
        then average across all metrics. Clip to [0,1] to handle edge cases.
        """
        
        fractions = []
        
        # For each observable metric, compute its fractional deviation
        for name in mean_dev.keys():
            # Determine the baseline value for this metric
            # (needed to normalize the deviation as a percentage)
            if "voltage" in name:
                baseline = nominal.battery_voltage.mean() if "battery" in name else nominal.bus_voltage.mean()
            elif "solar" in name:
                baseline = nominal.solar_input.mean()
            else:  # charge
                baseline = 50.0  # Typical mid-range charge state

            # Fractional deviation: actual_deviation / baseline
            # E.g., if solar input was 250W on average, and mean deviation is 50W,
            # fractional deviation = 50 / 250 = 0.2 (20% deviation)
            frac = mean_dev[name] / (baseline if baseline > 0 else 1.0)
            fractions.append(frac)

        # Average fractional deviations across all metrics
        severity = np.clip(np.mean(fractions), 0, 1)
        return float(severity)

    def print_report(self, stats: ResidualStats):
        """
        Pretty-print residual analysis report for human operators.
        
        Why formatted output: Operators need to quickly understand
        1. Overall severity (is this critical?)
        2. Which metrics deviated (where is the problem?)
        3. When did it start (do we have margin for response?)
        """
        
        print("\n" + "=" * 60)
        print("RESIDUAL ANALYSIS REPORT")
        print("=" * 60)

        # Overall severity at the top for quick decision making
        print(f"\nOverall Severity Score: {stats.severity_score:.2%}")
        
        # Mean deviations show typical magnitude of change
        print("\nMean Deviations:")
        for metric, value in sorted(stats.mean_deviation.items()):
            print(f"  {metric:20s}: {value:8.2f}")

        # Max deviations show worst-case impact
        print("\nMaximum Deviations:")
        for metric, value in sorted(stats.max_deviation.items()):
            print(f"  {metric:20s}: {value:8.2f}")

        # Onset times help operators understand fault timeline
        print("\nDegradation Onset Times (hours):")
        for metric, onset_h in sorted(stats.onset_time.items()):
            if np.isinf(onset_h):
                print(f"  {metric:20s}: No significant deviation detected")
            else:
                print(f"  {metric:20s}: {onset_h:6.2f}h")

        print("=" * 60 + "\n")


if __name__ == "__main__":
    # Quick test of residual analyzer
    from simulator.power import PowerSimulator

    sim = PowerSimulator(duration_hours=24)
    nominal = sim.run_nominal()
    degraded = sim.run_degraded(solar_degradation_hour=6.0, battery_degradation_hour=8.0)

    analyzer = ResidualAnalyzer(deviation_threshold=0.15)
    stats = analyzer.analyze(nominal, degraded)
    analyzer.print_report(stats)
