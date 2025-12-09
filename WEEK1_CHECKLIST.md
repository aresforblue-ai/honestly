# Week 1 Critical Path Checklist

**Goal**: Get ZK proofs working end-to-end (real cryptography, not fallbacks)
**Time Required**: 25-35 hours (one focused week)
**Blockers Removed**: 5 critical issues preventing production use

---

## 🔥 PRIORITY 1: ZK Circuit Compilation (BLOCKING EVERYTHING)

**Time**: 8-16 hours (mostly waiting for compilation)
**Why**: Without `.zkey` files, all proofs are in fallback mode (not cryptographically verified)

### Steps

```bash
# 1. Navigate to ZK directory
cd backend-python/zkp

# 2. Set Node memory (circuits are large)
export NODE_OPTIONS="--max-old-space-size=8192"

# 3. Install dependencies if not already done
npm install

# 4. Compile Level3Inequality circuit (for reputation proofs)
npm run build:level3

# Expected output:
# [SNARK] Compiling circuit...
# [SNARK] Writing r1cs...
# [SNARK] Writing wasm...
# [SNARK] Compilation successful

# 5. Generate proving key (this takes 5-10 minutes)
npm run setup:level3

# Expected output:
# [SNARK] Generating zkey...
# [SNARK] Contribution 1...
# [SNARK] Contribution 2...
# [SNARK] zkey generated: artifacts/level3_inequality_final.zkey

# 6. Extract verification key
npm run vk:level3

# Expected output:
# [SNARK] Extracting verification key...
# [SNARK] Written to: artifacts/verification_key.json

# 7. Test it works
npm run test

# Expected output:
# ✓ Circuit compiles
# ✓ Proof generation works
# ✓ Proof verification works
```

### Verify Success

```bash
# Check that .zkey file was created
ls -lh artifacts/level3_inequality_final.zkey

# Should show file ~10-50 MB in size
# If file doesn't exist, compilation failed
```

### If It Fails

**Error: "Out of memory"**
```bash
# Increase Node memory even more
export NODE_OPTIONS="--max-old-space-size=16384"
# Try again
```

**Error: "circom: command not found"**
```bash
# Install circom
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
cargo install --path circom
```

**Error: "snarkjs not found"**
```bash
# Install globally
npm install -g snarkjs
```

---

## 🔴 PRIORITY 2: Fix AgentCapability Circuit

**Time**: 4-8 hours
**Why**: Security vulnerability - agents can claim false capabilities
**File**: `backend-python/zkp/circuits/agent_capability.circom`

### Current Code (Line 58):

```circom
// VULNERABLE: Commitment check commented out
// The commitment should match (this is checked externally for now)
// In production, would constrain: agentHasher.out === agentCommitment
```

### Fixed Code:

```circom
// SECURE: Enforce identity commitment in circuit
component identityCheck = IsEqual();
identityCheck.in[0] <== agentHasher.out;
identityCheck.in[1] <== agentCommitment;
identityCheck.out === 1;  // This MUST be true for proof to verify
```

### Complete Fix

1. Open `backend-python/zkp/circuits/agent_capability.circom`
2. Find line ~58 (the commented section)
3. Replace with secure constraint above
4. Recompile circuit:

```bash
cd backend-python/zkp
npm run build:capability
npm run setup:capability
npm run vk:capability
```

5. Update tests to verify constraint works:

```python
# In backend-python/identity/tests/test_aaip_zkp.py
def test_capability_proof_rejects_wrong_commitment():
    """Ensure circuit enforces identity binding"""
    # Try to generate proof with wrong commitment
    # Should FAIL to generate valid proof
    # (Circuit constraint makes it impossible)
```

---

## 🟠 PRIORITY 3: Remove Mock Data from GraphQL

**Time**: 2-4 hours
**Why**: GraphQL returns fake data, not real database queries
**File**: `backend-graphql/src/graphql/resolvers.js`

### Current Code (Lines 4-30):

```javascript
// MOCK DATA - NOT REAL
const mockApps = [
  {
    id: "1",
    name: "SecureVault",
    trustScore: 95,
    // ... hardcoded fake data
  },
  // ...
];
```

### Fixed Code:

