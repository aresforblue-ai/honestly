"""
Timeline service for logging and retrieving user verification events.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from py2neo import Graph, Node

from vault.models import TimelineEvent, EventType


class TimelineService:
    """Service for managing user verification timeline."""
    
    def __init__(self, graph: Graph):
        """
        Initialize timeline service.
        
        Args:
            graph: Neo4j graph connection
        """
        self.graph = graph
    
    def log_event(
        self,
        user_id: str,
        event_type: str,
        document_id: Optional[str] = None,
        attestation_id: Optional[str] = None,
        proof_link_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an event to the timeline.
        
        Args:
            user_id: User identifier
            event_type: Type of event (from EventType enum)
            document_id: Optional document ID
            attestation_id: Optional attestation ID
            proof_link_id: Optional proof link ID
            metadata: Optional event metadata
            
        Returns:
            Event ID
        """
        import json
        
        event_id = f"event_{user_id}_{int(datetime.utcnow().timestamp() * 1000)}"
        timestamp = datetime.utcnow().isoformat()
        
        tx = self.graph.begin()
        
        # Create TimelineEvent node
        event_props = {
            "id": event_id,
            "user_id": user_id,
            "event_type": event_type,
            "timestamp": timestamp
        }
        
        if document_id:
            event_props["document_id"] = document_id
        if attestation_id:
            event_props["attestation_id"] = attestation_id
        if proof_link_id:
            event_props["proof_link_id"] = proof_link_id
        if metadata:
            event_props["metadata"] = json.dumps(metadata)
        
        event_node = Node("TimelineEvent", **event_props)
        tx.merge(event_node, "TimelineEvent", "id")
        
        # Link to User
        user_node = Node("User", id=user_id)
        tx.merge(user_node, "User", "id")
        
        from py2neo import Relationship
        user_event_rel = Relationship(user_node, "HAS_EVENT", event_node)
        tx.merge(user_event_rel)
        
        # Link to Document if provided
        if document_id:
            doc_node = Node("Document", id=document_id)
            tx.merge(doc_node, "Document", "id")
            doc_event_rel = Relationship(event_node, "REFERENCES", doc_node)
            tx.merge(doc_event_rel)
        
        # Link to Attestation if provided
        if attestation_id:
            att_node = Node("Attestation", id=attestation_id)
            tx.merge(att_node, "Attestation", "id")
            att_event_rel = Relationship(event_node, "REFERENCES", att_node)
            tx.merge(att_event_rel)
        
        tx.commit()
        
        return event_id
    
    def get_timeline(
        self,
        user_id: str,
        limit: int = 50,
        event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get user's timeline events.
        
        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            event_type: Optional filter by event type
            
        Returns:
            List of timeline events
        """
        import json
        
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_EVENT]->(e:TimelineEvent)
        """
        
        if event_type:
            query += " WHERE e.event_type = $event_type"
        
        query += """
        RETURN e
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        
        params = {"user_id": user_id, "limit": limit}
        if event_type:
            params["event_type"] = event_type
        
        results = self.graph.run(query, params).data()
        
        events = []
        for record in results:
            event_node = record['e']
            event_dict = dict(event_node)
            
            # Parse metadata JSON if present
            if 'metadata' in event_dict and event_dict['metadata']:
                try:
                    event_dict['metadata'] = json.loads(event_dict['metadata'])
                except:
                    pass
            
            events.append(event_dict)
        
        return events
    
    def get_timeline_with_relations(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get timeline events with related documents and attestations.
        
        Args:
            user_id: User identifier
            limit: Maximum number of events to return
            
        Returns:
            List of timeline events with relations
        """
        import json
        
        query = """
        MATCH (u:User {id: $user_id})-[:HAS_EVENT]->(e:TimelineEvent)
        OPTIONAL MATCH (e)-[:REFERENCES]->(d:Document)
        OPTIONAL MATCH (e)-[:REFERENCES]->(a:Attestation)
        RETURN e, d, a
        ORDER BY e.timestamp DESC
        LIMIT $limit
        """
        
        results = self.graph.run(query, {"user_id": user_id, "limit": limit}).data()
        
        events = []
        for record in results:
            event_node = record['e']
            doc_node = record.get('d')
            att_node = record.get('a')
            
            event_dict = dict(event_node)
            
            # Parse metadata JSON if present
            if 'metadata' in event_dict and event_dict['metadata']:
                try:
                    event_dict['metadata'] = json.loads(event_dict['metadata'])
                except:
                    pass
            
            # Add related document if present
            if doc_node:
                event_dict['document'] = dict(doc_node)
            
            # Add related attestation if present
            if att_node:
                event_dict['attestation'] = dict(att_node)
            
            events.append(event_dict)
        
        return events

