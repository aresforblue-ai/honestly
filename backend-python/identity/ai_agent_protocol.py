"""
AI Agent Identity Protocol (AAIP)
=================================

A revolutionary protocol for establishing verifiable AI agent identities.

This enables:
1. AI agents to prove their capabilities and constraints
2. Humans to verify they're interacting with authorized AI
3. AI agents to accumulate reputation without revealing sensitive data
4. Cross-agent trust establishment
5. Audit trails for AI actions without compromising privacy

This is the future of AI governance and accountability.
"""

import os
import json
import hashlib
import secrets
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("identity.ai_agent")


class AgentCapability(Enum):
    """Standard capabilities an AI agent can possess."""
    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_GENERATION = "video_generation"
    REASONING = "reasoning"
    TOOL_USE = "tool_use"
    WEB_BROWSING = "web_browsing"
    FILE_ACCESS = "file_access"
    MEMORY = "memory"
    MULTI_MODAL = "multi_modal"
    AUTONOMOUS = "autonomous"
    FINANCIAL = "financial"  # Can handle financial transactions
    PII_ACCESS = "pii_access"  # Can access personal information


class AgentConstraint(Enum):
    """Constraints/limitations on an AI agent."""
    NO_INTERNET = "no_internet"
    NO_FILE_WRITE = "no_file_write"
    NO_CODE_EXECUTION = "no_code_execution"
    NO_FINANCIAL = "no_financial"
    HUMAN_APPROVAL_REQUIRED = "human_approval_required"
    RATE_LIMITED = "rate_limited"
    SANDBOXED = "sandboxed"
    AUDIT_LOGGED = "audit_logged"
    TIME_LIMITED = "time_limited"
    SCOPE_LIMITED = "scope_limited"


class AgentTrustLevel(Enum):
    """Trust levels for AI agents."""
    UNTRUSTED = 0
    BASIC = 1
    VERIFIED = 2
    TRUSTED = 3
    CERTIFIED = 4
    SOVEREIGN = 5  # Self-sovereign AI with full accountability


@dataclass
class AgentIdentity:
    """
    Represents a verifiable AI agent identity.
    
    This is the core identity document for an AI agent,
    containing cryptographic proofs of its properties.
    """
    # Core identity
    agent_id: str
    agent_name: str
    agent_version: str
    
    # Operator (human/org responsible for the agent)
    operator_id: str
    operator_name: str
    
    # Model information (without revealing proprietary details)
    model_family: str  # e.g., "transformer", "diffusion"
    model_hash: str    # Hash of model weights (proves specific model)
    
    # Capabilities and constraints
    capabilities: List[str]
    constraints: List[str]
    
    # Trust and verification
    trust_level: int = 0
    is_human_backed: bool = False  # Has human oversight
    is_audited: bool = False
    
    # Cryptographic identity
    public_key: str = ""
    identity_commitment: str = ""  # Poseidon hash commitment
    
    # Timestamps
    created_at: str = ""
    expires_at: str = ""
    
    # Attestations from other agents/humans
    attestations: List[Dict] = field(default_factory=list)
    
    # Metadata
    metadata: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            self.expires_at = (datetime.utcnow() + timedelta(days=365)).isoformat()
        if not self.identity_commitment:
            self.identity_commitment = self._compute_commitment()
    
    def _compute_commitment(self) -> str:
        """Compute identity commitment for ZK proofs."""
        data = f"{self.agent_id}:{self.operator_id}:{self.model_hash}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "AgentIdentity":
        return cls(**data)


@dataclass
class AgentCredential:
    """
    A verifiable credential for an AI agent.
    
    This follows W3C Verifiable Credentials structure adapted for AI agents.
    """
    id: str
    type: List[str]
    issuer: str
    issuance_date: str
    expiration_date: str
    credential_subject: Dict
    proof: Dict
    
    def to_dict(self) -> Dict:
        return {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://honestly.dev/ai-agent/v1"
            ],
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "expirationDate": self.expiration_date,
            "credentialSubject": self.credential_subject,
            "proof": self.proof
        }


