# Quick Start

## Installation

```bash
cd /home/atix/pravaha
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Simulates nominal and degraded satellite telemetry, builds causal graph, ranks root causes. Outputs console report and plots to `output/`.

## Test

```bash
python -m unittest discover tests/ -v
```

Expected: 27 tests passing.

## What It Does

1. Simulates 24 hours of power and thermal telemetry
2. Detects observable deviations (>15% from nominal)
3. Traces deviations through causal graph to root causes
4. Scores hypotheses by path strength, consistency, severity
5. Returns ranked causes with confidence and mechanisms

## Modify Scenarios

Edit fault parameters in `main.py`:

```python
power_deg = power_sim.run_degraded(
    solar_degradation_hour=6.0,      # When fault occurs
    solar_factor=0.7,                # Severity
    battery_degradation_hour=8.0,
    battery_factor=0.8,
)
```

## Files

- `simulator/power.py` - Power subsystem
- `simulator/thermal.py` - Thermal subsystem
- `causal_graph/graph_definition.py` - DAG
- `causal_graph/root_cause_ranking.py` - Inference
- `main.py` - Entry point

## Documentation

- `README.md` - Full documentation
- `PROJECT_STATUS.md` - Architecture details
