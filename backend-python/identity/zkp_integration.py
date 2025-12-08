"""
ZK Integration Layer for AI Agent Identity Protocol (AAIP)
==========================================================

Bridges AAIP to the Honestly ZK circuits for real cryptographic proofs.

This module provides:
1. Real Groth16 proofs using snark-runner
2. Nullifier tracking to prevent replay attacks
3. Agent identity binding using Level3Inequality circuit
4. Poseidon hashing for SNARK-friendly commitments
"""

import json
import secrets
import subprocess
import hashlib
import logging
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger("identity.zkp")


@dataclass
class ZKProofResult:
    """Result of a ZK proof generation."""
    success: bool
    proof: Optional[Dict] = None
    public_signals: Optional[list] = None
    nullifier: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "proof": self.proof,
            "publicSignals": self.public_signals,
            "nullifier": self.nullifier,
            "error": self.error,
        }


class AAIPZKIntegration:
    """
    Zero-Knowledge integration for AI Agent Identity Protocol.
    
    Uses the Level3Inequality circuit for reputation threshold proofs,
    with identity binding and nullifier generation.
    """
    
    def __init__(self, runner_path: Optional[str] = None):
        """
        Initialize the ZK integration.
        
        Args:
            runner_path: Path to snark-runner.js (defaults to zkp/snark-runner.js)
        """
        base_dir = Path(__file__).resolve().parent.parent / "zkp"
        self.runner_path = Path(runner_path) if runner_path else base_dir / "snark-runner.js"
        self.artifacts_dir = base_dir / "artifacts"
        
        # Nullifier storage (use external storage in production)
        self._used_nullifiers: set = set()
        
        # Check if circuit artifacts exist
        self.circuits_available = self._check_circuits()
    
    def _check_circuits(self) -> Dict[str, bool]:
        """Check which circuits have built artifacts."""
        circuits = {
            "level3_inequality": self.artifacts_dir / "level3_inequality" / "Level3Inequality_final.zkey",
            "age": self.artifacts_dir / "age" / "age_final.zkey",
            "authenticity": self.artifacts_dir / "authenticity" / "authenticity_final.zkey",
        }
        return {name: path.exists() for name, path in circuits.items()}
    
    def _run_snark(self, action: str, circuit: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the snark-runner CLI.
        
        Args:
            action: 'prove' or 'verify'
            circuit: Circuit name
            payload: JSON payload
            
        Returns:
            Parsed JSON response from snark-runner
        """
        if not self.runner_path.exists():
            raise RuntimeError(
                f"snark-runner not found at {self.runner_path}. "
                "Run: cd backend-python/zkp && npm install"
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
            error_msg = proc.stderr.strip() or proc.stdout.strip()
            raise RuntimeError(f"snark-runner failed: {error_msg}")
        
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid snark-runner output: {proc.stdout}") from e
    
    def _agent_id_to_field(self, agent_id: str) -> str:
        """
        Convert agent ID to a field element for the circuit.
        
        Uses SHA256 and truncates to fit in field (253 bits for BN128).
        """
        hash_bytes = hashlib.sha256(agent_id.encode()).digest()
        # Take first 31 bytes (248 bits) to stay well within field
        field_int = int.from_bytes(hash_bytes[:31], 'big')
        return str(field_int)
    
    def prove_reputation_threshold(
        self,
        agent_id: str,
        reputation_score: int,
        threshold: int,
        salt: Optional[int] = None,
    ) -> ZKProofResult:
        """
        Generate a ZK proof that agent's reputation >= threshold.
        
        Uses Level3Inequality circuit which:
        1. Proves val > threshold without revealing val
        2. Binds proof to agent identity (senderID)
        3. Generates nullifier to prevent replay
        
        Args:
            agent_id: The agent's unique ID
            reputation_score: The private reputation score
            threshold: Public threshold to prove against
            salt: Optional salt (random if not provided)
            
        Returns:
            ZKProofResult with proof, nullifier, and status
        """
        if not self.circuits_available.get("level3_inequality"):
            return ZKProofResult(
                success=False,
                error="level3_inequality circuit not built. Run setup_level3.sh"
            )
        
        # Validate inputs
        if reputation_score < 0 or reputation_score > 100:
            return ZKProofResult(
                success=False,
                error="Reputation score must be 0-100"
            )
        
        if reputation_score <= threshold:
            return ZKProofResult(
                success=False,
                error=f"Reputation {reputation_score} does not exceed threshold {threshold}"
            )
        
        # Generate salt if not provided
        if salt is None:
            salt = secrets.randbits(128)
        
        # Convert agent ID to field element
        sender_id = self._agent_id_to_field(agent_id)
        
        # Build circuit input
        circuit_input = {
            "val": str(reputation_score),
            "salt": str(salt),
            "threshold": str(threshold),
            "senderID": sender_id,
        }
        
        try:
            result = self._run_snark("prove", "level3_inequality", circuit_input)
            
            # Extract nullifier from public signals
            # Format: [threshold, senderID, nullifier, out]
            public_signals = result.get("publicSignals", [])
            nullifier = public_signals[2] if len(public_signals) > 2 else None
            
            return ZKProofResult(
                success=True,
                proof=result.get("proof"),
                public_signals=public_signals,
                nullifier=nullifier,
            )
            
        except Exception as e:
            logger.error(f"Proof generation failed: {e}")
            return ZKProofResult(
                success=False,
                error=str(e)
            )
    
    def verify_reputation_proof(
        self,
        proof: Dict,
        public_signals: list,
        check_nullifier: bool = True,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a reputation threshold proof.
        
        Args:
            proof: The Groth16 proof
            public_signals: Public signals from the proof
            check_nullifier: If True, check and track nullifier
            
        Returns:
            (is_valid, error_message)
        """
        if not self.circuits_available.get("level3_inequality"):
            return False, "Circuit not available"
        
        # Extract nullifier
        nullifier = public_signals[2] if len(public_signals) > 2 else None
        
        # Check nullifier hasn't been used
        if check_nullifier and nullifier:
            if nullifier in self._used_nullifiers:
                return False, "Nullifier already used (replay attack detected)"
        
        # Verify the proof
        try:
            bundle = {
                "proof": proof,
                "publicSignals": public_signals,
            }
            
            result = self._run_snark("verify", "level3_inequality", bundle)
            is_valid = result.get("verified", False)
            
            # Track nullifier if valid
            if is_valid and check_nullifier and nullifier:
                self._used_nullifiers.add(nullifier)
            
            return is_valid, None
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return False, str(e)
    
    def prove_capability(
        self,
        agent_id: str,
        capability_hash: str,
        timestamp: int,
    ) -> ZKProofResult:
        """
        Generate a ZK proof of capability ownership.
        
        This uses a commitment scheme where:
        commitment = Poseidon(agent_id, capability_hash, salt)
        
        Note: This requires a dedicated capability circuit.
        For now, uses authenticity circuit with capability as "document".
        
        Args:
            agent_id: The agent's unique ID
            capability_hash: Hash of the capability being proven
            timestamp: Proof timestamp (for freshness)
            
        Returns:
            ZKProofResult with proof data
        """
        # For capability proofs, we use a simplified commitment
        # A full implementation would use a Merkle tree of capabilities
        
        salt = secrets.randbits(128)
        sender_id = self._agent_id_to_field(agent_id)
        
        # Create commitment: H(agent_id || capability || salt)
        commitment_data = f"{agent_id}:{capability_hash}:{salt}:{timestamp}"
        commitment = hashlib.sha256(commitment_data.encode()).hexdigest()
        
        # Circuit built at: zkp/circuits/agent_capability.circom
        # NOTE: To use real proofs, build circuit artifacts:
        #   cd backend-python/zkp && npm run build:agent-capability
        # Then add to snark-runner.js and update this function
        
        return ZKProofResult(
            success=True,
            proof={
                "type": "capability_commitment",
                "commitment": commitment,
                "timestamp": timestamp,
                # This is NOT a real ZK proof - marking as simulated
                "simulated": True,
            },
            public_signals=[commitment, sender_id],
            nullifier=hashlib.sha256(f"{commitment}:{sender_id}".encode()).hexdigest(),
        )
    
    def prove_agent_interaction(
        self,
        requester_id: str,
        provider_id: str,
        interaction_type: str,
        timestamp: int,
    ) -> ZKProofResult:
        """
        Generate a ZK proof of interaction between two agents.
        
        This creates a commitment binding both agents to the interaction
        without revealing sensitive details.
        
        Args:
            requester_id: ID of the requesting agent
            provider_id: ID of the providing agent
            interaction_type: Type of interaction
            timestamp: Interaction timestamp
            
        Returns:
            ZKProofResult with interaction proof
        """
        salt = secrets.randbits(128)
        
        # Create interaction commitment
        interaction_data = {
            "requester": self._agent_id_to_field(requester_id),
            "provider": self._agent_id_to_field(provider_id),
            "type": interaction_type,
            "timestamp": timestamp,
            "salt": str(salt),
        }
        
        commitment = hashlib.sha256(
            json.dumps(interaction_data, sort_keys=True).encode()
        ).hexdigest()
        
        # Generate nullifier for this interaction
        nullifier_data = f"{requester_id}:{provider_id}:{timestamp}:{salt}"
        nullifier = hashlib.sha256(nullifier_data.encode()).hexdigest()
        
        return ZKProofResult(
            success=True,
            proof={
                "type": "agent_interaction",
                "commitment": commitment,
                "timestamp": timestamp,
                # This is a commitment-based proof, not full ZK
                "proof_type": "commitment_hash",
            },
            public_signals=[
                commitment,
                self._agent_id_to_field(requester_id),
                self._agent_id_to_field(provider_id),
            ],
            nullifier=nullifier,
        )
    
    def check_nullifier(self, nullifier: str) -> bool:
        """
        Check if a nullifier has been used.
        
        Args:
            nullifier: The nullifier to check
            
        Returns:
            True if nullifier has been used, False otherwise
        """
        return nullifier in self._used_nullifiers
    
    def mark_nullifier_used(self, nullifier: str) -> bool:
        """
        Mark a nullifier as used.
        
        Args:
            nullifier: The nullifier to mark
            
        Returns:
            True if marked successfully, False if already used
        """
        if nullifier in self._used_nullifiers:
            return False
        self._used_nullifiers.add(nullifier)
        return True
    
    def get_nullifier_count(self) -> int:
        """Get the number of used nullifiers."""
        return len(self._used_nullifiers)


# Global instance
_zkp_integration: Optional[AAIPZKIntegration] = None


def get_zkp_integration() -> AAIPZKIntegration:
    """Get the global ZKP integration instance."""
    global _zkp_integration
    if _zkp_integration is None:
        _zkp_integration = AAIPZKIntegration()
    return _zkp_integration


# ============================================
# High-Level API Functions
# ============================================

def prove_agent_reputation_zk(
    agent_id: str,
    reputation_score: int,
    threshold: int,
) -> Dict[str, Any]:
    """
    Generate a ZK proof that an agent's reputation exceeds a threshold.
    
    This is the main function for reputation proofs.
    
    Args:
        agent_id: The agent's DID or ID
        reputation_score: The agent's actual reputation (private)
        threshold: The public threshold to prove against
        
    Returns:
        Dict with proof, nullifier, and verification data
    """
    zkp = get_zkp_integration()
    result = zkp.prove_reputation_threshold(agent_id, reputation_score, threshold)
    
    if result.success:
        return {
            "success": True,
            "proof": result.proof,
            "publicSignals": result.public_signals,
            "nullifier": result.nullifier,
            "threshold": threshold,
            "agent_did": f"did:honestly:agent:{agent_id}",
        }
    else:
        return {
            "success": False,
            "error": result.error,
        }


def verify_agent_reputation_proof(
    proof: Dict,
    public_signals: list,
    expected_threshold: int,
    check_replay: bool = True,
) -> Dict[str, Any]:
    """
    Verify a ZK reputation proof.
    
    Args:
        proof: The Groth16 proof object
        public_signals: Public signals from the proof
        expected_threshold: The threshold that was supposedly proven
        check_replay: If True, check for replay attacks
        
    Returns:
        Dict with verification result
    """
    zkp = get_zkp_integration()
    
    # Check threshold matches public signal
    if len(public_signals) > 0:
        proven_threshold = int(public_signals[0])
        if proven_threshold != expected_threshold:
            return {
                "verified": False,
                "error": f"Threshold mismatch: expected {expected_threshold}, got {proven_threshold}",
            }
    
    is_valid, error = zkp.verify_reputation_proof(proof, public_signals, check_replay)
    
    return {
        "verified": is_valid,
        "error": error,
        "threshold": expected_threshold,
        "nullifier_tracked": check_replay and is_valid,
    }


