# Causal Graph Framework

Framework for defining and visualizing causal graphs in satellite diagnostics.

## Core Components

- **graph_definition.py**: DAG structure (nodes, edges, traversal)
- **visualizer.py**: Render graphs to PNG/PDF/SVG
- **d_separation.py**: Conditional independence analysis
- **root_cause_ranking.py**: Hypothesis scoring

## Quick Start

```python
from causal_graph import CausalGraph, DAGVisualizer

# Load graph
graph = CausalGraph()

# Visualize
viz = DAGVisualizer(graph)
viz.save("dag.png")

# Analyze
from causal_graph.d_separation import check_d_separation
is_independent = check_d_separation(graph, "A", "B", {"C"})
```

## Graph Structure

- **23 nodes**: Root causes, intermediates, observables
- **29 edges**: Causal relationships with weights and mechanisms
- **Layer-based layout**: Top (causes) → middle (propagation) → bottom (observables)
