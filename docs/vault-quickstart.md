# Personal Proof Vault - Quick Start Guide

## Overview

This guide will walk you through setting up and using the Personal Proof Vault MVP to upload documents, generate zero-knowledge proofs, and create shareable attestations anchored on Hyperledger Fabric.

## Prerequisites

- Python 3.10+
- Docker and Docker Compose
- Neo4j (via Docker)
- Kafka (via Docker)
- Go 1.21+ (for Fabric chaincode, optional for MVP)

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=test
KAFKA_BOOTSTRAP=localhost:9092
KAFKA_TOPIC=raw_claims
KAFKA_VAULT_TOPIC=vault_documents

# Vault Configuration
VAULT_ENCRYPTION_KEY=  # Leave empty for auto-generation (not recommended for production)
SHARE_LINK_BASE_URL=http://localhost:8000/vault/share

# Fabric Configuration (optional for MVP)
FABRIC_CHANNEL_NAME=vaultchannel
FABRIC_CHAINCODE_NAME=vault_anchor
FABRIC_NETWORK_CONFIG=blockchain/network
```

### 3. Start Infrastructure Services

```bash
# Start Neo4j, Kafka, Zookeeper
docker-compose up -d

# Wait for services to be ready
sleep 10
```

### 4. Initialize Neo4j Schema

```bash
# Connect to Neo4j browser at http://localhost:7474
# Username: neo4j
# Password: test

# Run initialization scripts
cat neo4j/init.cypher | cypher-shell -u neo4j -p test -a bolt://localhost:7687
cat neo4j/vault_init.cypher | cypher-shell -u neo4j -p test -a bolt://localhost:7687
```

### 5. (Optional) Start Fabric Network

For full blockchain attestation support:

```bash
# Navigate to Fabric network directory
cd blockchain/network

# Generate crypto material (requires Fabric binaries)
# See blockchain/network/README.md for detailed instructions

# Start Fabric network
docker-compose -f docker-compose-fabric.yml up -d

# Deploy chaincode (requires Fabric CLI)
# See blockchain/chaincode/README.md for instructions
```

**Note:** For MVP testing, the Fabric client runs in simulation mode and stores attestations locally.

### 6. Start API Server

```bash
# From project root
uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- GraphQL Playground: http://localhost:8000/graphql
- REST API: http://localhost:8000/vault
- API Docs: http://localhost:8000/docs

### 7. (Optional) Start Vault Consumer

For processing documents via Kafka:

```bash
python ingestion/vault_consumer.py
```

## Usage Examples

### Example 1: Upload and Verify Identity Document

#### Step 1: Upload Document

```bash
curl -X POST http://localhost:8000/vault/upload \
  -F "file=@passport.pdf" \
  -F "document_type=IDENTITY" \
  -F "metadata={\"country\": \"US\", \"document_number\": \"123456\"}"
```

Response:
```json
{
  "document_id": "doc_test_user_1_1234567890",
  "hash": "abc123def456...",
  "fabric_tx_id": "tx_789...",
  "message": "Document uploaded and encrypted successfully"
}
```

#### Step 2: Query Document via GraphQL

```graphql
query {
  document(id: "doc_test_user_1_1234567890") {
    id
    documentType
    hash
    fileName
    createdAt
  }
}
```

#### Step 3: Generate Age Proof

```graphql
mutation {
  generateProof(
    documentId: "doc_test_user_1_1234567890"
    proofType: "age_proof"
    proofParams: "{\"birth_date\": \"1990-01-15\", \"min_age\": 21}"
  ) {
    proofType
    proofData
    publicInputs
    verified
  }
}
```

#### Step 4: Create Share Link

```graphql
mutation {
  createShareLink(
    documentId: "doc_test_user_1_1234567890"
    accessLevel: PROOF_ONLY
    proofType: "age_proof"
    expiresAt: "2024-12-31T23:59:59Z"
  ) {
    shareToken
    expiresAt
    accessLevel
  }
}
```

#### Step 5: Verify Share Link (Public)

```bash
curl http://localhost:8000/vault/share/{share_token}
```

