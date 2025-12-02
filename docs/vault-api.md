# Personal Proof Vault API Documentation

## Overview

The Personal Proof Vault API provides endpoints for uploading, encrypting, and managing identity documents with blockchain attestations and zero-knowledge proofs.

## Base URL

- Local: `http://localhost:8000`
- GraphQL: `http://localhost:8000/graphql`
- REST API: `http://localhost:8000/vault`

## Authentication

For MVP, authentication is simplified. In production, use JWT tokens:
- Header: `Authorization: Bearer <token>`
- User ID is extracted from token claims

## GraphQL API

### Queries

#### `myDocuments`

Get current user's documents.

```graphql
query {
  myDocuments {
    id
    userId
    documentType
    hash
    fileName
    mimeType
    sizeBytes
    createdAt
  }
}
```

#### `document(id: ID!)`

Get a specific document by ID.

```graphql
query {
  document(id: "doc_123") {
    id
    userId
    documentType
    hash
    fileName
    createdAt
  }
}
```

#### `myTimeline(limit: Int)`

Get user's verification timeline.

```graphql
query {
  myTimeline(limit: 50) {
    userId
    eventType
    documentId
    timestamp
    metadata
  }
}
```

#### `verifyShareLink(token: String!)`

Verify and get share link details.

```graphql
query {
  verifyShareLink(token: "abc123...") {
    shareToken
    documentId
    expiresAt
    accessLevel
    proofType
  }
}
```

#### `attestation(documentId: ID!)`

Get blockchain attestation for a document.

```graphql
query {
  attestation(documentId: "doc_123") {
    id
    fabricTxId
    merkleRoot
    timestamp
    verified
  }
}
```

### Mutations

#### `uploadDocument`

Upload a document (file upload via REST endpoint).

```graphql
mutation {
  uploadDocument(
    documentType: IDENTITY
    fileName: "passport.pdf"
    mimeType: "application/pdf"
  ) {
    id
    hash
    createdAt
  }
}
```

**Note:** Actual file upload must be done via REST endpoint `POST /vault/upload`.

#### `generateProof`

Generate a zero-knowledge proof.

```graphql
mutation {
  generateProof(
    documentId: "doc_123"
    proofType: "age_proof"
    proofParams: "{\"birth_date\": \"1990-01-01\", \"min_age\": 21}"
  ) {
    proofType
    proofData
    publicInputs
    verified
  }
}
```

**Proof Types:**
- `age_proof`: Prove age >= X without revealing birthdate
  - Parameters: `birth_date` (ISO format), `min_age` (integer)
- `authenticity_proof`: Prove document hash exists in Merkle tree
  - Parameters: `merkle_root` (optional, defaults to document hash)

#### `createShareLink`

Create a shareable proof link.

```graphql
mutation {
  createShareLink(
    documentId: "doc_123"
    accessLevel: PROOF_ONLY
    proofType: "age_proof"
    expiresAt: "2024-12-31T23:59:59Z"
    maxAccesses: 10
  ) {
    shareToken
    documentId
    expiresAt
    accessLevel
  }
}
```

**Access Levels:**
- `PROOF_ONLY`: Only proof data, no document content
- `METADATA`: Document metadata + proof
- `FULL`: Full document access (requires auth)

#### `verifyProof`

Verify a zero-knowledge proof.

```graphql
mutation {
  verifyProof(
    proofData: "{\"proof_type\": \"age_proof\", ...}"
    publicInputs: "{\"min_age\": 21, ...}"
    proofType: "age_proof"
  )
}
```

## REST API

### Upload Document

**POST** `/vault/upload`

Upload a document to the vault.

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `file` (required): File to upload
- `document_type` (required): `IDENTITY`, `LICENSE`, `FINANCIAL`, `CREDENTIAL`, or `OTHER`
- `user_id` (optional): User ID (defaults to authenticated user)
- `metadata` (optional): JSON string with additional metadata

**Response:**
```json
{
  "document_id": "doc_123",
  "hash": "abc123...",
  "fabric_tx_id": "tx_456",
  "message": "Document uploaded and encrypted successfully"
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/vault/upload \
  -F "file=@passport.pdf" \
  -F "document_type=IDENTITY" \
  -F "metadata={\"country\": \"US\"}"
```

### Get Document

**GET** `/vault/document/{document_id}`

Retrieve a decrypted document (requires authentication).

**Query Parameters:**
- `user_id` (optional): User ID for ownership verification

**Response:**
```json
{
  "document_id": "doc_123",
  "file_name": "passport.pdf",
  "mime_type": "application/pdf",
  "data": "base64_encoded_data"
}
```

### Verify Share Link

**GET** `/vault/share/{token}`

Public endpoint to verify a share link and return proof data.

**Response (PROOF_ONLY):**
```json
{
  "share_token": "abc123...",
  "document_id": "doc_123",
  "proof_type": "age_proof",
  "access_level": "PROOF_ONLY",
  "document_hash": "abc123...",
  "attestation": {
    "fabric_tx_id": "tx_456",
    "merkle_root": "def456...",
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

**Response (METADATA):**
```json
{
  "share_token": "abc123...",
  "document_id": "doc_123",
  "proof_type": "age_proof",
  "access_level": "METADATA",
  "metadata": {...},
  "file_name": "passport.pdf",
  "mime_type": "application/pdf",
  "document_hash": "abc123..."
}
```

### Get QR Code

**GET** `/vault/qr/{token}`

Generate QR code for a share link.

**Response:** PNG image

**Example:**
```bash
curl http://localhost:8000/vault/qr/abc123... -o qr_code.png
```

## Error Responses

All endpoints return standard HTTP status codes:

- `200 OK`: Success
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error response format:
```json
{
  "detail": "Error message"
}
```

## Examples

### Complete Workflow

1. **Upload Document:**
```bash
curl -X POST http://localhost:8000/vault/upload \
  -F "file=@id.pdf" \
  -F "document_type=IDENTITY"
```

2. **Generate Age Proof:**
```graphql
mutation {
  generateProof(
    documentId: "doc_123"
    proofType: "age_proof"
    proofParams: "{\"birth_date\": \"1990-01-01\", \"min_age\": 21}"
  ) {
    proofType
    proofData
    publicInputs
  }
}
```

3. **Create Share Link:**
```graphql
mutation {
  createShareLink(
    documentId: "doc_123"
    accessLevel: PROOF_ONLY
    proofType: "age_proof"
  ) {
    shareToken
  }
}
```

4. **Verify Share Link:**
```bash
curl http://localhost:8000/vault/share/abc123...
```

5. **Get QR Code:**
```bash
curl http://localhost:8000/vault/qr/abc123... -o qr.png
```

## Rate Limits

MVP has no rate limits. In production, implement:
- 100 requests/minute per user
- 10 uploads/minute per user
- 1000 share link verifications/minute

## Security Notes

- All documents are encrypted with AES-256-GCM
- Encryption keys are derived per-user using PBKDF2
- Blockchain attestations use cryptographic signatures
- Share links use cryptographically secure tokens
- Zero-knowledge proofs protect sensitive data

## Future Enhancements

- JWT authentication
- Rate limiting
- Webhook notifications
- Batch operations
- Advanced proof types
- Multi-chain support

