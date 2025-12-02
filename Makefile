
.PHONY: up down api producer consumer
up:
    docker-compose up -d
down:
    docker-compose down -v
api:
    uvicorn api.app:app --reload
producer:
    python ingestion/kafka_producer.py
consumer:
    python ingestion/kafka_consumer.py