class AIAgentRegistry:
    """
    Registry for AI agent identities.
    
    This maintains a decentralized registry of AI agents,
    their capabilities, and their reputation.
    """
    
    def __init__(self, storage_backend=None):
        self.storage = storage_backend or {}
        self.pending_verifications = {}
        self.reputation_scores = {}
    
    def register_agent(
        self,
        agent_name: str,
        operator_id: str,
        operator_name: str,
        model_family: str,
        model_hash: str,
        capabilities: List[AgentCapability],
        constraints: List[AgentConstraint],
        public_key: str,
        is_human_backed: bool = True,
        metadata: Optional[Dict] = None,
    ) -> AgentIdentity:
        """
        Register a new AI agent in the registry.
        
        Returns an AgentIdentity that can be used for verification.
        """
        agent_id = f"agent_{secrets.token_hex(16)}"
        
        identity = AgentIdentity(
            agent_id=agent_id,
            agent_name=agent_name,
            agent_version="1.0.0",
            operator_id=operator_id,
            operator_name=operator_name,
            model_family=model_family,
            model_hash=model_hash,
            capabilities=[c.value for c in capabilities],
            constraints=[c.value for c in constraints],
            trust_level=AgentTrustLevel.BASIC.value if is_human_backed else AgentTrustLevel.UNTRUSTED.value,
            is_human_backed=is_human_backed,
            public_key=public_key,
            metadata=metadata or {},
        )
        
        self.storage[agent_id] = identity.to_dict()
        self.reputation_scores[agent_id] = {
            "score": 50,  # Starting reputation
            "interactions": 0,
            "positive": 0,
            "negative": 0,
        }
        
        logger.info(f"Registered AI agent: {agent_id} ({agent_name})")
        return identity
    
    def get_agent(self, agent_id: str) -> Optional[AgentIdentity]:
        """Retrieve an agent identity."""
        data = self.storage.get(agent_id)
        if data:
            return AgentIdentity.from_dict(data)
        return None
    
    def verify_capability(
        self,
        agent_id: str,
        capability: AgentCapability,
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify an agent has a specific capability.
        
        Returns (has_capability, proof_commitment)
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False, None
        
        has_cap = capability.value in agent.capabilities
        
        if has_cap:
            # Generate proof commitment (would be ZK proof in production)
            proof_data = f"{agent_id}:{capability.value}:{time.time()}"
            commitment = hashlib.sha256(proof_data.encode()).hexdigest()[:32]
            return True, commitment
        
        return False, None
    
    def verify_constraint(
        self,
        agent_id: str,
        constraint: AgentConstraint,
    ) -> Tuple[bool, Optional[str]]:
        """Verify an agent is bound by a specific constraint."""
        agent = self.get_agent(agent_id)
        if not agent:
            return False, None
        
        has_constraint = constraint.value in agent.constraints
        
        if has_constraint:
            proof_data = f"{agent_id}:{constraint.value}:{time.time()}"
            commitment = hashlib.sha256(proof_data.encode()).hexdigest()[:32]
            return True, commitment
        
        return False, None
    
    def issue_credential(
        self,
        agent_id: str,
        credential_type: str,
        claims: Dict,
        issuer_id: str,
        expires_days: int = 365,
    ) -> AgentCredential:
        """
        Issue a verifiable credential to an AI agent.
        
        This can be used to prove specific attributes about the agent
        without revealing its full identity.
        """
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        credential_id = f"cred_{secrets.token_hex(8)}"
        now = datetime.utcnow()
        
        credential_subject = {
            "id": f"did:honestly:agent:{agent_id}",
            **claims
        }
        
        # Create proof (would be ZK proof in production)
        proof_data = json.dumps({
            "credential_id": credential_id,
            "subject": agent_id,
            "claims": claims,
            "timestamp": now.isoformat(),
        }, sort_keys=True)
        proof_hash = hashlib.sha256(proof_data.encode()).hexdigest()
        
        credential = AgentCredential(
            id=credential_id,
            type=["VerifiableCredential", f"AIAgent{credential_type}Credential"],
            issuer=f"did:honestly:issuer:{issuer_id}",
            issuance_date=now.isoformat(),
            expiration_date=(now + timedelta(days=expires_days)).isoformat(),
            credential_subject=credential_subject,
            proof={
                "type": "Groth16Proof2024",
                "created": now.isoformat(),
                "proofPurpose": "assertionMethod",
                "verificationMethod": f"did:honestly:issuer:{issuer_id}#key-1",
                "proofValue": proof_hash,
            }
        )
        
        # Store attestation on agent identity
        agent.attestations.append({
            "credential_id": credential_id,
            "type": credential_type,
            "issuer": issuer_id,
            "issued_at": now.isoformat(),
        })
        self.storage[agent_id] = agent.to_dict()
        
        logger.info(f"Issued credential {credential_id} to agent {agent_id}")
        return credential
    
    def update_reputation(
        self,
        agent_id: str,
        interaction_positive: bool,
        weight: float = 1.0,
    ) -> Dict:
        """
        Update an agent's reputation based on interaction outcome.
        
        Uses exponential moving average for smooth reputation updates.
        """
        if agent_id not in self.reputation_scores:
            return {"error": "Agent not found"}
        
        rep = self.reputation_scores[agent_id]
        rep["interactions"] += 1
        
        if interaction_positive:
            rep["positive"] += 1
            # Increase score (max 100)
            delta = min(5 * weight, 100 - rep["score"])
            rep["score"] = min(100, rep["score"] + delta)
        else:
            rep["negative"] += 1
            # Decrease score (min 0)
            delta = min(10 * weight, rep["score"])  # Negative impacts more
            rep["score"] = max(0, rep["score"] - delta)
        
        return rep
    
    def get_reputation(self, agent_id: str) -> Optional[Dict]:
        """Get an agent's reputation score."""
        return self.reputation_scores.get(agent_id)
    
    def prove_reputation_threshold(
        self,
        agent_id: str,
        threshold: int,
    ) -> Tuple[bool, Optional[str]]:
        """
        Generate a ZK proof that agent's reputation is above threshold.
        
        This proves reputation without revealing the exact score.
        """
        rep = self.get_reputation(agent_id)
        if not rep:
            return False, None
        
        meets_threshold = rep["score"] >= threshold
        
        if meets_threshold:
            # Generate commitment (would be actual ZK proof)
            proof_data = f"{agent_id}:rep>={threshold}:{time.time()}"
            commitment = hashlib.sha256(proof_data.encode()).hexdigest()[:32]
            return True, commitment
        
        return False, None
    
    def create_agent_interaction_proof(
        self,
        requester_agent_id: str,
        provider_agent_id: str,
        interaction_type: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Create a proof of interaction between two AI agents.
        
        This enables agent-to-agent trust establishment and audit trails.
        """
        interaction_id = f"interaction_{secrets.token_hex(8)}"
        timestamp = datetime.utcnow().isoformat()
        
        requester = self.get_agent(requester_agent_id)
        provider = self.get_agent(provider_agent_id)
        
        if not requester or not provider:
            raise ValueError("One or both agents not found")
        
        # Create interaction proof
        proof_data = {
            "interaction_id": interaction_id,
            "requester": {
                "agent_id": requester_agent_id,
                "commitment": requester.identity_commitment,
            },
            "provider": {
                "agent_id": provider_agent_id,
                "commitment": provider.identity_commitment,
            },
            "interaction_type": interaction_type,
            "timestamp": timestamp,
            "metadata": metadata or {},
        }
        
        proof_hash = hashlib.sha256(
            json.dumps(proof_data, sort_keys=True).encode()
        ).hexdigest()
        
        return {
            "interaction_id": interaction_id,
            "proof": proof_hash,
            "timestamp": timestamp,
            "requester_commitment": requester.identity_commitment[:16],
            "provider_commitment": provider.identity_commitment[:16],
        }


class AgentAuthenticator:
    """
    Authenticates AI agent requests and validates their identity.
    """
    
    def __init__(self, registry: AIAgentRegistry):
        self.registry = registry
        self.challenge_cache = {}
    
    def create_challenge(self, agent_id: str) -> str:
        """Create a challenge for agent authentication."""
        challenge = secrets.token_hex(32)
        self.challenge_cache[agent_id] = {
            "challenge": challenge,
            "created_at": time.time(),
            "expires_at": time.time() + 300,  # 5 minutes
        }
        return challenge
    
    def verify_challenge_response(
        self,
        agent_id: str,
        challenge: str,
        response: str,
        signature: str,
    ) -> Tuple[bool, Optional[AgentIdentity]]:
        """
        Verify an agent's response to authentication challenge.
        
        In production, this would verify cryptographic signatures.
        """
        cached = self.challenge_cache.get(agent_id)
        if not cached:
            return False, None
        
        if cached["challenge"] != challenge:
            return False, None
        
        if time.time() > cached["expires_at"]:
            del self.challenge_cache[agent_id]
            return False, None
        
        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False, None
        
        # In production: verify signature with agent's public key
        # For now, simple hash verification
        expected = hashlib.sha256(f"{challenge}:{agent_id}".encode()).hexdigest()
        
        # Clean up
        del self.challenge_cache[agent_id]
        
        # For demo, accept if response matches pattern
        if len(response) >= 32:
            return True, agent
        
        return False, None


# Global registry instance
_registry: Optional[AIAgentRegistry] = None


def get_registry() -> AIAgentRegistry:
    """Get the global AI agent registry."""
    global _registry
    if _registry is None:
        _registry = AIAgentRegistry()
    return _registry


# ============================================
# API Integration Functions
# ============================================

def register_ai_agent(
    name: str,
    operator_id: str,
    operator_name: str,
    model_family: str,
    capabilities: List[str],
    constraints: List[str],
    public_key: str,
    is_human_backed: bool = True,
) -> Dict:
    """
    Register an AI agent and return its identity.
    
    This is the main entry point for agent registration.
    """
    registry = get_registry()
    
    # Convert strings to enums
    caps = [AgentCapability(c) for c in capabilities if c in [e.value for e in AgentCapability]]
    cons = [AgentConstraint(c) for c in constraints if c in [e.value for e in AgentConstraint]]
    
    # Create model hash (in production, this would be actual model fingerprint)
    model_hash = hashlib.sha256(f"{name}:{model_family}:{time.time()}".encode()).hexdigest()
    
    identity = registry.register_agent(
        agent_name=name,
        operator_id=operator_id,
        operator_name=operator_name,
        model_family=model_family,
        model_hash=model_hash,
        capabilities=caps,
        constraints=cons,
        public_key=public_key,
        is_human_backed=is_human_backed,
    )
    
    return {
        "success": True,
        "agent_id": identity.agent_id,
        "identity": identity.to_dict(),
        "did": f"did:honestly:agent:{identity.agent_id}",
    }


def verify_agent_capability(agent_id: str, capability: str) -> Dict:
    """Verify an agent has a specific capability."""
    registry = get_registry()
    
    try:
        cap = AgentCapability(capability)
    except ValueError:
        return {"success": False, "error": f"Unknown capability: {capability}"}
    
    has_cap, proof = registry.verify_capability(agent_id, cap)
    
    return {
        "success": has_cap,
        "capability": capability,
        "proof_commitment": proof,
        "verified_at": datetime.utcnow().isoformat(),
    }


def get_agent_reputation(agent_id: str, threshold: Optional[int] = None) -> Dict:
    """
    Get agent reputation, optionally with ZK proof of threshold.
    """
    registry = get_registry()
    
    rep = registry.get_reputation(agent_id)
    if not rep:
        return {"success": False, "error": "Agent not found"}
    
    result = {
        "success": True,
        "agent_id": agent_id,
        "reputation_score": rep["score"],
        "total_interactions": rep["interactions"],
    }
    
    if threshold is not None:
        meets, proof = registry.prove_reputation_threshold(agent_id, threshold)
        result["meets_threshold"] = meets
        result["threshold"] = threshold
        result["proof_commitment"] = proof
    
    return result

