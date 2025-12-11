# Honestly API Reference

**Complete API documentation for the Honestly Truth Engine**

Version: 1.0.0 | Last Updated: December 11, 2024

---

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [REST API](#rest-api)
  - [Vault Endpoints](#vault-endpoints)
  - [AI Endpoints](#ai-endpoints)
  - [ZKP Endpoints](#zkp-endpoints)
- [GraphQL API](#graphql-api)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## Overview

The Honestly API provides three main interfaces:

1. **REST API** (`/vault/*`, `/ai/*`) — Document management and AI integration
2. **GraphQL API** (`/graphql`) — Advanced queries and mutations
3. **WebSocket API** (coming soon) — Real-time updates

**Base URL**: `http://localhost:8000` (development) | `https://api.honestly.dev` (production)

**API Versions**: Currently v1 (default)

---

## Authentication

### JWT Authentication

Most endpoints require JWT authentication via the `Authorization` header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/vault/document/doc_123
```

### API Key Authentication (AI Endpoints)

AI endpoints use API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: YOUR_API_KEY" \
  http://localhost:8000/ai/verify-proof
```

### HMAC Signature (Optional)

For enhanced security, AI endpoints support HMAC signatures:

```bash
# Request body
BODY='{"circuit":"age","proof":{...}}'

# Generate signature
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$API_SECRET" | cut -d' ' -f2)

# Make request
curl -X POST http://localhost:8000/ai/verify-proof \
  -H "X-API-Key: $API_KEY" \
  -H "X-Signature: $SIGNATURE" \
  -H "Content-Type: application/json" \
  -d "$BODY"
```

---

## REST API

### Vault Endpoints

#### Upload Document

```http
POST /vault/upload
Content-Type: application/json
Authorization: Bearer {token}

{
  "type": "passport",
  "data": "base64_encrypted_data",
  "metadata": {
    "country": "US",
    "issue_date": "2024-01-01"
  }
}
```

**Response:**
```json
{
  "id": "doc_abc123xyz",
  "type": "passport",
  "uploaded_at": "2024-12-11T12:00:00Z",
  "status": "uploaded"
}
```

**Status Codes:**
- `200` — Success
- `400` — Invalid request
- `401` — Unauthorized
- `413` — Document too large
- `429` — Rate limit exceeded

---

#### Retrieve Document

```http
GET /vault/document/{document_id}
Authorization: Bearer {token}
```

**Response:**
```json
{
  "id": "doc_abc123xyz",
  "type": "passport",
  "data": "base64_encrypted_data",
  "metadata": {
    "country": "US",
    "issue_date": "2024-01-01"
  },
  "created_at": "2024-12-11T12:00:00Z"
}
```

---

#### Create Share Link

```http
POST /vault/share
Content-Type: application/json
Authorization: Bearer {token}

{
  "document_id": "doc_abc123xyz",
  "proof_type": "age",
  "access_level": "PROOF_ONLY",
  "expires_in": 3600
}
```

**Response:**
```json
{
  "token": "hns_share_token_123",
  "url": "https://honestly.dev/vault/share/hns_share_token_123",
  "qr_code_url": "https://honestly.dev/vault/qr/hns_share_token_123",
  "expires_at": "2024-12-11T13:00:00Z"
}
```

**Access Levels:**
- `PROOF_ONLY` — Only the ZK proof is revealed
- `PROOF_AND_METADATA` — Proof + limited metadata
- `FULL_DOCUMENT` — Complete document (requires extra auth)

---

#### Verify Share Link

```http
GET /vault/share/{token}
```

**Response:**
```json
{
  "valid": true,
  "proof_type": "age",
  "claim": "Age >= 18",
  "verified_at": "2024-12-11T12:00:00Z",
  "expires_at": "2024-12-11T13:00:00Z"
}
```

---

#### Get Verification Bundle

```http
GET /vault/share/{token}/bundle
```

**Response:**
```json
{
  "proof": {
    "pi_a": ["...", "...", "1"],
    "pi_b": [["...", "..."], ["...", "..."], ["1", "0"]],
    "pi_c": ["...", "...", "1"],
    "protocol": "groth16",
    "curve": "bn128"
  },
  "public_signals": [
    "18",
    "1733443200",
    "..."
  ],
  "metadata": {
    "circuit": "age",
    "claim": "Age >= 18",
    "verified": true
  },
  "verification_key_hash": "sha256:abc123...",
  "cached": true,
  "response_time_ms": 145
}
```

---

#### Generate QR Code

```http
GET /vault/qr/{token}
```

**Response:**
- `Content-Type: image/png`
- Returns PNG image of QR code containing share URL

**Query Parameters:**
- `size` — QR code size in pixels (default: 300, max: 1000)
- `format` — `png` or `svg` (default: png)

---

### AI Endpoints

#### Verify Single Proof

```http
POST /ai/verify-proof
Content-Type: application/json
X-API-Key: {api_key}

{
  "circuit": "age",
  "proof": {
    "pi_a": ["...", "...", "1"],
    "pi_b": [["...", "..."], ["...", "..."], ["1", "0"]],
    "pi_c": ["...", "...", "1"]
  },
  "public_signals": ["18", "1733443200", "..."]
}
```

**Response:**
```json
{
  "valid": true,
  "circuit": "age",
  "verification_time_ms": 178,
  "public_signals_parsed": {
    "min_age": 18,
    "reference_timestamp": 1733443200,
    "document_hash": "0xabc123..."
  }
}
```

---

#### Batch Verify Proofs

```http
POST /ai/verify-proofs-batch
Content-Type: application/json
X-API-Key: {api_key}

{
  "proofs": [
    {
      "circuit": "age",
      "proof": {...},
      "public_signals": [...]
    },
    {
      "circuit": "authenticity",
      "proof": {...},
      "public_signals": [...]
    }
  ]
}
```

**Response:**
```json
{
  "results": [
    {"valid": true, "circuit": "age", "index": 0},
    {"valid": true, "circuit": "authenticity", "index": 1}
  ],
  "total": 2,
  "valid": 2,
  "invalid": 0,
  "verification_time_ms": 345
}
```

**Limits:**
- Max 100 proofs per batch
- Timeout: 30 seconds

---

#### Create Share Link (AI)

```http
POST /ai/share-link
Content-Type: application/json
Authorization: Bearer {token}
X-API-Key: {api_key}

{
  "document_id": "doc_abc123xyz",
  "proof_type": "age",
  "access_level": "PROOF_ONLY"
}
```

**Response:**
```json
{
  "share_token": "hns_share_token_123",
  "url": "https://honestly.dev/vault/share/hns_share_token_123",
  "expires_in": 3600
}
```

---

#### Get Share Link Info

```http
GET /ai/share/{token}/info
X-API-Key: {api_key}
```

**Response:**
```json
{
  "valid": true,
  "proof_type": "age",
  "access_level": "PROOF_ONLY",
  "created_at": "2024-12-11T12:00:00Z",
  "expires_at": "2024-12-11T13:00:00Z",
  "uses_remaining": 5
}
```

---

#### API Status

```http
GET /ai/status
X-API-Key: {api_key}
```

**Response:**
```json
{
  "status": "operational",
  "version": "1.0.0",
  "capabilities": {
    "circuits": ["age", "authenticity", "age_level3", "level3_inequality"],
    "max_batch_size": 100,
    "supported_curves": ["bn128"],
    "rate_limits": {
      "verify_proof": "100/minute",
      "batch_verify": "20/minute"
    }
  },
  "uptime_seconds": 86400
}
```

---

### ZKP Endpoints

#### Get Verification Key

```http
GET /zkp/artifacts/{circuit}/verification_key.json
```

**Response:**
```json
{
  "protocol": "groth16",
  "curve": "bn128",
  "nPublic": 4,
  "vk_alpha_1": [...],
  "vk_beta_2": [...],
  "vk_gamma_2": [...],
  "vk_delta_2": [...],
  "vk_alphabeta_12": [...],
  "IC": [...]
}
```

**Headers:**
- `ETag` — SHA-256 hash of verification key
- `Cache-Control` — `public, max-age=31536000, immutable`

---

#### Get Verification Key Hash

```http
GET /zkp/vkey-hash/{circuit}
```

**Response:**
```json
{
  "circuit": "age",
  "sha256": "abc123def456...",
  "algorithm": "sha256"
}
```

---

#### List Available Circuits

```http
GET /capabilities
```

**Response:**
```json
{
  "circuits": [
    {
      "name": "age",
      "description": "Age verification (>= min_age)",
      "public_inputs": ["minAge", "referenceTs", "documentHash", "commitment"],
      "constraints": 1234,
      "proving_time_avg_ms": 450,
      "verification_time_avg_ms": 150
    },
    {
      "name": "authenticity",
      "description": "Document authenticity via Merkle proof",
      "public_inputs": ["root", "leaf"],
      "constraints": 2345,
      "proving_time_avg_ms": 520,
      "verification_time_avg_ms": 160
    }
  ]
}
```

---

## GraphQL API

### Endpoint

```
POST /graphql
Content-Type: application/json
Authorization: Bearer {token}
```

### Schema

```graphql
type Query {
  # Document queries
  document(id: ID!): Document
  documents(filter: DocumentFilter): [Document!]!
  
  # Proof queries
  proof(id: ID!): Proof
  proofs(documentId: ID!): [Proof!]!
  
  # Claim queries
  claim(id: ID!): Claim
  claims(filter: ClaimFilter): [Claim!]!
  
  # Agent queries (AAIP)
  agent(agentId: ID!): Agent
  agents(filter: AgentFilter): [Agent!]!
  agentReputation(agentId: ID!, threshold: Int!): ReputationProof
}

type Mutation {
  # Document mutations
  uploadDocument(input: DocumentInput!): Document!
  deleteDocument(id: ID!): Boolean!
  
  # Proof mutations
  generateProof(input: ProofInput!): Proof!
  verifyProof(input: VerifyProofInput!): VerificationResult!
  
  # Share mutations
  createShareLink(input: ShareLinkInput!): ShareLink!
  revokeShareLink(token: String!): Boolean!
  
  # Agent mutations (AAIP)
  registerAgent(input: AgentInput!): Agent!
  updateAgentReputation(agentId: ID!, score: Int!): Agent!
}

type Document {
  id: ID!
  type: String!
  createdAt: DateTime!
  metadata: JSON
}

type Proof {
  id: ID!
  circuit: String!
  proof: JSON!
  publicSignals: [String!]!
  verified: Boolean!
  createdAt: DateTime!
}

type ShareLink {
  token: String!
  url: String!
  qrCodeUrl: String!
  expiresAt: DateTime!
}
```

### Example Queries

#### Get Document

```graphql
query GetDocument {
  document(id: "doc_abc123xyz") {
    id
    type
    createdAt
    metadata
  }
}
```

#### Generate Proof

```graphql
mutation GenerateAgeProof {
  generateProof(input: {
    documentId: "doc_abc123xyz"
    circuit: "age"
    parameters: {
      minAge: 18
      referenceTs: 1733443200
    }
  }) {
    id
    circuit
    proof
    publicSignals
    verified
  }
}
```

#### Verify Proof

```graphql
mutation VerifyProof {
  verifyProof(input: {
    circuit: "age"
    proof: {
      pi_a: ["...", "...", "1"]
      pi_b: [[...], [...], [...]]
      pi_c: ["...", "...", "1"]
    }
    publicSignals: ["18", "1733443200", "..."]
  }) {
    valid
    circuit
    verificationTimeMs
  }
}
```

---

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "error": {
    "code": "INVALID_PROOF",
    "message": "Proof verification failed",
    "details": {
      "circuit": "age",
      "reason": "Public signals mismatch"
    },
    "correlation_id": "req_abc123xyz",
    "timestamp": "2024-12-11T12:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request |
| `UNAUTHORIZED` | 401 | Missing or invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INVALID_PROOF` | 400 | Proof verification failed |
| `CIRCUIT_NOT_FOUND` | 404 | Unknown circuit |
| `VKEY_MISSING` | 503 | Verification key unavailable |
| `INTERNAL_ERROR` | 500 | Internal server error |

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1733443260
```

### Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/vault/upload` | 10 | 1 minute |
| `/vault/share` | 20 | 1 minute |
| `/vault/share/*/bundle` | 100 | 1 minute |
| `/ai/verify-proof` | 100 | 1 minute |
| `/ai/verify-proofs-batch` | 20 | 1 minute |
| `/graphql` | 60 | 1 minute |

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "retry_after": 45
  }
}
```

---

## Examples

### Complete Age Verification Flow

```bash
#!/bin/bash

# 1. Upload document
UPLOAD_RESPONSE=$(curl -X POST http://localhost:8000/vault/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "passport",
    "data": "base64_encrypted_data",
    "metadata": {"country": "US"}
  }')

DOC_ID=$(echo $UPLOAD_RESPONSE | jq -r '.id')

# 2. Create share link with age proof
SHARE_RESPONSE=$(curl -X POST http://localhost:8000/vault/share \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"document_id\": \"$DOC_ID\",
    \"proof_type\": \"age\",
    \"access_level\": \"PROOF_ONLY\"
  }")

SHARE_TOKEN=$(echo $SHARE_RESPONSE | jq -r '.token')

# 3. Verify the share link
curl http://localhost:8000/vault/share/$SHARE_TOKEN

# 4. Get verification bundle
curl http://localhost:8000/vault/share/$SHARE_TOKEN/bundle
```

### Batch Proof Verification

```python
import requests

API_URL = "http://localhost:8000"
API_KEY = "your_api_key"

# Prepare batch of proofs
proofs = [
    {
        "circuit": "age",
        "proof": {...},  # Groth16 proof
        "public_signals": ["18", "1733443200", "..."]
    },
    {
        "circuit": "authenticity",
        "proof": {...},
        "public_signals": ["root_hash", "leaf_hash"]
    }
]

# Batch verify
response = requests.post(
    f"{API_URL}/ai/verify-proofs-batch",
    headers={"X-API-Key": API_KEY},
    json={"proofs": proofs}
)

result = response.json()
print(f"Verified {result['valid']}/{result['total']} proofs")
```

### GraphQL Query with Python

```python
import requests

API_URL = "http://localhost:8000/graphql"
JWT_TOKEN = "your_jwt_token"

query = """
  query GetDocuments {
    documents(filter: { type: "passport" }) {
      id
      type
      createdAt
      metadata
    }
  }
"""

response = requests.post(
    API_URL,
    headers={"Authorization": f"Bearer {JWT_TOKEN}"},
    json={"query": query}
)

data = response.json()
print(data["data"]["documents"])
```

---

## Additional Resources

- [API Quickstart Guide](vault-quickstart.md)
- [AI Endpoints Guide](ai-endpoints.md)
- [GraphQL Schema](../backend-python/api/graphql_schema.py)
- [OpenAPI/Swagger Docs](http://localhost:8000/docs)
- [Postman Collection](../examples/honestly-api.postman_collection.json) (coming soon)

---

<div align="center">

**Need Help?**

[GitHub Issues](https://github.com/veridicusio/honestly/issues) • [Documentation](../DOCUMENTATION_INDEX.md) • [Contributing](../CONTRIBUTING.md)

</div>
