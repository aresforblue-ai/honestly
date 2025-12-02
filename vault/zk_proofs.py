"""
Zero-knowledge proof generation and verification for vault documents.
Uses Python-based ZK libraries for age and document authenticity proofs.
"""
import json
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend

# For MVP, we'll use a simplified ZK approach with cryptographic commitments
# In production, this would use proper ZK-SNARK libraries like zkpy or circom


class ZKProofService:
    """Service for generating and verifying zero-knowledge proofs."""
    
    def __init__(self):
        """Initialize ZK proof service."""
        pass
    
    def generate_age_proof(
        self,
        birth_date: str,  # ISO format: YYYY-MM-DD
        min_age: int,
        document_hash: str
    ) -> Dict[str, Any]:
        """
        Generate a zero-knowledge proof that age >= min_age without revealing birthdate.
        
        This is a simplified implementation. In production, use proper ZK-SNARK circuits.
        
        Args:
            birth_date: Birth date in ISO format
            min_age: Minimum age to prove
            document_hash: Hash of the document containing birthdate
            
        Returns:
            Dictionary containing proof data and public inputs
        """
        # Parse birth date
        birth_dt = datetime.fromisoformat(birth_date)
        current_dt = datetime.utcnow()
        age_years = (current_dt - birth_dt).days // 365
        
        if age_years < min_age:
            raise ValueError(f"Age {age_years} is less than required minimum {min_age}")
        
        # Create commitment to birth date (simplified - in production use proper commitment scheme)
        commitment_secret = f"{birth_date}_{document_hash}"
        commitment = hashlib.sha256(commitment_secret.encode()).hexdigest()
        
        # Create proof that age >= min_age
        # In a real ZK system, this would be a SNARK proof
        # For MVP, we create a cryptographic signature-like structure
        proof_data = {
            "proof_type": "age_proof",
            "commitment": commitment,
            "min_age": min_age,
            "age_verified": True,
            "document_hash": document_hash,
            "timestamp": current_dt.isoformat()
        }
        
        # Sign the proof (simplified - in production use proper ZK signature)
        proof_signature = self._sign_proof(proof_data)
        proof_data["signature"] = proof_signature
        
        public_inputs = {
            "min_age": min_age,
            "commitment": commitment,
            "age_verified": True,
            "document_hash": document_hash
        }
        
        return {
            "proof_data": json.dumps(proof_data),
            "public_inputs": json.dumps(public_inputs),
            "proof_type": "age_proof"
        }
    
    def verify_age_proof(
        self,
        proof_data: str,
        public_inputs: str
    ) -> bool:
        """
        Verify an age proof.
        
        Args:
            proof_data: JSON string of proof data
            public_inputs: JSON string of public inputs
            
        Returns:
            True if proof is valid, False otherwise
        """
        try:
            proof = json.loads(proof_data)
            inputs = json.loads(public_inputs)
            
            # Verify proof type
            if proof.get("proof_type") != "age_proof":
                return False
            
            # Verify commitment matches
            if proof.get("commitment") != inputs.get("commitment"):
                return False
            
            # Verify minimum age matches
            if proof.get("min_age") != inputs.get("min_age"):
                return False
            
            # Verify age was actually verified
            if not proof.get("age_verified") or not inputs.get("age_verified"):
                return False
            
            # Verify signature (simplified)
            if not self._verify_proof_signature(proof):
                return False
            
            return True
        except Exception as e:
            print(f"Error verifying age proof: {e}")
            return False
    
    def generate_authenticity_proof(
        self,
        document_hash: str,
        merkle_root: str,
        merkle_proof: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate a zero-knowledge proof that a document hash is authentic
        (exists in a Merkle tree) without revealing the document content.
        
        Args:
            document_hash: SHA-256 hash of the document
            merkle_root: Root hash of the Merkle tree
            merkle_proof: Optional Merkle proof path (for full verification)
            
        Returns:
            Dictionary containing proof data and public inputs
        """
        # Create proof structure
        proof_data = {
            "proof_type": "authenticity_proof",
            "document_hash": document_hash,
            "merkle_root": merkle_root,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if merkle_proof:
            proof_data["merkle_proof"] = merkle_proof
        
        # Sign the proof
        proof_signature = self._sign_proof(proof_data)
        proof_data["signature"] = proof_signature
        
        public_inputs = {
            "merkle_root": merkle_root,
            "document_hash": document_hash
        }
        
        return {
            "proof_data": json.dumps(proof_data),
            "public_inputs": json.dumps(public_inputs),
            "proof_type": "authenticity_proof"
        }
    
    def verify_authenticity_proof(
        self,
        proof_data: str,
        public_inputs: str
    ) -> bool:
        """
        Verify a document authenticity proof.
        
        Args:
            proof_data: JSON string of proof data
            public_inputs: JSON string of public inputs
            
        Returns:
            True if proof is valid, False otherwise
        """
        try:
            proof = json.loads(proof_data)
            inputs = json.loads(public_inputs)
            
            # Verify proof type
            if proof.get("proof_type") != "authenticity_proof":
                return False
            
            # Verify document hash matches
            if proof.get("document_hash") != inputs.get("document_hash"):
                return False
            
            # Verify merkle root matches
            if proof.get("merkle_root") != inputs.get("merkle_root"):
                return False
            
            # Verify signature
            if not self._verify_proof_signature(proof):
                return False
            
            # If Merkle proof provided, verify it
            if "merkle_proof" in proof:
                if not self._verify_merkle_proof(
                    inputs.get("document_hash"),
                    proof.get("merkle_proof"),
                    inputs.get("merkle_root")
                ):
                    return False
            
            return True
        except Exception as e:
            print(f"Error verifying authenticity proof: {e}")
            return False
    
    def _sign_proof(self, proof_data: Dict[str, Any]) -> str:
        """
        Sign proof data (simplified implementation).
        In production, use proper ZK signature scheme.
        """
        # Create a deterministic signature from proof data
        proof_str = json.dumps(proof_data, sort_keys=True)
        signature = hashlib.sha256(proof_str.encode()).hexdigest()
        return signature
    
    def _verify_proof_signature(self, proof: Dict[str, Any]) -> bool:
        """Verify proof signature."""
        signature = proof.pop("signature", None)
        if not signature:
            return False
        
        # Recompute signature
        expected_signature = self._sign_proof(proof)
        proof["signature"] = signature  # Restore for caller
        
        return signature == expected_signature
    
    def _verify_merkle_proof(
        self,
        leaf_hash: str,
        merkle_proof: list,
        root_hash: str
    ) -> bool:
        """
        Verify a Merkle proof.
        
        Args:
            leaf_hash: Hash of the leaf node
            merkle_proof: List of (hash, position) tuples for proof path
            root_hash: Expected root hash
            
        Returns:
            True if proof is valid
        """
        current_hash = leaf_hash
        
        for sibling_hash, is_right in merkle_proof:
            if is_right:
                # Sibling is on the right
                combined = current_hash + sibling_hash
            else:
                # Sibling is on the left
                combined = sibling_hash + current_hash
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == root_hash

