"""
Share link generation and validation service for proof sharing.
"""
import os
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from py2neo import Graph, Node

from vault.models import ProofLink, AccessLevel


class ShareLinkService:
    """Service for generating and managing shareable proof links."""
    
    def __init__(self, graph: Graph, base_url: Optional[str] = None):
        """
        Initialize share link service.
        
        Args:
            graph: Neo4j graph connection
            base_url: Base URL for share links (defaults to env var)
        """
        self.graph = graph
        self.base_url = base_url or os.getenv('SHARE_LINK_BASE_URL', 'http://localhost:8000/vault/share')
    
    def create_share_link(
        self,
        document_id: str,
        user_id: str,
        access_level: AccessLevel = AccessLevel.PROOF_ONLY,
        expires_at: Optional[datetime] = None,
        proof_type: Optional[str] = None,
        max_accesses: Optional[int] = None
    ) -> ProofLink:
        """
        Create a shareable proof link.
        
        Args:
            document_id: Document identifier
            user_id: User identifier (owner)
            access_level: Access level for the link
            expires_at: Optional expiration datetime
            proof_type: Optional proof type (e.g., "age_proof")
            max_accesses: Optional maximum number of accesses
            
        Returns:
            ProofLink instance
        """
        # Generate cryptographically secure token
        token = self._generate_token()
        
        # Set default expiration (30 days)
        if expires_at is None:
            expires_at = datetime.utcnow() + timedelta(days=30)
        
        # Create proof link
        proof_link = ProofLink(
            share_token=token,
            document_id=document_id,
            expires_at=expires_at,
            access_level=access_level,
            proof_type=proof_type,
            max_accesses=max_accesses
        )
        
        # Persist to Neo4j
        self._persist_link(proof_link, user_id)
        
        return proof_link
    
    def validate_token(self, token: str) -> Optional[ProofLink]:
        """
        Validate a share token and return proof link if valid.
        
        Args:
            token: Share token
            
        Returns:
            ProofLink if valid, None otherwise
        """
        query = """
        MATCH (p:ProofLink {share_token: $token})
        RETURN p
        LIMIT 1
        """
        
        results = self.graph.run(query, {"token": token}).data()
        if not results:
            return None
        
        link_node = results[0]['p']
        link_dict = dict(link_node)
        
        # Check expiration
        if link_dict.get('expires_at'):
            expires_at = datetime.fromisoformat(link_dict['expires_at'])
            if datetime.utcnow() > expires_at:
                return None
        
        # Check max accesses
        if link_dict.get('max_accesses'):
            access_count = link_dict.get('access_count', 0)
            if access_count >= link_dict['max_accesses']:
                return None
        
        # Increment access count
        self._increment_access_count(token)
        
        # Convert to ProofLink object
        proof_link = ProofLink(
            share_token=link_dict['share_token'],
            document_id=link_dict['document_id'],
            expires_at=datetime.fromisoformat(link_dict['expires_at']) if link_dict.get('expires_at') else None,
            access_level=AccessLevel(link_dict.get('access_level', 'PROOF_ONLY')),
            proof_type=link_dict.get('proof_type'),
            created_at=datetime.fromisoformat(link_dict.get('created_at', datetime.utcnow().isoformat())),
            access_count=link_dict.get('access_count', 0),
            max_accesses=link_dict.get('max_accesses')
        )
        
        return proof_link
    
    def get_share_url(self, token: str) -> str:
        """Get full share URL for a token."""
        return f"{self.base_url}/{token}"
    
    def revoke_link(self, token: str, user_id: str) -> bool:
        """
        Revoke a share link (only owner can revoke).
        
        Args:
            token: Share token
            user_id: User identifier (must be owner)
            
        Returns:
            True if revoked, False otherwise
        """
        query = """
        MATCH (u:User {id: $user_id})-[:OWNS]->(d:Document)<-[:FOR_DOCUMENT]-(p:ProofLink {share_token: $token})
        SET p.expires_at = $now
        RETURN p
        """
        
        now = datetime.utcnow().isoformat()
        results = self.graph.run(query, {"user_id": user_id, "token": token, "now": now}).data()
        
        return len(results) > 0
    
    def _generate_token(self) -> str:
        """Generate a cryptographically secure token."""
        # Generate 32 bytes of random data and encode as URL-safe base64
        token_bytes = secrets.token_bytes(32)
        token = secrets.token_urlsafe(32)
        return token
    
    def _persist_link(self, proof_link: ProofLink, user_id: str):
        """Persist proof link to Neo4j."""
        tx = self.graph.begin()
        
        link_props = {
            "share_token": proof_link.share_token,
            "document_id": proof_link.document_id,
            "expires_at": proof_link.expires_at.isoformat() if proof_link.expires_at else None,
            "access_level": proof_link.access_level.value,
            "proof_type": proof_link.proof_type,
            "created_at": proof_link.created_at.isoformat(),
            "access_count": proof_link.access_count,
            "max_accesses": proof_link.max_accesses
        }
        
        link_node = Node("ProofLink", **link_props)
        tx.merge(link_node, "ProofLink", "share_token")
        
        # Link to document
        doc_node = Node("Document", id=proof_link.document_id)
        tx.merge(doc_node, "Document", "id")
        
        from py2neo import Relationship
        link_doc_rel = Relationship(link_node, "FOR_DOCUMENT", doc_node)
        tx.merge(link_doc_rel)
        
        # Link to user (via document)
        user_node = Node("User", id=user_id)
        tx.merge(user_node, "User", "id")
        
        tx.commit()
    
    def _increment_access_count(self, token: str):
        """Increment access count for a link."""
        query = """
        MATCH (p:ProofLink {share_token: $token})
        SET p.access_count = coalesce(p.access_count, 0) + 1
        """
        self.graph.run(query, {"token": token})

