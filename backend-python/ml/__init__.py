"""
ML Module for Honestly
======================

Phase 3 ML integration: Anomaly detection, zkML, and pattern analysis.

Components:
- anomaly_detector: Isolation forest + heuristics for proof anomalies
- reputation_analyzer: Time series analysis for reputation proofs
- autoencoder: LSTM autoencoder for sequence anomaly detection
- zkml_prover: Zero-knowledge ML proofs (DeepProve integration)
- neo4j_loader: Training data from Neo4j graph

Architecture:
    Neo4j → neo4j_loader → autoencoder (train)
                              ↓
    agent_features → autoencoder → anomaly_score
                              ↓
                     zkml_prover → ZK proof of "score > threshold"
                              ↓
                     Hyperledger Fabric (on-chain anchor)
"""

from .anomaly_detector import AnomalyDetector, get_detector, AnomalyScore
from .reputation_analyzer import ReputationAnalyzer
from .autoencoder import (
    create_autoencoder,
    get_autoencoder,
    AnomalyResult,
)
from .zkml_prover import ZKMLProver, get_zkml_prover, ZKMLProof
from .deepprove_integration import DeepProveZKML, get_deepprove_zkml, DeepProveProof
from .neo4j_loader import Neo4jDataLoader, create_training_dataset

__all__ = [
    # Anomaly detection
    "AnomalyDetector",
    "get_detector",
    "AnomalyScore",
    # Reputation analysis
    "ReputationAnalyzer",
    # Autoencoder
    "create_autoencoder",
    "get_autoencoder",
    "AnomalyResult",
    # zkML
    "ZKMLProver",
    "get_zkml_prover",
    "ZKMLProof",
    # DeepProve zkML
    "DeepProveZKML",
    "get_deepprove_zkml",
    "DeepProveProof",
    # Data loading
    "Neo4jDataLoader",
    "create_training_dataset",
]
