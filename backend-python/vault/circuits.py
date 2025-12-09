"""
Proof circuit definitions and schemas for ZK proofs.
This module defines the structure and constraints for zero-knowledge proofs.
"""

from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class AgeProofCircuit:
    """Circuit definition for age verification proof."""

    # Public inputs (visible to verifier)
    min_age: int
    commitment: str  # Commitment to birth date
    age_verified: bool

    # Private inputs (hidden from verifier)
    birth_date: str  # ISO format: YYYY-MM-DD
    document_hash: str

    # Constraints
    def validate(self) -> bool:
        """Validate circuit constraints."""
        from datetime import datetime

        # Parse birth date
        birth_dt = datetime.fromisoformat(self.birth_date)
        current_dt = datetime.utcnow()
        age_years = (current_dt - birth_dt).days // 365

        # Constraint 1: Age must be >= min_age
        if age_years < self.min_age:
            return False

        # Constraint 2: Commitment must match birth date
        import hashlib

        commitment_secret = f"{self.birth_date}_{self.document_hash}"
        expected_commitment = hashlib.sha256(commitment_secret.encode()).hexdigest()
        if self.commitment != expected_commitment:
            return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "min_age": self.min_age,
            "commitment": self.commitment,
            "age_verified": self.age_verified,
        }


@dataclass
class AuthenticityProofCircuit:
    """Circuit definition for document authenticity proof."""

    # Public inputs
    merkle_root: str
    document_hash: str

    # Private inputs
    merkle_proof: list  # Merkle proof path

    # Constraints
    def validate(self) -> bool:
        """Validate circuit constraints."""
        # Verify Merkle proof
        import hashlib

        current_hash = self.document_hash

        for sibling_hash, is_right in self.merkle_proof:
            if is_right:
                combined = current_hash + sibling_hash
            else:
                combined = sibling_hash + current_hash

            current_hash = hashlib.sha256(combined.encode()).hexdigest()

        return current_hash == self.merkle_root

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {"merkle_root": self.merkle_root, "document_hash": self.document_hash}


class ProofSchema:
    """Schema definitions for different proof types."""

    AGE_PROOF = {
        "name": "age_proof",
        "description": "Prove age >= X without revealing birthdate",
        "public_inputs": ["min_age", "commitment", "age_verified"],
        "private_inputs": ["birth_date", "document_hash"],
        "circuit": AgeProofCircuit,
    }

    AUTHENTICITY_PROOF = {
        "name": "authenticity_proof",
        "description": "Prove document hash exists in Merkle tree without revealing content",
        "public_inputs": ["merkle_root", "document_hash"],
        "private_inputs": ["merkle_proof"],
        "circuit": AuthenticityProofCircuit,
    }

    @classmethod
    def get_schema(cls, proof_type: str) -> Dict[str, Any]:
        """Get schema for a proof type."""
        schemas = {"age_proof": cls.AGE_PROOF, "authenticity_proof": cls.AUTHENTICITY_PROOF}
        return schemas.get(proof_type)
