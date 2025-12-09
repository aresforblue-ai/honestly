import os
import json
import time
import logging

from kafka import KafkaConsumer
from dotenv import load_dotenv
from py2neo import Graph, Node, Relationship
from sentence_transformers import SentenceTransformer
from vector_index.faiss_index import FaissIndex

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

load_dotenv()

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "raw_claims")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "test")


def connect_consumer() -> KafkaConsumer:
    return KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="truth-engine-consumer",
    )


def main():
    # External deps
    graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    faiss = FaissIndex(index_path="faiss.index")

    consumer = None
    try:
        consumer = connect_consumer()
        logging.info("Kafka consumer connected to %s, topic=%s", KAFKA_BOOTSTRAP, TOPIC)
        for msg in consumer:
            try:
                claim = msg.value or {}
                claim_id = claim.get("id") or f"msg-{int(time.time()*1000)}"
                text = (claim.get("text") or "").strip()
                source = claim.get("source") or "unknown"
                timestamp = claim.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%SZ")

                if not text:
                    logging.warning("Skipping empty text for id=%s", claim_id)
                    continue

                # Persist to Neo4j
                tx = graph.begin()
                cnode = Node(
                    "Claim",
                    id=claim_id,
                    text=text,
                    veracity=0.5,
                    state="plausible",
                    timestamp=timestamp,
                )
                tx.merge(cnode, "Claim", "id")
                snode = Node("Source", name=source)
                tx.merge(snode, "Source", "name")
                rel = Relationship(snode, "REPORTS", cnode, confidence=0.5)
                tx.merge(rel)
                tx.commit()

                # Embed and add to FAISS
                vec = embed_model.encode(text)
                faiss.add(
                    id=claim_id,
                    vector=vec,
                    metadata={"text": text[:256], "source": source, "timestamp": timestamp},
                )
                logging.info("Persisted & indexed claim %s", claim_id)
            except Exception as e:
                logging.exception("Error handling message: %s", e)
    except KeyboardInterrupt:
        logging.info("Shutting down consumer...")
    finally:
        if consumer is not None:
            consumer.close()
            logging.info("Kafka consumer closed.")


if __name__ == "__main__":
    main()
