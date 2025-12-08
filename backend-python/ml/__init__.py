"""
ML Module for Honestly
======================

Anomaly detection and pattern analysis for ZK proofs and AAIP.

Components:
- anomaly_detector: Isolation forest for proof pattern anomalies
- reputation_analyzer: Time series analysis for reputation proofs
- sybil_detector: Nullifier clustering for sybil attack detection
"""

from .anomaly_detector import AnomalyDetector, get_detector
from .reputation_analyzer import ReputationAnalyzer

__all__ = [
    "AnomalyDetector",
    "get_detector",
    "ReputationAnalyzer",
]

