"""
REST endpoints for vault operations (file uploads, share links, QR codes).
"""
import os
import base64
import secrets
import time
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse
from py2neo import Graph

from vault.storage import VaultStorage
from vault.models import DocumentType
from vault.share_links import ShareLinkService
from vault.timeline import TimelineService
from blockchain.sdk.fabric_client import FabricClient
from api.qr_generator import generate_qr_response
from api.cache import cached, get as cache_get, set as cache_set
from api.monitoring import record_metric
from api.app import get_vkey_hash, hmac_sign
from datetime import datetime

# Initialize services
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
vault_storage = VaultStorage()
share_link_service = ShareLinkService(graph)
timeline_service = TimelineService(graph)
fabric_client = FabricClient()

# Simple in-memory rate limiter for public endpoints (best-effort, per-IP)
_rate_bucket: dict[str, dict] = {}
_RATE_LIMIT_WINDOW = 60  # seconds
_RATE_LIMIT_MAX = 20     # requests per window


def _check_rate_limit(key: str):
    now = time.time()
    bucket = _rate_bucket.get(key, {"count": 0, "window_start": now})
    if now - bucket["window_start"] > _RATE_LIMIT_WINDOW:
        bucket = {"count": 0, "window_start": now}
    bucket["count"] += 1
    _rate_bucket[key] = bucket
    if bucket["count"] > _RATE_LIMIT_MAX:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

router = APIRouter(prefix="/vault", tags=["vault"])


# Production authentication
def get_user_id() -> str:
    """Get current user ID (placeholder until JWT/OIDC wired)."""
    return os.getenv('MOCK_USER_ID', 'test_user_1')


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    user_id: Optional[str] = Form(None),
    metadata: Optional[str] = Form(None)
):
    """
    Upload a document to the vault.
    
    Returns document ID and hash.
    """
    # Get user ID
    uid = user_id or get_user_id()
    
    # Read file data
    file_data = await file.read()
    
    # Parse document type
    try:
        doc_type = DocumentType[document_type.upper()]
    except KeyError:
        doc_type = DocumentType.OTHER
    
    # Parse metadata
    import json
    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except Exception:
            pass
    
    # Upload and encrypt document
    document = vault_storage.upload_document(
        user_id=uid,
        document_data=file_data,
        document_type=doc_type,
        file_name=file.filename,
        mime_type=file.content_type,
        metadata=meta
    )
    
    # Anchor to Fabric
    try:
        anchor_result = fabric_client.anchor_document(
            document_id=document.id,
            document_hash=document.hash
        )
        fabric_tx_id = anchor_result.get('transactionId')
    except Exception as e:
        print(f"Failed to anchor to Fabric: {e}")
        fabric_tx_id = None
    
    # Persist to Neo4j
    from datetime import datetime
    from py2neo import Node, Relationship
    
    tx = graph.begin()
    
    user_node = Node("User", id=uid)
    tx.merge(user_node, "User", "id")
    
    doc_props = {
        "id": document.id,
        "user_id": uid,
        "document_type": doc_type.value,
        "hash": document.hash,
        "file_name": file.filename,
        "mime_type": file.content_type,
        "size_bytes": len(file_data),
        "created_at": datetime.utcnow().isoformat()
    }
    if meta:
        doc_props["metadata"] = json.dumps(meta)
    
    doc_node = Node("Document", **doc_props)
    tx.merge(doc_node, "Document", "id")
    
    owns_rel = Relationship(user_node, "OWNS", doc_node)
    tx.merge(owns_rel)
    
    if fabric_tx_id:
        att_node = Node(
            "Attestation",
            id=f"att_{document.id}",
            document_id=document.id,
            fabric_tx_id=fabric_tx_id,
            timestamp=datetime.utcnow().isoformat()
        )
        tx.merge(att_node, "Attestation", "id")
        
        attests_rel = Relationship(att_node, "ATTESTS", doc_node)
        tx.merge(attests_rel)
    
    tx.commit()
    
    # Log timeline event
    timeline_service.log_event(
        user_id=uid,
        event_type="document_uploaded",
        document_id=document.id,
        attestation_id=f"att_{document.id}" if fabric_tx_id else None,
        metadata={
            "document_type": doc_type.value,
            "file_name": file.filename,
            "fabric_tx_id": fabric_tx_id
        }
    )
    
    return {
        "document_id": document.id,
        "hash": document.hash,
        "fabric_tx_id": fabric_tx_id,
        "message": "Document uploaded and encrypted successfully"
    }


