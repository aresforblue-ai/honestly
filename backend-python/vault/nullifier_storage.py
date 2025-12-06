"""
Nullifier storage for Level 3 security.
Prevents double-spending and proof replay attacks.
"""
import os
import hashlib
from typing import Optional, Set
from datetime import datetime
from py2neo import Graph, Node, Relationship

# Try Redis for distributed nullifier storage
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class NullifierStorage:
    """Storage for nullifiers to prevent double-spending."""
    
    def __init__(self, graph: Optional[Graph] = None, redis_client=None):
        """
        Initialize nullifier storage.
        
        Args:
            graph: Neo4j graph connection (for persistent storage)
            redis_client: Redis client (for fast lookups)
        """
        self.graph = graph
        self.redis_client = redis_client
        
        # In-memory fallback
        self._memory_store: Set[str] = set()
    
    def _get_redis_key(self, nullifier: str) -> str:
        """Generate Redis key for nullifier."""
        return f"nullifier:{nullifier}"
    
    def is_nullifier_used(self, nullifier: str) -> bool:
        """
        Check if a nullifier has been used.
        
        Args:
            nullifier: The nullifier to check (hex string)
            
        Returns:
            True if nullifier has been used, False otherwise
        """
        # Try Redis first
        if self.redis_client:
            try:
                key = self._get_redis_key(nullifier)
                exists = self.redis_client.exists(key)
                if exists:
                    return True
            except Exception:
                pass
        
        # Try Neo4j
        if self.graph:
            try:
                query = """
                MATCH (n:Nullifier {hash: $nullifier})
                RETURN n
                LIMIT 1
                """
                results = self.graph.run(query, {"nullifier": nullifier}).data()
                if results:
                    return True
            except Exception:
                pass
        
        # Check memory
        return nullifier in self._memory_store
    
    def mark_nullifier_used(
        self,
        nullifier: str,
        user_id: Optional[str] = None,
        proof_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Mark a nullifier as used.
        
        Args:
            nullifier: The nullifier to mark (hex string)
            user_id: Optional user ID
            proof_type: Optional proof type
            metadata: Optional metadata
            
        Returns:
            True if successfully marked, False if already used
        """
        # Check if already used
        if self.is_nullifier_used(nullifier):
            return False
        
        # Store in Redis
        if self.redis_client:
            try:
                key = self._get_redis_key(nullifier)
                # Store with expiration (optional, for cleanup)
                # Set expiration to 1 year (31536000 seconds)
                self.redis_client.setex(key, 31536000, "1")
            except Exception:
                pass
        
        # Store in Neo4j
        if self.graph:
            try:
                tx = self.graph.begin()
                
                nullifier_node = Node(
                    "Nullifier",
                    hash=nullifier,
                    user_id=user_id,
                    proof_type=proof_type,
                    created_at=datetime.utcnow().isoformat(),
                    metadata=str(metadata) if metadata else None
                )
                tx.merge(nullifier_node, "Nullifier", "hash")
                
                # Link to user if provided
                if user_id:
                    user_node = Node("User", id=user_id)
                    tx.merge(user_node, "User", "id")
                    rel = Relationship(user_node, "USED_NULLIFIER", nullifier_node)
                    tx.merge(rel)
                
                tx.commit()
            except Exception:
                pass
        
        # Store in memory
        self._memory_store.add(nullifier)
        
        return True
    
    def get_nullifier_count(self) -> int:
        """Get total number of used nullifiers."""
        count = 0
        
        # Count in Redis
        if self.redis_client:
            try:
                keys = self.redis_client.keys("nullifier:*")
                count += len(keys)
            except Exception:
                pass
        
        # Count in Neo4j
        if self.graph:
            try:
                query = "MATCH (n:Nullifier) RETURN count(n) as cnt"
                results = self.graph.run(query).data()
                if results:
                    count += results[0].get('cnt', 0)
            except Exception:
                pass
        
        # Add memory count (avoid double counting)
        # In production, use only one storage backend
        
        return count
    
    def purge_old_nullifiers(self, days: int = 365) -> int:
        """
        Purge nullifiers older than specified days.
        
        Args:
            days: Number of days to keep
            
        Returns:
            Number of nullifiers purged
        """
        purged = 0
        
        # Purge from Neo4j
        if self.graph:
            try:
                cutoff_date = datetime.utcnow().replace(
                    day=datetime.utcnow().day - days
                ).isoformat()
                
                query = """
                MATCH (n:Nullifier)
                WHERE n.created_at < $cutoff
                DELETE n
                RETURN count(n) as cnt
                """
                results = self.graph.run(query, {"cutoff": cutoff_date}).data()
                if results:
                    purged += results[0].get('cnt', 0)
            except Exception:
                pass
        
        return purged
