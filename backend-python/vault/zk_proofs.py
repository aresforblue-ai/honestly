"""
Zero-knowledge proof generation and verification.

Supports two backends:
- SnarkJS (Node.js): Default for simple circuits (age, authenticity)
- Rapidsnark (C++): 5-10x faster for Level 3 and AAIP circuits

The service automatically selects the optimal backend based on circuit type.
"""

import json
import logging
import os
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Circuits that benefit from rapidsnark (Level 3 + AAIP)
RAPIDSNARK_CIRCUITS = {
    "age_level3",
    "level3_inequality",
    "agent_capability",
    "agent_reputation",
}


class ZKProofService:
    """
    Service for generating and verifying zkSNARK proofs.
    
    Automatically uses rapidsnark for Level 3/AAIP circuits when available,
    falls back to SnarkJS otherwise.
    """

    def __init__(
        self,
        runner_path: Optional[str] = None,
        use_rapidsnark: bool = True,
    ):
        base_dir = Path(__file__).resolve().parent.parent / "zkp"
        self.runner_path = Path(runner_path) if runner_path else base_dir / "snark-runner.js"
        self.use_rapidsnark = use_rapidsnark
        self._rapidsnark_prover = None
        
        # Lazy-load rapidsnark prover
        if use_rapidsnark:
            try:
                from zkp.rapidsnark_prover import RapidsnarkProver
                self._rapidsnark_prover = RapidsnarkProver(artifacts_dir=base_dir / "artifacts")
                if self._rapidsnark_prover._rapidsnark_available:
                    logger.info("Rapidsnark prover initialized successfully")
                else:
                    logger.warning("Rapidsnark binary not found, using SnarkJS for all circuits")
                    self._rapidsnark_prover = None
            except ImportError:
                logger.warning("rapidsnark_prover module not found, using SnarkJS for all circuits")

    def _should_use_rapidsnark(self, circuit: str) -> bool:
        """Determine if rapidsnark should be used for this circuit."""
        return (
            self._rapidsnark_prover is not None
            and circuit in RAPIDSNARK_CIRCUITS
        )

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

    # =========================================================================
    # Level 3 Circuits (use Rapidsnark for 5-10x speedup)
    # =========================================================================

    def generate_age_level3_proof(
        self,
        birth_date: str,
        min_age: int,
        document_hash: str,
        reference_ts: Optional[int] = None,
        epoch: int = 0,
    ) -> Dict[str, Any]:
        """
        Generate Level 3 age proof with nullifier binding.
        Uses rapidsnark for fast proving (~2s vs 10s+ with SnarkJS).
        """
        birth_dt = datetime.fromisoformat(birth_date)
        birth_ts = int(birth_dt.timestamp())
        ref_ts = reference_ts or int(datetime.utcnow().timestamp())

        payload = {
            "birthTs": str(birth_ts),
            "referenceTs": str(ref_ts),
            "minAge": str(min_age),
            "documentHashHex": self._strip_hex_prefix(document_hash),
            "salt": str(secrets.randbits(128)),
            "epoch": str(epoch),
        }

        if self._should_use_rapidsnark("age_level3"):
            logger.info("Using rapidsnark for age_level3 proof")
            proof, public_signals = self._rapidsnark_prover.prove("age_level3", payload)
            nullifier = public_signals[-1] if public_signals else None
            return {
                "proof_data": json.dumps({"proof": proof, "publicSignals": public_signals}),
                "public_inputs": json.dumps({"publicSignals": public_signals}),
                "proof_type": "age_level3_proof",
                "nullifier": nullifier,
            }
        else:
            bundle = self._run("prove", "age_level3", payload)
            nullifier = bundle.get("publicSignals", [])[-1] if bundle.get("publicSignals") else None
            return {
                "proof_data": json.dumps(bundle),
                "public_inputs": json.dumps(bundle.get("namedSignals", {})),
                "proof_type": "age_level3_proof",
                "nullifier": nullifier,
            }

    # =========================================================================
    # AAIP Circuits (AI Agent Identity Protocol)
    # =========================================================================

    def generate_agent_capability_proof(
        self,
        agent_id: str,
        capability_hash: str,
        capability_index: int,
        capabilities: list,
        agent_commitment: str,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate proof that an AI agent has a specific capability.
        
        Args:
            agent_id: Private agent identifier
            capability_hash: Public hash of capability to prove
            capability_index: Private index of capability in agent's list
            capabilities: Private list of agent's capability hashes (8 elements)
            agent_commitment: Public commitment to agent identity
            timestamp: Proof timestamp (default: now)
        
        Returns:
            Proof bundle with nullifier for replay prevention
        """
        ts = timestamp or int(datetime.utcnow().timestamp())
        salt = secrets.randbits(128)

        # Pad capabilities to 8 elements
        caps = capabilities[:8] + ["0"] * (8 - len(capabilities))

        payload = {
            "agentID": agent_id,
            "capabilityIndex": str(capability_index),
            "salt": str(salt),
            "capabilities": caps,
            "capabilityHash": capability_hash,
            "agentCommitment": agent_commitment,
            "timestamp": str(ts),
        }

        if self._should_use_rapidsnark("agent_capability"):
            logger.info("Using rapidsnark for agent_capability proof")
            proof, public_signals = self._rapidsnark_prover.prove("agent_capability", payload)
            nullifier = public_signals[0] if public_signals else None
            return {
                "proof_data": json.dumps({"proof": proof, "publicSignals": public_signals}),
                "proof_type": "agent_capability_proof",
                "nullifier": nullifier,
                "verified": public_signals[1] == "1" if len(public_signals) > 1 else False,
            }
        else:
            bundle = self._run("prove", "agent_capability", payload)
            public_signals = bundle.get("publicSignals", [])
            return {
                "proof_data": json.dumps(bundle),
                "proof_type": "agent_capability_proof",
                "nullifier": public_signals[0] if public_signals else None,
                "verified": public_signals[1] == "1" if len(public_signals) > 1 else False,
            }

    def generate_agent_reputation_proof(
        self,
        reputation_score: int,
        threshold: int,
        agent_did_hash: str,
        interaction_count: int = 0,
        positive_count: int = 0,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate proof that an AI agent's reputation exceeds a threshold.
        
        Args:
            reputation_score: Private actual reputation (0-100)
            threshold: Public minimum reputation to prove
            agent_did_hash: Public hash of agent's DID
            interaction_count: Private total interactions
            positive_count: Private positive interactions
            timestamp: Proof timestamp (default: now)
        
        Returns:
            Proof bundle with nullifier and reputation commitment
        """
        ts = timestamp or int(datetime.utcnow().timestamp())
        salt = secrets.randbits(128)

        payload = {
            "reputationScore": str(reputation_score),
            "salt": str(salt),
            "interactionCount": str(interaction_count),
            "positiveCount": str(positive_count),
            "threshold": str(threshold),
            "agentDIDHash": agent_did_hash,
            "timestamp": str(ts),
        }

        if self._should_use_rapidsnark("agent_reputation"):
            logger.info("Using rapidsnark for agent_reputation proof")
            proof, public_signals = self._rapidsnark_prover.prove("agent_reputation", payload)
            return {
                "proof_data": json.dumps({"proof": proof, "publicSignals": public_signals}),
                "proof_type": "agent_reputation_proof",
                "nullifier": public_signals[0] if public_signals else None,
                "verified": public_signals[1] == "1" if len(public_signals) > 1 else False,
                "reputation_commitment": public_signals[2] if len(public_signals) > 2 else None,
            }
        else:
            bundle = self._run("prove", "agent_reputation", payload)
            public_signals = bundle.get("publicSignals", [])
            return {
                "proof_data": json.dumps(bundle),
                "proof_type": "agent_reputation_proof",
                "nullifier": public_signals[0] if public_signals else None,
                "verified": public_signals[1] == "1" if len(public_signals) > 1 else False,
                "reputation_commitment": public_signals[2] if len(public_signals) > 2 else None,
            }

    def verify_agent_proof(
        self,
        proof_data: str,
        circuit: str = "agent_capability",
        check_nullifier: bool = True,
    ) -> bool:
        """
        Verify an AAIP agent proof (capability or reputation).
        
        Args:
            proof_data: JSON string containing proof bundle
            circuit: Circuit name (agent_capability or agent_reputation)
            check_nullifier: If True, check nullifier hasn't been used
        
        Returns:
            True if proof is valid and nullifier not used
        """
        try:
            bundle = json.loads(proof_data)
        except Exception:
            return False

        public_signals = bundle.get("publicSignals", [])
        if not public_signals:
            return False

        nullifier = public_signals[0]

        # Check nullifier
        if check_nullifier:
            from vault.nullifier_storage import verify_nullifier_not_used, mark_nullifier_used
            if not verify_nullifier_not_used(nullifier):
                return False

        # Verify proof
        try:
            if self._rapidsnark_prover:
                proof = bundle.get("proof", bundle)
                verified = self._rapidsnark_prover.verify(circuit, proof, public_signals)
            else:
                result = self._run("verify", circuit, bundle)
                verified = bool(result.get("verified"))

            if verified and check_nullifier:
                from vault.nullifier_storage import mark_nullifier_used
                mark_nullifier_used(nullifier)

            return verified
        except Exception:
            return False

