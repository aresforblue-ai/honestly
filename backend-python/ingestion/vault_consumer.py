"""
Kafka consumer for vault documents that encrypts, stores, and anchors to Fabric.
"""

import os
import json
import logging
from typing import Optional
from datetime import datetime
from kafka import KafkaConsumer
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship

from vault.storage import VaultStorage
from vault.models import DocumentType
from blockchain.sdk.fabric_client import FabricClient
from vault.timeline import TimelineService

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
VAULT_TOPIC = os.getenv("KAFKA_VAULT_TOPIC", "vault_documents")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "test")


def connect_consumer() -> KafkaConsumer:
    """Create Kafka consumer for vault documents."""
    return KafkaConsumer(
        VAULT_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="vault-consumer",
    )


def persist_to_neo4j(
    graph: Graph,
    document_id: str,
    user_id: str,
    document_type: str,
    document_hash: str,
    fabric_tx_id: Optional[str] = None,
    metadata: Optional[dict] = None,
):
    """Persist document and attestation to Neo4j."""
    tx = graph.begin()

    # Create or get User node
    user_node = Node("User", id=user_id)
    tx.merge(user_node, "User", "id")

    # Create Document node
    doc_props = {
        "id": document_id,
        "user_id": user_id,
        "document_type": document_type,
        "hash": document_hash,
        "created_at": datetime.utcnow().isoformat(),
    }
    if metadata:
        doc_props["metadata"] = json.dumps(metadata)

    doc_node = Node("Document", **doc_props)
    tx.merge(doc_node, "Document", "id")

    # Create OWNS relationship
    owns_rel = Relationship(user_node, "OWNS", doc_node)
    tx.merge(owns_rel)

    # Create Attestation node if Fabric tx exists
    if fabric_tx_id:
        attestation_node = Node(
            "Attestation",
            id=f"att_{document_id}",
            document_id=document_id,
            fabric_tx_id=fabric_tx_id,
            timestamp=datetime.utcnow().isoformat(),
        )
        tx.merge(attestation_node, "Attestation", "id")

        # Create ATTESTS relationship
        attests_rel = Relationship(attestation_node, "ATTESTS", doc_node)
        tx.merge(attests_rel)

    tx.commit()


def main():
    """Main consumer loop."""
    # Initialize services
    graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    vault_storage = VaultStorage()
    fabric_client = FabricClient()
    timeline_service = TimelineService(graph)

    consumer = None
    try:
        consumer = connect_consumer()
        logging.info("Vault consumer connected to %s, topic=%s", KAFKA_BOOTSTRAP, VAULT_TOPIC)

        for msg in consumer:
            try:
                document_data = msg.value or {}
                user_id = document_data.get("user_id")
                document_type_str = document_data.get("document_type", "OTHER")
                file_data = document_data.get("file_data")  # Base64 encoded
                file_name = document_data.get("file_name")
                mime_type = document_data.get("mime_type")
                metadata = document_data.get("metadata", {})

                if not user_id:
                    logging.warning("Skipping message without user_id")
                    continue

                if not file_data:
                    logging.warning("Skipping message without file_data")
                    continue

                # Decode file data
                import base64

                file_bytes = base64.b64decode(file_data)

                # Convert document type string to enum
                try:
                    doc_type = DocumentType[document_type_str.upper()]
                except KeyError:
                    doc_type = DocumentType.OTHER

                # Upload and encrypt document
                document = vault_storage.upload_document(
                    user_id=user_id,
                    document_data=file_bytes,
                    document_type=doc_type,
                    file_name=file_name,
                    mime_type=mime_type,
                    metadata=metadata,
                )

                logging.info("Encrypted and stored document %s for user %s", document.id, user_id)

                # Anchor to Fabric blockchain
                try:
                    anchor_result = fabric_client.anchor_document(
                        document_id=document.id, document_hash=document.hash
                    )
                    fabric_tx_id = anchor_result.get("transactionId")
                    logging.info("Anchored document %s to Fabric: %s", document.id, fabric_tx_id)
                except Exception as e:
                    logging.error("Failed to anchor document %s to Fabric: %s", document.id, e)
                    fabric_tx_id = None

                # Persist to Neo4j
                persist_to_neo4j(
                    graph=graph,
                    document_id=document.id,
                    user_id=user_id,
                    document_type=doc_type.value,
                    document_hash=document.hash,
                    fabric_tx_id=fabric_tx_id,
                    metadata=metadata,
                )

                # Log timeline event
                timeline_service.log_event(
                    user_id=user_id,
                    event_type="document_uploaded",
                    document_id=document.id,
                    metadata={
                        "document_type": doc_type.value,
                        "file_name": file_name,
                        "fabric_tx_id": fabric_tx_id,
                    },
                )

                if fabric_tx_id:
                    timeline_service.log_event(
                        user_id=user_id,
                        event_type="attestation_created",
                        document_id=document.id,
                        attestation_id=f"att_{document.id}",
                        metadata={"fabric_tx_id": fabric_tx_id},
                    )

                logging.info("Processed document %s", document.id)

            except Exception as e:
                logging.exception("Error processing message: %s", e)

    except KeyboardInterrupt:
        logging.info("Shutting down vault consumer...")
    finally:
        if consumer is not None:
            consumer.close()
            logging.info("Vault consumer closed.")


if __name__ == "__main__":
    main()
