"""
Framework for visualizing causal graphs as static images.

Exports:
    - DAGVisualizer: Renders causal graphs to PNG images
    - Supported formats: PNG, PDF, SVG
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from typing import Dict, Tuple
import os

from causal_graph.graph_definition import CausalGraph, NodeType


class DAGVisualizer:
    """Convert causal graph to image visualization."""
    
    # Color scheme by node type
    COLORS = {
        NodeType.ROOT_CAUSE: "#FF6B6B",      # Red
        NodeType.INTERMEDIATE: "#4ECDC4",    # Teal
        NodeType.OBSERVABLE: "#45B7D1",      # Blue
    }
    
    SYMBOLS = {
        NodeType.ROOT_CAUSE: "*",
        NodeType.INTERMEDIATE: "D",
        NodeType.OBSERVABLE: "o",
    }
    
    def __init__(self, graph: CausalGraph, figsize: Tuple[int, int] = (16, 10)):
        """
        Initialize visualizer.
        
        Args:
            graph: CausalGraph instance
            figsize: Figure size (width, height) in inches
        """
        self.graph = graph
        self.figsize = figsize
        self.node_positions = {}
        self._compute_positions()
    
    def _compute_positions(self):
        """Compute 2D positions for nodes using layer-based layout."""
        root_causes = []
        intermediates = []
        observables = []
        
        for name, node in self.graph.nodes.items():
            if node.node_type == NodeType.ROOT_CAUSE:
                root_causes.append(name)
            elif node.node_type == NodeType.INTERMEDIATE:
                intermediates.append(name)
            else:
                observables.append(name)
        
        root_causes.sort()
        intermediates.sort()
        observables.sort()
        
        layers = [root_causes, intermediates, observables]
        for layer_idx, layer in enumerate(layers):
            y = -layer_idx * 3
            if len(layer) > 0:
                x_start = -(len(layer) - 1) * 1.5 / 2
                for node_idx, node_name in enumerate(layer):
                    x = x_start + node_idx * 1.5
                    self.node_positions[node_name] = (x, y)
    
    def save(self, output_path: str = "dag.png", dpi: int = 150) -> str:
        """
        Generate and save visualization to image file.
        
        Args:
            output_path: Output file path (auto-detects format from extension)
            dpi: Resolution for PNG/JPEG output
            
        Returns:
            Path to saved file
        """
        fig, ax = plt.subplots(figsize=self.figsize)
        
        # Draw edges
        for edge in self.graph.edges:
            x0, y0 = self.node_positions[edge.source]
            x1, y1 = self.node_positions[edge.target]
            
            arrow = FancyArrowPatch(
                (x0, y0), (x1, y1),
                arrowstyle='-|>',
                mutation_scale=20,
                linewidth=max(0.5, edge.weight * 2),
                alpha=edge.weight * 0.6 + 0.2,
                color='gray',
            )
            ax.add_patch(arrow)
        
        # Draw nodes
        for name, node in self.graph.nodes.items():
            x, y = self.node_positions[name]
            color = self.COLORS[node.node_type]
            marker = self.SYMBOLS[node.node_type]
            
            ax.scatter(x, y, s=400, c=color, marker=marker, 
                      edgecolors='white', linewidth=2, zorder=10)
            ax.text(x, y - 0.4, name, ha='center', va='top', 
                   fontsize=8, wrap=True)
        
        # Legend
        legend_elements = [
            mpatches.Patch(color=self.COLORS[NodeType.ROOT_CAUSE], 
                          label='Root Causes'),
            mpatches.Patch(color=self.COLORS[NodeType.INTERMEDIATE], 
                          label='Intermediates'),
            mpatches.Patch(color=self.COLORS[NodeType.OBSERVABLE], 
                          label='Observables'),
        ]
        ax.legend(handles=legend_elements, loc='upper right')
        
        ax.set_xlim(-8, 8)
        ax.set_ylim(-8, 2)
        ax.axis('off')
        ax.set_aspect('equal')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=dpi, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        return output_path
