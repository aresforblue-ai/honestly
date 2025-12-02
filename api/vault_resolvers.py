"""
GraphQL resolvers for vault operations.
"""
import os
import base64
from typing import Optional, Dict, Any
from datetime import datetime
from ariadne import MutationType, QueryType
from py2neo import Graph

from vault.storage import VaultStorage
from vault.models import DocumentType, AccessLevel, EventType
from vault.zk_proofs import ZKProofService
from vault.share_links import ShareLinkService
from vault.timeline import TimelineService
from blockchain.sdk.fabric_client import FabricClient

# Initialize services
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
vault_storage = VaultStorage()
zk_service = ZKProofService()
share_link_service = ShareLinkService(graph)
timeline_service = TimelineService(graph)
fabric_client = FabricClient()

# Resolvers
query = QueryType()
mutation = MutationType()


@query.field("myDocuments")
def resolve_my_documents(_, info):
    """Get current user's documents."""
    # TODO: Get user_id from authentication context
    user_id = info.context.get('user_id', 'test_user_1')  # Mock for MVP
    
    query_cypher = """
    MATCH (u:User {id: $user_id})-[:OWNS]->(d:Document)
    RETURN d
    ORDER BY d.created_at DESC
    """
    
    results = graph.run(query_cypher, {"user_id": user_id}).data()
    
    documents = []
    for record in results:
        doc_node = record['d']
        doc_dict = dict(doc_node)
        documents.append({
            "id": doc_dict.get('id'),
            "userId": doc_dict.get('user_id'),
            "documentType": doc_dict.get('document_type'),
            "hash": doc_dict.get('hash'),
            "fileName": doc_dict.get('file_name'),
            "mimeType": doc_dict.get('mime_type'),
            "sizeBytes": doc_dict.get('size_bytes'),
            "metadata": doc_dict.get('metadata', '{}'),
            "createdAt": doc_dict.get('created_at'),
            "updatedAt": doc_dict.get('updated_at')
        })
    
    return documents


@query.field("document")
def resolve_document(_, info, id):
    """Get a specific document by ID."""
    query_cypher = """
    MATCH (d:Document {id: $id})
    RETURN d
    LIMIT 1
    """
    
    results = graph.run(query_cypher, {"id": id}).data()
    if not results:
        return None
    
    doc_node = results[0]['d']
    doc_dict = dict(doc_node)
    
    return {
        "id": doc_dict.get('id'),
        "userId": doc_dict.get('user_id'),
        "documentType": doc_dict.get('document_type'),
        "hash": doc_dict.get('hash'),
        "fileName": doc_dict.get('file_name'),
        "mimeType": doc_dict.get('mime_type'),
        "sizeBytes": doc_dict.get('size_bytes'),
        "metadata": doc_dict.get('metadata', '{}'),
        "createdAt": doc_dict.get('created_at'),
        "updatedAt": doc_dict.get('updated_at')
    }


@query.field("myTimeline")
def resolve_my_timeline(_, info, limit=50):
    """Get current user's timeline."""
    user_id = info.context.get('user_id', 'test_user_1')  # Mock for MVP
    
    events = timeline_service.get_timeline(user_id=user_id, limit=limit)
    
    timeline = []
    for event in events:
        timeline.append({
            "userId": event.get('user_id'),
            "eventType": event.get('event_type'),
            "documentId": event.get('document_id'),
            "timestamp": event.get('timestamp'),
            "metadata": str(event.get('metadata', {})),
            "attestationId": event.get('attestation_id'),
            "proofLinkId": event.get('proof_link_id')
        })
    
    return timeline


@query.field("verifyShareLink")
def resolve_verify_share_link(_, info, token):
    """Verify and get share link details."""
    proof_link = share_link_service.validate_token(token)
    
    if not proof_link:
        return None
    
    return {
        "shareToken": proof_link.share_token,
        "documentId": proof_link.document_id,
        "expiresAt": proof_link.expires_at.isoformat() if proof_link.expires_at else None,
        "accessLevel": proof_link.access_level.value,
        "proofType": proof_link.proof_type,
        "createdAt": proof_link.created_at.isoformat(),
        "accessCount": proof_link.access_count,
        "maxAccesses": proof_link.max_accesses
    }


@query.field("attestation")
def resolve_attestation(_, info, documentId):
    """Get attestation for a document."""
    attestation = fabric_client.query_attestation(documentId)
    
    if not attestation:
        return None
    
    return {
        "id": f"att_{documentId}",
        "documentId": documentId,
        "fabricTxId": attestation.get('fabricTxId'),
        "merkleRoot": attestation.get('merkleRoot'),
        "timestamp": attestation.get('timestamp'),
        "signature": attestation.get('signature'),
        "publicKey": attestation.get('publicKey'),
        "verified": True,
        "verifiedAt": attestation.get('timestamp')
    }


