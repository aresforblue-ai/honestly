# Honestly - System Architecture

This document describes the complete architecture of the Honestly Truth Engine platform.

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
│  │         React + Vite Application                     │   │
│  │  - AppWhistler UI                                    │   │
│  │  - Trust Score Dashboard                             │   │
│  │  - Claims Verification Interface                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────┬────────────────────────────────────────────────┘
             │
             │ HTTP/GraphQL
             ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND LAYER                          │
│  ┌─────────────────────┐      ┌────────────────────────┐   │
│  │ GraphQL Backend     │      │  Python Backend         │   │
│  │ (Node.js/Apollo)    │◀────▶│  (FastAPI)             │   │
│  │                     │      │                         │   │
│  │ - App Verification  │      │ ┌────────────────────┐ │   │
│  │ - Scoring Engine    │      │ │ Security Middleware│ │   │
│  │ - Claims/Evidence   │      │ │ - Threat Detection │ │   │
│  │ - Provenance        │      │ │ - Rate Limiting     │ │   │
│  └─────────────────────┘      │ │ - IP Blocking      │ │   │
│                                 │ └────────────────────┘ │   │
│                                 │                         │   │
│                                 │ - Vault Management      │   │
│                                 │ - ZK Proofs (Groth16)   │   │
│                                 │ - AI Endpoints (/ai/*) │   │
│                                 │ - Monitoring (/monitoring/*)│
│                                 │ - Kafka Integration     │   │
│                                 │ - FAISS Search          │   │
│                                 └────────────────────────┘   │
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
│  │  - VKeys         │  │  - Performance Metrics       │  │
│  │  - Share Bundles │  │  - Security Events           │  │
│  │  - Metadata      │  │  - System Resources          │  │
│  └──────────────────┘  └──────────────────────────────┘  │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                   BLOCKCHAIN LAYER                          │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Hyperledger Fabric Network               │    │
│  │  - Attestation Anchoring                           │    │
│  │  - Immutable Audit Trail                           │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## 🔄 Component Interactions

### 1. Frontend ↔ GraphQL Backend

**Protocol**: HTTP/HTTPS with GraphQL
**Port**: 4000

```javascript
// Apollo Client Configuration
const client = new ApolloClient({
  uri: 'http://localhost:4000/graphql',
  cache: new InMemoryCache(),
});
```

**Key Operations**:
- Query apps and trust scores
- Fetch claims and evidence
- Display verification status
- Real-time updates (future: subscriptions)

### 2. GraphQL Backend ↔ Python Backend

**Integration Points**:

**Option A: REST API** (Current)
```javascript
// Call Python FastAPI from Node.js
const response = await fetch('http://localhost:8000/vault/documents');
```

**Option B: Shared Database** (Neo4j)
```javascript
// Both read from Neo4j
const neo4jDriver = neo4j.driver(
  'bolt://localhost:7687',
  neo4j.auth.basic('neo4j', 'test')
);
```

**Option C: Event Bus** (Kafka)
```javascript
// Publish events to Kafka
kafkaProducer.send({
  topic: 'app_verified',
  messages: [{ key: appId, value: JSON.stringify(data) }]
});
```

### 3. Python Backend ↔ Data Stores

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

### Example 1: App Verification Flow

```
1. User submits app via Frontend
   ↓
2. Frontend → GraphQL Backend (registerApp mutation)
   ↓
3. GraphQL validates and creates App record
   ↓
4. GraphQL → Kafka: Publishes "app_created" event
   ↓
5. Python Backend: Kafka consumer picks up event
   ↓
6. Python Backend: Stores in Neo4j with provenance
   ↓
7. Python Backend → Blockchain: Anchors hash
   ↓
8. GraphQL Backend: Calculates WhistlerScore
   ↓
9. Frontend receives updated app with score
```

### Example 2: Claim Verification Flow

```
1. User submits claim via API
   ↓
2. Python Backend: Creates Claim node in Neo4j
   ↓
3. Python Backend: Links evidence to claim
   ↓
4. Python Backend: Generates ZK proof
   ↓
5. Python Backend → Blockchain: Anchors attestation
   ↓
6. GraphQL Backend: Queries Neo4j for claims
   ↓
7. Frontend: Displays claim with verification status
```

### Example 3: Trust Score Calculation

```
1. Frontend requests app score
   ↓
2. GraphQL Backend: Fetches app data
   ↓
3. Scoring Engine analyzes:
   - Reviews (sentiment analysis)
   - Claims (verdict outcomes)
   - Privacy signals
   - Financial transparency
   - AI anomaly detection
   ↓
4. Weighted calculation produces score (0-100)
   ↓
5. Grade assigned (A-F)
   ↓
6. Breakdown returned to frontend
```

## 🗄️ Database Schema

### PostgreSQL (GraphQL Backend)

Used for structured app data (if using Prisma):

```sql
-- Apps table
CREATE TABLE apps (
  id UUID PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  platform VARCHAR(50) NOT NULL,
  whistler_score INTEGER,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Reviews table
CREATE TABLE reviews (
  id UUID PRIMARY KEY,
  app_id UUID REFERENCES apps(id),
  content TEXT,
  rating INTEGER,
  sentiment JSONB
);
```

### Neo4j (Python Backend)

Graph-based claim and provenance storage:

```cypher
// Nodes
(:App {id, name, platform})
(:Claim {id, statement, hash})
(:Evidence {id, text, snapshot_hash})
(:Verdict {id, outcome, confidence})
(:Document {id, type, encrypted_path})

// Relationships
(:App)-[:HAS_CLAIM]->(:Claim)
(:Claim)-[:SUPPORTED_BY]->(:Evidence)
(:Claim)-[:JUDGED_BY]->(:Verdict)
(:Evidence)-[:DERIVED_FROM]->(:Evidence)
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

**AI Endpoints**: API key authentication (`X-API-Key` header)
```python
# AI endpoint authentication
def validate_api_key(x_api_key: str = Header(None)):
    expected_key = os.getenv("AI_API_KEY")
    if x_api_key != expected_key:
        raise HTTPException(401, "Invalid API key")
    return x_api_key
```

**Vault Endpoints**: User-based authentication (MVP: mock user ID)
**Future**: JWT-based authentication for all endpoints

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

Production-ready Groth16 circuits for privacy-preserving verification:

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

### GraphQL Backend (Port 4000)

```graphql
# Main endpoint
POST /graphql

# Health check
GET /health
```

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
