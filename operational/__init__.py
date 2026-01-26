"""
Operational integration components for Aethelix.

Connects the causal inference engine to real satellite operations:
- Telemetry ingestion and simulation
- Continuous monitoring service
- Alert management
- Dashboard integration
- Data persistence

See OPERATIONAL_INTEGRATION_ROADMAP.md for architecture and timeline.
"""

from .telemetry_simulator import TelemetrySimulator, Measurement

__all__ = [
    'TelemetrySimulator',
    'Measurement',
]
