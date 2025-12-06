# Honestly - Python Backend

Production-ready Python backend for the Honestly Truth Engine, providing secure vault operations, zero-knowledge proofs, AI integration, and enterprise-grade monitoring.

## 🚀 Features

### Core Capabilities
- **FastAPI REST API** for vault operations
- **GraphQL API** via Ariadne
- **Zero-Knowledge Proofs** (Groth16) for privacy-preserving verification
- **Encrypted Document Storage** (AES-256-GCM)
- **Neo4j Graph Database** integration for claims and provenance

### Production Features
- **Security Middleware**: Threat detection, IP blocking, rate limiting, security headers
- **AI Endpoints**: Structured APIs for programmatic access (`/ai/*`) with HMAC signature verification
- **Monitoring**: Health checks, performance metrics (`/monitoring/*`), Prometheus/Grafana integration
- **Caching**: Redis caching with in-memory fallback for <0.2s response times
- **Performance Optimization**: Connection pooling, response time tracking, P95/P99 monitoring
- **Prometheus Metrics**: Comprehensive metrics export at `/metrics` endpoint
- **Grafana Dashboards**: Pre-configured dashboards for P95/P99 trends and system health
- **Chaos Testing**: Network partition simulation with ToxiProxy for resilience testing
- **Comprehensive Testing**: ZK attack surface tests (proof replay, timestamp manipulation, field overflow, malformed Merkle paths)

### Optional Integrations
- **Kafka** event streaming for data ingestion
- **FAISS** vector search for semantic similarity
- **Hyperledger Fabric** blockchain integration for attestations

## 📋 Quick Start

### Prerequisites
- Python 3.11+
- Neo4j 5.x (or use Docker)
- Redis (optional, for distributed caching)

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Development Server

```bash
# From backend-python directory
uvicorn api.app:app --reload --port 8000
```

Access at: http://localhost:8000

## 🌐 API Endpoints

### REST Endpoints (`/vault/*`)

#### Document Management
- `POST /vault/upload` - Upload encrypted document
- `GET /vault/document/{document_id}` - Retrieve document (requires auth)
- `GET /vault/share/{token}` - Verify share link
- `GET /vault/share/{token}/bundle` - Get verification bundle (cached, <0.2s)
- `GET /vault/qr/{token}` - Generate QR code for share link

#### Proof Operations
- Proof generation and verification via GraphQL mutations

### AI Endpoints (`/ai/*`)

Structured APIs for programmatic access:

- `POST /ai/verify-proof` - Verify single proof
- `POST /ai/verify-proofs-batch` - Batch verify (up to 100 proofs)
- `POST /ai/share-link` - Create shareable proof link
- `GET /ai/share/{token}/info` - Get share link information (cached)
- `GET /ai/status` - API status and capabilities

**Authentication**: Include `X-API-Key` header (set `AI_API_KEY` env var)

See [AI Endpoints Guide](../docs/ai-endpoints.md) for complete documentation.

### Monitoring Endpoints (`/monitoring/*`)

- `GET /monitoring/health` - Comprehensive health check
- `GET /monitoring/metrics` - Performance metrics
- `GET /monitoring/security/events` - Security event log
- `GET /monitoring/security/threats` - Threat detection summary

See [Monitoring Guide](../docs/monitoring.md) for details.

### Health Checks

- `GET /health` - Lightweight health check (<0.05s)
- `GET /` - API information

### GraphQL Endpoint

- `POST /graphql` - GraphQL API (Ariadne)
- Interactive docs: `GET /graphql` (if enabled)

## 🔒 Security Features

### Threat Detection
- Automatic IP blocking after suspicious activity
- XSS/SQL injection detection
- Path traversal prevention
- Security event logging

### Rate Limiting
- Per-endpoint rate limits (20-100 req/min)
- Configurable via environment variables
- Automatic throttling

### Security Headers
- CSP, HSTS, XSS protection
- Frame options, referrer policy
- Content type options

### Input Validation
- Token format validation
- Document ID validation
- String sanitization
- Pattern matching for threats

## ⚡ Performance

### Response Time Targets
- Share bundle: <0.2s (cached)
- Proof verification: <0.2s (cached vkeys)
- Health check: <0.05s
- AI endpoints: <0.3s

