# Honestly - Python Backend

**Last updated**: December 11, 2024

Production-ready Python backend for the Honestly Truth Engine, providing secure vault operations, zero-knowledge proofs, AI integration, and enterprise-grade monitoring.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.5-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](../LICENSE)

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [API Endpoints](#-api-endpoints)
- [Zero-Knowledge Proofs](#-zero-knowledge-proofs)
- [AI Agent Identity Protocol](#-ai-agent-identity-protocol)
- [Testing](#-testing)
- [Security](#-security)
- [Configuration](#-configuration)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Production Deployment](#-production-deployment)

---

## 🚀 Features

### Core Capabilities

- **FastAPI REST API** for vault operations
- **GraphQL API** via Ariadne
- **Zero-Knowledge Proofs** (Groth16) for privacy-preserving verification (age, authenticity, level3 nullifier-binding variants)
- **Encrypted Document Storage** (AES-256-GCM)
- **Neo4j Graph Database** integration for claims and provenance

### Production Features

- **Auth**: JWT/OIDC (JWKS RS/ES) with optional HS256 fallback; strict mode available
- **Key Management**: Vault key loader (KMS hook/env/file) with fail-fast if missing
- **Security Middleware**: Threat detection, IP blocking, rate limiting, security headers
- **AI Endpoints**: Structured APIs for programmatic access (`/ai/*`) with HMAC signature verification
- **Monitoring**: Health/readiness + Prometheus `/metrics` (Grafana-ready)
- **Caching**: Redis caching with in-memory fallback for <0.2s response times
- **Performance Optimization**: Connection pooling, response time tracking, P95/P99 monitoring
- **VKey Integrity**: zk verification keys served with ETag/sha256; gated if missing
- **Comprehensive Testing**: ZK property tests (replay, timestamp, overflow, Merkle path)

### Optional Integrations

- **Kafka** event streaming for data ingestion
- **FAISS** vector search for semantic similarity
- **Base/Arbitrum L2** blockchain anchoring for attestations (~$0.001/doc)

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

Access at: <http://localhost:8000>

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

### Monitoring & Metrics

- `GET /health/live` - Liveness
- `GET /health/ready` - Readiness (vkeys + Neo4j)
- `GET /metrics` - Prometheus (if enabled)

See [Monitoring Guide](../docs/monitoring.md) for details.

### Health & Readiness

- `GET /health` - Lightweight health check (<0.05s)
- `GET /health/ready` - Readiness (vkeys present, Neo4j reachable)
- `GET /` - API information

### GraphQL Endpoint

- `POST /graphql` - GraphQL API (Ariadne) with user context from JWT/OIDC

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
- VKey integrity/ETag (sha256) for immutable verification keys

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
# Auth (prefer OIDC JWKS)
OIDC_JWKS_URL=https://issuer.example.com/.well-known/jwks.json
OIDC_ALGS=RS256,ES256
OIDC_REQUIRED=true          # fail if JWKS missing
ALLOW_HS_FALLBACK=false     # set true only if you intentionally use HS256
JWT_SECRET=change-me        # only used if HS fallback allowed
JWT_ALGO=HS256
# Optional:
# JWT_AUDIENCE=your-audience
# JWT_ISSUER=your-issuer

# Redis (optional)
REDIS_URL=redis://localhost:6379/0

# API Keys
AI_API_KEY=your-api-key-here

# Vault Encryption
VAULT_ENCRYPTION_KEY=<base64-encoded-256-bit-key>
VAULT_KEY_FILE=<path-to-key-file>       # optional file-based key
KMS_KEY_ID=<kms-key-id>                 # recommended: manage keys via KMS/Vault
KMS_REGION=<region>                     # if using cloud KMS
ALLOW_GENERATED_VAULT_KEY=false         # set true only for local dev if no key is provided

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

```text
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
├── identity/               # Identity infrastructure (AAIP)
│   ├── ai_agent_protocol.py   # AI Agent Identity Protocol
│   ├── zkp_integration.py     # ZK proof integration
│   ├── verifiable_credentials.py  # W3C VCs
│   ├── social_recovery.py     # Shamir's Secret Sharing
│   └── cross_chain_bridge.py  # Cross-chain identity
│
├── zkp/                    # Zero-knowledge proofs
│   ├── circuits/          # Circom circuits
│   │   ├── Level3Inequality.circom  # Reputation proofs
│   │   ├── agent_capability.circom  # Capability proofs
│   │   └── agent_reputation.circom  # Agent-specific proofs
│   ├── artifacts/         # Compiled artifacts
│   └── snark-runner.js    # Proof runner (incl. level3_inequality)
│
├── ingestion/              # Kafka integration (optional)
├── blockchain/            # Fabric integration (optional)
├── vector_index/          # FAISS search (optional)
│
├── requirements.txt       # Python dependencies
├── PRODUCTION.md         # Production deployment guide
└── README.md             # This file
```

## 🤖 AI Agent Identity Protocol (AAIP)

The backend includes a complete AI agent identity infrastructure:

### Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Agent Registration** | ✅ | Register AI agents with verifiable identities |
| **Real ZK Proofs** | ✅ | Groth16 reputation proofs via `level3_inequality` |
| **Nullifier Tracking** | ✅ | Replay attack prevention with Redis persistence |
| **ECDSA Signatures** | ✅ | Agent authentication with challenge-response |
| **Model Fingerprinting** | ✅ | Deterministic, reproducible model hashes |
| **W3C VC Compatible** | ✅ | DIDs: `did:honestly:agent:{id}` |

### Usage

```python
from identity import (
    register_ai_agent,
    get_agent_reputation,
    verify_reputation_proof,
    AgentAuthenticator,
)

# Register an AI agent
agent = register_ai_agent(
    name="claude-3-opus",
    operator_id="anthropic",
    operator_name="Anthropic",
    model_family="transformer",
    capabilities=["text_generation", "reasoning"],
    constraints=["audit_logged"],
    public_key="-----BEGIN PUBLIC KEY-----\n...",
)

# Get reputation with ZK proof
rep = get_agent_reputation(agent["agent_id"], threshold=40)

# Real Groth16 proof + nullifier
print(rep["proof"])        # Groth16 proof
print(rep["nullifier"])    # Prevents replay attacks
print(rep["zk_verified"])  # True if circuit verified
```

### API Endpoints

See `/api/identity_routes.py` for REST endpoints:

- `POST /identity/agent/register` - Register new agent
- `GET /identity/agent/{id}` - Get agent info
- `POST /identity/agent/{id}/reputation` - Get reputation with ZK proof
- `POST /identity/agent/authenticate` - Challenge-response auth

---

## 🔐 Zero-Knowledge Proofs

The backend includes production-ready Groth16 circuits for:

- **Age Verification** (`age`): Prove age >= threshold without revealing birthdate
- **Document Authenticity** (`authenticity`): Prove document hash exists in Merkle tree
- **Level 3 / Nullifier-Binding** (`age_level3`, `Level3Inequality`): Identity-bound variants to prevent replay/transfer
- **Agent Reputation** (`level3_inequality`): Prove agent reputation >= threshold without revealing score

Rebuild & integrity:

```bash
cd zkp
make zkp-rebuild                       # rebuild wasm/zkey/vkey + hashes
python scripts/verify_key_integrity.py # regenerate INTEGRITY.json
```

Memory note: for level3 proving/compilation locally, set `NODE_OPTIONS="--max-old-space-size=8192"` (Windows often needs this) before running `npm run build:*` or `node snark-runner.js`.

Tests:

```bash
cd ..
ZK_TESTS=1 pytest tests/test_zk_properties.py -v  # requires built artifacts and node on PATH
```

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
- [Security Features](../docs/security-features.md) - Auth, rate limits, headers, key management
- [Performance Guide](../docs/performance.md) - Targets, caching, load testing
- [ZK-SNARK Guide](zkp/README.md) - Zero-knowledge proof setup
- [Architecture](../ARCHITECTURE.md) - System architecture

## 🔗 Related Components

- **Frontend**: [frontend-app/](../frontend-app/)
- **GraphQL Backend**: [backend-graphql/](../backend-graphql/)
- **Documentation**: [docs/](../docs/)

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/veridicus/honestly/issues)
- **Security**: See [SECURITY.md](../SECURITY.md)
- **Documentation**: See `docs/` folder

---

**Version**: 1.0.0  
**Last Updated**: 2025-12-06
