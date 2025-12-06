# Honestly - Truth Engine & Personal Proof Vault

A production-ready blockchain-verified identity and credential verification system with zero-knowledge proofs, AI integration, and enterprise-grade security.

## 🎯 What is Honestly?

Honestly is a comprehensive platform for:
- **Personal Proof Vault**: Encrypted document storage with zero-knowledge proofs
- **App Verification**: Trust scoring and verification for applications
- **AI Integration**: Structured APIs for programmatic access
- **Blockchain Anchoring**: Immutable attestations via Hyperledger Fabric
- **Privacy-Preserving Verification**: ZK-SNARK proofs for selective disclosure

## 🏗️ Architecture

The Honestly platform consists of three main components:

### 1. **Frontend Application** (`frontend-app/`)
- React + Vite application
- TailwindCSS for styling
- Apollo Client for GraphQL
- Real-time proof verification UI
- QR code scanning and verification

### 2. **GraphQL Backend** (`backend-graphql/`)
- Node.js + Apollo Server
- App verification and scoring engine
- Claims, evidence, and verdict management
- WhistlerScore calculation

### 3. **Python Backend** (`backend-python/`)
- FastAPI REST API with production-grade security
- Neo4j graph database
- Zero-knowledge proof generation (Groth16)
- AI-friendly endpoints (`/ai/*`)
- Monitoring and health checks (`/monitoring/*`)
- Redis caching for <0.2s response times
- Kafka event streaming (optional)
- FAISS vector search (optional)
- Hyperledger Fabric blockchain (optional)

## 🚀 Quick Start

### Minimal Stack (Recommended for Development)

```bash
# Start everything with one command
docker compose -f docker-compose.min.yml up --build
```

This starts:
- **API**: http://localhost:8000 (REST/GraphQL)
- **Frontend**: http://localhost:5173
- **Neo4j**: http://localhost:7474 (bolt://localhost:7687)

### Full Stack Setup

See [SETUP.md](SETUP.md) for complete setup instructions.

## ✨ Production Features

### 🔒 Security
- **Security Middleware**: Automatic threat detection, IP blocking, rate limiting
- **Security Headers**: CSP, HSTS, XSS protection, frame options
- **Input Validation**: XSS/SQL injection detection, token validation
- **Rate Limiting**: Per-endpoint limits (20-100 req/min)
- **Threat Detection**: Automatic IP blocking after suspicious activity

### ⚡ Performance
- **Sub-0.2s Response Times**: Optimized endpoints with caching
- **Redis Caching**: Distributed caching with in-memory fallback
- **Connection Pooling**: Optimized database connections
- **Performance Monitoring**: P95/P99 metrics, response time tracking

### 🤖 AI Integration
- **Structured Endpoints**: `/ai/verify-proof`, `/ai/verify-proofs-batch`
- **Standardized Responses**: Consistent `{success, data, error, metadata}` format
- **Batch Operations**: Verify up to 100 proofs in one request
- **API Key Authentication**: Secure access control

### 📊 Monitoring
- **Health Checks**: `/health` (lightweight), `/monitoring/health` (comprehensive)
- **Metrics**: Request counts, error rates, response times, cache stats
- **Security Events**: Real-time threat detection and logging
- **System Monitoring**: CPU, memory, disk usage tracking

### 🔐 Zero-Knowledge Proofs
- **Groth16 Circuits**: Age verification and document authenticity
- **Fast Verification**: <1s verification times
- **QR-Friendly**: Shareable proof links with QR codes
- **Production-Ready**: Real zkSNARK circuits (Circom + snarkjs)

## 📚 Documentation

### Getting Started
- [Complete Setup Guide](SETUP.md) - Step-by-step setup instructions
- [Production Deployment](backend-python/PRODUCTION.md) - Production deployment guide
- [Production Validation](PRODUCTION_VALIDATION.md) - Load testing, security audit, chaos engineering
- [Architecture Overview](ARCHITECTURE.md) - System architecture details

### API Documentation
- [Vault API Reference](docs/vault-api.md) - Complete vault API documentation
- [AI Endpoints Guide](docs/ai-endpoints.md) - AI-friendly API endpoints
- [Monitoring Guide](docs/monitoring.md) - Health checks and metrics

### Security & Performance
- [Security Policy](SECURITY.md) - Security policy and vulnerability reporting
- [ZK-SNARK Guide](backend-python/zkp/README.md) - Zero-knowledge proof setup