```javascript
// REAL DATA from Neo4j
const resolvers = {
  Query: {
    apps: async (_, { filter }) => {
      const session = driver.session();
      try {
        const result = await session.run(
          `MATCH (app:Application)
           WHERE ($category IS NULL OR app.category = $category)
           RETURN app {
             .id,
             .name,
             .category,
             trustScore: app.trust_score,
             verificationStatus: app.verification_status,
             lastAudited: app.last_audited
           }
           ORDER BY app.trust_score DESC
           LIMIT 20`,
          { category: filter?.category || null }
        );
        return result.records.map(r => r.get('app'));
      } finally {
        await session.close();
      }
    },

    app: async (_, { id }) => {
      const session = driver.session();
      try {
        const result = await session.run(
          `MATCH (app:Application {id: $id})
           OPTIONAL MATCH (app)-[:HAS_CLAIM]->(claim)
           OPTIONAL MATCH (app)<-[:REVIEWS]-(review)
           RETURN app, collect(claim) AS claims, collect(review) AS reviews`,
          { id }
        );
        if (result.records.length === 0) return null;
        const record = result.records[0];
        const app = record.get('app').properties;
        app.claims = record.get('claims').map(c => c.properties);
        app.reviews = record.get('reviews').map(r => r.properties);
        return app;
      } finally {
        await session.close();
      }
    }
  }
};
```

### Steps

1. Open `backend-graphql/src/graphql/resolvers.js`
2. Delete lines 4-30 (mockApps array)
3. Add Neo4j driver import at top:
```javascript
const { driver } = require('../config/database');
```
4. Replace resolver functions with real queries above
5. Test with GraphQL playground:
```graphql
query {
  apps {
    id
    name
    trustScore
  }
}
```

---

## 🟠 PRIORITY 4: Implement Hash Lookup

**Time**: 2 hours
**Why**: Endpoint returns 501 Not Implemented
**File**: `backend-python/api/ai_agents.py` (Line 175)

### Current Code:

```python
elif request.document_hash:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Hash lookup not implemented"
    )
```

### Fixed Code:

```python
elif request.document_hash:
    # Look up agent by document hash
    result = await neo4j_service.run_query(
        """
        MATCH (agent:AIAgent)-[:HAS_DOCUMENT]->(doc:Document)
        WHERE doc.hash = $hash
        RETURN agent {
            .agent_id,
            .name,
            .operator_id,
            .operator_name,
            .capabilities,
            .reputation_score,
            .created_at,
            .updated_at
        }
        """,
        {"hash": request.document_hash}
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No agent found with document hash: {request.document_hash}"
        )

    agent = result[0]["agent"]
    return AgentResponse(**agent)
```

### Steps

1. Open `backend-python/api/ai_agents.py`
2. Find line 175 (the 501 error)
3. Replace with code above
4. Test with curl:
```bash
curl -X POST http://localhost:8000/api/v1/ai/agents/lookup \
  -H "Content-Type: application/json" \
  -d '{"document_hash": "abc123..."}'
```

---

## 🟡 PRIORITY 5: Security Hardening

**Time**: 4-8 hours
**Why**: Production safety, remove TODOs, fix placeholder code

### Fix 1: User Validation (auth.py:331)

**Current**:
```python
# TODO: Replace with actual user validation
pass
```

**Fixed**:
```python
# Validate user exists and token is valid
result = await neo4j_service.run_query(
    """
    MATCH (u:User {user_id: $user_id})
    WHERE u.active = true
    RETURN u
    """,
    {"user_id": user_id}
)

if not result:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid user or inactive account"
    )

return result[0]["u"].get("user_id")
```

### Fix 2: Production Secrets (docker-compose.yml)

**Current**:
```yaml
NEO4J_PASS: test
POSTGRES_PASSWORD: honestly123
```

**Fixed**:
```yaml
# Use environment variables, not hardcoded values
NEO4J_PASS: ${NEO4J_PASSWORD:-changeme}
POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-changeme}
```

Then create `.env` file (DO NOT COMMIT):
```bash
NEO4J_PASSWORD=<random-32-char-string>
POSTGRES_PASSWORD=<random-32-char-string>
JWT_SECRET=<random-64-char-string>
```

