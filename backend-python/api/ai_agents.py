"""
AI Agent endpoints with validation, audit trails, rate limiting, and ML anomaly detection.
Designed for flawless AI interaction with the vault system.

Features:
- ZK proof verification with anomaly scoring
- Batch proof verification (100+ req/min)
- AAIP agent reputation/capability proofs
- ML-based anomaly detection (isolation forest)
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, Field, validator
from py2neo import Graph

from vault.storage import VaultStorage
from vault.zk_proofs import ZKProofService
from vault.share_links import ShareLinkService
from api.security import verify_ai_agent_signature, get_current_user, rate_limit, sanitize_input
from api.monitoring import log_ai_interaction

# ML anomaly detection
try:
    from ml.anomaly_detector import get_detector, AnomalyScore
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    get_detector = None

logger = logging.getLogger(__name__)

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
        allowed_actions = [
            'verify_proof',
            'verify_proofs_batch',
            'get_document_hash',
            'create_share_link',
            'query_timeline',
        ]
        if v not in allowed_actions:
            raise ValueError(f"Action must be one of {allowed_actions}")
        return v


class ProofVerificationRequest(BaseModel):
    """Request model for proof verification."""
    proof_data: str = Field(..., min_length=1)
    proof_type: str = Field(..., pattern=r'^(age_proof|authenticity_proof|agent_reputation|agent_capability)$')
    public_inputs: Optional[str] = None
    include_anomaly_score: bool = Field(default=True, description="Include ML anomaly analysis")


class BatchProofRequest(BaseModel):
    """Request model for batch proof verification."""
    proofs: List[ProofVerificationRequest] = Field(..., min_items=1, max_items=50)
    include_anomaly_score: bool = Field(default=True)


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


def lookup_document_by_hash(document_hash: str) -> Optional[Dict[str, Any]]:
    """
    Reverse lookup a document by its hash.
    
    Queries Neo4j for documents with matching hash.
    
    Args:
        document_hash: The document hash to look up
        
    Returns:
        Document metadata dict or None if not found
    """
    try:
        # Sanitize input
        clean_hash = sanitize_input(document_hash)
        
        # Query Neo4j for document with this hash
        query = """
        MATCH (d:Document {hash: $hash})
        RETURN d.id as id, d.hash as hash, d.document_type as document_type,
               d.created_at as created_at, d.owner_id as owner_id
        LIMIT 1
        """
        
        results = graph.run(query, {"hash": clean_hash}).data()
        
        if results:
            return results[0]
        
        # Also check vault storage for local documents
        # This handles documents not yet synced to Neo4j
        all_docs = vault_storage.list_documents() if hasattr(vault_storage, 'list_documents') else []
        for doc_id in all_docs:
            meta = vault_storage.get_document_metadata(doc_id)
            if meta and meta.get('hash') == clean_hash:
                return {
                    'id': doc_id,
                    'hash': meta.get('hash'),
                    'document_type': meta.get('document_type'),
                    'created_at': meta.get('created_at'),
                    'owner_id': meta.get('owner_id'),
                }
        
        return None
        
    except Exception as e:
        # Log error but don't expose details
        import logging
        logging.getLogger('api.ai_agents').error(f"Hash lookup error: {e}")
        return None


@router.post("/verify-proof", response_model=Dict[str, Any])
@rate_limit(calls=AI_AGENT_RATE_LIMIT, period=60)
async def ai_verify_proof(
    request: ProofVerificationRequest,
    agent_request: AIAgentRequest = Depends(),
    x_ai_signature: Optional[str] = Header(None, alias='X-AI-Signature')
):
    """
    AI agent endpoint to verify zkSNARK proofs.
    Returns verification result with ML anomaly analysis.
    
    Supports:
    - age_proof: Standard age verification
    - authenticity_proof: Document authenticity
    - agent_reputation: AAIP reputation proof
    - agent_capability: AAIP capability proof
    """
    start_time = datetime.utcnow()
    
    # Verify signature
    if not verify_ai_request(agent_request, x_ai_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    try:
        # Parse proof data for anomaly analysis
        try:
            proof_data_parsed = json.loads(request.proof_data)
        except json.JSONDecodeError:
            proof_data_parsed = {}
        
        # Verify proof based on type
        if request.proof_type == 'age_proof':
            verified = zk_service.verify_age_proof(request.proof_data, request.public_inputs or '')
        elif request.proof_type == 'authenticity_proof':
            verified = zk_service.verify_authenticity_proof(request.proof_data, request.public_inputs or '')
        elif request.proof_type in ('agent_reputation', 'agent_capability'):
            verified = zk_service.verify_agent_proof(request.proof_data, request.proof_type)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid proof type")
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # ML anomaly analysis
        anomaly_result = None
        if request.include_anomaly_score and ML_AVAILABLE:
            try:
                detector = get_detector()
                anomaly_score = detector.analyze_proof(
                    proof_data_parsed,
                    agent_id=agent_request.agent_id,
                    proof_type=request.proof_type,
                )
                anomaly_result = anomaly_score.to_dict()
            except Exception as e:
                logger.warning(f"Anomaly detection failed: {e}")
                anomaly_result = {"error": "analysis_failed"}
        
        # Log interaction
        log_ai_interaction(
            agent_id=agent_request.agent_id,
            action='verify_proof',
            success=True,
            duration=duration,
            metadata={
                'proof_type': request.proof_type,
                'verified': verified,
                'anomaly_score': anomaly_result.get('anomaly_score') if anomaly_result else None,
            }
        )
        
        response = {
            'verified': verified,
            'proof_type': request.proof_type,
            'verification_time_ms': round(duration * 1000, 2),
            'timestamp': datetime.utcnow().isoformat(),
        }
        
        if anomaly_result:
            response['anomaly'] = anomaly_result
        
        return response
    
    except HTTPException:
        raise
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


@router.post("/verify-proofs-batch", response_model=Dict[str, Any])
@rate_limit(calls=AI_AGENT_RATE_LIMIT * 2, period=60)  # Higher limit for batch
async def ai_verify_proofs_batch(
    request: BatchProofRequest,
    agent_request: AIAgentRequest = Depends(),
    x_ai_signature: Optional[str] = Header(None, alias='X-AI-Signature')
):
    """
    Batch verify multiple zkSNARK proofs.
    
    Enterprise endpoint for high-throughput verification.
    Target: 100+ req/min on 8-core pod.
    
    Returns verification results with aggregated anomaly analysis.
    """
    start_time = datetime.utcnow()
    
    # Verify signature
    if not verify_ai_request(agent_request, x_ai_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature")
    
    results = []
    total_verified = 0
    total_anomalous = 0
    
    for i, proof_req in enumerate(request.proofs):
        proof_start = datetime.utcnow()
        
        try:
            # Parse proof data
            try:
                proof_data_parsed = json.loads(proof_req.proof_data)
            except json.JSONDecodeError:
                proof_data_parsed = {}
            
            # Verify based on type
            if proof_req.proof_type == 'age_proof':
                verified = zk_service.verify_age_proof(proof_req.proof_data, proof_req.public_inputs or '')
            elif proof_req.proof_type == 'authenticity_proof':
                verified = zk_service.verify_authenticity_proof(proof_req.proof_data, proof_req.public_inputs or '')
            elif proof_req.proof_type in ('agent_reputation', 'agent_capability'):
                verified = zk_service.verify_agent_proof(proof_req.proof_data, proof_req.proof_type)
            else:
                verified = False
            
            if verified:
                total_verified += 1
            
            # ML anomaly analysis
            anomaly_result = None
            if request.include_anomaly_score and ML_AVAILABLE:
                try:
                    detector = get_detector()
                    anomaly_score = detector.analyze_proof(
                        proof_data_parsed,
                        agent_id=agent_request.agent_id,
                        proof_type=proof_req.proof_type,
                    )
                    anomaly_result = anomaly_score.to_dict()
                    if anomaly_score.is_anomalous:
                        total_anomalous += 1
                except Exception:
                    pass
            
            proof_duration = (datetime.utcnow() - proof_start).total_seconds()
            
            result = {
                'index': i,
                'verified': verified,
                'proof_type': proof_req.proof_type,
                'verification_time_ms': round(proof_duration * 1000, 2),
            }
            
            if anomaly_result:
                result['anomaly'] = anomaly_result
            
            results.append(result)
            
        except Exception as e:
            results.append({
                'index': i,
                'verified': False,
                'error': str(e),
                'proof_type': proof_req.proof_type,
            })
    
    total_duration = (datetime.utcnow() - start_time).total_seconds()
    
    # Log batch interaction
    log_ai_interaction(
        agent_id=agent_request.agent_id,
        action='verify_proofs_batch',
        success=True,
        duration=total_duration,
        metadata={
            'batch_size': len(request.proofs),
            'total_verified': total_verified,
            'total_anomalous': total_anomalous,
        }
    )
    
    return {
        'results': results,
        'summary': {
            'total': len(request.proofs),
            'verified': total_verified,
            'failed': len(request.proofs) - total_verified,
            'anomalous': total_anomalous,
            'total_time_ms': round(total_duration * 1000, 2),
            'avg_time_ms': round((total_duration / len(request.proofs)) * 1000, 2) if request.proofs else 0,
        },
        'timestamp': datetime.utcnow().isoformat(),
    }


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
            # Reverse lookup by document hash via Neo4j
            doc = lookup_document_by_hash(request.document_hash)
            if not doc:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document with hash not found")
            
            return {
                'document_id': doc.get('id'),
                'hash': request.document_hash,
                'document_type': doc.get('document_type'),
                'created_at': doc.get('created_at'),
                'owner_id': doc.get('owner_id'),
            }
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
    # Get ML status
    ml_status = "unavailable"
    ml_stats = {}
    if ML_AVAILABLE:
        try:
            detector = get_detector()
            ml_stats = detector.get_stats()
            ml_status = "available"
        except Exception:
            ml_status = "error"
    
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'vault': 'available',
            'zk_proofs': 'available',
            'neo4j': 'available',
            'ml_anomaly_detection': ml_status,
        },
        'ml_stats': ml_stats if ml_stats else None,
    }


@router.get("/anomaly-stats")
async def get_anomaly_stats():
    """Get ML anomaly detection statistics."""
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML anomaly detection not available"
        )
    
    try:
        detector = get_detector()
        return {
            'status': 'available',
            'stats': detector.get_stats(),
            'timestamp': datetime.utcnow().isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


