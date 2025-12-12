# Dependency Audit Report
**Date:** 2025-12-12
**Project:** Honestly - Privacy-preserving identity verification

## Executive Summary

This audit analyzed all dependencies across the project's multiple packages (Node.js, Python, Rust) for security vulnerabilities, outdated packages, and unnecessary bloat.

### Key Findings
- ✅ **No critical security vulnerabilities** in production dependencies
- ⚠️ **6 high-severity vulnerabilities** in bridge package (dev dependencies)
- 📦 **21 outdated packages** in conductme frontend
- 🔄 **Major version updates available** for React, Next.js, and other core libraries
- 📊 **Heavy ML dependencies** that could be optimized for production

---

## 1. Security Vulnerabilities

### 🔴 HIGH PRIORITY - Bridge Package (`conductme/bridge`)
**Status:** 6 high-severity vulnerabilities found

| Package | Severity | Issue | CVE |
|---------|----------|-------|-----|
| `snarkjs` | High | Double spend vulnerability | [GHSA-xp5g-jhg3-3rg2](https://github.com/advisories/GHSA-xp5g-jhg3-3rg2) |
| `@semaphore-protocol/core` | High | Indirect via @zk-kit/artifacts | - |
| `@semaphore-protocol/proof` | High | Indirect via circomkit | - |
| `@zk-kit/artifacts` | High | Indirect via circomkit | - |
| `circomkit` | High | Chain dependency issue | - |
| `circom_tester` | High | Uses vulnerable snarkjs ≤0.6.11 | - |

**Impact:** The vulnerability chain originates from an old version of snarkjs (≤0.6.11) in nested dependencies. The Semaphore protocol packages use circomkit, which depends on circom_tester with the vulnerable snarkjs version.

**Recommendation:**
```bash
cd conductme/bridge
npm audit fix
```
This should update to safe versions. Verify Semaphore protocol functionality after update.

### ✅ Other Packages - No Vulnerabilities
- **conductme**: 0 vulnerabilities (582 dependencies scanned)
- **cli**: 0 vulnerabilities (65 dependencies scanned)
- **backend-python/zkp**: 0 vulnerabilities (104 dependencies scanned)
- **backend-solana**: No lockfile (needs initialization)
- **backend-python/blockchain/contracts**: No lockfile (needs initialization)

---

## 2. Outdated Packages

### Frontend (`conductme`) - 21 Outdated Packages

#### Critical Updates (Breaking Changes Expected)

| Package | Current | Wanted | Latest | Priority |
|---------|---------|--------|--------|----------|
| `next` | 14.2.35 | 14.2.35 | **16.0.10** | HIGH |
| `react` | 18.3.1 | 18.3.1 | **19.2.3** | HIGH |
| `react-dom` | 18.3.1 | 18.3.1 | **19.2.3** | HIGH |
| `date-fns` | 3.0.0 | 3.6.0 | **4.1.0** | MEDIUM |
| `recharts` | 2.10.0 | 2.15.4 | **3.5.1** | MEDIUM |
| `cmdk` | 0.2.1 | 0.2.1 | **1.1.1** | MEDIUM |
| `tailwind-merge` | 2.2.1 | 2.6.0 | **3.4.0** | LOW |

**Notes:**
- **React 19** includes major breaking changes (new compiler, hooks changes)
- **Next.js 16** is a major version jump (currently on 14)
- These updates require careful testing and may need code refactoring

#### Minor/Patch Updates (Safe to Update)

| Package | Current | Latest |
|---------|---------|--------|
| `@radix-ui/react-*` (10 packages) | Various | All have patch updates available |
| `lucide-react` | 0.456.0 | 0.561.0 |
| `@solana/web3.js` | 1.87.0 | 1.98.4 |

### Python (`backend-python`) - Analyzed Versions

| Package | Version | Status | Notes |
|---------|---------|--------|-------|
| `fastapi` | 0.115.5 | ✅ Secure | 0 CVEs in 2025 |
| `py2neo` | 2021.2.4 | ⚠️ EOL | **END OF LIFE** - No security updates |
| `kafka-python` | 2.0.2 | ✅ Secure | No CVEs (server CVEs don't apply) |
| `torch` | ≥2.0.0 | ⚠️ Heavy | Large dependency for production |
| `sentence-transformers` | 3.1.1 | ⚠️ Heavy | Large dependency for production |
| `faiss-cpu` | 1.8.0.post1 | ✅ Current | Latest available |

### ZKP Circuits (`backend-python/zkp`)

| Package | Current | Latest |
|---------|---------|--------|
| `commander` | 11.0.0 | **14.0.2** |
| `snarkjs` | 0.7.5 | 0.7.5 (current) |
| `circomlibjs` | 0.1.7 | 0.1.7 (current) |

---

## 3. Unnecessary Bloat & Optimization Opportunities

### 🔴 CRITICAL - Duplicate `@solana/web3.js`
**Issue:** Package appears in 2 locations with same version
- `conductme/package.json` - version ^1.87.0
- `backend-solana/package.json` - version ^1.87.0

**Recommendation:** Consider monorepo structure or shared dependencies to avoid duplication.

### 🟡 MEDIUM - Heavy ML Dependencies (Production)

The project includes heavy ML libraries that may not be needed in all deployments:

**Current Setup:**
- `requirements.txt`: Includes torch, sentence-transformers, faiss-cpu (~2GB+)
- `requirements-prod.txt`: Excludes heavy ML deps (lightweight)
- `requirements-cpu.txt`: Includes CPU-only versions

**Files Using ML Dependencies:**
1. `/backend-python/ml/autoencoder.py` - LSTM autoencoder (torch)
2. `/backend-python/vector_index/faiss_index.py` - Vector search (faiss)
3. `/backend-python/ingestion/kafka_consumer.py` - Uses faiss index
4. `/backend-python/api/app.py` - Initializes faiss index

**Usage Analysis:**
- ML features have **graceful fallbacks** (statistical methods if torch unavailable)
- Imports are **conditional** with try/except blocks
- Production could use `requirements-prod.txt` for faster cold starts

**Recommendation:**
```python
# Current approach is good - keep conditional imports
# Use requirements-prod.txt for Cloud Run deployments
# Add ML deps only when anomaly detection is actually needed
```

### 🟢 LOW - Multiple Package Managers

**Current State:**
- 7 separate `package.json` files across the monorepo
- No workspace configuration (npm/yarn/pnpm workspaces)
- Potential for version conflicts

**Recommendation:** Consider using npm workspaces:
```json
// Root package.json
{
  "workspaces": [
    "conductme",
    "cli",
    "backend-solana",
    "backend-python/zkp",
    "backend-python/blockchain/contracts",
    "conductme/bridge"
  ]
}
```

### 🟢 LOW - Missing Lock Files

**Missing in:**
- `backend-solana/` (no package-lock.json)
- `backend-python/blockchain/contracts/` (no package-lock.json)

**Recommendation:**
```bash
cd backend-solana && npm install --package-lock-only
cd backend-python/blockchain/contracts && npm install --package-lock-only
```

### 🟡 MEDIUM - EOL Dependencies

**`py2neo` version 2021.2.4**
- **Status:** END OF LIFE (no longer maintained)
- **Security:** 0 current CVEs, but won't receive future patches
- **Recommendation:** Migrate to official Neo4j Python driver

**Migration Path:**
```python
# Current (py2neo)
from py2neo import Graph
graph = Graph("bolt://localhost:7687", auth=("neo4j", "password"))

# Recommended (neo4j official driver)
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
```

---

## 4. Recommendations Summary

### Immediate Actions (High Priority)

1. **Fix Bridge Vulnerabilities**
   ```bash
   cd conductme/bridge
   npm audit fix
   npm test  # Verify functionality
   ```

2. **Create Missing Lock Files**
   ```bash
   cd backend-solana && npm install --package-lock-only
   cd backend-python/blockchain/contracts && npm install --package-lock-only
   ```

3. **Update Safe Patches** (conductme)
   ```bash
   cd conductme
   npm update @radix-ui/react-avatar @radix-ui/react-dialog \
     @radix-ui/react-dropdown-menu @radix-ui/react-label \
     @radix-ui/react-select @radix-ui/react-separator \
     @radix-ui/react-slot @radix-ui/react-tabs \
     @radix-ui/react-toast @radix-ui/react-tooltip \
     lucide-react @solana/web3.js
   ```

### Medium-Term Actions (2-4 weeks)

4. **Plan React 19 Migration**
   - Review [React 19 migration guide](https://react.dev/blog/2024/12/05/react-19)
   - Test in development environment
   - Update components for new compiler

5. **Plan Next.js 16 Migration**
   - Review [Next.js upgrade guide](https://nextjs.org/docs/app/building-your-application/upgrading)
   - Test App Router changes
   - Update middleware and API routes

6. **Migrate from py2neo to neo4j driver**
   - Install: `pip install neo4j>=5.0.0`
   - Refactor graph database queries
   - Update tests

7. **Update ZKP Commander**
   ```bash
   cd backend-python/zkp
   npm update commander@14
   ```

### Long-Term Optimizations (1-3 months)

8. **Implement npm Workspaces**
   - Consolidate package management
   - Reduce duplicate dependencies
   - Improve build performance

9. **Optimize Production Dependencies**
   - Continue using `requirements-prod.txt` for Cloud Run
   - Add ML dependencies only when needed
   - Consider lazy-loading heavy modules

10. **Set Up Automated Dependency Scanning**
    ```bash
    # Add to CI/CD pipeline
    npm audit --production
    pip-audit
    ```

---

## 5. Dependency Statistics

### Node.js Ecosystem
- **Total packages:** 7 package.json files
- **Total dependencies:** ~1,300+ across all packages
- **Vulnerabilities:** 6 (all in one package, fixable)
- **Outdated:** 21 packages in conductme

### Python Ecosystem
- **Main dependencies:** 18 packages (requirements.txt)
- **Production deps:** 10 packages (requirements-prod.txt)
- **Vulnerabilities:** 0 current CVEs
- **EOL packages:** 1 (py2neo)

### Rust Ecosystem
- **Solana program:** 4 dependencies (Cargo.toml)
- **Versions:** Using Anchor 0.29.0, Solana 1.18.0
- **Status:** Current and secure

---

## 6. Cost-Benefit Analysis

### High ROI (Do First)
- Fix bridge vulnerabilities: **5 min effort, eliminates 6 CVEs**
- Create lock files: **2 min effort, ensures reproducible builds**
- Update safe patches: **10 min effort, gets latest bug fixes**

### Medium ROI (Plan Carefully)
- React/Next.js upgrade: **2-3 days effort, future-proofs codebase**
- Migrate py2neo: **1-2 days effort, ensures long-term support**
- npm workspaces: **1 day effort, improves dev workflow**

### Low ROI (Nice to Have)
- Optimize ML deps: **Already optimized with fallbacks**
- Update commander: **Breaking changes, low impact**

---

## Appendix: Security Research Sources

### Python Dependencies
- [py2neo Security Analysis - Snyk](https://snyk.io/advisor/python/py2neo)
- [kafka-python Vulnerability Database - OSV](https://osv.dev/vulnerability/GHSA-5w6v-399v-w3cc)
- [FastAPI Security Vulnerabilities - Snyk](https://security.snyk.io/package/pip/fastapi)

### Node.js Dependencies
- [snarkjs Double Spend Vulnerability](https://github.com/advisories/GHSA-xp5g-jhg3-3rg2)
- npm audit reports (run locally for latest)

---

**Report Generated By:** Claude Code Dependency Auditor
**Next Audit Recommended:** 2026-01-12 (30 days)
