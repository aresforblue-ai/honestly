# 🛡️ Honestly — Truth Engine & Personal Proof Vault

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Build](https://github.com/aresforblue-ai/honestly/workflows/CI/badge.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0--only-blue.svg)
![Coverage](https://img.shields.io/badge/coverage-85%25-yellow.svg)

**A production-ready, blockchain-verified identity and credential verification system with zero-knowledge proofs, AI integration, and enterprise-grade security.**

[🚀 Quick Start](#-quick-start) • [📚 Documentation](#-documentation) • [🔐 Security](#-security) • [🤖 AI Integration](#-ai-integration)

</div>

---

## 🎯 What is Honestly?

Honestly is a comprehensive **privacy-preserving identity platform** that enables:

| Feature | Description |
|---------|-------------|
| 🔐 **Personal Proof Vault** | AES-256-GCM encrypted document storage with zero-knowledge proofs |
| ✅ **App Verification** | Trust scoring and verification engine for applications |
| 🤖 **AI Integration** | Structured APIs for LLM and autonomous agent consumption |
| ⛓️ **Blockchain Anchoring** | Immutable attestations via Hyperledger Fabric |
| 🎭 **Selective Disclosure** | ZK-SNARK proofs for privacy-preserving verification |

## ✨ What's New

### 📦 Recent Releases

**v1.0.0** — AI Agent Identity Protocol, Enterprise Security, World-Class UI  
[View Changelog →](https://github.com/aresforblue-ai/honestly/releases/tag/v1.0.0)

### 🤖 AI Agent Identity Protocol (AAIP)
- **Verifiable AI Identities** — First-of-its-kind protocol for AI agent authentication
- **Real Groth16 ZK Proofs** — Reputation thresholds proven without revealing scores
- **Nullifier Tracking** — Replay attack prevention with Redis persistence
- **ECDSA Signatures** — Cryptographic authentication for agents
- **W3C VC Compatible** — DIDs in format `did:honestly:agent:{id}`

### 🎨 World-Class UI
- **Stunning Frontend** — Glassmorphism, animations, and premium design patterns
- **Responsive Design** — Beautiful on all devices
- **Dark Theme** — Custom Space Grotesk + JetBrains Mono typography

### 🛡️ Enterprise Security
- **Redis Rate Limiting** — Sliding window algorithm with in-memory fallback
- **Input Sanitization** — Protection against XSS, Cypher injection, and more
- **Structured Errors** — Correlation IDs for debugging across services

### 🧪 Comprehensive Testing
- **Unit Tests** — pytest + Vitest coverage
- **E2E Tests** — Playwright for cross-browser testing
- **Integration Tests** — Full API testing with mocked services

### 🔧 Developer Experience
- **Pre-commit Hooks** — Black, Ruff, Prettier, ESLint
- **Setup Scripts** — One-command environment setup
- **Docker Dev** — Full development stack with hot reload

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           HONESTLY PLATFORM                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │  Frontend   │  │  ConductMe  │  │   GraphQL   │  │   Python   │ │
│  │   (Vite)    │  │  (Next.js)  │  │   Backend   │  │   Backend  │ │
│  │             │  │             │  │             │  │            │ │
│  │  • React    │  │  • AI       │  │  • Apollo   │  │  • FastAPI │ │
│  │  • Apollo   │  │  • Workflow │  │  • Claims   │  │  • ZK-SNARK│ │
│  │  • Tailwind │  │  • Trust    │  │  • Scoring  │  │  • Vault   │ │
│  │  • snarkjs  │  │    Bridge   │  │             │  │  • Redis   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬─────┘ │
│         │                │                │                │        │
│         └────────────────┴────────────────┴────────────────┘        │
│                                   │                                  │
│  ┌─────────────┐  ┌─────────────┐  │  ┌─────────────┐  ┌─────────┐ │
│  │    Neo4j    │  │    Redis    │──┘  │  Prometheus │  │ Grafana │ │
│  │   (Graph)   │  │   (Cache)   │     │  (Metrics)  │  │  (UI)   │ │
│  └─────────────┘  └─────────────┘     └─────────────┘  └─────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 AI Agent Identity Protocol (AAIP)

AAIP enables **verifiable AI agent identities** with real zero-knowledge proofs. This is the missing link between AI orchestration and cryptographic verification.

### Key Features

| Feature | Status | Description |
|---------|--------|-------------|
| **Real ZK Proofs** | ✅ | Groth16 via Level3Inequality circuit |
| **Nullifier Tracking** | ✅ | Prevents replay attacks |
| **ECDSA Signatures** | ✅ | Agent authentication |
| **Redis Persistence** | ✅ | Production-ready storage |
| **W3C VC Compatible** | ✅ | `did:honestly:agent:{id}` |
| **Model Fingerprinting** | ✅ | Deterministic model hashes |

### Usage

```python
from identity import register_ai_agent, get_agent_reputation

# Register an AI agent with verifiable identity
agent = register_ai_agent(
    name="claude-3-opus",
    operator_id="anthropic",
    operator_name="Anthropic",
    model_family="transformer",
    capabilities=["text_generation", "reasoning", "code_generation"],
    constraints=["audit_logged", "human_approval_required"],
    public_key="-----BEGIN PUBLIC KEY-----\n...",
)

# Generate ZK proof that reputation > threshold
rep = get_agent_reputation(agent["agent_id"], threshold=40)

# Returns real Groth16 proof + nullifier
print(rep["proof"])         # Groth16 proof object
print(rep["nullifier"])     # Unique, prevents replay
print(rep["zk_verified"])   # True = cryptographically verified
```

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ConductMe Core                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Claude    │  │   Gemini    │  │   Local LLM │         │
│  │  Agent ID   │  │  Agent ID   │  │  Agent ID   │         │
│  │  ┌───────┐  │  │  ┌───────┐  │  │  ┌───────┐  │         │
│  │  │Nullif.│  │  │  │Nullif.│  │  │  │Nullif.│  │         │
│  │  └───────┘  │  │  └───────┘  │  │  └───────┘  │         │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘         │
│         │                │                │                 │
│         └────────────────┼────────────────┘                 │
│                          ▼                                  │
│            ┌───────────────────────┐                        │
│            │   AAIP ZK Integration │                        │
│            │   (Level3Inequality)  │                        │
│            └───────────┬───────────┘                        │
│                        ▼                                    │
│            ┌───────────────────────┐                        │
│            │    Groth16 Prover     │                        │
│            │    (snark-runner.js)  │                        │
│            └───────────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

See [Identity Module](backend-python/identity/) for full documentation.

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Development stack with hot reload
docker-compose -f docker-compose.dev.yml up

# Or minimal stack
docker-compose -f docker-compose.min.yml up
```

### Option 2: Local Setup

```bash
# Windows (PowerShell)
.\scripts\setup-dev.ps1

# Or manually:
# 1. Install dependencies
pip install -r backend-python/requirements.txt
cd frontend-app && npm install

# 2. Start Neo4j
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/test neo4j:5

# 3. Start backend
cd backend-python && uvicorn api.app:app --reload

# 4. Start frontend
cd frontend-app && npm run dev
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | AppWhistler UI |
| ConductMe | http://localhost:3000 | AI Orchestration |
| API | http://localhost:8000 | REST + GraphQL |
| Docs | http://localhost:8000/docs | OpenAPI/Swagger |
| Neo4j | http://localhost:7474 | Graph Browser |
| Grafana | http://localhost:3001 | Dashboards |

### 🛠️ Troubleshooting

- **Neo4j connection issues?** Nuke volumes: `docker-compose down -v && docker-compose up`
- **Port conflicts?** Check for existing services: `lsof -i :8000` (Mac/Linux) or `netstat -ano | findstr :8000` (Windows)
- **ZK compilation fails?** Increase memory: `export NODE_OPTIONS="--max-old-space-size=8192"`

---

## 🔐 Zero-Knowledge Proofs

| Circuit | Purpose | Public Inputs |
|---------|---------|---------------|
| `age` | Age verification (≥ minAge) | minAgeOut, referenceTsOut, documentHashOut, commitment |
| `authenticity` | Document authenticity | rootOut, leafOut |
| `age_level3` | Identity-bound age proof | referenceTs, minAge, userID, documentHash, nullifier |
| `level3_inequality` | Value comparison | value, threshold, nullifier |

### Rebuild Circuits

```bash
cd backend-python/zkp

# Set memory for large circuits
$env:NODE_OPTIONS="--max-old-space-size=8192"

# Build all circuits
npm run build:age
npm run build:auth
npm run build:age-level3

# Generate keys
npm run setup:age
npm run vk:age
```

---

## 🧪 Testing

```bash
# Python unit tests
cd backend-python && pytest tests/ -v --cov

# Frontend E2E tests
cd frontend-app
npm run test:e2e         # Headless
npm run test:e2e:headed  # With browser
npm run test:e2e:ui      # Interactive

# ZK property tests
ZK_TESTS=1 pytest tests/test_zk_properties.py -v
```

---

## 🤖 AI Integration

Structured endpoints for LLMs and autonomous agents:

```bash
# Verify a proof
curl -X POST http://localhost:8000/ai/verify-proof \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"circuit": "age", "proof": {...}, "public_signals": [...]}'

# Batch verification (up to 100)
curl -X POST http://localhost:8000/ai/verify-proofs-batch \
  -H "X-API-Key: $API_KEY" \
  -d '{"proofs": [...]}'

# Create share link
curl -X POST http://localhost:8000/ai/share-link \
  -H "Authorization: Bearer $JWT" \
  -d '{"document_id": "doc_123", "proof_type": "age", "access_level": "PROOF_ONLY"}'
```

---

## 📊 Monitoring

| Endpoint | Purpose |
|----------|---------|
| `GET /health/live` | Kubernetes liveness probe |
| `GET /health/ready` | Readiness probe (checks Neo4j, vkeys) |
| `GET /metrics` | Prometheus metrics |
| `GET /capabilities` | Proof capabilities |

### Performance Targets

| Operation | Target | Measured |
|-----------|--------|----------|
| Share bundle | <200ms | ~150ms |
| Proof verification | <200ms | ~180ms |
| Health check | <50ms | ~20ms |

---

## 📚 Documentation

| Guide | Description |
|-------|-------------|
| [SETUP.md](SETUP.md) | Complete setup instructions |
| [SECURITY.md](SECURITY.md) | Security policy |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [AUDIT.md](AUDIT.md) | Audit checklist |
| [docs/vault-api.md](docs/vault-api.md) | Vault API reference |
| [docs/ai-endpoints.md](docs/ai-endpoints.md) | AI endpoint guide |
| [backend-python/zkp/README.md](backend-python/zkp/README.md) | ZK-SNARK setup |

---

## 🛡️ Security

### Features

- ✅ **JWT/OIDC** — RS256/ES256 with JWKS verification
- ✅ **Rate Limiting** — Redis-backed sliding window
- ✅ **Input Sanitization** — XSS, injection protection
- ✅ **Security Headers** — CSP, HSTS, X-Frame-Options
- ✅ **Encryption** — AES-256-GCM for vault documents
- ✅ **Audit Logging** — Structured security events

### Reporting Vulnerabilities

Email: security@honestly.dev  
See [SECURITY.md](SECURITY.md) for details.

---

## 🏆 What Makes This World-Class

1. **Production-Ready** — Not a prototype; built for real deployments
2. **Privacy-First** — Zero-knowledge proofs for selective disclosure
3. **Enterprise Security** — Rate limiting, sanitization, audit logging
4. **Developer Experience** — Pre-commit hooks, setup scripts, Docker dev
5. **Comprehensive Testing** — Unit, integration, and E2E coverage
6. **Beautiful UI** — Modern glassmorphism design, animations
7. **Extensible** — Modular architecture for custom circuits/features
8. **Well-Documented** — Extensive docs and inline comments

---

## 📄 License

**GNU Affero General Public License v3.0 (AGPL-3.0-only)**

This software is licensed under the GNU Affero General Public License version 3 ONLY, with additional attribution requirements. Key points:

- ✅ Free to use, modify, and distribute
- ✅ Source code must be made available
- ✅ Network use triggers copyleft (AGPL requirement)
- ⚠️ Must include attribution to aresforblue-ai
- ⚠️ Production deployments should publish on-chain proof

See [LICENSE](LICENSE) and [LICENSE-EXTRAS.md](LICENSE-EXTRAS.md) for full terms and additional requirements.

---

<div align="center">

**Built with ❤️ for privacy, security, and trust.**

[⭐ Star on GitHub](https://github.com/aresforblue-ai/honestly) • [🐛 Report Bug](https://github.com/aresforblue-ai/honestly/issues) • [💡 Request Feature](https://github.com/aresforblue-ai/honestly/issues)

</div>
