# Honestly - System Architecture
**Last Updated**: December 2024

This document describes the complete architecture of the Honestly Truth Engine platform, including the AI Agent Identity Protocol (AAIP).

## 🆕 What's New

- **AI Agent Identity Protocol (AAIP)** — Verifiable identities for AI agents
- **Real ZK Proofs** — Groth16 with nullifier tracking
- **Cross-Chain Identity** — Bridge identities across blockchains
- **Social Recovery** — Shamir's Secret Sharing for key recovery

## 🏛️ High-Level Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         USER LAYER                          │
│  ┌────────────────┐         ┌─────────────────────┐         │
│  │   Web Browser  │────────▶│  Mobile App (Future)│         │
│  └────────────────┘         └─────────────────────┘         │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      FRONTEND LAYER                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  React + Vite (frontend-app)                         │   │
│  │  - AppWhistler UI                                    │   │
│  │  - Trust Score Dashboard                             │   │
│  │  - Claims Verification Interface                     │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │  ConductMe Core (Next.js)                            │   │
│  │  - Trust Bridge (Semaphore identity + proofs)        │   │
│  │  - Workflow Builder (React Flow + Zustand)           │   │
│  │  - EIP-712 signing + wallet placeholder              │   │
│  │  - Local LLM proxy route                             │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTP/GraphQL/REST
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND LAYER                          │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │ GraphQL Backend     │      │  Python Backend         │   │
│  │ (Node.js/Apollo)    │◀────▶│  (FastAPI)              │   │
│  │                     │      │                         │   │
│  │ - App Verification  │      │ ┌────────────────────┐ │   │
│  │ - Scoring Engine    │      │ │ Security Middleware│ │   │
│  │ - Claims/Evidence   │      │ │ - Threat Detection │ │   │
│  │ - Provenance        │      │ │ - Rate Limiting     │ │   │
│  └─────────────────────┘      │ │ - IP Blocking       │ │   │
│                                │ │ - Security Headers  │ │   │
│                                │ │ - CORS + strict allowlist││   │
│                                │ └────────────────────┘ │   │
│                                │                         │   │
│                                │ - JWT/OIDC auth (JWKS; HS fallback) │
│                                │ - Vault key loader (KMS/env/file; fail-fast) │
│                                │ - Vault Management      │   │
│                                │ - ZK Proofs (Groth16: age, authenticity, level3 nullifier-binding) │
│                                │ - VKey caching (ETag/sha256 + integrity gate) │
│                                │ - AI Endpoints (/ai/*)  │   │
│                                │ - Monitoring (/monitoring/*)│
│                                │ - Kafka Integration      │  │
│                                │ - FAISS Search           │  │
│                                └────────────────────────┘   │
└────────────┬──────────────────────────┬────────────────────┘
             │                          │
             ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────────┐    │
│  │ PostgreSQL   │  │  Neo4j    │  │  Kafka           │    │
│  │              │  │  Graph DB │  │  Event Stream    │    │
│  └──────────────┘  └───────────┘  └──────────────────┘    │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐  │
│  │  Redis Cache     │  │  Monitoring & Metrics        │  │
│  │  (Optional)      │  │  - Health Checks             │  │
│  │  - VKeys (ETag/sha256) │  │  - Performance Metrics       │  │
│  │  - Share Bundles │  │  - Security Events           │  │
│  │  - Metadata      │  │  - System Resources          │  │
│  └──────────────────┘  └──────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   BLOCKCHAIN LAYER                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Base / Arbitrum L2                       │    │
│  │  - VaultAnchor.sol Smart Contract                  │    │
│  │  - Attestation Anchoring (~$0.001/anchor)          │    │
│  │  - Batched Merkle Root Publishing                  │    │
│  │  - Immutable Audit Trail                           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Component Interactions

### 1. ConductMe ↔ Python Backend

**Protocol**: HTTP/HTTPS with REST API
**Port**: 8000

```javascript
// Call Python FastAPI from ConductMe
const response = await fetch('http://localhost:8000/vault/documents');
```

**Key Operations**:
- Vault operations (upload, retrieve, share)
- ZK proof generation and verification
- AI agent identity protocol (AAIP)
- Share link management

### 2. Python Backend ↔ Data Stores

**Neo4j**: Claims, provenance, relationships
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "test")
)
```

**Kafka**: Event streaming
```python
from kafka import KafkaProducer

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092']
)
```

**FAISS**: Vector similarity search
```python
import faiss

index = faiss.IndexFlatL2(dimension)
```

## 📊 Data Flow Examples

### Example 1: ZK Proof Generation Flow

```
1. User uploads document via ConductMe
   ↓
2. ConductMe → Python Backend (POST /vault/upload)
   ↓
3. Python Backend: Encrypts document (AES-256-GCM)
   ↓
4. Python Backend: Generates ZK proof (Groth16)
   ↓
5. Python Backend: Stores in Neo4j with provenance
   ↓
6. Python Backend → Blockchain: Anchors hash
   ↓
7. Python Backend: Returns share link
   ↓
8. ConductMe: Displays share link to user
```

### Example 2: AI Agent Identity Verification Flow

```
1. AI Agent requests reputation proof via API
   ↓
2. Python Backend: Checks agent registry (AAIP)
   ↓
3. Python Backend: Generates ZK proof (level3_inequality)
   ↓
4. Python Backend: Tracks nullifier (prevents replay)
   ↓
5. Python Backend: Returns proof + nullifier
   ↓
6. AI Agent: Uses proof for authentication
```

### Example 3: VERIDICUS Quantum Job Execution

```
1. User calls execute_quantum_job on Solana
   ↓
2. VERIDICUS Program: Validates rate limits
   ↓
3. VERIDICUS Program: Fetches SOL/USD price from Pyth
   ↓
4. VERIDICUS Program: Calculates dynamic burn amount
   ↓
5. VERIDICUS Program: Burns tokens based on qubits
   ↓
6. VERIDICUS Program: Updates job counter
   ↓
7. Event emitted: QuantumJobExecuted
```

## 🗄️ Database Schema

### Neo4j (Python Backend)

Graph-based claim and provenance storage:

```cypher
// Nodes
(:Document {id, type, encrypted_path, hash})
(:Agent {id, name, operator_id, capabilities})
(:Proof {id, circuit, nullifier, verified})
(:ShareLink {token, document_id, access_level})

// Relationships
(:Document)-[:HAS_PROOF]->(:Proof)
(:Document)-[:HAS_SHARE_LINK]->(:ShareLink)
(:Agent)-[:HAS_REPUTATION]->(:Proof)
```

## 🔐 Security Architecture

### Security Middleware Layer

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. HTTP Request
       ▼
┌─────────────────────────────────────┐
│     Security Middleware             │
│  ┌───────────────────────────────┐  │
│  │ Threat Detection             │  │
│  │ - XSS/SQL Injection Detection│  │
│  │ - Path Traversal Prevention  │  │
│  │ - Suspicious Pattern Matching│  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ Rate Limiting                 │  │
│  │ - Per-endpoint limits         │  │
│  │ - IP-based tracking          │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ IP Blocking                   │  │
│  │ - Automatic blocking          │  │
│  │ - Threat threshold tracking  │  │
│  └───────────────────────────────┘  │
│  ┌───────────────────────────────┐  │
│  │ Security Headers              │  │
│  │ - CSP, HSTS, XSS Protection  │  │
│  │ - Frame Options, Referrer     │  │
│  └───────────────────────────────┘  │
└──────────────┬───────────────────────┘
               │ 2. Validated Request
               ▼
┌─────────────┐
│  Backend    │
│  Handler    │
└─────────────┘
```

### Authentication & Authorization

- **Vault/GraphQL**: JWT/OIDC via JWKS (RS/ES) with HS256 fallback; user attached to request context.
- **AI Endpoints**: API key authentication (`X-API-Key`) plus optional IP allowlist.
- **Public Bundles**: `/vault/share/{token}` and `/vault/share/{token}/bundle` rate-limited and error-sanitized.
- **Key Management**: Vault master key loaded from KMS/env/file; generation only if `ALLOW_GENERATED_VAULT_KEY=true` (dev).

### Security Features

- **Threat Detection**: Automatic detection of XSS, SQL injection, path traversal
- **Rate Limiting**: Per-endpoint limits (20-100 req/min)
- **IP Blocking**: Automatic blocking after 5 suspicious requests
- **Security Headers**: CSP, HSTS, XSS protection, frame options
- **Input Validation**: Token format, document ID, string sanitization
- **Audit Logging**: All security events logged and monitored

### Data Encryption

- **At Rest**: AES-256-GCM for vault documents
- **In Transit**: HTTPS/TLS for all API calls
- **Hashing**: SHA-256 for claim and evidence hashes

### Zero-Knowledge Proofs

Production-ready Groth16 circuits for privacy-preserving verification (age, authenticity, level3 nullifier-binding). Verification keys are served from `/zkp/artifacts/...` with ETag/sha256 integrity gating; rebuild via `make zkp-rebuild` to regenerate wasm/zkey/vkey plus `INTEGRITY.json`.

```python
# Age verification proof (Groth16)
def generate_age_proof(birth_date, min_age, document_hash):
    """
    Proves age >= min_age without revealing birth_date.
    Uses Groth16 SNARK for fast verification (<1s).
    """
    # Circuit: age.circom
    # Prover: snarkjs
    # Verification: <0.2s (cached vkeys)
    proof = zk_service.generate_age_proof(
        birth_date=birth_date,
        min_age=min_age,
        document_hash=document_hash
    )
    return proof

# Document authenticity proof (Groth16)
def generate_authenticity_proof(document_hash, merkle_root, merkle_proof):
    """
    Proves document hash exists in Merkle tree without revealing content.
    Uses Poseidon hash for constraint efficiency.
    """
    proof = zk_service.generate_authenticity_proof(
        document_hash=document_hash,
        merkle_root=merkle_root,
        merkle_proof=merkle_proof
    )
    return proof
```

**Circuit Details**:
- **Age Circuit**: Poseidon commitment, timestamp comparison
- **Authenticity Circuit**: Poseidon Merkle inclusion proof (depth 16)
- **Verification**: Groth16 with BLS12-381 curve
- **Performance**: <1s verification, <0.2s with caching

## 🚦 API Endpoints

### Python Backend (Port 8000)

```
# REST API - Vault Operations
POST   /vault/upload
GET    /vault/document/{document_id}
GET    /vault/share/{token}
GET    /vault/share/{token}/bundle
GET    /vault/qr/{token}

# AI Endpoints - Structured APIs
POST   /ai/verify-proof
POST   /ai/verify-proofs-batch
POST   /ai/share-link
GET    /ai/share/{token}/info
GET    /ai/status

# Monitoring & Health
GET    /health
GET    /monitoring/health
GET    /monitoring/metrics
GET    /monitoring/security/events
GET    /monitoring/security/threats

# GraphQL (Ariadne)
POST   /graphql

# Static Assets
GET    /zkp/artifacts/{circuit}/verification_key.json

# Docs (if enabled)
GET    /docs
GET    /redoc
```

## 📈 Scaling Strategy

### Horizontal Scaling

```
┌─────────────────────────────────────┐
│      Load Balancer (Nginx)          │
└──────────┬──────────────────────────┘
           │
    ┌──────┴──────┬──────────┐
    │             │          │
    ▼             ▼          ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Backend 1│  │Backend 2│  │Backend 3│
└─────────┘  └─────────┘  └─────────┘
    │             │          │
    └──────┬──────┴──────────┘
           │
    ┌──────┴──────────┐
    │  Shared Cache   │
    │    (Redis)      │
    └─────────────────┘
```

### Database Sharding

- **App Data**: Partition by platform (ANDROID, IOS, WEB)
- **Claims**: Partition by hash prefix
- **Documents**: Partition by user region

## 🔄 CI/CD Pipeline

```
┌─────────────┐
│ Git Push    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ GitHub      │
│ Actions     │
└──────┬──────┘
       │
   ┌───┴───┬────────────┬──────────┐
   │       │            │          │
   ▼       ▼            ▼          ▼
┌─────┐ ┌─────┐  ┌───────────┐ ┌────────┐
│Lint │ │Test │  │  Build    │ │Security│
│     │ │     │  │  Docker   │ │  Scan  │
└─────┘ └─────┘  └───────────┘ └────────┘
   │       │            │          │
   └───┬───┴────────────┴──────────┘
       │
       ▼
┌─────────────┐
│  Deploy     │
│  (k8s/ECS)  │
└─────────────┘
```

## 📊 Monitoring & Observability

### Health Checks

**Lightweight Health Check** (`/health`):
- Response time: <0.05s
- Use case: Load balancer health checks
- Returns: `{"status": "healthy"}`

**Comprehensive Health Check** (`/monitoring/health`):
- System metrics: CPU, memory, disk
- Service status: Database, cache
- Performance metrics: Response times, error rates

### Metrics Endpoints

**Performance Metrics** (`/monitoring/metrics`):
- Request count, error count
- Average, P95, P99 response times
- Cache statistics (hit rate, backend)

**Security Events** (`/monitoring/security/events`):
- Suspicious input detection
- Rate limit violations
- IP blocking events
- Failed authentication attempts

### Caching Layer

**Redis Cache** (with in-memory fallback):
- Verification keys: Cached indefinitely (immutable)
- Share bundles: 60s TTL
- Document metadata: 5min TTL
- Attestations: 10min TTL

**Performance Impact**:
- Share bundle: <0.2s (cached)
- Proof verification: <0.2s (cached vkeys)
- Cache hit rate: Target >80%

### Logging

**Structured Logging**:
```python
# Python structured logging
logger.info('Proof verified', extra={
    'proof_type': 'age_proof',
    'verified': True,
    'response_time_ms': 125,
    'request_id': 'abc123'
})
```

**Security Event Logging**:
```python
log_security_event(
    event_type='suspicious_input',
    details={'ip': '192.168.1.100', 'pattern': 'XSS'},
    severity='warning'
)
```

### Tracing

**Current**: Request ID tracking via `X-Request-ID` header  
**Future**: OpenTelemetry for distributed tracing

## 🤖 AI Agent Identity Protocol (AAIP)

AAIP is a first-of-its-kind protocol for verifiable AI agent identities.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      AAIP LAYER                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │  Agent Registry │  │  ZK Prover      │  │  Nullifier  │ │
│  │                 │  │                 │  │  Tracker    │ │
│  │  • DID Format   │  │  • Groth16      │  │             │ │
│  │  • Capabilities │  │  • Level3       │  │  • Redis    │ │
│  │  • Constraints  │  │  • Reputation   │  │  • Replay   │ │
│  │  • Public Keys  │  │                 │  │    Prevent  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   Trust Bridge                          ││
│  │  • Agent-to-Agent Trust    • Capability Verification    ││
│  │  • Reputation Proofs       • ECDSA Signatures           ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Key Components

1. **Agent Registry**: Stores agent identities with W3C DID format
2. **ZK Prover**: Generates Groth16 proofs for reputation thresholds
3. **Nullifier Tracker**: Prevents replay attacks on proofs
4. **Trust Bridge**: Enables agent-to-agent trust verification

### DID Format

```
did:honestly:agent:{config_fingerprint_prefix}:{agent_id}
```

Example: `did:honestly:agent:a1b2c3d4e5f67890:agent_abc123def456`

**CRITICAL**: The DID includes a config fingerprint prefix because:
- Agent identity = Model + Prompt + Configuration
- If ANY factor changes, it's a DIFFERENT agent
- `claude-3-opus with "Be helpful"` ≠ `claude-3-opus with "Be evil"`

The config fingerprint is computed from:
- `model_hash` (specific model weights)
- `system_prompt_hash` (exact instructions)
- `capabilities` and `constraints`

### Usage Example

```python
from identity import register_ai_agent, get_agent_reputation

# Register an AI agent
agent = register_ai_agent(
    name="claude-3-opus",
    operator_id="anthropic",
    capabilities=["text_generation", "reasoning"],
    constraints=["audit_logged"],
    public_key="-----BEGIN PUBLIC KEY-----\n..."
)

# Generate ZK proof of reputation
rep = get_agent_reputation(agent["agent_id"], threshold=40)
# Returns: proof, nullifier, zk_verified
```

---

## 🔮 Future Enhancements

### Phase 1 (MVP) ✅
- Basic app verification
- Simple trust scoring
- Claim and evidence tracking

### Phase 2 (Current)
- Full frontend integration
- Enhanced scoring engine
- ZK proof generation

### Phase 3 (Planned)
- Real-time subscriptions
- Advanced ML models
- Mobile applications
- API marketplace

### Phase 4 (Vision)
- Decentralized network
- Cross-chain verification
- AI-powered analysis
- Global trust network

## 📚 References

- [GraphQL Spec](https://spec.graphql.org/)
- [Apollo Server Docs](https://apollographql.com/docs/apollo-server/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Neo4j Graph Data Science](https://neo4j.com/product/graph-data-science/)
- [Hyperledger Fabric](https://hyperledger-fabric.readthedocs.io/)
