"""
Identity API Routes
===================

REST endpoints for the world-changing identity features.

Features:
- AI Agent Identity Protocol
- Verifiable Credentials
- Social Recovery
- Cross-Chain Identity Bridge
- Proof of Humanity
"""

import os
import secrets
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

# Import identity modules
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from identity.ai_agent_protocol import (
    get_registry,
    register_ai_agent,
    verify_agent_capability,
    get_agent_reputation,
)
from identity.verifiable_credentials import (
    CredentialIssuer,
    CredentialVerifier,
    CredentialType,
    SelectiveDisclosure,
    create_proof_of_humanity_credential,
)
from identity.social_recovery import (
    SocialRecoveryManager,
    create_recovery_setup,
)
from identity.cross_chain_bridge import (
    get_bridge,
    get_resolver,
    Chain,
)

router = APIRouter(prefix="/identity", tags=["identity"])


# ============================================
# PYDANTIC MODELS
# ============================================


class RegisterAgentRequest(BaseModel):
    """Request to register an AI agent.

    CRITICAL: Agent identity = Model + Prompt + Configuration.
    The system_prompt is required to create a unique, verifiable identity.
    """

    name: str = Field(..., description="Agent name (e.g., claude-3-opus)")
    operator_id: str = Field(..., description="Operator identifier")
    operator_name: str = Field(..., description="Operator name (organization)")
    model_family: str = Field(..., description="Model family (e.g., transformer)")
    capabilities: List[str] = Field(..., description="Agent capabilities")
    constraints: List[str] = Field(default=[], description="Agent constraints")
    public_key: str = Field(..., description="Agent's public key (PEM format)")
    is_human_backed: bool = Field(default=True, description="Has human oversight")
    system_prompt: Optional[str] = Field(
        None, description="System prompt/instructions (CRITICAL for identity)"
    )
    model_version: Optional[str] = Field("1.0.0", description="Model version")
    weights_hash: Optional[str] = Field(None, description="Hash of model weights (optional)")
    config_hash: Optional[str] = Field(None, description="Hash of model configuration (optional)")


class VerifyCapabilityRequest(BaseModel):
    """Request to verify agent capability."""

    agent_id: str
    capability: str


class IssueCredentialRequest(BaseModel):
    """Request to issue a credential."""

    subject_did: str = Field(..., description="Subject DID")
    credential_type: str = Field(..., description="Type of credential")
    claims: Dict[str, Any] = Field(..., description="Credential claims")
    expires_days: int = Field(default=365, description="Days until expiration")
    selective_disclosure: bool = Field(default=False, description="Enable ZK selective disclosure")


class SetupRecoveryRequest(BaseModel):
    """Request to setup social recovery."""

    user_id: str
    guardians: List[Dict[str, Any]] = Field(..., description="Guardian configurations")
    threshold: Optional[int] = Field(None, description="Recovery threshold")


class BridgeIdentityRequest(BaseModel):
    """Request to bridge identity to a new chain."""

    universal_did: str
    target_chain: str
    target_address: str


class CreateUniversalIdentityRequest(BaseModel):
    """Request to create a universal identity."""

    primary_chain: str = Field(default="ethereum")
    primary_address: str
    metadata: Optional[Dict] = None


class ProofOfHumanityRequest(BaseModel):
    """Request proof of humanity."""

    subject_did: str
    verification_method: str = Field(default="liveness_check")
    liveness_score: float = Field(default=0.95, ge=0, le=1)


# ============================================
# AI AGENT IDENTITY ENDPOINTS
# ============================================


