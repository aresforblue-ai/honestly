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
│  │ - App Verification  │      │ - Vault Management      │   │
│  │ - Scoring Engine    │      │ - ZK Proofs             │   │
│  │ - Claims/Evidence   │      │ - Kafka Integration     │   │
│  │ - Provenance        │      │ - FAISS Search          │   │
│  └─────────────────────┘      └────────────────────────┘   │
└────────────┬──────────────────────────┬────────────────────┘
             │                          │
             ▼                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     DATA LAYER                              │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────────┐    │
│  │ PostgreSQL   │  │  Neo4j    │  │  Kafka           │    │
│  │              │  │  Graph DB │  │  Event Stream    │    │
│  └──────────────┘  └───────────┘  └──────────────────┘    │
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

### Authentication & Authorization

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ 1. Login Request
       ▼
┌─────────────┐
│   Auth      │
│   Service   │──────▶ JWT Token Generated
└──────┬──────┘
       │ 2. JWT Returned
       ▼
┌─────────────┐
│   Client    │──────▶ Stores JWT
└──────┬──────┘
       │ 3. API Requests (with JWT)
       ▼
┌─────────────┐
│  Backend    │──────▶ Validates JWT
│  Middleware │
└─────────────┘
```

**Current State**: MVP mode (no auth)
**Future**: JWT-based authentication

### Data Encryption

- **At Rest**: AES-256-GCM for vault documents
- **In Transit**: HTTPS/TLS for all API calls
- **Hashing**: SHA-256 for claim and evidence hashes

### Zero-Knowledge Proofs

```python
# Simplified ZK proof for age verification
def generate_age_proof(birth_date, threshold):
    """
    Proves age >= threshold without revealing birth_date
    """
    age = calculate_age(birth_date)
    proof = {
        'statement': f'age >= {threshold}',
        'valid': age >= threshold,
        'commitment': hash(birth_date + salt)
    }
    return proof
```

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
# REST API
POST   /vault/upload
GET    /vault/documents
POST   /vault/proof
GET    /vault/share/{share_id}

# GraphQL (Strawberry)
POST   /graphql

# Docs
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

### Metrics

- **Application**: Response times, error rates
- **Infrastructure**: CPU, memory, disk
- **Business**: Apps verified, claims processed

### Logging

```javascript
// Winston structured logging
logger.info('App verified', {
  appId,
  platform,
  score,
  duration: elapsed
});
```

### Tracing

Future: OpenTelemetry for distributed tracing

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
