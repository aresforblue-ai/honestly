"""
Anomaly Detection Service
=========================

Isolation Forest-based anomaly detection for ZK proof patterns.
Detects:
- Suspicious reputation jumps
- Proof generation bursts
- Nullifier clustering (sybil detection)
- Capability fraud patterns

Usage:
    from ml.anomaly_detector import get_detector

    detector = get_detector()
    score = detector.analyze_proof(proof_data, agent_id="...")
    # score.anomaly_score: 0.0 (normal) to 1.0 (highly anomalous)
    # score.flags: ["reputation_jump", "burst_pattern", ...]
"""

import logging
import os
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# Try to import sklearn, fallback to simple heuristics if not available
try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler

    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available, using heuristic anomaly detection")


@dataclass
class AnomalyScore:
    """Result of anomaly analysis."""

    anomaly_score: float  # 0.0 (normal) to 1.0 (highly anomalous)
    is_anomalous: bool  # True if score > threshold
    flags: List[str] = field(default_factory=list)  # Specific anomaly flags
    details: Dict[str, Any] = field(default_factory=dict)  # Additional context
    confidence: float = 0.0  # Model confidence (0-1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_score": round(self.anomaly_score, 4),
            "is_anomalous": self.is_anomalous,
            "flags": self.flags,
            "details": self.details,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class ProofFeatures:
    """Extracted features from a proof for anomaly detection."""

    # Timing features
    hour_of_day: int
    day_of_week: int
    time_since_last_proof: float  # seconds

    # Pattern features
    proof_count_1h: int  # Proofs from same agent in last hour
    proof_count_24h: int  # Proofs from same agent in last 24h
    unique_nullifiers_1h: int  # Unique nullifiers in last hour

    # Reputation features (for reputation proofs)
    reputation_delta: float  # Change from last known reputation
    threshold_requested: int  # Threshold in proof

    # Capability features (for capability proofs)
    capability_count: int  # Number of capabilities claimed
    new_capabilities: int  # Capabilities not seen before

    def to_array(self) -> np.ndarray:
        return np.array(
            [
                self.hour_of_day,
                self.day_of_week,
                self.time_since_last_proof,
                self.proof_count_1h,
                self.proof_count_24h,
                self.unique_nullifiers_1h,
                self.reputation_delta,
                self.threshold_requested,
                self.capability_count,
                self.new_capabilities,
            ]
        )


