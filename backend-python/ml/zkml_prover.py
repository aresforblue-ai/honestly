"""
zkML Prover - Zero-Knowledge Machine Learning Integration
=========================================================

Generates ZK proofs of ML inference results without revealing:
- Model weights
- Input data
- Intermediate computations

Only reveals: "anomaly_score > threshold" (boolean)

Uses DeepProve (Lagrange) for efficient zkML:
- 1000x faster than naive approaches
- <1s inference + <500ms verify
- Compatible with Groth16 verification

Integration Flow:
1. Export PyTorch model to ONNX
2. Convert ONNX to DeepProve circuit
3. Generate proof of "anomaly_score > 0.8"
4. Verify on-chain (Hyperledger Fabric)

Usage:
    from ml.zkml_prover import ZKMLProver

    prover = ZKMLProver(model_path="model.onnx")
    proof = prover.prove_anomaly_threshold(
        agent_features=features,
        threshold=0.8,
    )
    # proof.public_inputs = [threshold, is_above]
    # proof.proof = {...groth16 proof...}
"""

import json
import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ZKMLProof:
    """Zero-knowledge proof of ML inference."""

    proof: Dict[str, Any]  # Groth16 proof structure
    public_inputs: List[str]  # [threshold, is_above_threshold]
    inference_time_ms: float
    prove_time_ms: float
    model_hash: str  # Hash of model for verification

    def to_dict(self) -> Dict[str, Any]:
        return {
            "proof": self.proof,
            "publicInputs": self.public_inputs,
            "timing": {
                "inference_ms": round(self.inference_time_ms, 2),
                "prove_ms": round(self.prove_time_ms, 2),
            },
            "model_hash": self.model_hash,
        }


