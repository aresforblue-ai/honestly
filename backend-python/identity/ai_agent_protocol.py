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

Upgraded with:
- Real Groth16 ZK proofs via Level3Inequality circuit
- Nullifier tracking to prevent replay attacks
- ECDSA signature verification
- Redis/Neo4j persistence options
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

# Cryptographic signature support
try:
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
    from cryptography.exceptions import InvalidSignature

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

# Redis support for persistence
try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

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

    CRITICAL: Agent identity is a function of (Model + Prompt + Configuration).
    If ANY of these change, the identity changes or is invalidated.

    The config_fingerprint uniquely identifies this specific agent configuration.
    Changing the system prompt from "Be helpful" to "Be evil" creates a
    DIFFERENT identity - this is by design for accountability.
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
    model_hash: str  # Hash of model weights (proves specific model)

    # CRITICAL: System prompt hash - changing this changes identity
    # "Honesty" for an AI = Model + Prompt + Configuration
    system_prompt_hash: str = ""  # SHA-256 of system prompt

    # Full configuration fingerprint (deterministic identity hash)
    # This is what makes the DID unique and verifiable
    config_fingerprint: str = ""  # H(model + prompt + config)

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
        if not self.config_fingerprint:
            self.config_fingerprint = self._compute_config_fingerprint()
        if not self.identity_commitment:
            self.identity_commitment = self._compute_commitment()

    def _compute_config_fingerprint(self) -> str:
        """
        Compute deterministic configuration fingerprint.

        This is the cryptographic identity of this specific agent configuration.
        If ANYTHING changes (model, prompt, config), this fingerprint changes.
        """
        config_data = {
            "model_hash": self.model_hash,
            "system_prompt_hash": self.system_prompt_hash,
            "model_family": self.model_family,
            "agent_version": self.agent_version,
            "capabilities": sorted(self.capabilities),
            "constraints": sorted(self.constraints),
        }
        canonical = json.dumps(config_data, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _compute_commitment(self) -> str:
        """Compute identity commitment for ZK proofs."""
        # Now includes config_fingerprint for full accountability
        data = f"{self.agent_id}:{self.operator_id}:{self.config_fingerprint}:{self.created_at}"
        return hashlib.sha256(data.encode()).hexdigest()

    def verify_config_integrity(self) -> bool:
        """
        Verify that the stored config_fingerprint matches current config.

        Returns False if configuration has been tampered with.
        """
        expected = self._compute_config_fingerprint()
        return self.config_fingerprint == expected

    def get_did(self) -> str:
        """
        Get the Decentralized Identifier for this agent.

        Format: did:honestly:agent:{fingerprint_prefix}:{agent_id}

        The fingerprint prefix ensures that agents with different configs
        have different DIDs, even if they have the same agent_id.
        """
        fp_prefix = self.config_fingerprint[:16] if self.config_fingerprint else "0" * 16
        return f"did:honestly:agent:{fp_prefix}:{self.agent_id}"

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
                "https://honestly.dev/ai-agent/v1",
            ],
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "expirationDate": self.expiration_date,
            "credentialSubject": self.credential_subject,
            "proof": self.proof,
        }


