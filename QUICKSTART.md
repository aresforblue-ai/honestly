# 🚀 Proof-of-Human Quickstart Guide

**Goal: Get the system running in under 30 minutes.**

This guide is designed for the "new hire" test. If anything takes longer than expected or is confusing, please open an issue - we'll fix it.

---

## ⏱️ Time Estimates

| Step | Time |
|------|------|
| Prerequisites | 5 min |
| Clone & Install | 3 min |
| Start Services | 2 min |
| Verify It Works | 5 min |
| Generate Your First Proof | 5 min |
| **Total** | **20 min** |

---

## 📋 Prerequisites

You need these installed:

```bash
# Check if you have them
docker --version      # Need 20.10+
docker-compose --version  # Need 2.0+
node --version        # Need 18+
python --version      # Need 3.10+
```

**Don't have them?**
- Docker: https://docs.docker.com/get-docker/
- Node.js: https://nodejs.org/ (LTS version)
- Python: https://www.python.org/downloads/

---

## 1️⃣ Clone & Install (3 min)

```bash
# Clone the repo
git clone https://github.com/aresforblue-ai/honestly.git
cd honestly

# Install Python dependencies
cd backend-python
pip install -r requirements.txt
cd ..

# Install ZKP dependencies
cd backend-python/zkp
npm install
cd ../..

# Install CLI (optional but recommended)
cd cli
npm install
npm link  # Makes 'honestly' command available globally
cd ..
```

---

## 2️⃣ Start Services (2 min)

**Option A: Minimal Stack (Recommended for first run)**

```bash
# Start only essential services (API + Neo4j)
docker-compose -f docker-compose.min.yml up -d

# Check they're running
docker-compose -f docker-compose.min.yml ps
```

You should see:
```
NAME                STATUS
honestly-api        running (healthy)
honestly-neo4j      running (healthy)
```

**Option B: Full Stack**

```bash
# Start everything (API + Neo4j + Kafka + Redis + Frontend)
docker-compose up -d
```

---

## 3️⃣ Verify It Works (5 min)

### Check API Health

```bash
curl http://localhost:8000/health
```

Expected:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Check GraphQL Playground

Open in browser: http://localhost:8000/graphql

Try this query:
```graphql
{
  __schema {
    types {
      name
    }
  }
}
```

### Check Neo4j (Optional)

Open: http://localhost:7474

Login with:
- Username: `neo4j`
- Password: `honestly123` (or check your `.env`)

---

## 4️⃣ Generate Your First ZK Proof (5 min)

### Using the CLI

```bash
# Generate an age proof (prove you're 18+)
honestly share --age 18 --dob 1995

# You'll see:
# ✓ Proof generated!
# 📋 Proof Details:
#   Type:      age
#   Circuit:   groth16
#   Claim:     Age ≥ 18
# 🔗 Share Link: http://localhost:8000/vault/share/hns_abc123
```

### Using the API Directly

```bash
# Generate proof via API
curl -X POST http://localhost:8000/vault/proof/generate \
  -H "Content-Type: application/json" \
  -d '{
    "proof_type": "age",
    "birth_year": 1995,
    "min_age": 18
  }'
```

### Verify a Proof

```bash
# Verify the proof you just generated
honestly verify --url http://localhost:8000/vault/share/hns_abc123

# Or via API
curl http://localhost:8000/vault/share/hns_abc123/bundle
```

---

## 5️⃣ Run Tests (Optional, 5 min)

```bash
# Run unit tests
pytest tests/unit/ -v

# Run security validation
python backend-python/api/security_checks.py

# Run the full validation suite
make validate  # or: python scripts/generate_validation_report.py
```

---

## 🎯 Quick Commands Reference

```bash
# Start services
docker-compose -f docker-compose.min.yml up -d

# Stop services
docker-compose -f docker-compose.min.yml down

# View logs
docker-compose -f docker-compose.min.yml logs -f api

# Restart API only
docker-compose -f docker-compose.min.yml restart api

# Generate age proof
honestly share --age 18 --dob 1995 --qr

# Verify a proof
honestly verify --url <share-url>

# Run tests
pytest tests/unit/ -v

# Check security config
python backend-python/api/security_checks.py
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=honestly123

# Security (CHANGE IN PRODUCTION!)
JWT_SECRET=your-32-character-secret-key-here

# Optional
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Common Issues

**Port already in use?**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill it or change the port in docker-compose.yml
```

**Neo4j won't start?**
```bash
# Clear Neo4j data and restart
docker-compose down -v
docker-compose up -d
```

**Proof generation fails?**
```bash
# Make sure ZKP artifacts are built
cd backend-python/zkp
npm run build:age
npm run setup:age
npm run contribute:age
npm run vk:age
```

---

## 📚 Next Steps

1. **Read the Architecture**: See `ARCHITECTURE.md` for how it all fits together
2. **Try ConductMe**: The AI orchestration layer at `conductme/`
3. **Run Load Tests**: `make perf-k6` to test performance
4. **Read the Audit Doc**: `AUDIT.md` for security review info

---

## ⏱️ Tracking Your Time

Did you complete this guide in under 30 minutes?

- ✅ Yes → Great! The docs are working.
- ❌ No → Please tell us what took longer:
  - Open an issue: https://github.com/aresforblue-ai/honestly/issues
  - Include: Which step, how long it took, what was confusing

Your feedback makes this better for everyone. Thank you! 🙏

---

## 🆘 Need Help?

- **Discord**: [Join our server](#) (TODO: Add link)
- **GitHub Issues**: https://github.com/aresforblue-ai/honestly/issues
- **Email**: support@proof-of-human.org (TODO: Set up)

---

*Last updated: December 2024*
*Target time: 30 minutes*
*Actual average: [tracking]*