Generate random secrets:
```bash
# Linux/Mac
openssl rand -hex 32

# Or Python
python -c "import secrets; print(secrets.token_hex(32))"
```

### Fix 3: Error Handling (Remove bare `pass` statements)

Search for all files with bare `pass`:
```bash
cd backend-python
grep -rn "except.*:\s*pass" --include="*.py"
```

Replace each with proper error handling:
```python
# BAD
try:
    do_something()
except Exception:
    pass  # Silent failure, impossible to debug

# GOOD
except Exception as e:
    logger.error(f"Failed to do_something: {e}", exc_info=True)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal error processing request"
    )
```

---

## ✅ Verification Tests

After completing all 5 priorities, run these tests:

### Test 1: ZK Proof End-to-End

```bash
cd backend-python
python -c "
from identity.ai_agent_protocol import register_ai_agent, get_agent_reputation

# Register agent
agent = register_ai_agent(
    name='test-agent',
    operator_id='test',
    operator_name='Test Operator',
    model_family='transformer',
    capabilities=['test'],
    constraints=[]
)

# Generate ZK proof
rep = get_agent_reputation(agent['agent_id'], threshold=40)

# Verify it's REAL cryptographic proof, not fallback
assert 'fallback' not in rep['circuit'], 'Still using fallback mode!'
assert rep['zk_verified'] == True, 'ZK verification failed!'
assert rep['nullifier'] is not None, 'No nullifier generated!'

print('✅ ZK proofs working correctly!')
"
```

### Test 2: GraphQL Real Data

```bash
# Start backend
cd backend-graphql
npm start

# In another terminal, test query
curl -X POST http://localhost:4000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ apps { id name trustScore } }"}'

# Should return real data from Neo4j, not mockApps
```

### Test 3: Hash Lookup

```bash
curl -X POST http://localhost:8000/api/v1/ai/agents/lookup \
  -H "Content-Type: application/json" \
  -d '{"document_hash": "test123"}'

# Should return 404 (not found) instead of 501 (not implemented)
```

### Test 4: Security Audit

```bash
cd backend-python/tests/security
python3 security_audit.py http://localhost:8000

# Check report for criticals
cat security_audit_report.json | grep '"severity": "CRITICAL"'

# Should have 0 critical vulnerabilities
```

---

## 📊 Success Criteria

After Week 1, you should have:

- ✅ Real Groth16 ZK proofs generating (not fallback mode)
- ✅ Proof generation time < 5 seconds
- ✅ GraphQL returning real Neo4j data
- ✅ All API endpoints returning proper status codes (no 501s)
- ✅ No bare `pass` statements in error handling
- ✅ Production secrets in `.env`, not hardcoded
- ✅ Security audit showing 0 critical vulnerabilities

---

## 🚨 If You Get Stuck

### Circuit Compilation Issues
- Check Node version: `node --version` (need v16+)
- Increase memory: `export NODE_OPTIONS="--max-old-space-size=16384"`
- Try on a different machine (compilation is memory-intensive)

### Neo4j Connection Issues
- Verify Neo4j is running: `docker ps | grep neo4j`
- Check credentials match in `.env`
- Test connection: `curl http://localhost:7474`

### Import Errors
- Reinstall deps: `pip install -r backend-python/requirements.txt`
- Check Python version: `python --version` (need 3.9+)

---

## 📅 Time Budget

| Priority | Time | When |
|----------|------|------|
| P1: Compile circuits | 8-16h | Mon-Tue |
| P2: Fix capability circuit | 4-8h | Wed |
| P3: Remove mock data | 2-4h | Thu AM |
| P4: Hash lookup | 2h | Thu PM |
| P5: Security hardening | 4-8h | Fri |
| Testing & verification | 4h | Fri PM |
| **TOTAL** | **25-35h** | **1 week** |

---

## 🎯 What This Unlocks

Once Week 1 is complete, you can:

✅ Record demo video (real ZK proofs on camera)
✅ Apply for grants (working prototype, not vaporware)
✅ Deploy to production (no critical blockers)
✅ Tweet @AnthropicAI with working Claude agent identity
✅ Post to Hacker News / Reddit with confidence

**You're 1 focused week away from having fundable infrastructure. Let's go! 🚀**
