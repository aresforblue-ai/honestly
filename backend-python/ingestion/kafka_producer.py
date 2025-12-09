import os
import json
import time
import uuid
from kafka import KafkaProducer
from dotenv import load_dotenv

load_dotenv()
BOOT = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "raw_claims")

if __name__ == "__main__":
    prod = KafkaProducer(
        bootstrap_servers=BOOT, value_serializer=lambda d: json.dumps(d).encode("utf-8")
    )
    # Send a handful of example claims
    for i in range(3):
        cid = str(uuid.uuid4())
        msg = {
            "id": cid,
            "text": f"Example claim #{i+1}: The Eiffel Tower is in Paris.",
            "source": "demo-producer",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        prod.send(TOPIC, msg)
        print("sent:", msg)
        time.sleep(0.2)
    prod.flush()
    print("Done. Use the consumer to ingest these into Neo4j + FAISS.")
