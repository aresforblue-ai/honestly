"""
Decision tracking service for logging major decisions linked to documents.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from py2neo import Graph

from vault.timeline import TimelineService


class DecisionService:
    """Service for tracking and logging decisions."""

    def __init__(self, graph: Graph, timeline_service: TimelineService):
        """
        Initialize decision service.

        Args:
            graph: Neo4j graph connection
            timeline_service: Timeline service instance
        """
        self.graph = graph
        self.timeline = timeline_service

    def log_decision(
        self,
        user_id: str,
        decision_type: str,
        decision_data: Dict[str, Any],
        document_ids: Optional[List[str]] = None,
        attestation_ids: Optional[List[str]] = None,
    ) -> str:
        """
        Log a major decision.

        Args:
            user_id: User identifier
            decision_type: Type of decision (e.g., "financial_transaction", "identity_verification")
            decision_data: Decision details
            document_ids: Optional list of related document IDs
            attestation_ids: Optional list of related attestation IDs

        Returns:
            Decision event ID
        """
        metadata = {
            "decision_type": decision_type,
            "decision_data": decision_data,
            "related_documents": document_ids or [],
            "related_attestations": attestation_ids or [],
        }

        event_id = self.timeline.log_event(
            user_id=user_id, event_type="decision_logged", metadata=metadata
        )

        # Optionally create a Decision node in Neo4j
        tx = self.graph.begin()

        from py2neo import Node, Relationship

        decision_node = Node(
            "Decision",
            id=f"decision_{event_id}",
            user_id=user_id,
            decision_type=decision_type,
            timestamp=datetime.utcnow().isoformat(),
        )
        tx.merge(decision_node, "Decision", "id")

        # Link to user
        user_node = Node("User", id=user_id)
        tx.merge(user_node, "User", "id")
        user_decision_rel = Relationship(user_node, "MADE_DECISION", decision_node)
        tx.merge(user_decision_rel)

        # Link to documents
        if document_ids:
            for doc_id in document_ids:
                doc_node = Node("Document", id=doc_id)
                tx.merge(doc_node, "Document", "id")
                decision_doc_rel = Relationship(decision_node, "USES", doc_node)
                tx.merge(decision_doc_rel)

        tx.commit()

        return event_id

    def get_decision_summary(
        self, user_id: str, decision_type: Optional[str] = None, limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get decision summaries for a user.

        Args:
            user_id: User identifier
            decision_type: Optional filter by decision type
            limit: Maximum number of decisions to return

        Returns:
            List of decision summaries
        """
        query = """
        MATCH (u:User {id: $user_id})-[:MADE_DECISION]->(d:Decision)
        """

        if decision_type:
            query += " WHERE d.decision_type = $decision_type"

        query += """
        OPTIONAL MATCH (d)-[:USES]->(doc:Document)
        RETURN d, collect(doc) as documents
        ORDER BY d.timestamp DESC
        LIMIT $limit
        """

        params = {"user_id": user_id, "limit": limit}
        if decision_type:
            params["decision_type"] = decision_type

        results = self.graph.run(query, params).data()

        decisions = []
        for record in results:
            decision_node = record["d"]
            documents = record.get("documents", [])

            decision_dict = dict(decision_node)
            decision_dict["documents"] = [dict(doc) for doc in documents if doc]
            decisions.append(decision_dict)

        return decisions
