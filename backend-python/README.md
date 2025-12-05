# Honestly - Python Backend

This is the Python-based backend for the Honestly Truth Engine, providing:

- **FastAPI REST API** for vault operations
- **GraphQL API** via Strawberry
- **Neo4j Graph Database** integration for claims and provenance
- **Kafka** event streaming for data ingestion
- **FAISS** vector search for semantic similarity
- **Hyperledger Fabric** blockchain integration for attestations
- **Zero-Knowledge Proofs** for privacy-preserving verification

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start infrastructure:**
   ```bash
   docker-compose up -d
   ```

3. **Run the API:**
   ```bash
   uvicorn api.app:app --reload
   ```

4. **Access endpoints:**
   - REST API: http://localhost:8000/docs
   - GraphQL: http://localhost:8000/graphql

## Project Structure

```
backend-python/
├── api/              # FastAPI application and routes
├── vault/            # Personal proof vault implementation
├── ingestion/        # Kafka consumers and producers
├── blockchain/       # Hyperledger Fabric integration
└── vector_index/     # FAISS vector search
```

## See Also

- Main documentation: `../docs/`
- Frontend application: `../frontend-app/`
- GraphQL backend: `../backend-graphql/`