@router.post("/agent/register")
async def api_register_agent(request: RegisterAgentRequest):
    """
    Register a new AI agent identity.

    This creates a verifiable identity for an AI agent, allowing it to:
    - Prove its capabilities
    - Accumulate reputation
    - Interact with other agents trustfully
    """
    try:
        result = register_ai_agent(
            name=request.name,
            operator_id=request.operator_id,
            operator_name=request.operator_name,
            model_family=request.model_family,
            capabilities=request.capabilities,
            constraints=request.constraints,
            public_key=request.public_key,
            is_human_backed=request.is_human_backed,
            system_prompt=request.system_prompt,  # CRITICAL: Required for identity
            model_version=request.model_version,
            weights_hash=request.weights_hash,
            config_hash=request.config_hash,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/agent/verify-capability")
async def api_verify_capability(request: VerifyCapabilityRequest):
    """
    Verify an agent has a specific capability.

    Returns a proof commitment that can be verified on-chain.
    """
    result = verify_agent_capability(request.agent_id, request.capability)
    return result


@router.get("/agent/{agent_id}")
async def api_get_agent(agent_id: str):
    """Get agent identity details."""
    registry = get_registry()
    agent = registry.get_agent(agent_id)

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    return {
        "success": True,
        "agent": agent.to_dict(),
        "did": f"did:honestly:agent:{agent_id}",
    }


@router.get("/agent/{agent_id}/reputation")
async def api_get_agent_reputation(
    agent_id: str,
    threshold: Optional[int] = None,
):
    """
    Get agent reputation, optionally with threshold proof.

    If threshold is provided, returns a ZK proof that
    reputation meets the threshold without revealing exact score.
    """
    return get_agent_reputation(agent_id, threshold)


@router.post("/agent/{agent_id}/interaction")
async def api_record_interaction(
    agent_id: str,
    positive: bool = Body(..., embed=True),
    weight: float = Body(1.0, embed=True),
):
    """Record an interaction outcome for reputation update."""
    registry = get_registry()
    result = registry.update_reputation(agent_id, positive, weight)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return {"success": True, "reputation": result}


# ============================================
# VERIFIABLE CREDENTIALS ENDPOINTS
# ============================================

# Global credential issuer
_issuer = None


def get_issuer() -> CredentialIssuer:
    global _issuer
    if _issuer is None:
        _issuer = CredentialIssuer(
            issuer_did="did:honestly:issuer:main",
            issuer_name="Honestly Platform",
        )
    return _issuer


@router.post("/credentials/issue")
async def api_issue_credential(request: IssueCredentialRequest):
    """
    Issue a verifiable credential.

    Supports W3C Verifiable Credentials format with
    optional ZK selective disclosure.
    """
    issuer = get_issuer()

    try:
        credential_type = CredentialType(request.credential_type)
    except ValueError:
        # Default to generic credential
        credential_type = CredentialType.VERIFIABLE_CREDENTIAL

    credential = issuer.issue_credential(
        subject_did=request.subject_did,
        credential_type=credential_type,
        claims=request.claims,
        expires_days=request.expires_days,
        enable_selective_disclosure=request.selective_disclosure,
    )

    return {
        "success": True,
        "credential": credential.to_dict(),
        "credential_hash": credential.get_hash(),
    }


@router.post("/credentials/verify")
async def api_verify_credential(credential: Dict = Body(...)):
    """
    Verify a credential's authenticity.

    Checks structure, signature, expiration, and revocation status.
    """
    from identity.verifiable_credentials import VerifiableCredential, CredentialSubject, Proof

    verifier = CredentialVerifier()

    # Reconstruct credential object
    try:
        subject = CredentialSubject(
            id=credential["credentialSubject"]["id"],
            claims={k: v for k, v in credential["credentialSubject"].items() if k != "id"},
        )

        proof_data = credential.get("proof", {})
        proof = (
            Proof(
                type=proof_data.get("type", ""),
                created=proof_data.get("created", ""),
                verification_method=proof_data.get("verificationMethod", ""),
                proof_value=proof_data.get("proofValue", ""),
            )
            if proof_data
            else None
        )

        vc = VerifiableCredential(
            id=credential["id"],
            type=credential["type"],
            issuer=credential["issuer"],
            issuance_date=credential["issuanceDate"],
            expiration_date=credential.get("expirationDate"),
            credential_subject=subject,
            proof=proof,
        )

        result = verifier.verify_credential(vc)
        return result

    except Exception as e:
        return {"valid": False, "error": str(e)}


@router.post("/credentials/proof-of-humanity")
async def api_proof_of_humanity(request: ProofOfHumanityRequest):
    """
    Issue a Proof of Humanity credential.

    This credential proves the subject is human without
    revealing their identity - critical for the AI age.
    """
    issuer = get_issuer()

    credential = create_proof_of_humanity_credential(
        issuer=issuer,
        subject_did=request.subject_did,
        verification_method=request.verification_method,
        liveness_score=request.liveness_score,
    )

    return {
        "success": True,
        "credential": credential.to_dict(),
        "message": "Proof of Humanity issued successfully",
    }


@router.post("/credentials/selective-disclose")
async def api_selective_disclosure(
    credential: Dict = Body(...),
    claims_to_disclose: List[str] = Body(...),
    holder_did: str = Body(...),
):
    """
    Create a selective disclosure presentation.

    Reveals only specified claims, with ZK proof of others existing.
    """
    from identity.verifiable_credentials import VerifiableCredential, CredentialSubject

    try:
        subject = CredentialSubject(
            id=credential["credentialSubject"]["id"],
            claims={k: v for k, v in credential["credentialSubject"].items() if k != "id"},
        )

        vc = VerifiableCredential(
            id=credential["id"],
            type=credential["type"],
            issuer=credential["issuer"],
            issuance_date=credential["issuanceDate"],
            credential_subject=subject,
            selective_disclosure_enabled=True,
        )

        presentation = SelectiveDisclosure.create_disclosed_presentation(
            credential=vc,
            claims_to_disclose=claims_to_disclose,
            holder_did=holder_did,
        )

        return {
            "success": True,
            "presentation": presentation.to_dict(),
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================
# SOCIAL RECOVERY ENDPOINTS
# ============================================

_recovery_manager = None


def get_recovery_manager() -> SocialRecoveryManager:
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = SocialRecoveryManager()
    return _recovery_manager


@router.post("/recovery/setup")
async def api_setup_recovery(request: SetupRecoveryRequest):
    """
    Set up social recovery for an identity.

    Uses Shamir's Secret Sharing to split the master key
    among trusted guardians.
    """
    # Generate a master key for demo (in production, user provides their key)
    master_key = secrets.token_bytes(32)

    try:
        config, shares = create_recovery_setup(
            user_id=request.user_id,
            master_key=master_key,
            guardians=request.guardians,
            threshold=request.threshold,
        )

        return {
            "success": True,
            "config": {
                "user_id": config.user_id,
                "threshold": config.threshold,
                "total_shares": config.total_shares,
                "guardians": [g.name for g in config.guardians],
            },
            "shares": shares,  # These should be distributed to guardians securely
            "message": f"Recovery set up with {config.threshold}-of-{config.total_shares} scheme",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recovery/initiate/{user_id}")
async def api_initiate_recovery(user_id: str):
    """
    Initiate the recovery process.

    This starts collecting shares from guardians.
    """
    manager = get_recovery_manager()

    try:
        process = manager.initiate_recovery(user_id)
        return {
            "success": True,
            "recovery_id": process.recovery_id,
            "status": process.status.value,
            "threshold": process.threshold,
            "expires_at": process.expires_at,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/recovery/{recovery_id}/submit-share")
async def api_submit_share(
    recovery_id: str,
    guardian_id: str = Body(...),
    share_index: int = Body(...),
    share_value: str = Body(...),  # Hex string
):
    """
    Submit a recovery share from a guardian.
    """
    manager = get_recovery_manager()

    try:
        # Convert hex share value to int
        share_int = int(share_value, 16) if share_value.startswith("0x") else int(share_value, 16)

        result = manager.submit_share(
            recovery_id=recovery_id,
            guardian_id=guardian_id,
            share_index=share_index,
            share_value=share_int,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/recovery/{recovery_id}/status")
async def api_recovery_status(recovery_id: str):
    """Get the current status of a recovery process."""
    manager = get_recovery_manager()
    return manager.get_recovery_status(recovery_id)


# ============================================
# CROSS-CHAIN BRIDGE ENDPOINTS
# ============================================


@router.post("/bridge/create")
async def api_create_universal_identity(request: CreateUniversalIdentityRequest):
    """
    Create a universal cross-chain identity.

    This identity can be bridged to any supported blockchain.
    """
    bridge = get_bridge()

    try:
        chain = Chain(request.primary_chain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.primary_chain}")

    # Generate identity secret
    identity_secret = secrets.token_hex(32)

    identity = bridge.create_universal_identity(
        identity_secret=identity_secret,
        primary_chain=chain,
        primary_address=request.primary_address,
        metadata=request.metadata,
    )

    return {
        "success": True,
        "identity": identity.to_dict(),
        "identity_secret": identity_secret,  # User must save this securely!
        "message": "Save your identity secret securely - it cannot be recovered!",
    }


@router.post("/bridge/bridge")
async def api_bridge_identity(request: BridgeIdentityRequest):
    """
    Bridge an identity to a new blockchain.

    This creates a verifiable presence on the target chain
    linked to the universal identity.
    """
    bridge = get_bridge()

    try:
        target_chain = Chain(request.target_chain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {request.target_chain}")

    try:
        chain_identity, proof = bridge.bridge_identity(
            universal_did=request.universal_did,
            target_chain=target_chain,
            target_address=request.target_address,
        )

        return {
            "success": True,
            "chain_identity": chain_identity.to_dict(),
            "merkle_proof": proof.to_dict(),
            "message": f"Identity bridged to {request.target_chain}",
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bridge/{universal_did}")
async def api_get_universal_identity(universal_did: str):
    """Get a universal identity's details."""
    bridge = get_bridge()
    identity = bridge.get_identity(universal_did)

    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    return {"success": True, "identity": identity}


@router.post("/bridge/{universal_did}/verify")
async def api_verify_on_chain(
    universal_did: str,
    chain: str = Body(..., embed=True),
):
    """Verify an identity on a specific chain."""
    bridge = get_bridge()

    try:
        target_chain = Chain(chain)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Unsupported chain: {chain}")

    result = bridge.verify_cross_chain_identity(universal_did, target_chain)
    return result


@router.post("/bridge/{universal_did}/sync")
async def api_sync_identity(universal_did: str):
    """Synchronize identity state across all chains."""
    bridge = get_bridge()
    return bridge.sync_identity(universal_did)


@router.get("/bridge/chains")
async def api_list_chains():
    """List all supported blockchains."""
    bridge = get_bridge()
    return {"chains": bridge.list_supported_chains()}


# ============================================
# DID RESOLVER ENDPOINTS
# ============================================


@router.get("/did/resolve/{did:path}")
async def api_resolve_did(did: str):
    """
    Resolve a DID to its document.

    Supports:
    - did:honestly:universal:<id>
    - did:honestly:ethereum:<address>
    - did:honestly:polygon:<address>
    - etc.
    """
    resolver = get_resolver()
    document = resolver.resolve(did)

    if not document:
        raise HTTPException(status_code=404, detail="DID not found")

    return {"didDocument": document}


# ============================================
# STATISTICS & INFO
# ============================================


@router.get("/stats")
async def api_identity_stats():
    """Get identity system statistics."""
    bridge = get_bridge()
    registry = get_registry()

    return {
        "ai_agents_registered": len(registry.storage),
        "universal_identities": len(bridge.identities),
        "supported_chains": len(bridge.adapters),
        "features": {
            "ai_agent_identity": True,
            "verifiable_credentials": True,
            "social_recovery": True,
            "cross_chain_bridge": True,
            "proof_of_humanity": True,
            "selective_disclosure": True,
        },
    }
