"""
REST endpoints for vault operations (file uploads, share links, QR codes).
"""
import os
import base64
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from py2neo import Graph

from vault.storage import VaultStorage
from vault.models import DocumentType
from vault.share_links import ShareLinkService
from vault.timeline import TimelineService
from blockchain.sdk.fabric_client import FabricClient
from api.qr_generator import generate_qr_response, generate_qr_code

# Initialize services
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
vault_storage = VaultStorage()
share_link_service = ShareLinkService(graph)
timeline_service = TimelineService(graph)
fabric_client = FabricClient()

router = APIRouter(prefix="/vault", tags=["vault"])


# Mock authentication for MVP
def get_user_id() -> str:
    """Get current user ID (mock for MVP)."""
    # In production, extract from JWT token
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
        except:
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
async def verify_share_link(token: str):
    """
    Public endpoint to verify a share link and return proof data.
    """
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
async def get_qr_code(token: str):
    """
    Generate QR code for a share link.
    """
    share_url = share_link_service.get_share_url(token)
    return generate_qr_response(share_url)

