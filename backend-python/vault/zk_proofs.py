"""
Zero-knowledge proof generation and verification using circom/snarkjs.
Relies on the local Node-based runner at backend-python/zkp/snark-runner.js.
"""

import json
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class ZKProofService:
    """Service for generating and verifying zkSNARK proofs via snarkjs runner."""

    def __init__(self, runner_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent / "zkp"
        self.runner_path = Path(runner_path) if runner_path else base_dir / "snark-runner.js"

    def _run(self, action: str, circuit: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the Node snark-runner with JSON payload via stdin."""
        if not self.runner_path.exists():
            raise RuntimeError(
                f"snark runner not found at {self.runner_path}. Build zk artifacts under backend-python/zkp."
            )

        cmd = ["node", str(self.runner_path), action, circuit]
        proc = subprocess.run(
            cmd,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError(f"zk runner failed: {proc.stderr.strip() or proc.stdout.strip()}")

        try:
            return json.loads(proc.stdout)
        except Exception as exc:
            raise RuntimeError(f"invalid runner output: {proc.stdout}") from exc

    def _strip_hex_prefix(self, value: str) -> str:
        return value[2:] if value.startswith("0x") else value

    def generate_age_proof(
        self,
        birth_date: str,  # ISO format: YYYY-MM-DD
        min_age: int,
        document_hash: str,
        reference_ts: Optional[int] = None,
        epoch: int = 0,
    ) -> Dict[str, Any]:
        """Generate zkSNARK age proof using Groth16 with nullifier."""
        birth_dt = datetime.fromisoformat(birth_date)
        birth_ts = int(birth_dt.timestamp())
        ref_ts = reference_ts or int(datetime.utcnow().timestamp())

        if ref_ts <= birth_ts:
            raise ValueError("reference timestamp must be after birth date")

        payload = {
            "birthTs": str(birth_ts),
            "referenceTs": str(ref_ts),
            "minAge": str(min_age),
            "documentHashHex": self._strip_hex_prefix(document_hash),
            "salt": str(secrets.randbits(128)),
            "epoch": str(epoch),  # Private epoch for age circuit
        }

        bundle = self._run("prove", "age", payload)
        public_inputs = bundle.get("namedSignals", {})
        
        # Extract nullifier from public signals (last signal)
        nullifier = bundle.get("publicSignals", [])[-1] if bundle.get("publicSignals") else None

        return {
            "proof_data": json.dumps(bundle),
            "public_inputs": json.dumps(public_inputs),
            "proof_type": "age_proof",
            "nullifier": nullifier,  # For nullifier tracking
        }

    def verify_age_proof(
        self,
        proof_data: str,
        public_inputs: str = "",
        check_nullifier: bool = True,
    ) -> bool:
        """
        Verify zkSNARK age proof with nullifier check.
        
        Args:
            proof_data: JSON string containing proof bundle
            public_inputs: JSON string containing public inputs (unused, kept for compatibility)
            check_nullifier: If True, check nullifier hasn't been used (one-time use)
        
        Returns:
            True if proof is valid and nullifier not used, False otherwise
        """
        try:
            bundle = json.loads(proof_data)
        except Exception:
            return False

        # Extract nullifier from public signals (last signal)
        public_signals = bundle.get("publicSignals", [])
        if not public_signals:
            return False
        
        nullifier = public_signals[-1]
        
        # Check nullifier hasn't been used (one-time use prevention)
        if check_nullifier:
            from vault.nullifier_storage import verify_nullifier_not_used, mark_nullifier_used
            
            if not verify_nullifier_not_used(nullifier):
                return False  # Nullifier already used
        
        # Verify proof
        try:
            result = self._run("verify", "age", bundle)
            verified = bool(result.get("verified"))
            
            # Mark nullifier as used AFTER successful verification
            if verified and check_nullifier:
                from vault.nullifier_storage import mark_nullifier_used
                mark_nullifier_used(nullifier)
            
            return verified
        except Exception:
            return False

    def generate_authenticity_proof(
        self,
        document_hash: str,
        merkle_root: str,
        merkle_proof: Optional[list] = None,
        merkle_positions: Optional[list] = None,
        epoch: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate a zkSNARK Merkle inclusion proof with nullifier.
        merkle_proof: list of sibling hex hashes (same length as positions)
        merkle_positions: list of 0/1 integers (0 = sibling on left, 1 = sibling on right)
        epoch: public epoch number (for freshness enforcement and nullifier purging)
        """
        if merkle_proof is None or merkle_positions is None:
            raise ValueError("merkle_proof and merkle_positions are required for authenticity proofs")

        if len(merkle_proof) != len(merkle_positions):
            raise ValueError("merkle_proof and merkle_positions must have the same length")

        payload = {
            "leafHex": self._strip_hex_prefix(document_hash),
            "rootHex": self._strip_hex_prefix(merkle_root),
            "pathElementsHex": [self._strip_hex_prefix(p) for p in merkle_proof],
            "pathIndices": merkle_positions,
            "salt": str(secrets.randbits(128)),  # Private salt for nullifier
            "epoch": str(epoch),  # Public epoch for authenticity circuit
        }

        bundle = self._run("prove", "authenticity", payload)
        public_inputs = bundle.get("namedSignals", {})
        
        # Extract epoch and nullifier from public signals
        public_signals = bundle.get("publicSignals", [])
        epoch_out = int(public_signals[-2]) if len(public_signals) >= 2 else None
        nullifier = public_signals[-1] if public_signals else None

        return {
            "proof_data": json.dumps(bundle),
            "public_inputs": json.dumps(public_inputs),
            "proof_type": "authenticity_proof",
            "epoch": epoch_out,  # For freshness checks
            "nullifier": nullifier,  # For nullifier tracking
        }

    def verify_authenticity_proof(
        self,
        proof_data: str,
        public_inputs: str = "",
        check_nullifier: bool = True,
        current_epoch: Optional[int] = None,
    ) -> bool:
        """
        Verify zkSNARK authenticity proof with nullifier and epoch checks.
        
        Args:
            proof_data: JSON string containing proof bundle
            public_inputs: JSON string containing public inputs (unused, kept for compatibility)
            check_nullifier: If True, check nullifier hasn't been used (one-time use)
            current_epoch: Current epoch number (for freshness enforcement)
        
        Returns:
            True if proof is valid, nullifier not used, and epoch is current
        """
        try:
            bundle = json.loads(proof_data)
        except Exception:
            return False

        # Extract epoch and nullifier from public signals
        public_signals = bundle.get("publicSignals", [])
        if len(public_signals) < 2:
            return False
        
        epoch_out = int(public_signals[-2])  # Second-to-last signal
        nullifier = public_signals[-1]  # Last signal
        
        # Enforce freshness: require current epoch (if specified)
        if current_epoch is not None and epoch_out < current_epoch:
            return False  # Proof from old epoch
        
        # Check nullifier hasn't been used (one-time use prevention)
        if check_nullifier:
            from vault.nullifier_storage import verify_nullifier_not_used, mark_nullifier_used
            
            if not verify_nullifier_not_used(nullifier, epoch=epoch_out):
                return False  # Nullifier already used
        
        # Verify proof
        try:
            result = self._run("verify", "authenticity", bundle)
            verified = bool(result.get("verified"))
            
            # Mark nullifier as used AFTER successful verification
            if verified and check_nullifier:
                from vault.nullifier_storage import mark_nullifier_used
                mark_nullifier_used(nullifier, epoch=epoch_out)
            
            return verified
        except Exception:
            return False

