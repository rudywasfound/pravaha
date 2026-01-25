# Quick Start

## Installation

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run Full Analysis

```bash
python main.py
```

Simulates 24h of nominal and degraded satellite telemetry, detects deviations, ranks root causes. Output: plots + console report.

## Test Suite

```bash
python -m unittest discover tests/ -v
```

Expected: 27 tests passing.

## Using the Causal Graph Framework

```python
from causal_graph import CausalGraph, DAGVisualizer

# Load graph and visualize
graph = CausalGraph()
viz = DAGVisualizer(graph)
viz.save("dag.png")  # Outputs PNG image

# Analyze structure
from causal_graph.dag_visualization import print_structure_by_type
print_structure_by_type(graph)
```

## Customize Fault Scenarios

Edit `main.py`:

```python
power_deg = power_sim.run_degraded(
    solar_degradation_hour=6.0,   # When fault starts
    solar_factor=0.7,              # Severity (0-1)
    battery_degradation_hour=8.0,
    battery_factor=0.8,
)
```

## Key Modules

| Module | Purpose |
|--------|---------|
| `causal_graph/graph_definition.py` | DAG: 23 nodes, 29 edges |
| `causal_graph/visualizer.py` | Render graphs to PNG/PDF/SVG |
| `causal_graph/root_cause_ranking.py` | Bayesian inference |
| `simulator/power.py` | Power subsystem simulator |
| `simulator/thermal.py` | Thermal subsystem simulator |
| `main.py` | Full workflow orchestration |

See `README.md` for detailed architecture.
