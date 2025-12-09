# Honestly - Complete Setup Guide

This guide will help you set up the complete Honestly Truth Engine platform with all three components.

## 📋 Prerequisites

### Required Software
- **Node.js** 18.x or higher ([Download](https://nodejs.org/))
- **Python** 3.10 or higher ([Download](https://python.org/))
- **Docker** and **Docker Compose** ([Download](https://docker.com/))
- **Git** ([Download](https://git-scm.com/))

### Optional but Recommended
- **PostgreSQL** 16+ (or use Docker)
- **Neo4j** 5.x (or use Docker)

## 🚀 Quick Start (All Components)

### Step 1: Clone and Setup

```bash
# Clone the repository
git clone https://github.com/aresforblue-ai/honestly.git
cd honestly

# Install all dependencies
make install
```

### Step 2: Start Infrastructure

```bash
# Start Docker services (Neo4j, Kafka, PostgreSQL)
make up

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### Step 3: Initialize Databases

```bash
# Initialize Neo4j schema
docker exec honestly-neo4j cypher-shell -u neo4j -p test < neo4j/init.cypher
docker exec honestly-neo4j cypher-shell -u neo4j -p test < neo4j/vault_init.cypher

# (Optional) Initialize PostgreSQL for GraphQL backend
# If using Prisma:
cd backend-graphql
npm run prisma:migrate
cd ..
```

### Step 4: Configure Environment

```bash
# Frontend
cp frontend-app/.env.example frontend-app/.env

# GraphQL Backend
cp backend-graphql/.env.example backend-graphql/.env

# Python Backend (if needed)
# Edit DATABASE_URL, NEO4J credentials if different
```

### Step 5: Start Development Servers

Open **two separate terminals**:

**Terminal 1 - Python Backend:**
```bash
make dev-backend-py
# or
cd backend-python
uvicorn api.app:app --reload --port 8000
```

**Terminal 2 - ConductMe (AI Orchestration):**
```bash
cd conductme
npm run dev
```

## 🚦 Minimal Stack (simpler dev)
If you just need the Python API + Neo4j without Kafka/Fabric/FAISS:

```bash
docker compose -f docker-compose.min.yml up --build
```

- Backend API: http://localhost:8000 (REST/GraphQL on FastAPI)
- ConductMe: http://localhost:3000
- Neo4j Browser: http://localhost:7474 (bolt://localhost:7687, neo4j/test)

This uses a single compose file and disables the heavier services.

## 🌐 Access Applications

Once all services are running:

- **ConductMe UI**: http://localhost:3000
- **Python REST API**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (user: neo4j, pass: test)

### Environment Hygiene
- `ALLOWED_ORIGINS` (default `http://localhost:5173`) controls CORS for the Python API.
- `ENABLE_CORS=true|false` toggles CORS middleware.
- `STRICT_CORS=true` will require ALLOWED_ORIGINS to be set (fails fast otherwise).
- `RATE_LIMIT_WINDOW`, `RATE_LIMIT_MAX`, `RATE_LIMIT_PATHS` tune public GET rate limiting (defaults cover `/vault/share` and `/zkp/artifacts`).
- `DISABLE_KAFKA`, `DISABLE_FAISS`, `DISABLE_FABRIC` can be set to disable unused services in code paths.
- Verification keys are served from `/zkp/artifacts/...`; replace placeholder files with real generated keys for production.
- Sample zk inputs/proofs live in `backend-python/zkp/samples/` for quick local runs.
- Performance/load: k6 script at `tests/perf/k6-load.js` (target p99 < 200ms). Run with `make perf-k6` and set `BASE_URL`.

### ZK build shortcuts
- `make zkp-build` — builds circuits, zkeys, and exports verification keys (requires circom/snarkjs locally).
- `make zkp-verify` — generates and verifies sample proofs using the sample inputs.

### ZK Circuit Optimization (Important!)

Level 3 circuits use `-O2` optimization + C++ witness generation to avoid WASM OOM:

```bash
# Production builds (C++ witness, -O2 optimization)
npm run build:age-level3           # Outputs C++ witness generator
npm run compile:age-level3:cpp     # Compile the C++ witness gen

# Development builds (WASM, if -O1 is OK)
npm run build:age-level3:dev       # Uses -O1, WASM

# Full optimization for large circuits
export NODE_OPTIONS="--max-old-space-size=16384"  # 16GB heap
npm run build:age-level3
npm run compile:age-level3:cpp
```

**Constraint counts (with `-O2`)**:
| Circuit | Raw | Optimized |
|---------|-----|-----------|
| `age_level3` | ~50K | ~14K |
| `level3_inequality` | ~45K | ~12K |
| Recursive verifier | 1M+ | ~300K |

**Memory requirements**:
- Simple circuits (age, authenticity): 4GB heap, WASM OK
- Level 3 circuits: 16GB heap, C++ witness recommended
- Recursive verifiers: 32GB heap, C++ witness required

## 🔧 Detailed Setup Instructions

### ConductMe Setup (AI Orchestration)

```bash
cd conductme

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build
```

### Python Backend Setup

```bash
cd backend-python

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn api.app:app --reload --port 8000
```

**Environment Variables**:
The Python backend reads from environment or uses defaults. You can set:
```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=test
export KAFKA_BOOTSTRAP=localhost:9092
```

## 🧪 Testing

### Run All Tests

```bash
make test
```

### Test Individual Components

```bash
# ConductMe
cd conductme
npm test

# Python Backend
cd backend-python
pytest
```

## 🐛 Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Check what's using the port
lsof -i :3000  # ConductMe
lsof -i :8000  # Python Backend

# Kill the process or change the port in config
```

### Docker Services Not Starting

```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs

# Restart services
make down
make up
```

### Neo4j Connection Issues

```bash
# Check Neo4j is running
docker ps | grep neo4j

# Access Neo4j browser
open http://localhost:7474

# Check logs
docker logs honestly-neo4j
```

### Database Migrations

If you need to reset the database:

```bash
# Neo4j
docker exec honestly-neo4j cypher-shell -u neo4j -p test "MATCH (n) DETACH DELETE n"
```

## 📦 Production Deployment

### Using Docker

```bash
# Build all containers
docker-compose -f docker-compose.prod.yml build

# Start in production mode
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

1. **ConductMe**: Build and serve static files
   ```bash
   cd conductme
   npm run build
   # Serve the .next/ directory with nginx or similar
   ```

2. **Python Backend**: Run with Gunicorn
   ```bash
   cd backend-python
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.app:app
   ```

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change default database passwords
- [ ] Set `NODE_ENV=production`
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up authentication (JWT tokens)
- [ ] Configure rate limiting
- [ ] Enable logging and monitoring
- [ ] Set up backup strategies
- [ ] Review and update security headers
- [ ] Implement input validation
- [ ] Set up firewall rules

## 📚 Additional Resources

- [ConductMe README](conductme/README.md) - AI orchestration documentation
- [Python Backend README](backend-python/README.md) - Vault API documentation
- [VERIDICUS Solana README](backend-solana/README.md) - Solana program documentation
- [Vault API Docs](docs/vault-api.md) - Complete API reference
- [Architecture Overview](ARCHITECTURE.md) - System architecture

## 🆘 Getting Help

- **Issues**: [GitHub Issues](https://github.com/aresforblue-ai/honestly/issues)
- **Discussions**: [GitHub Discussions](https://github.com/aresforblue-ai/honestly/discussions)
- **Documentation**: [docs/](docs/)

## 📝 Next Steps

1. Explore ConductMe at http://localhost:3000
2. Check the REST API docs at http://localhost:8000/docs
3. Review the documentation in the `docs/` folder
4. Set up VERIDICUS Solana program (optional)
5. Start building your own features!

---

**Happy Building! 🚀**
