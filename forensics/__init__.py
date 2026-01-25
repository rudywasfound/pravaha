"""
Forensics module for post-mortem satellite failure analysis.

Provides specialized capabilities for reconstructing failure timelines,
identifying early warning signs, and computing lead-time advantages
over traditional threshold-based monitoring.
"""

from forensics.gsat6a_forensic import GSAT6AForensicAnalyzer, ForensicEvent, ForensicLeadTime

__all__ = ["GSAT6AForensicAnalyzer", "ForensicEvent", "ForensicLeadTime"]