### Additional Resources
- [Vault Quick Start](docs/vault-quickstart.md) - Quick start for vault features
- [Personal Proof Vault](docs/personal-proof-vault.md) - Vault overview
- [Project Scope](docs/Scope.md) - Project scope and requirements

## 🔑 Key Features

### AppWhistler (GraphQL Backend)
- ✅ App verification and trust scoring
- ✅ Claims and evidence management
- ✅ Verdict tracking and provenance
- ✅ Multi-signal scoring engine
- ✅ Privacy, financial, and sentiment analysis

### Personal Proof Vault (Python Backend)
- ✅ Encrypted document storage (AES-256-GCM)
- ✅ Zero-knowledge proofs (Groth16) for selective disclosure
- ✅ Hyperledger Fabric attestations
- ✅ QR code generation for sharing
- ✅ Complete audit timeline
- ✅ Graph-based claim verification
- ✅ AI-friendly API endpoints
- ✅ Production-grade security middleware
- ✅ Performance monitoring and health checks

## 🛠️ Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Docker & Docker Compose
- Neo4j 5.x (or use Docker)
- Redis (optional, for distributed caching)

### Quick Development Setup

```bash
# Install dependencies
make install

# Start minimal stack
make up-min

# Or start full stack
make up
```

### Running Tests

```bash
# Run all tests
make test

# Individual components
cd frontend-app && npm test
cd backend-graphql && npm test
cd backend-python && pytest
```

## 📦 Project Structure

```
honestly/
├── frontend-app/           # React frontend application
│   ├── src/
│   │   ├── App.jsx        # Main application component
│   │   └── main.jsx       # Application entry point
│   └── package.json
│
├── backend-graphql/        # Node.js GraphQL backend
│   ├── src/
│   │   ├── config/        # Configuration files
│   │   ├── graphql/       # Schema and resolvers
│   │   └── utils/         # Utility functions
│   └── package.json
│
├── backend-python/         # Python FastAPI backend
│   ├── api/               # FastAPI routes
│   │   ├── middleware/    # Security, caching, monitoring
│   │   ├── ai_routes.py   # AI endpoints
│   │   └── vault_routes.py # Vault endpoints
│   ├── vault/             # Vault implementation
│   ├── zkp/               # ZK-SNARK circuits
│   └── requirements.txt
│
├── docs/                   # Documentation
├── docker-compose.min.yml  # Minimal stack (recommended)
└── docker-compose.yml      # Full stack
```

## 🔐 Security

**Production-Ready Security Features**:
- ✅ Automatic threat detection and IP blocking
- ✅ Rate limiting per endpoint
- ✅ Input validation and sanitization
- ✅ Security headers (CSP, HSTS, etc.)
- ✅ Audit logging for all security events
- ✅ API key authentication for AI endpoints
- ✅ Encrypted document storage (AES-256-GCM)
- ✅ Zero-knowledge proofs for privacy

See [SECURITY.md](SECURITY.md) for complete security policy and vulnerability reporting.

## ⚡ Performance

**Target Response Times**:
- Share bundle: <0.2s (cached)
- Proof verification: <0.2s (cached vkeys)
- Health check: <0.05s
- AI endpoints: <0.3s

**Optimization Features**:
- Redis caching with in-memory fallback
- Connection pooling
- Response time monitoring
- Cache hit rate tracking

## 🤖 AI Integration

The platform provides structured AI endpoints for programmatic access:

- `POST /ai/verify-proof` - Verify single proof
- `POST /ai/verify-proofs-batch` - Batch verify (up to 100)
- `POST /ai/share-link` - Create shareable link
- `GET /ai/share/{token}/info` - Get share info
- `GET /ai/status` - API status

See [AI Endpoints Guide](docs/ai-endpoints.md) for complete documentation.

## 📊 Monitoring

Real-time monitoring and health checks:

- `GET /health` - Lightweight health check
- `GET /monitoring/health` - Comprehensive health check
- `GET /monitoring/metrics` - Performance metrics
- `GET /monitoring/security/events` - Security event log

See [Monitoring Guide](docs/monitoring.md) for details.

## 🚀 Production Deployment

For production deployment, see:
- [Production Deployment Guide](backend-python/PRODUCTION.md)
- [Security Checklist](SECURITY.md#security-checklist)
- [Performance Optimization](backend-python/PRODUCTION.md#performance-optimization)

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/aresforblue-ai/honestly/issues)
- **Documentation**: See `docs/` folder
- **Security**: See [SECURITY.md](SECURITY.md) for vulnerability reporting

---

**Built with ❤️ for privacy, security, and trust.**
