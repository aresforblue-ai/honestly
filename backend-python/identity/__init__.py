"""
Honestly Identity Module
========================

World-changing identity infrastructure for the decentralized future.

This module provides:
- AI Agent Identity Protocol (AAIP) - Verified AI agent identities
- W3C Verifiable Credentials - Universal credential format
- Social Recovery - Shamir's Secret Sharing for key recovery
- Cross-Chain Identity Bridge - Portable identity across blockchains
- Proof of Humanity - ZK proof of human-ness
- Privacy-Preserving Reputation - Prove reputation without revealing history

Usage:
    from identity import (
        register_ai_agent,
        create_credential,
        setup_social_recovery,
        bridge_identity,
    )
"""

from .ai_agent_protocol import (
    AIAgentRegistry,
    AgentIdentity,
    AgentCapability,
    AgentConstraint,
    AgentTrustLevel,
    AgentAuthenticator,
    register_ai_agent,
    verify_agent_capability,
    validate_agent_config,  # NEW: Validate agent config integrity
    get_agent_reputation,
    get_registry,
    reset_registry,
    verify_reputation_proof,
    compute_model_fingerprint,
    compute_system_prompt_hash,  # NEW: Hash system prompt for identity
)

from .zkp_integration import (
    AAIPZKIntegration,
    ZKProofResult,
    get_zkp_integration,
    prove_agent_reputation_zk,
    verify_agent_reputation_proof,
)

from .verifiable_credentials import (
    VerifiableCredential,
    VerifiablePresentation,
    CredentialIssuer,
    CredentialVerifier,
    CredentialType,
    SelectiveDisclosure,
    create_age_credential,
    create_education_credential,
    create_proof_of_humanity_credential,
    create_reputation_credential,
)

from .social_recovery import (
    SocialRecoveryManager,
    ShamirSecretSharing,
    GuardianType,
    RecoveryStatus,
    Guardian,
    RecoveryConfig,
    create_recovery_setup,
)

from .cross_chain_bridge import (
    CrossChainBridge,
    Chain,
    ChainType,
    CrossChainIdentity,
    ChainIdentity,
    UniversalDIDResolver,
    get_bridge,
    get_resolver,
)

__all__ = [
    # AI Agent Protocol
    "AIAgentRegistry",
    "AgentIdentity",
    "AgentCapability",
    "AgentConstraint",
    "AgentTrustLevel",
    "AgentAuthenticator",
    "register_ai_agent",
    "verify_agent_capability",
    "validate_agent_config",  # Validate agent hasn't changed
    "get_agent_reputation",
    "get_registry",
    "reset_registry",
    "verify_reputation_proof",
    "compute_model_fingerprint",
    "compute_system_prompt_hash",  # Hash system prompts for identity
    # ZK Integration
    "AAIPZKIntegration",
    "ZKProofResult",
    "get_zkp_integration",
    "prove_agent_reputation_zk",
    "verify_agent_reputation_proof",
    # Verifiable Credentials
    "VerifiableCredential",
    "VerifiablePresentation",
    "CredentialIssuer",
    "CredentialVerifier",
    "CredentialType",
    "SelectiveDisclosure",
    "create_age_credential",
    "create_education_credential",
    "create_proof_of_humanity_credential",
    "create_reputation_credential",
    # Social Recovery
    "SocialRecoveryManager",
    "ShamirSecretSharing",
    "GuardianType",
    "RecoveryStatus",
    "Guardian",
    "RecoveryConfig",
    "create_recovery_setup",
    # Cross-Chain Bridge
    "CrossChainBridge",
    "Chain",
    "ChainType",
    "CrossChainIdentity",
    "ChainIdentity",
    "UniversalDIDResolver",
    "get_bridge",
    "get_resolver",
]

__version__ = "1.0.0"
