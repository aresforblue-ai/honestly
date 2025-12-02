# Truth Engine – Personal Proof Vault MVP

A blockchain-verified identity and credential verification system with zero-knowledge proofs and Hyperledger Fabric attestations.

This bundle contains drop-in replacements for a few files in the starter repository:
- `vector_index/faiss_index.py` – ID-stable FAISS wrapper using `IndexIDMap`
- `ingestion/kafka_consumer.py` – fixed init/loop, error handling, and safe upserts
- `api/schema.graphql` – adds optional `provenance` field
- `api/app.py` – robust schema path + provenance passthrough
- `docker-compose.yml` – exposes Kafka on host and container networks

## Quick start (local dev)
1. Ensure Python 3.10+ and Docker are installed.
2. Copy these files over your repo (or unzip `truth-engine-fixes.zip` at repo root).
3. Create `.env` from the example:
   ```
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASS=test
   KAFKA_BOOTSTRAP=localhost:9092
   KAFKA_TOPIC=raw_claims
   ```
4. Start services:
   ```bash
   docker-compose up -d
   ```
5. Initialize Neo4j constraints (browser http://localhost:7474) with your `neo4j/init.cypher`.
6. Start API and ingestion:
   ```bash
   python -m uvicorn api.app:app --reload
   python ingestion/kafka_producer.py
   python ingestion/kafka_consumer.py
   ```
7. Open GraphQL Playground: http://localhost:8000/graphql

## Notes
- FAISS now maintains stable numeric IDs across restarts and keeps metadata in sync.
- Kafka is reachable at `localhost:9092` from your host **and** `kafka:9092` from containers.
- Neo4j relationship and node upserts are idempotent via `merge()`.

---

## Full End-to-End (fresh clone)
1. Create and activate a virtualenv (optional but recommended).
2. Install deps:
   ```bash
   pip install -r requirements.txt
   ```
3. Start infra:
   ```bash
   docker-compose up -d
   ```
4. (Optional) Load Neo4j constraints:
   - Open http://localhost:7474 → run `neo4j/init.cypher`
5. Run API locally:
   ```bash
   uvicorn api.app:app --reload
   ```
6. Produce a few demo messages:
   ```bash
   python ingestion/kafka_producer.py
   ```
7. Start consumer (ingests -> Neo4j + FAISS):
   ```bash
   python ingestion/kafka_consumer.py
   ```
8. Try a GraphQL query at http://localhost:8000/graphql:
   ```graphql
   query {
     search(query: "Eiffel Tower", topK: 3) {
       id
       text
       source
       veracity
       state
     }
   }
   ```

### Notes
- FAISS index files (`faiss.index`, `faiss_meta.pkl`) are written to the project root.
- Kafka advertised listeners are set so host tools use `localhost:9092` while containers use `kafka:9092`.
- If `faiss-cpu` install fails on Apple Silicon or Windows, install via `conda` or use WSL for simplicity.

---

## Personal Proof Vault MVP

The Personal Proof Vault MVP enables users to:
- **Upload and encrypt** sensitive documents (ID, licenses, financial records)
- **Generate zero-knowledge proofs** for selective disclosure (age, authenticity)
- **Anchor attestations** on Hyperledger Fabric blockchain
- **Create shareable proof links** with QR codes
- **Track verification timeline** of all operations

### Quick Start (Vault)

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Initialize Neo4j vault schema:**
   ```bash
   cat neo4j/vault_init.cypher | cypher-shell -u neo4j -p test
   ```

3. **Start API:**
   ```bash
   uvicorn api.app:app --reload
   ```

4. **Upload a document:**
   ```bash
   curl -X POST http://localhost:8000/vault/upload \
     -F "file=@document.pdf" \
     -F "document_type=IDENTITY"
   ```

5. **Query via GraphQL:**
   ```graphql
   query {
     myDocuments {
       id
       documentType
       hash
       createdAt
     }
   }
   ```

### Documentation

- **API Documentation:** See `docs/vault-api.md`
- **Quick Start Guide:** See `docs/vault-quickstart.md`
- **GraphQL Playground:** http://localhost:8000/graphql
- **REST API Docs:** http://localhost:8000/docs

### Features

- **Encrypted Storage:** AES-256-GCM encryption with user-specific keys
- **Zero-Knowledge Proofs:** Age and document authenticity proofs
- **Blockchain Attestations:** Hyperledger Fabric integration for tamper-proof records
- **Share Links:** Cryptographically secure, expirable proof sharing
- **Timeline Tracking:** Complete audit trail of all operations
- **QR Codes:** Easy sharing via QR code generation

### Architecture

```
Client → FastAPI → Vault Storage (Encrypted)
                ↓
            Neo4j (Graph DB)
                ↓
            Kafka (Events)
                ↓
        Hyperledger Fabric (Blockchain)
```

### Security Notes

**MVP Warning:** This is a development MVP. For production use:
- Implement proper JWT authentication
- Use production Fabric network
- Integrate real ZK-SNARK circuits (not simplified proofs)
- Add rate limiting and security auditing
- Implement proper key management
