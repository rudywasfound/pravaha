"""
Utility functions for analyzing causal graph structure.
"""

from causal_graph.graph_definition import CausalGraph, NodeType


def print_structure_by_type(graph: CausalGraph):
    """Print nodes grouped by type."""
    for node_type in [NodeType.ROOT_CAUSE, NodeType.INTERMEDIATE, NodeType.OBSERVABLE]:
        nodes = [n for n, nd in graph.nodes.items() if nd.node_type == node_type]
        if nodes:
            print(f"\n{node_type.value.upper()}:")
            for name in sorted(nodes):
                node = graph.nodes[name]
                print(f"  • {name:30s} - {node.description}")


def print_edges(graph: CausalGraph):
    """Print all edges with weights."""
    print("\nCAUSAL EDGES:")
    for edge in sorted(graph.edges, key=lambda e: (e.source, e.target)):
        print(f"  {edge.source:30s} → {edge.target:30s} (w={edge.weight:.2f})")


def find_paths_from_observable(graph: CausalGraph, observable: str, max_depth: int = 10):
    """Trace causal paths from observable back to root causes."""
    return graph.get_paths_to_root(observable, max_depth)