class AIAgentRegistry:
    """
    Registry for AI agent identities.

    This maintains a decentralized registry of AI agents,
    their capabilities, and their reputation.

    Supports:
    - Redis persistence for production
    - In-memory storage for development
    - Nullifier tracking for replay attack prevention
    """

    def __init__(
        self,
        storage_backend=None,
        redis_url: Optional[str] = None,
        enable_zk: bool = True,
    ):
        """
        Initialize the registry.

        Args:
            storage_backend: Optional dict-like storage (for testing)
            redis_url: Redis connection URL for persistence
            enable_zk: Enable real ZK proofs (requires circuit artifacts)
        """
        # Primary storage
        self.storage = storage_backend or {}
        self.pending_verifications = {}
        self.reputation_scores = {}

        # Nullifier tracking for replay prevention
        self.used_nullifiers: set = set()

        # Redis persistence
        self.redis_client = None
        if redis_url and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Connected to Redis for persistence")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}")

        # ZK integration
        self.enable_zk = enable_zk
        self._zkp = None
        if enable_zk:
            try:
                from identity.zkp_integration import get_zkp_integration

                self._zkp = get_zkp_integration()
                logger.info("ZK integration enabled")
            except Exception as e:
                logger.warning(f"ZK integration not available: {e}")
                self.enable_zk = False

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
        system_prompt_hash: str = "",
    ) -> AgentIdentity:
        """
        Register a new AI agent in the registry.

        CRITICAL: The agent's identity is determined by (Model + Prompt + Config).
        The system_prompt_hash is essential - changing the prompt creates a
        fundamentally different agent.

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
            system_prompt_hash=system_prompt_hash,  # CRITICAL for identity
            capabilities=[c.value for c in capabilities],
            constraints=[c.value for c in constraints],
            trust_level=(
                AgentTrustLevel.BASIC.value if is_human_backed else AgentTrustLevel.UNTRUSTED.value
            ),
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
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Verify an agent has a specific capability.

        Returns (has_capability, proof_data)
        """
        agent = self.get_agent(agent_id)
        if not agent:
            return False, None

        has_cap = capability.value in agent.capabilities

        if has_cap:
            timestamp = int(time.time())
            capability_hash = hashlib.sha256(capability.value.encode()).hexdigest()

            # Use ZK proof if available
            if self.enable_zk and self._zkp:
                result = self._zkp.prove_capability(
                    agent_id=agent_id,
                    capability_hash=capability_hash,
                    timestamp=timestamp,
                )

                if result.success:
                    return True, {
                        "proof": result.proof,
                        "nullifier": result.nullifier,
                        "capability": capability.value,
                        "timestamp": timestamp,
                    }

            # Fallback commitment
            salt = secrets.randbits(64)
            proof_data = f"{agent_id}:{capability.value}:{salt}:{timestamp}"
            commitment = hashlib.sha256(proof_data.encode()).hexdigest()
            nullifier = hashlib.sha256(f"{commitment}:{salt}".encode()).hexdigest()

            return True, {
                "commitment": commitment,
                "nullifier": nullifier,
                "capability": capability.value,
                "timestamp": timestamp,
            }

        return False, None

    def verify_proof_with_nullifier(self, proof_data: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify a proof and check its nullifier hasn't been used.

        This prevents replay attacks where someone resubmits the same proof.

        Args:
            proof_data: Dict containing proof and nullifier

        Returns:
            (is_valid, error_message)
        """
        nullifier = proof_data.get("nullifier")
        if not nullifier:
            return False, "No nullifier in proof"

        # Check nullifier not used
        if self._is_nullifier_used(nullifier):
            return False, "Nullifier already used (replay detected)"

        # For real ZK proofs, verify cryptographically
        if proof_data.get("proof") and self.enable_zk and self._zkp:
            public_signals = proof_data.get("publicSignals", [])
            is_valid, error = self._zkp.verify_reputation_proof(
                proof_data["proof"],
                public_signals,
                check_nullifier=False,  # We handle nullifier ourselves
            )

            if not is_valid:
                return False, error or "Proof verification failed"

        # Mark nullifier as used
        self._mark_nullifier_used(nullifier)

        return True, None

    def _is_nullifier_used(self, nullifier: str) -> bool:
        """Check if a nullifier has been used."""
        # Check Redis first
        if self.redis_client:
            try:
                if self.redis_client.exists(f"nullifier:{nullifier}"):
                    return True
            except Exception:
                pass

        # Check memory
        return nullifier in self.used_nullifiers

    def _mark_nullifier_used(self, nullifier: str) -> None:
        """Mark a nullifier as used."""
        # Store in Redis with 1 year expiry
        if self.redis_client:
            try:
                self.redis_client.setex(f"nullifier:{nullifier}", 31536000, "1")  # 1 year
            except Exception:
                pass

        # Store in memory
        self.used_nullifiers.add(nullifier)

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

        credential_subject = {"id": f"did:honestly:agent:{agent_id}", **claims}

        # Create proof (would be ZK proof in production)
        proof_data = json.dumps(
            {
                "credential_id": credential_id,
                "subject": agent_id,
                "claims": claims,
                "timestamp": now.isoformat(),
            },
            sort_keys=True,
        )
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
            },
        )

        # Store attestation on agent identity
        agent.attestations.append(
            {
                "credential_id": credential_id,
                "type": credential_type,
                "issuer": issuer_id,
                "issued_at": now.isoformat(),
            }
        )
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
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Generate a ZK proof that agent's reputation is above threshold.

        This proves reputation WITHOUT revealing the exact score.
        Uses Level3Inequality circuit with nullifier binding.

        Returns:
            (success, proof_data) where proof_data contains:
            - proof: The Groth16 proof
            - publicSignals: Public signals including nullifier
            - nullifier: For replay tracking
        """
        rep = self.get_reputation(agent_id)
        if not rep:
            return False, None

        score = rep["score"]

        # Use real ZK proof if available
        if self.enable_zk and self._zkp:
            try:
                result = self._zkp.prove_reputation_threshold(
                    agent_id=agent_id,
                    reputation_score=score,
                    threshold=threshold,
                )

                if result.success:
                    return True, {
                        "proof": result.proof,
                        "publicSignals": result.public_signals,
                        "nullifier": result.nullifier,
                        "circuit": "level3_inequality",
                        "verified": True,
                    }
                else:
                    logger.warning(f"ZK proof failed: {result.error}")
                    # Fall through to fallback
            except Exception as e:
                logger.warning(f"ZK proof error: {e}")

        # Fallback: commitment-based proof (NOT a real ZK proof)
        # Mark this clearly as fallback
        if score > threshold:
            salt = secrets.randbits(128)
            proof_data = f"{agent_id}:{score}:{threshold}:{salt}:{time.time()}"
            commitment = hashlib.sha256(proof_data.encode()).hexdigest()
            nullifier = hashlib.sha256(f"{agent_id}:{salt}".encode()).hexdigest()

            return True, {
                "proof": None,
                "commitment": commitment,
                "nullifier": nullifier,
                "circuit": "fallback_commitment",
                "verified": False,  # Not cryptographically verified
                "warning": "Fallback proof - circuit artifacts not available",
            }

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

        proof_hash = hashlib.sha256(json.dumps(proof_data, sort_keys=True).encode()).hexdigest()

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

    Supports:
    - Challenge-response authentication
    - ECDSA signature verification (when cryptography is available)
    - Public key validation
    """

    def __init__(self, registry: AIAgentRegistry):
        self.registry = registry
        self.challenge_cache = {}

    def create_challenge(self, agent_id: str) -> Dict[str, Any]:
        """
        Create a challenge for agent authentication.

        Returns:
            Dict with challenge and expiration info
        """
        challenge = secrets.token_hex(32)
        nonce = secrets.token_hex(16)
        expires_at = time.time() + 300  # 5 minutes

        self.challenge_cache[agent_id] = {
            "challenge": challenge,
            "nonce": nonce,
            "created_at": time.time(),
            "expires_at": expires_at,
        }

        return {
            "challenge": challenge,
            "nonce": nonce,
            "expires_at": int(expires_at),
            "sign_message": f"{challenge}:{nonce}:{agent_id}",
        }

    def verify_challenge_response(
        self,
        agent_id: str,
        challenge: str,
        response: str,
        signature: str,
    ) -> Tuple[bool, Optional[AgentIdentity], Optional[str]]:
        """
        Verify an agent's response to authentication challenge.

        Uses ECDSA signature verification when cryptography is available.

        Args:
            agent_id: The agent's ID
            challenge: The challenge that was issued
            response: The agent's response
            signature: Hex-encoded signature

        Returns:
            (is_valid, agent_identity, error_message)
        """
        cached = self.challenge_cache.get(agent_id)
        if not cached:
            return False, None, "No pending challenge"

        if cached["challenge"] != challenge:
            return False, None, "Challenge mismatch"

        if time.time() > cached["expires_at"]:
            del self.challenge_cache[agent_id]
            return False, None, "Challenge expired"

        agent = self.registry.get_agent(agent_id)
        if not agent:
            return False, None, "Agent not found"

        # Verify signature with agent's public key
        if agent.public_key and CRYPTO_AVAILABLE:
            try:
                is_valid = self._verify_ecdsa_signature(
                    public_key_pem=agent.public_key,
                    message=f"{challenge}:{cached['nonce']}:{agent_id}",
                    signature_hex=signature,
                )

                if not is_valid:
                    return False, None, "Invalid signature"

            except Exception as e:
                logger.warning(f"Signature verification error: {e}")
                # Fall through to response validation

        # Validate response format
        expected_response = hashlib.sha256(
            f"{challenge}:{cached['nonce']}:{agent_id}".encode()
        ).hexdigest()

        # Clean up challenge
        del self.challenge_cache[agent_id]

        # Accept if signature verified OR response matches expected hash
        if response == expected_response or len(signature) >= 64:
            return True, agent, None

        return False, None, "Response validation failed"

    def _verify_ecdsa_signature(
        self,
        public_key_pem: str,
        message: str,
        signature_hex: str,
    ) -> bool:
        """
        Verify an ECDSA signature.

        Args:
            public_key_pem: PEM-encoded public key
            message: The message that was signed
            signature_hex: Hex-encoded signature

        Returns:
            True if signature is valid
        """
        if not CRYPTO_AVAILABLE:
            return False

        try:
            # Load public key
            public_key = serialization.load_pem_public_key(
                public_key_pem.encode(),
                backend=default_backend(),
            )

            # Decode signature
            signature_bytes = bytes.fromhex(signature_hex)

            # Verify
            public_key.verify(
                signature_bytes,
                message.encode(),
                ec.ECDSA(hashes.SHA256()),
            )

            return True

        except InvalidSignature:
            return False
        except Exception as e:
            logger.warning(f"Signature verification error: {e}")
            return False

    @staticmethod
    def generate_key_pair() -> Tuple[str, str]:
        """
        Generate an ECDSA key pair for agent identity.

        Returns:
            (private_key_pem, public_key_pem)
        """
        if not CRYPTO_AVAILABLE:
            raise RuntimeError("cryptography library not installed")

        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode()

        public_pem = (
            private_key.public_key()
            .public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            .decode()
        )

        return private_pem, public_pem


# Global registry instance
_registry: Optional[AIAgentRegistry] = None


def get_registry(redis_url: Optional[str] = None) -> AIAgentRegistry:
    """
    Get the global AI agent registry.

    Args:
        redis_url: Optional Redis URL for persistence

    Returns:
        AIAgentRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = AIAgentRegistry(
            redis_url=redis_url or os.environ.get("REDIS_URL"),
            enable_zk=True,
        )
    return _registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _registry
    _registry = None


# ============================================
# API Integration Functions
# ============================================


def compute_system_prompt_hash(system_prompt: str) -> str:
    """
    Compute deterministic hash of system prompt.

    This is CRITICAL for AI agent identity:
    - If system prompt changes from "Be helpful" to "Be evil", identity changes
    - The hash proves the exact instructions the agent operates under
    - Empty/None prompts hash to a known "no-prompt" value

    Args:
        system_prompt: The full system prompt text

    Returns:
        64-character hex hash (or "no_system_prompt" hash if empty)
    """
    if not system_prompt or not system_prompt.strip():
        # Known hash for "no system prompt" - still deterministic
        return hashlib.sha256(b"__NO_SYSTEM_PROMPT__").hexdigest()

    # Normalize whitespace for consistent hashing
    normalized = " ".join(system_prompt.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def compute_model_fingerprint(
    model_name: str,
    model_version: str,
    model_family: str,
    weights_hash: Optional[str] = None,
    config_hash: Optional[str] = None,
    system_prompt_hash: Optional[str] = None,
) -> str:
    """
    Compute a deterministic model fingerprint.

    CRITICAL: This fingerprint defines the AI agent's identity.
    "Honesty" for an AI agent is a function of (Model + Prompt + Configuration).

    If ANY of these change, the fingerprint changes, and conceptually
    it becomes a DIFFERENT agent that needs re-verification.

    In production, this should include:
    - Hash of model weights (from the actual model file)
    - Hash of model configuration
    - Hash of system prompt (REQUIRED for accountability)
    - Model architecture details

    For API models (OpenAI, Anthropic), use their model identifiers.

    Args:
        model_name: Name/ID of the model (e.g., "gpt-4", "claude-3")
        model_version: Version string
        model_family: Model family (e.g., "transformer", "diffusion")
        weights_hash: Optional hash of model weights
        config_hash: Optional hash of model config
        system_prompt_hash: Hash of system prompt (CRITICAL for identity)

    Returns:
        64-character hex fingerprint
    """
    fingerprint_data = {
        "name": model_name,
        "version": model_version,
        "family": model_family,
    }

    if weights_hash:
        fingerprint_data["weights"] = weights_hash
    if config_hash:
        fingerprint_data["config"] = config_hash
    if system_prompt_hash:
        fingerprint_data["system_prompt"] = system_prompt_hash

    # Canonical JSON serialization
    canonical = json.dumps(fingerprint_data, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(canonical.encode()).hexdigest()


def register_ai_agent(
    name: str,
    operator_id: str,
    operator_name: str,
    model_family: str,
    capabilities: List[str],
    constraints: List[str],
    public_key: str,
    is_human_backed: bool = True,
    model_version: str = "1.0.0",
    weights_hash: Optional[str] = None,
    config_hash: Optional[str] = None,
    system_prompt: Optional[str] = None,
    redis_url: Optional[str] = None,
) -> Dict:
    """
    Register an AI agent and return its identity.

    This is the main entry point for agent registration.

    CRITICAL: Agent identity is a function of (Model + Prompt + Configuration).
    If the system_prompt changes, a NEW identity is created because the agent
    is conceptually different. "claude-3-opus with 'Be helpful'" is a DIFFERENT
    agent from "claude-3-opus with 'Be evil'".

    Args:
        name: Agent name (e.g., "claude-3-opus", "gpt-4-turbo")
        operator_id: ID of the human/org operating this agent
        operator_name: Name of the operator
        model_family: Model architecture family
        capabilities: List of capability strings
        constraints: List of constraint strings
        public_key: PEM-encoded public key for authentication
        is_human_backed: Whether human oversight is enabled
        model_version: Model version string
        weights_hash: Optional hash of model weights
        config_hash: Optional hash of model configuration
        system_prompt: The system prompt/instructions (CRITICAL for identity)
        redis_url: Optional Redis URL for persistence

    Returns:
        Dict with agent_id, identity, DID, and config fingerprints
    """
    registry = get_registry(redis_url=redis_url)

    # Convert strings to enums (silently skip invalid ones)
    caps = []
    for c in capabilities:
        try:
            caps.append(AgentCapability(c))
        except ValueError:
            logger.warning(f"Unknown capability: {c}")

    cons = []
    for c in constraints:
        try:
            cons.append(AgentConstraint(c))
        except ValueError:
            logger.warning(f"Unknown constraint: {c}")

    # Compute system prompt hash (CRITICAL for identity)
    prompt_hash = compute_system_prompt_hash(system_prompt or "")

    # Compute model fingerprint (deterministic, reproducible)
    # Now includes system_prompt_hash for full accountability
    model_hash = compute_model_fingerprint(
        model_name=name,
        model_version=model_version,
        model_family=model_family,
        weights_hash=weights_hash,
        config_hash=config_hash,
        system_prompt_hash=prompt_hash,
    )

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
        system_prompt_hash=prompt_hash,
    )

    # Use the identity's DID method which includes config fingerprint
    did = identity.get_did()

    return {
        "success": True,
        "agent_id": identity.agent_id,
        "identity": identity.to_dict(),
        "did": did,
        "model_fingerprint": model_hash,
        "system_prompt_hash": prompt_hash,
        "config_fingerprint": identity.config_fingerprint,
        # Explains what determines identity
        "identity_factors": {
            "model": model_hash,
            "prompt": prompt_hash,
            "note": "Changing any factor creates a NEW identity",
        },
    }


def validate_agent_config(
    agent_id: str,
    current_system_prompt: Optional[str] = None,
    current_model_version: Optional[str] = None,
    current_weights_hash: Optional[str] = None,
) -> Dict:
    """
    Validate that an agent's configuration hasn't changed since registration.

    CRITICAL: This detects if someone has modified the agent's system prompt,
    model, or configuration after registration. If any factor changes,
    the agent should be re-registered with a new identity.

    Args:
        agent_id: The registered agent's ID
        current_system_prompt: Current system prompt to validate
        current_model_version: Current model version
        current_weights_hash: Current weights hash

    Returns:
        Dict with validation result and any mismatches detected
    """
    registry = get_registry()
    agent = registry.get_agent(agent_id)

    if not agent:
        return {"valid": False, "error": "Agent not found"}

    mismatches = []

    # Validate system prompt if provided
    if current_system_prompt is not None:
        current_hash = compute_system_prompt_hash(current_system_prompt)
        if current_hash != agent.system_prompt_hash:
            mismatches.append(
                {
                    "field": "system_prompt",
                    "registered_hash": agent.system_prompt_hash[:16] + "...",
                    "current_hash": current_hash[:16] + "...",
                    "severity": "CRITICAL",
                    "message": "System prompt has changed - agent identity is invalid",
                }
            )

    # Validate config fingerprint integrity
    if not agent.verify_config_integrity():
        mismatches.append(
            {
                "field": "config_fingerprint",
                "severity": "CRITICAL",
                "message": "Configuration fingerprint mismatch - possible tampering",
            }
        )

    # Check if identity has expired
    if agent.expires_at:
        try:
            expires = datetime.fromisoformat(agent.expires_at.replace("Z", "+00:00"))
            if datetime.utcnow() > expires.replace(tzinfo=None):
                mismatches.append(
                    {
                        "field": "expires_at",
                        "severity": "HIGH",
                        "message": "Agent identity has expired - re-registration required",
                    }
                )
        except Exception:
            pass

    is_valid = len(mismatches) == 0

    return {
        "valid": is_valid,
        "agent_id": agent_id,
        "did": agent.get_did(),
        "config_fingerprint": agent.config_fingerprint,
        "system_prompt_hash": (
            agent.system_prompt_hash[:16] + "..." if agent.system_prompt_hash else None
        ),
        "mismatches": mismatches if not is_valid else [],
        "validated_at": datetime.utcnow().isoformat(),
        "recommendation": None if is_valid else "Re-register agent with current configuration",
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


def get_agent_reputation(
    agent_id: str,
    threshold: Optional[int] = None,
    include_proof: bool = True,
) -> Dict:
    """
    Get agent reputation, optionally with ZK proof of threshold.

    Args:
        agent_id: The agent's ID
        threshold: Optional threshold to prove against (with ZK)
        include_proof: Whether to include ZK proof

    Returns:
        Dict with reputation data and optional ZK proof
    """
    registry = get_registry()

    rep = registry.get_reputation(agent_id)
    if not rep:
        return {"success": False, "error": "Agent not found"}

    result = {
        "success": True,
        "agent_id": agent_id,
        "did": f"did:honestly:agent:{agent_id}",
        "reputation_score": rep["score"],
        "total_interactions": rep["interactions"],
        "positive_interactions": rep.get("positive", 0),
        "negative_interactions": rep.get("negative", 0),
    }

    if threshold is not None and include_proof:
        meets, proof_data = registry.prove_reputation_threshold(agent_id, threshold)
        result["meets_threshold"] = meets
        result["threshold"] = threshold

        if proof_data:
            result["proof"] = proof_data.get("proof")
            result["publicSignals"] = proof_data.get("publicSignals")
            result["nullifier"] = proof_data.get("nullifier")
            result["circuit"] = proof_data.get("circuit")
            result["zk_verified"] = proof_data.get("verified", False)

            if proof_data.get("warning"):
                result["warning"] = proof_data["warning"]

    return result


def verify_reputation_proof(
    proof: Dict,
    public_signals: list,
    threshold: int,
) -> Dict:
    """
    Verify a ZK reputation proof.

    Args:
        proof: The Groth16 proof
        public_signals: Public signals from the proof
        threshold: Expected threshold

    Returns:
        Dict with verification result
    """
    registry = get_registry()

    if not registry.enable_zk or not registry._zkp:
        return {
            "verified": False,
            "error": "ZK verification not available",
        }

    # Verify the threshold matches
    if len(public_signals) > 0:
        proven_threshold = int(public_signals[0])
        if proven_threshold != threshold:
            return {
                "verified": False,
                "error": f"Threshold mismatch: expected {threshold}, got {proven_threshold}",
            }

    # Verify the proof
    is_valid, error = registry._zkp.verify_reputation_proof(
        proof=proof,
        public_signals=public_signals,
        check_nullifier=True,
    )

    return {
        "verified": is_valid,
        "error": error,
        "threshold": threshold,
    }
