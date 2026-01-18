# Pravaha: Project Status

## Overview

Causal inference framework for multi-fault satellite failure diagnosis. Implements Bayesian graph-based root cause ranking across power and thermal subsystems.

**Status:** Phases 1-3 complete. 27 tests passing.

## Architecture

```
Telemetry Simulators
  - power.py (250 LOC): Solar panels, battery, bus voltage
  - thermal.py (250 LOC): Panel, battery, payload temps
       |
       v
Causal Graph (23 nodes, 29 edges)
  - 7 root causes
  - 8 intermediate states
  - 8 observable telemetry
  - Power-thermal coupling
       |
       v
Root Cause Ranker
  - Anomaly detection
  - Graph traversal
  - Bayesian scoring
  - Probability normalization
       |
       v
Ranked Hypotheses + Mechanisms
```

## Components

| Module | Lines | Purpose |
|--------|-------|---------|
| simulator/power.py | 250 | Power subsystem telemetry |
| simulator/thermal.py | 250 | Thermal subsystem telemetry |
| causal_graph/graph_definition.py | 400 | DAG: nodes, edges, traversal |
| causal_graph/root_cause_ranking.py | 350 | Bayesian inference |
| analysis/residual_analyzer.py | 150 | Deviation quantification |
| visualization/plotter.py | 150 | Comparison plots |

**Total core:** ~1500 LOC  
**Total tests:** ~600 LOC  
**Test count:** 27 (100% pass)

## Root Causes Detected

**Power subsystem:**
- solar_degradation
- battery_aging
- battery_thermal
- sensor_bias

**Thermal subsystem:**
- panel_insulation_degradation
- battery_heatsink_failure
- payload_radiator_degradation

## Usage

```bash
# Phases 1-2: Power subsystem analysis
python main.py

# Phase 3: Thermal + multi-fault scenarios
python main_phase3.py

# Run all tests
python -m unittest discover tests/ -v
```

## Test Coverage

- Power simulator: 5 tests (initialization, bounds, degradation)
- Causal graph: 5 tests (construction, traversal, paths)
- Root cause ranking: 7 tests (ranking, probability, detection)
- Thermal simulator: 10 tests (oscillations, stress, failures)
- Integration: 1 test (power+thermal combined)

## Performance

- 24-hour simulation: < 1 second
- Root cause ranking: 0.05 seconds
- All tests: 0.6 seconds
- Memory: < 50 MB

## Causal Graph Structure

### Root Causes (7)
```
solar_degradation
battery_aging
battery_thermal
sensor_bias
panel_insulation_degradation
battery_heatsink_failure
payload_radiator_degradation
```

### Intermediate Nodes (8)
```
solar_input → battery_state → bus_regulation
battery_efficiency ↔ battery_temp
solar_panel_temp ↔ battery_temp
payload_temp ↔ thermal_stress
```

### Observables (8)
```
Power:
  - solar_input_measured
  - battery_voltage_measured
  - battery_charge_measured
  - bus_voltage_measured

Thermal:
  - solar_panel_temp_measured
  - battery_temp_measured
  - payload_temp_measured
  - bus_current_measured
```

## Key Technical Decisions

1. **Graph-based reasoning** - Domain knowledge encoded as DAG, not learned
2. **Simulation-first** - Realistic simulators for controlled experimentation
3. **Lightweight Bayesian** - No heavy math; path strength × consistency × severity
4. **Power-thermal coupling** - Models feedback loops between subsystems

## Example Output

```
ROOT CAUSE RANKING ANALYSIS

Most Likely Root Causes:

1. solar_degradation         P=46.3%  Confidence=93.3%
2. battery_aging             P=18.8%  Confidence=71.7%
3. battery_thermal           P=18.7%  Confidence=75.0%
4. sensor_bias               P=16.3%  Confidence=75.0%

DETAILED EXPLANATIONS:

• solar_degradation (P=46.3%)
  Evidence: solar_input deviation, battery_charge deviation
  Mechanism: Reduced solar input is propagating through the power subsystem.
  This suggests solar panel degradation or shadowing, which reduces
  available power for charging the battery.
```

## Phase 4: Benchmarking (Future)

- Correlation baseline implementation
- 50+ multi-fault scenario generator
- Noise injection (1%, 5%, 10%)
- Missing data robustness (10%, 25%, 50%)
- Accuracy/precision metrics
- Paper-style results


## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Run framework: `python main.py`
3. Run tests: `python -m unittest discover tests/ -v`
4. See QUICKSTART.md for detailed instructions