class AnomalyDetector:
    """
    ML-based anomaly detector for ZK proofs.

    Uses Isolation Forest for unsupervised anomaly detection,
    with heuristic fallback when sklearn is not available.
    """

    # Thresholds for heuristic detection
    REPUTATION_JUMP_THRESHOLD = 25  # Points per 24h
    BURST_THRESHOLD_1H = 20  # Max proofs per hour
    BURST_THRESHOLD_24H = 100  # Max proofs per 24h
    SYBIL_NULLIFIER_RATIO = 0.5  # Unique nullifiers / total proofs

    def __init__(
        self,
        model_path: Optional[Path] = None,
        anomaly_threshold: float = 0.7,
        use_ml: bool = True,
    ):
        """
        Initialize the anomaly detector.

        Args:
            model_path: Path to saved model (optional)
            anomaly_threshold: Score threshold for flagging anomalies (0-1)
            use_ml: Whether to use ML model (if available)
        """
        self.anomaly_threshold = anomaly_threshold
        self.use_ml = use_ml and SKLEARN_AVAILABLE

        self.model: Optional[IsolationForest] = None
        self.scaler: Optional[StandardScaler] = None
        self._history: Dict[str, List[Dict]] = {}  # agent_id -> proof history

        if model_path and model_path.exists():
            self._load_model(model_path)
        elif self.use_ml:
            self._init_model()

    def _init_model(self) -> None:
        """Initialize a new Isolation Forest model."""
        self.model = IsolationForest(
            n_estimators=100,
            contamination=0.1,  # Expected proportion of anomalies
            random_state=42,
            n_jobs=-1,  # Use all cores
        )
        self.scaler = StandardScaler()
        logger.info("Initialized new Isolation Forest model")

    def _load_model(self, path: Path) -> None:
        """Load a pre-trained model."""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.scaler = data["scaler"]
            logger.info(f"Loaded anomaly detection model from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            if self.use_ml:
                self._init_model()

    def save_model(self, path: Path) -> None:
        """Save the trained model."""
        if self.model and self.scaler:
            with open(path, "wb") as f:
                pickle.dump({"model": self.model, "scaler": self.scaler}, f)
            logger.info(f"Saved model to {path}")

    def _extract_features(
        self,
        proof_data: Dict[str, Any],
        agent_id: str,
        proof_type: str,
    ) -> ProofFeatures:
        """Extract features from a proof for anomaly detection."""
        now = datetime.utcnow()
        history = self._history.get(agent_id, [])

        # Timing features
        hour_of_day = now.hour
        day_of_week = now.weekday()

        # Time since last proof
        if history:
            last_ts = history[-1].get("timestamp", now - timedelta(days=1))
            time_since_last = (now - last_ts).total_seconds()
        else:
            time_since_last = 86400  # Default to 24h

        # Count proofs in time windows
        proof_count_1h = sum(
            1 for p in history if (now - p.get("timestamp", now)).total_seconds() < 3600
        )
        proof_count_24h = sum(
            1 for p in history if (now - p.get("timestamp", now)).total_seconds() < 86400
        )

        # Unique nullifiers (sybil detection)
        recent_nullifiers = set(
            p.get("nullifier")
            for p in history
            if (now - p.get("timestamp", now)).total_seconds() < 3600 and p.get("nullifier")
        )
        unique_nullifiers_1h = len(recent_nullifiers)

        # Reputation features
        reputation_delta = 0.0
        threshold_requested = 0
        if proof_type == "agent_reputation":
            public_signals = proof_data.get("publicSignals", [])
            if len(public_signals) > 1:
                threshold_requested = (
                    int(public_signals[1]) if str(public_signals[1]).isdigit() else 0
                )

            # Check reputation history
            rep_history = [
                p.get("threshold", 0) for p in history if p.get("proof_type") == "agent_reputation"
            ]
            if rep_history:
                reputation_delta = threshold_requested - rep_history[-1]

        # Capability features
        capability_count = 0
        new_capabilities = 0
        if proof_type == "agent_capability":
            capability_count = len(proof_data.get("capabilities", []))
            known_caps = set(cap for p in history for cap in p.get("capabilities", []))
            current_caps = set(proof_data.get("capabilities", []))
            new_capabilities = len(current_caps - known_caps)

        return ProofFeatures(
            hour_of_day=hour_of_day,
            day_of_week=day_of_week,
            time_since_last_proof=time_since_last,
            proof_count_1h=proof_count_1h,
            proof_count_24h=proof_count_24h,
            unique_nullifiers_1h=unique_nullifiers_1h,
            reputation_delta=reputation_delta,
            threshold_requested=threshold_requested,
            capability_count=capability_count,
            new_capabilities=new_capabilities,
        )

    def _heuristic_score(self, features: ProofFeatures) -> Tuple[float, List[str]]:
        """Calculate anomaly score using heuristics (no ML)."""
        score = 0.0
        flags = []

        # Reputation jump detection
        if abs(features.reputation_delta) > self.REPUTATION_JUMP_THRESHOLD:
            score += 0.3
            flags.append("reputation_jump")

        # Burst detection
        if features.proof_count_1h > self.BURST_THRESHOLD_1H:
            score += 0.3
            flags.append("burst_1h")
        if features.proof_count_24h > self.BURST_THRESHOLD_24H:
            score += 0.2
            flags.append("burst_24h")

        # Sybil detection (low nullifier diversity)
        if features.proof_count_1h > 5:
            nullifier_ratio = features.unique_nullifiers_1h / features.proof_count_1h
            if nullifier_ratio < self.SYBIL_NULLIFIER_RATIO:
                score += 0.4
                flags.append("sybil_pattern")

        # Unusual timing (late night activity)
        if features.hour_of_day >= 2 and features.hour_of_day <= 5:
            score += 0.1
            flags.append("unusual_timing")

        # Rapid-fire proofs
        if features.time_since_last_proof < 1.0:  # < 1 second
            score += 0.2
            flags.append("rapid_fire")

        # New capabilities spike
        if features.new_capabilities > 3:
            score += 0.2
            flags.append("capability_spike")

        return min(score, 1.0), flags

    def _ml_score(self, features: ProofFeatures) -> Tuple[float, float]:
        """Calculate anomaly score using Isolation Forest."""
        if not self.model or not self.scaler:
            return 0.5, 0.0  # Uncertain score

        try:
            X = features.to_array().reshape(1, -1)
            X_scaled = self.scaler.transform(X)

            # Get anomaly score (-1 = anomaly, 1 = normal)
            raw_score = self.model.decision_function(X_scaled)[0]

            # Convert to 0-1 scale (higher = more anomalous)
            anomaly_score = max(0, min(1, 0.5 - raw_score * 0.5))

            # Confidence based on how far from decision boundary
            confidence = min(1.0, abs(raw_score) / 0.5)

            return anomaly_score, confidence
        except Exception as e:
            logger.error(f"ML scoring failed: {e}")
            return 0.5, 0.0

    def analyze_proof(
        self,
        proof_data: Dict[str, Any],
        agent_id: str,
        proof_type: str = "age",
        record: bool = True,
    ) -> AnomalyScore:
        """
        Analyze a proof for anomalies.

        Args:
            proof_data: The proof data (parsed JSON)
            agent_id: Agent/user identifier
            proof_type: Type of proof (age, agent_reputation, etc.)
            record: Whether to record this proof in history

        Returns:
            AnomalyScore with score, flags, and details
        """
        features = self._extract_features(proof_data, agent_id, proof_type)

        # Get heuristic score (always)
        heuristic_score, flags = self._heuristic_score(features)

        # Get ML score if available
        ml_score = 0.0
        confidence = 0.0
        if self.use_ml and self.model:
            ml_score, confidence = self._ml_score(features)
            # Combine scores (weighted average)
            final_score = 0.6 * ml_score + 0.4 * heuristic_score
        else:
            final_score = heuristic_score
            confidence = 0.8  # High confidence in heuristics

        # Record proof in history
        if record:
            if agent_id not in self._history:
                self._history[agent_id] = []

            self._history[agent_id].append(
                {
                    "timestamp": datetime.utcnow(),
                    "proof_type": proof_type,
                    "nullifier": proof_data.get("publicSignals", [None])[-1],
                    "threshold": features.threshold_requested,
                    "capabilities": proof_data.get("capabilities", []),
                }
            )

            # Trim history (keep last 1000 proofs per agent)
            if len(self._history[agent_id]) > 1000:
                self._history[agent_id] = self._history[agent_id][-1000:]

        return AnomalyScore(
            anomaly_score=final_score,
            is_anomalous=final_score > self.anomaly_threshold,
            flags=flags,
            details={
                "features": {
                    "proof_count_1h": features.proof_count_1h,
                    "proof_count_24h": features.proof_count_24h,
                    "reputation_delta": features.reputation_delta,
                    "time_since_last": features.time_since_last_proof,
                },
                "ml_score": round(ml_score, 4) if self.use_ml else None,
                "heuristic_score": round(heuristic_score, 4),
            },
            confidence=confidence,
        )

    def analyze_batch(
        self,
        proofs: List[Dict[str, Any]],
        agent_id: str,
    ) -> List[AnomalyScore]:
        """Analyze a batch of proofs."""
        return [
            self.analyze_proof(
                proof.get("proof_data", {}),
                agent_id,
                proof.get("proof_type", "age"),
            )
            for proof in proofs
        ]

    def train(self, training_data: List[Dict[str, Any]]) -> None:
        """
        Train the ML model on historical proof data.

        Args:
            training_data: List of proof records with features
        """
        if not self.use_ml:
            logger.warning("ML not available, skipping training")
            return

        if len(training_data) < 100:
            logger.warning(f"Insufficient training data ({len(training_data)}), need 100+")
            return

        # Extract features from training data
        X = []
        for record in training_data:
            features = ProofFeatures(
                hour_of_day=record.get("hour_of_day", 12),
                day_of_week=record.get("day_of_week", 0),
                time_since_last_proof=record.get("time_since_last", 3600),
                proof_count_1h=record.get("proof_count_1h", 1),
                proof_count_24h=record.get("proof_count_24h", 5),
                unique_nullifiers_1h=record.get("unique_nullifiers_1h", 1),
                reputation_delta=record.get("reputation_delta", 0),
                threshold_requested=record.get("threshold", 50),
                capability_count=record.get("capability_count", 0),
                new_capabilities=record.get("new_capabilities", 0),
            )
            X.append(features.to_array())

        X = np.array(X)

        # Fit scaler and model
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)

        logger.info(f"Trained anomaly detection model on {len(X)} samples")

    def get_stats(self) -> Dict[str, Any]:
        """Get detector statistics."""
        total_agents = len(self._history)
        total_proofs = sum(len(h) for h in self._history.values())

        return {
            "total_agents_tracked": total_agents,
            "total_proofs_analyzed": total_proofs,
            "ml_enabled": self.use_ml,
            "model_trained": self.model is not None and hasattr(self.model, "estimators_"),
            "anomaly_threshold": self.anomaly_threshold,
        }


# Singleton instance
_detector: Optional[AnomalyDetector] = None


def get_detector() -> AnomalyDetector:
    """Get the global anomaly detector instance."""
    global _detector
    if _detector is None:
        model_path = Path(os.environ.get("ANOMALY_MODEL_PATH", ""))
        _detector = AnomalyDetector(
            model_path=model_path if model_path.exists() else None,
            anomaly_threshold=float(os.environ.get("ANOMALY_THRESHOLD", "0.7")),
        )
    return _detector