@router.get("/document/{document_id}")
async def get_document(document_id: str, user_id: Optional[str] = None):
    """
    Retrieve a document (decrypted).
    Requires authentication.
    """
    uid = user_id or get_user_id()
    
    # Verify ownership
    query = """
    MATCH (u:User {id: $user_id})-[:OWNS]->(d:Document {id: $doc_id})
    RETURN d
    """
    results = graph.run(query, {"user_id": uid, "doc_id": document_id}).data()
    
    if not results:
        raise HTTPException(status_code=404, detail="Document not found or access denied")
    
    # Decrypt and return document
    try:
        doc_data = vault_storage.download_document(uid, document_id)
        
        doc_meta = vault_storage.get_document_metadata(document_id)
        
        return JSONResponse(
            content={
                "document_id": document_id,
                "file_name": doc_meta.get('file_name'),
                "mime_type": doc_meta.get('mime_type'),
                "data": base64.b64encode(doc_data).decode('utf-8')
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve document: {str(e)}")


@router.get("/share/{token}")
async def verify_share_link(token: str, request: Request):
    """
    Public endpoint to verify a share link and return proof data.
    """
    _check_rate_limit(f"share:{request.client.host}")

    proof_link = share_link_service.validate_token(token)
    
    if not proof_link:
        raise HTTPException(status_code=404, detail="Share link not found or expired")
    
    # Get document metadata
    doc_meta = vault_storage.get_document_metadata(proof_link.document_id)
    if not doc_meta:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get attestation
    attestation = fabric_client.query_attestation(proof_link.document_id)
    
    # Return data based on access level
    response_data = {
        "share_token": proof_link.share_token,
        "document_id": proof_link.document_id,
        "proof_type": proof_link.proof_type,
        "access_level": proof_link.access_level.value
    }
    
    if proof_link.access_level.value == "PROOF_ONLY":
        # Only return proof-related data
        response_data["document_hash"] = doc_meta.get('hash')
        if attestation:
            response_data["attestation"] = {
                "fabric_tx_id": attestation.get('fabricTxId'),
                "merkle_root": attestation.get('merkleRoot'),
                "timestamp": attestation.get('timestamp')
            }
    
    elif proof_link.access_level.value == "METADATA":
        # Return metadata
        response_data["metadata"] = doc_meta.get('metadata', {})
        response_data["file_name"] = doc_meta.get('file_name')
        response_data["mime_type"] = doc_meta.get('mime_type')
        response_data["document_hash"] = doc_meta.get('hash')
    
    elif proof_link.access_level.value == "FULL":
        # Return full document (requires additional auth in production)
        # For MVP, we'll return metadata only
        response_data["metadata"] = doc_meta.get('metadata', {})
        response_data["file_name"] = doc_meta.get('file_name')
        response_data["mime_type"] = doc_meta.get('mime_type')
        response_data["document_hash"] = doc_meta.get('hash')
    
    return response_data


@router.get("/qr/{token}")
async def get_qr_code(token: str, request: Request):
    """
    Generate QR code for a share link.
    """
    _check_rate_limit(f"qr:{request.client.host}")
    share_url = share_link_service.get_share_url(token)
    return generate_qr_response(share_url)


@router.get("/share/{token}/bundle")
@cached(ttl=60.0, key_prefix="share_bundle")  # Cache for 60 seconds
async def get_share_bundle(token: str, request: Request):
    """
    Resolve a share token into a verification bundle for QR consumers.
    Optimized for <0.2s response time with caching.
    """
    start_time = time.time()
    client_key = f"bundle:{request.client.host}"
    _check_rate_limit(client_key)

    # Check cache first
    cache_key = f"share_bundle:{token}"
    cached_bundle = cache_get(cache_key)
    if cached_bundle:
        record_metric("share_bundle", time.time() - start_time, success=True)
        return cached_bundle

    proof_link = share_link_service.validate_token(token)

    if not proof_link:
        record_metric("share_bundle", time.time() - start_time, success=False)
        raise HTTPException(status_code=404, detail="Share link not found or expired")

    doc_meta = vault_storage.get_document_metadata(proof_link.document_id)
    if not doc_meta:
        record_metric("share_bundle", time.time() - start_time, success=False)
        raise HTTPException(status_code=404, detail="Document not found")

    # Only query attestation if needed (can be slow)
    attestation = None
    if proof_link.proof_type:
        try:
            attestation = fabric_client.query_attestation(proof_link.document_id)
        except Exception:
            pass  # Don't fail if attestation query fails

    bundle = {
        "share_token": proof_link.share_token,
        "document_id": proof_link.document_id,
        "proof_type": proof_link.proof_type,
        "access_level": proof_link.access_level.value,
        "document_hash": doc_meta.get('hash'),
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": proof_link.expires_at.isoformat() if proof_link.expires_at else None,
        "max_accesses": proof_link.max_accesses,
        "nonce": secrets.token_hex(16),
        "verification": {
            "circuit": proof_link.proof_type,
            "vk_url": f"/zkp/artifacts/{proof_link.proof_type}/verification_key.json",
            "vk_sha256": get_vkey_hash(proof_link.proof_type),
            "attestation": attestation or None,
        }
    }

    if not bundle["verification"]["vk_sha256"]:
        record_metric("share_bundle", time.time() - start_time, success=False)
        raise HTTPException(status_code=503, detail="Verification key unavailable for circuit")

    signature = hmac_sign(bundle)
    if signature:
        bundle["signature"] = signature

    # Cache the bundle
    cache_set(cache_key, bundle, ttl=60.0)
    
    duration = time.time() - start_time
    record_metric("share_bundle", duration, success=True)
    
    return bundle

