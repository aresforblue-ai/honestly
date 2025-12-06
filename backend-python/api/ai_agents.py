"""
AI Agent endpoints with validation, audit trails, and rate limiting.
Designed for flawless AI interaction with the vault system.
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Depends, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from py2neo import Graph

from vault.storage import VaultStorage
from vault.zk_proofs import ZKProofService
from vault.share_links import ShareLinkService
from api.security import verify_ai_agent_signature, get_current_user, rate_limit, sanitize_input
from api.monitoring import log_ai_interaction

router = APIRouter(prefix="/ai", tags=["ai-agents"])

# AI Agent configuration
AI_AGENT_SECRET = os.getenv('AI_AGENT_SECRET', os.urandom(32).hex())
AI_AGENT_RATE_LIMIT = int(os.getenv('AI_AGENT_RATE_LIMIT', 100))  # requests per minute

# Initialize services
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
vault_storage = VaultStorage()
zk_service = ZKProofService()
share_link_service = ShareLinkService(graph)


# Request/Response Models
class AIAgentRequest(BaseModel):
    """Base model for AI agent requests with validation."""
    agent_id: str = Field(..., min_length=1, max_length=100)
    action: str = Field(..., pattern=r'^[a-z_]+$')
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timestamp: Optional[float] = None
    signature: Optional[str] = None
    
    @validator('agent_id')
    def validate_agent_id(cls, v):
        return sanitize_input(v)
    
    @validator('action')
    def validate_action(cls, v):
        allowed_actions = ['verify_proof', 'get_document_hash', 'create_share_link', 'query_timeline']
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of {allowed_actions}")
        return v


class ProofVerificationRequest(BaseModel):
    """Request model for proof verification."""
    proof_data: str = Field(..., min_length=1)
    proof_type: str = Field(..., pattern=r'^(age_proof|authenticity_proof)$')
    public_inputs: Optional[str] = None


class ShareLinkRequest(BaseModel):
    """Request model for creating share links."""
    document_id: str = Field(..., min_length=1, max_length=100)
    access_level: str = Field(default='proof_only', pattern=r'^(proof_only|metadata|full)$')
    expires_in_hours: Optional[int] = Field(default=24, ge=1, le=720)  # Max 30 days
    proof_type: Optional[str] = None


class DocumentQueryRequest(BaseModel):
    """Request model for querying documents."""
    document_id: Optional[str] = None
    user_id: Optional[str] = None
    document_hash: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=100)


def verify_ai_request(request: AIAgentRequest, signature: Optional[str] = None) -> bool:
    """Verify AI agent request signature."""
    if not signature:
        return False
    
    # Create payload string for signing
    payload_dict = request.dict(exclude={'signature'})
    payload_str = json.dumps(payload_dict, sort_keys=True)
    
    return verify_ai_agent_signature(payload_str, signature, AI_AGENT_SECRET)


@router.post("/verify-proof", response_model=Dict[str, Any])
@rate_limit(calls=AI_AGENT_RATE_LIMIT, period=60)
async def ai_verify_proof(
    request: ProofVerificationRequest,
    agent_request: AIAgentRequest = Depends(),
    x_ai_signature: Optional[str] = Header(None, alias='X-AI-Signature')
):
    """
    AI agent endpoint to verify zkSNARK proofs.
    Returns verification result with detailed metadata.
    """
    start_time = datetime.utcnow()
    
    # Verify signature
    if not verify_ai_request(agent_request, x_ai_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    try:
        # Verify proof
        if request.proof_type == 'age_proof':
            verified = zk_service.verify_age_proof(request.proof_data, request.public_inputs or '')
        elif request.proof_type == 'authenticity_proof':
            verified = zk_service.verify_authenticity_proof(request.proof_data, request.public_inputs or '')
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof type")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Log interaction
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='verify_proof',
            success=True,
            duration=duration,
            metadata={'proof_type': request.proof_type, 'verified': verified}
        )
        
        return {
            'verified': verified,
            'proof_type': request.proof_type,
            'verification_time_ms': duration * 1000,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        duration = (datetime.utcnow() - start_time).total_seconds()
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='verify_proof',
            success=False,
            duration=duration,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/get-document-hash", response_model=Dict[str, Any])
@rate_limit(calls=AI_AGENT_RATE_LIMIT, period=60)
async def ai_get_document_hash(
    request: DocumentQueryRequest,
    agent_request: AIAgentRequest = Depends(),
    x_ai_signature: Optional[str] = Header(None, alias='X-AI-Signature')
):
    """AI agent endpoint to get document hash without revealing content."""
    if not verify_ai_request(agent_request, x_ai_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    try:
        if request.document_id:
            meta = vault_storage.get_document_metadata(request.document_id)
            if not meta:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
            
            return {
                'document_id': request.document_id,
                'hash': meta.get('hash'),
                'document_type': meta.get('document_type'),
                'created_at': meta.get('created_at')
            }
        elif request.document_hash:
            # Query by hash (if you have reverse lookup)
            raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Hash lookup not implemented")
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="document_id or document_hash required")
    
    except HTTPException:
        raise
    except Exception as e:
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='get_document_hash',
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/create-share-link", response_model=Dict[str, Any])
@rate_limit(calls=AI_AGENT_RATE_LIMIT, period=60)
async def ai_create_share_link(
    request: ShareLinkRequest,
    agent_request: AIAgentRequest = Depends(),
    x_ai_signature: Optional[str] = Header(None, alias='X-AI-Signature'),
    user_id: str = Depends(get_current_user)
):
    """AI agent endpoint to create shareable proof links."""
    if not verify_ai_request(agent_request, x_ai_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    try:
        from datetime import timedelta
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)
        
        from vault.models import AccessLevel
        access_level_map = {
            'proof_only': AccessLevel.PROOF_ONLY,
            'metadata': AccessLevel.METADATA,
            'full': AccessLevel.FULL
        }
        
        proof_link = share_link_service.create_share_link(
            document_id=request.document_id,
            user_id=user_id,
            access_level=access_level_map.get(request.access_level, AccessLevel.PROOF_ONLY),
            expires_at=expires_at,
            proof_type=request.proof_type
        )
        
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='create_share_link',
            success=True,
            metadata={'document_id': request.document_id, 'share_token': proof_link.share_token}
        )
        
        return {
            'share_token': proof_link.share_token,
            'share_url': share_link_service.get_share_url(proof_link.share_token),
            'expires_at': proof_link.expires_at.isoformat() if proof_link.expires_at else None,
            'access_level': proof_link.access_level.value
        }
    
    except Exception as e:
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='create_share_link',
            success=False,
            error=str(e)
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/health")
async def ai_health_check():
    """Health check endpoint for AI agents."""
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'vault': 'available',
            'zk_proofs': 'available',
            'neo4j': 'available'
        }
    }