#### Step 6: Get QR Code

```bash
curl http://localhost:8000/vault/qr/{share_token} -o qr_code.png
```

### Example 2: View Timeline

```graphql
query {
  myTimeline(limit: 20) {
    eventType
    documentId
    timestamp
    metadata
  }
}
```

### Example 3: Verify Attestation

```graphql
query {
  attestation(documentId: "doc_test_user_1_1234567890") {
    fabricTxId
    merkleRoot
    timestamp
    verified
  }
}
```

## Testing with Python

```python
import requests
import json

# Upload document
with open('test_document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/vault/upload',
        files={'file': f},
        data={
            'document_type': 'IDENTITY',
            'metadata': json.dumps({'test': True})
        }
    )
    doc_data = response.json()
    print(f"Document ID: {doc_data['document_id']}")

# Query via GraphQL
query = """
query {
  myDocuments {
    id
    documentType
    hash
    createdAt
  }
}
"""
response = requests.post(
    'http://localhost:8000/graphql',
    json={'query': query}
)
print(response.json())
```

## Architecture Overview

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  FastAPI    │────▶│   Neo4j      │     │   Kafka     │
│   (API)     │     │  (Graph DB)  │     │  (Events)   │
└──────┬──────┘     └──────────────┘     └─────────────┘
       │
       ▼
┌─────────────┐     ┌──────────────┐
│   Vault     │────▶│   Fabric     │
│  Storage    │     │ (Blockchain) │
│ (Encrypted) │     └──────────────┘
└─────────────┘
```

## Troubleshooting

### Neo4j Connection Issues

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Test connection
cypher-shell -u neo4j -p test -a bolt://localhost:7687
```

### Kafka Connection Issues

```bash
# Check Kafka is running
docker ps | grep kafka

# Test Kafka
kafka-console-producer --bootstrap-server localhost:9092 --topic vault_documents
```

### Storage Issues

```bash
# Check vault storage directory exists
ls -la vault_storage/

# Check permissions
chmod -R 755 vault_storage/
```

### Fabric Issues

For MVP, Fabric runs in simulation mode. Attestations are stored locally in `blockchain/storage/`.

To use real Fabric:
1. Install Fabric binaries
2. Generate crypto material
3. Start Fabric network
4. Deploy chaincode
5. Update `FABRIC_NETWORK_CONFIG` in `.env`

## Next Steps

1. **Production Hardening:**
   - Implement proper JWT authentication
   - Add rate limiting
   - Use production Fabric network
   - Implement proper key management

2. **Advanced Features:**
   - Biometric liveness detection
   - Multi-chain support
   - Webhook notifications
   - Batch operations

3. **Integration:**
   - Mobile SDK (Flutter)
   - No-code platforms (Salesforce, Shopify)
   - SIEM integrations

## Support

For issues or questions:
- Check API documentation: `docs/vault-api.md`
- Review code comments in source files
- Check logs: API logs in console, Neo4j logs in Docker

## Demo Script

Run the complete demo:

```bash
# 1. Start services
docker-compose up -d

# 2. Initialize Neo4j
cat neo4j/init.cypher | cypher-shell -u neo4j -p test
cat neo4j/vault_init.cypher | cypher-shell -u neo4j -p test

# 3. Start API
uvicorn api.app:app --reload &

# 4. Upload test document
curl -X POST http://localhost:8000/vault/upload \
  -F "file=@test.pdf" \
  -F "document_type=IDENTITY"

# 5. Query documents
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ myDocuments { id documentType hash } }"}'
```

## Security Notes

- **MVP Warning:** This is a development MVP. Do not use in production without:
  - Proper key management
  - Production-grade Fabric network
  - Real ZK-SNARK circuits (not simplified proofs)
  - Authentication and authorization
  - Rate limiting
  - Security auditing

- **Encryption Keys:** Store `VAULT_ENCRYPTION_KEY` securely. If lost, encrypted documents cannot be decrypted.

- **Share Links:** Share links are cryptographically secure but verify expiration and access limits.