@mutation.field("uploadDocument")
def resolve_upload_document(
    _,
    info,
    documentType,
    fileName=None,
    mimeType=None,
    metadata=None
):
    """Upload a document (requires file upload via REST endpoint)."""
    # This mutation is a placeholder - actual file upload happens via REST
    # In a real implementation, file data would come from multipart form
    user_id = info.context.get('user_id', 'test_user_1')  # Mock for MVP
    
    # For MVP, return a placeholder
    # Real implementation would handle file upload here
    return {
        "id": f"doc_{user_id}_{int(datetime.utcnow().timestamp() * 1000)}",
        "userId": user_id,
        "documentType": documentType,
        "hash": "placeholder_hash",
        "fileName": fileName,
        "mimeType": mimeType,
        "sizeBytes": 0,
        "metadata": metadata or "{}",
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": None
    }


@mutation.field("generateProof")
def resolve_generate_proof(
    _,
    info,
    documentId,
    proofType,
    proofParams=None
):
    """Generate a zero-knowledge proof."""
    import json
    
    user_id = info.context.get('user_id', 'test_user_1')  # Mock for MVP
    
    # Get document metadata
    doc_meta = vault_storage.get_document_metadata(documentId)
    if not doc_meta:
        raise ValueError(f"Document {documentId} not found")
    
    # Parse proof parameters
    params = {}
    if proofParams:
        try:
            params = json.loads(proofParams)
        except:
            pass
    
    # Generate proof based on type
    if proofType == "age_proof":
        birth_date = params.get('birth_date')
        min_age = params.get('min_age', 18)
        
        if not birth_date:
            raise ValueError("birth_date required for age_proof")
        
        proof_result = zk_service.generate_age_proof(
            birth_date=birth_date,
            min_age=min_age,
            document_hash=doc_meta['hash']
        )
    
    elif proofType == "authenticity_proof":
        merkle_root = params.get('merkle_root', doc_meta['hash'])
        
        proof_result = zk_service.generate_authenticity_proof(
            document_hash=doc_meta['hash'],
            merkle_root=merkle_root
        )
    
    else:
        raise ValueError(f"Unknown proof type: {proofType}")
    
    # Log timeline event
    timeline_service.log_event(
        user_id=user_id,
        event_type="proof_generated",
        document_id=documentId,
        metadata={"proof_type": proofType}
    )
    
    return {
        "proofType": proof_result['proof_type'],
        "proofData": proof_result['proof_data'],
        "publicInputs": proof_result['public_inputs'],
        "verified": None
    }


@mutation.field("createShareLink")
def resolve_create_share_link(
    _,
    info,
    documentId,
    expiresAt=None,
    accessLevel="PROOF_ONLY",
    proofType=None,
    maxAccesses=None
):
    """Create a shareable proof link."""
    user_id = info.context.get('user_id', 'test_user_1')  # Mock for MVP
    
    # Parse expiration
    expires_dt = None
    if expiresAt:
        expires_dt = datetime.fromisoformat(expiresAt)
    
    # Parse access level
    access_level = AccessLevel[accessLevel]
    
    # Create share link
    proof_link = share_link_service.create_share_link(
        document_id=documentId,
        user_id=user_id,
        access_level=access_level,
        expires_at=expires_dt,
        proof_type=proofType,
        max_accesses=maxAccesses
    )
    
    # Log timeline event
    timeline_service.log_event(
        user_id=user_id,
        event_type="share_link_created",
        document_id=documentId,
        proof_link_id=proof_link.share_token,
        metadata={"access_level": access_level.value}
    )
    
    return {
        "shareToken": proof_link.share_token,
        "documentId": proof_link.document_id,
        "expiresAt": proof_link.expires_at.isoformat() if proof_link.expires_at else None,
        "accessLevel": proof_link.access_level.value,
        "proofType": proof_link.proof_type,
        "createdAt": proof_link.created_at.isoformat(),
        "accessCount": proof_link.access_count,
        "maxAccesses": proof_link.max_accesses
    }


@mutation.field("verifyProof")
def resolve_verify_proof(_, info, proofData, publicInputs, proofType):
    """Verify a zero-knowledge proof."""
    if proofType == "age_proof":
        verified = zk_service.verify_age_proof(proofData, publicInputs)
    elif proofType == "authenticity_proof":
        verified = zk_service.verify_authenticity_proof(proofData, publicInputs)
    else:
        raise ValueError(f"Unknown proof type: {proofType}")
    
    return verified