### Caching Strategy
- **Verification Keys**: Cached indefinitely (immutable)
- **Share Bundles**: 60s TTL
- **Document Metadata**: 5min TTL
- **Attestations**: 10min TTL

### Optimization Features
- Redis caching with in-memory fallback
- Neo4j connection pooling
- Response time monitoring
- Cache hit rate tracking

## 🔧 Configuration

### Environment Variables

```bash
# Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASS=test

# CORS & Security
ALLOWED_ORIGINS=http://localhost:5173
ENABLE_CORS=true
ENABLE_HSTS=true
ENABLE_DOCS=true  # Set to false in production

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# API Keys
AI_API_KEY=your-api-key-here

# Vault Encryption
VAULT_ENCRYPTION_KEY=<base64-encoded-256-bit-key>

# Performance
WORKERS=4  # uvicorn workers
```

### Feature Flags

Disable optional services:
```bash
DISABLE_KAFKA=true
DISABLE_FAISS=true
DISABLE_FABRIC=true
```

## 📁 Project Structure

```
backend-python/
├── api/                    # FastAPI application
│   ├── middleware/         # Security, caching, monitoring
│   │   ├── security.py     # Security middleware
│   │   ├── cache.py        # Redis/in-memory caching
│   │   └── monitoring.py   # Health checks and metrics
│   ├── ai_routes.py        # AI endpoints
│   ├── vault_routes.py     # Vault REST endpoints
│   ├── vault_resolvers.py  # GraphQL resolvers
│   └── app.py              # Main FastAPI app
│
├── vault/                  # Vault implementation
│   ├── storage.py          # Encrypted storage
│   ├── zk_proofs.py       # ZK proof service
│   ├── share_links.py     # Share link management
│   └── models.py          # Data models
│
├── zkp/                    # Zero-knowledge proofs
│   ├── circuits/          # Circom circuits
│   ├── artifacts/         # Compiled artifacts
│   └── snark-runner.js    # Proof runner
│
├── ingestion/              # Kafka integration (optional)
├── blockchain/            # Fabric integration (optional)
├── vector_index/          # FAISS search (optional)
│
├── requirements.txt       # Python dependencies
├── PRODUCTION.md         # Production deployment guide
└── README.md             # This file
```

## 🔐 Zero-Knowledge Proofs

The backend includes production-ready Groth16 circuits for:
- **Age Verification**: Prove age >= threshold without revealing birthdate
- **Document Authenticity**: Prove document hash exists in Merkle tree

See [ZK-SNARK Guide](zkp/README.md) for setup and usage.

## 📊 Monitoring

### Health Checks

```bash
# Lightweight check
curl http://localhost:8000/health

# Comprehensive check
curl http://localhost:8000/monitoring/health
```

### Metrics

```bash
# Performance metrics
curl http://localhost:8000/monitoring/metrics

# Security events
curl http://localhost:8000/monitoring/security/events
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=api --cov=vault

# Specific test file
pytest tests/test_vault.py
```

## 🚀 Production Deployment

For production deployment, see:
- [Production Deployment Guide](PRODUCTION.md)
- [Main SETUP Guide](../SETUP.md)

Key production considerations:
- Set strong passwords
- Configure SSL/TLS
- Enable Redis for distributed caching
- Set `ENABLE_DOCS=false`
- Configure monitoring alerts
- Set up log aggregation

## 📚 Documentation

- [Main README](../README.md) - Project overview
- [Setup Guide](../SETUP.md) - Complete setup instructions
- [Production Guide](PRODUCTION.md) - Production deployment
- [AI Endpoints](../docs/ai-endpoints.md) - AI API documentation
- [Monitoring Guide](../docs/monitoring.md) - Monitoring documentation
- [ZK-SNARK Guide](zkp/README.md) - Zero-knowledge proof setup
- [Architecture](../ARCHITECTURE.md) - System architecture

## 🔗 Related Components

- **Frontend**: [frontend-app/](../frontend-app/)
- **GraphQL Backend**: [backend-graphql/](../backend-graphql/)
- **Documentation**: [docs/](../docs/)

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/aresforblue-ai/honestly/issues)
- **Security**: See [SECURITY.md](../SECURITY.md)
- **Documentation**: See `docs/` folder

---

**Version**: 1.0.0  
**Last Updated**: 2024-12-19