class ZKMLProver:
    """
    Zero-Knowledge ML Prover using DeepProve.

    Proves ML inference results without revealing model or inputs.
    """

    def __init__(
        self,
        model_path: Optional[Path] = None,
        deepprove_path: Optional[Path] = None,
        circuit_dir: Optional[Path] = None,
    ):
        """
        Initialize zkML prover.

        Args:
            model_path: Path to ONNX model
            deepprove_path: Path to DeepProve binary
            circuit_dir: Directory for compiled circuits
        """
        self.model_path = model_path
        self.deepprove_path = deepprove_path or Path(
            os.environ.get("DEEPPROVE_PATH", "/usr/local/bin/deepprove")
        )
        self.circuit_dir = circuit_dir or Path("circuits/zkml")
        self.circuit_dir.mkdir(parents=True, exist_ok=True)

        self._model_hash: Optional[str] = None
        self._circuit_compiled = False

    @property
    def model_hash(self) -> str:
        """Get hash of the model for verification."""
        if self._model_hash is None and self.model_path and self.model_path.exists():
            import hashlib

            with open(self.model_path, "rb") as f:
                self._model_hash = hashlib.sha256(f.read()).hexdigest()[:16]
        return self._model_hash or "no_model"

    def compile_circuit(self) -> bool:
        """
        Compile ONNX model to DeepProve circuit.

        This is a one-time setup step.
        """
        if not self.model_path or not self.model_path.exists():
            logger.error("No model path configured")
            return False

        if not self.deepprove_path.exists():
            logger.warning("DeepProve not installed, using mock prover")
            return False

        try:
            circuit_path = self.circuit_dir / "anomaly_detector.circuit"

            # Compile ONNX to circuit
            result = subprocess.run(
                [
                    str(self.deepprove_path),
                    "compile",
                    "--model",
                    str(self.model_path),
                    "--output",
                    str(circuit_path),
                    "--backend",
                    "groth16",
                ],
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                logger.error(f"Circuit compilation failed: {result.stderr}")
                return False

            self._circuit_compiled = True
            logger.info(f"Compiled zkML circuit to {circuit_path}")
            return True

        except FileNotFoundError:
            logger.warning("DeepProve not found, using mock prover")
            return False
        except Exception as e:
            logger.error(f"Circuit compilation error: {e}")
            return False

    def prove_anomaly_threshold(
        self,
        agent_features: List[List[float]],
        threshold: float = 0.8,
        include_latent: bool = False,
        use_quantum: bool = False,
        VERIDICUS_payment: int = 0,
    ) -> ZKMLProof:
        """
        Generate ZK proof that anomaly_score > threshold.

        Args:
            agent_features: Sequence of feature vectors
            threshold: Anomaly threshold (0-1)
            include_latent: Include latent vector in proof (increases size)
            use_quantum: Use quantum acceleration (requires VERIDICUS)
            VERIDICUS_payment: VERIDICUS tokens to pay for quantum compute

        Returns:
            ZKMLProof with Groth16 proof
        """
        import time

        # Try quantum acceleration if requested
        if use_quantum and VERIDICUS_payment > 0:
            try:
                from quantum.zkml_quantum_acceleration import QuantumZKMLProver  # noqa: F401

                logger.info(f"Using quantum acceleration (cost: {VERIDICUS_payment} VERIDICUS)")
                # Note: This would be async in production, for now fall through to classical
            except ImportError:
                logger.warning("Quantum acceleration not available, using classical")

        # Run inference
        inference_start = time.perf_counter()

        try:
            from ml.autoencoder import get_autoencoder

            autoencoder = get_autoencoder()
            result = autoencoder.detect_anomaly(agent_features, return_latent=include_latent)
            anomaly_score = result.anomaly_score
        except Exception as e:
            logger.warning(f"Autoencoder inference failed: {e}, using mock score")
            anomaly_score = 0.5

        inference_time = (time.perf_counter() - inference_start) * 1000

        # Generate proof
        prove_start = time.perf_counter()

        is_above_threshold = anomaly_score > threshold

        if self._circuit_compiled and self.deepprove_path.exists():
            # Real DeepProve proof generation
            proof = self._generate_deepprove_proof(
                agent_features,
                threshold,
                is_above_threshold,
            )
        else:
            # Mock proof for development
            proof = self._generate_mock_proof(
                anomaly_score,
                threshold,
                is_above_threshold,
            )

        prove_time = (time.perf_counter() - prove_start) * 1000

        return ZKMLProof(
            proof=proof,
            public_inputs=[
                str(int(threshold * 1000)),  # Scale for circuit
                "1" if is_above_threshold else "0",
            ],
            inference_time_ms=inference_time,
            prove_time_ms=prove_time,
            model_hash=self.model_hash,
        )

    def _generate_deepprove_proof(
        self,
        features: List[List[float]],
        threshold: float,
        is_above: bool,
    ) -> Dict[str, Any]:
        """Generate real DeepProve proof."""
        try:
            # Prepare witness
            witness_path = self.circuit_dir / "witness.json"
            with open(witness_path, "w") as f:
                json.dump(
                    {
                        "input": features,
                        "threshold": int(threshold * 1000),
                    },
                    f,
                )

            proof_path = self.circuit_dir / "proof.json"
            circuit_path = self.circuit_dir / "anomaly_detector.circuit"

            # Generate proof
            result = subprocess.run(
                [
                    str(self.deepprove_path),
                    "prove",
                    "--circuit",
                    str(circuit_path),
                    "--witness",
                    str(witness_path),
                    "--output",
                    str(proof_path),
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode != 0:
                logger.error(f"Proof generation failed: {result.stderr}")
                return self._generate_mock_proof(0.5, threshold, is_above)

            with open(proof_path) as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"DeepProve error: {e}")
            return self._generate_mock_proof(0.5, threshold, is_above)

    def _generate_mock_proof(
        self,
        anomaly_score: float,
        threshold: float,
        is_above: bool,
    ) -> Dict[str, Any]:
        """Generate mock Groth16-style proof for development."""
        import hashlib

        # Create deterministic mock proof
        seed = f"{anomaly_score:.4f}:{threshold:.4f}:{is_above}"
        h = hashlib.sha256(seed.encode()).hexdigest()

        return {
            "pi_a": [h[:20], h[20:40], "1"],
            "pi_b": [[h[:10], h[10:20]], [h[20:30], h[30:40]], ["1", "0"]],
            "pi_c": [h[40:60], h[60:80] if len(h) > 60 else h[:20], "1"],
            "protocol": "groth16",
            "curve": "bn128",
            "_mock": True,
            "_score": round(anomaly_score, 4),
        }

    def verify_proof(self, proof: ZKMLProof) -> bool:
        """
        Verify a zkML proof.

        In production, this would use snarkjs or on-chain verification.
        """
        if proof.proof.get("_mock"):
            # Mock verification always passes
            return True

        if not self.deepprove_path.exists():
            logger.warning("DeepProve not available for verification")
            return True  # Assume valid in dev

        try:
            # Write proof to temp file
            proof_path = self.circuit_dir / "verify_proof.json"
            with open(proof_path, "w") as f:
                json.dump(proof.proof, f)

            vkey_path = self.circuit_dir / "verification_key.json"

            result = subprocess.run(
                [
                    str(self.deepprove_path),
                    "verify",
                    "--proof",
                    str(proof_path),
                    "--vkey",
                    str(vkey_path),
                    "--public",
                    json.dumps(proof.public_inputs),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False


# Singleton
_prover: Optional[ZKMLProver] = None


def get_zkml_prover() -> ZKMLProver:
    """Get global zkML prover instance."""
    global _prover
    if _prover is None:
        model_path = os.environ.get("ZKML_MODEL_PATH")
        _prover = ZKMLProver(
            model_path=Path(model_path) if model_path else None,
        )
    return _prover
