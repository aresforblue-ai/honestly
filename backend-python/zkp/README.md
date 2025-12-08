# Honestly ZK-SNARK kit

Groth16 + Circom/snarkjs pipeline for fast (<1s) verification and QR-friendly payloads. Circuits cover:

- `age`: prove birth timestamp is at least `minAge` years before a reference timestamp, and bind to the document hash via a Poseidon commitment.
- `authenticity`: Poseidon Merkle inclusion proof for a document hash.
- `age_level3` / `Level3Inequality`: extended/nullifier-aware variants (rebuild artifacts if you change these circuits).

## Layout

- `circuits/age.circom`, `circuits/authenticity.circom`
- `snark-runner.js`: thin CLI for proving/verifying (Node + snarkjs + circomlibjs)
- `artifacts/`: place compiled wasm/zkey/vkey outputs here
- `package.json`: dependencies + helper scripts

## Quick start (age + authenticity)

```bash
cd backend-python/zkp
npm install
# Get a ptau (example: powers of tau 16); adjust size to your tree depth/constraints
curl -L https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau

# Build circuits
npx circom circuits/age.circom --r1cs --wasm --sym -o artifacts/age
npx circom circuits/authenticity.circom --r1cs --wasm --sym -o artifacts/authenticity

# Groth16 setup
npx snarkjs groth16 setup artifacts/age/age.r1cs artifacts/common/pot16_final.ptau artifacts/age/age_0000.zkey
npx snarkjs zkey contribute artifacts/age/age_0000.zkey artifacts/age/age_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/age/age_final.zkey artifacts/age/verification_key.json

# Repeat for authenticity
npx snarkjs groth16 setup artifacts/authenticity/authenticity.r1cs artifacts/common/pot16_final.ptau artifacts/authenticity/authenticity_0000.zkey
npx snarkjs zkey contribute artifacts/authenticity/authenticity_0000.zkey artifacts/authenticity/authenticity_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/authenticity/authenticity_final.zkey artifacts/authenticity/verification_key.json
```

## Rebuild (all circuits, including nullifier/level3)

You can use npm scripts already defined in `package.json`:

```bash
cd backend-python/zkp
npm install
# Download ptau once (mirror that works in CI)
curl -L https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau

# Compile
npm run build:age
npm run build:auth
npm run build:age-level3
npm run build:inequality-level3

# Groth16 setup
npm run setup:age
npm run setup:auth
npm run setup:age-level3
npm run setup:inequality-level3

# Contribute + export vkeys
npm run contribute:age && npm run vk:age
npm run contribute:auth && npm run vk:auth
npm run contribute:age-level3 && npm run vk:age-level3
npm run contribute:inequality-level3 && npm run vk:inequality-level3
npm run hash:vkeys
python scripts/verify_key_integrity.py   # refresh INTEGRITY.json + *.sha256
```

Artifacts land under `artifacts/<circuit>/` (wasm/zkey/vkey). Regenerate proofs after rebuilding.

Alternatively, from repo root:

```bash
make zkp-rebuild
```

## Prove/verify via runner

```bash
# Prove (reads JSON from file/stdin)
node snark-runner.js prove age --input-file ./samples/age-input.sample.json > ./samples/age-proof.sample.json

# Verify
node snark-runner.js verify age --proof-file ./samples/age-proof.sample.json
```

Input format for age (all numbers as decimal strings):

```json
{
  "birthTs": "631152000",          // private
  "referenceTs": "1733443200",     // public (usually issuance time)
  "minAge": "18",                  // public
  "documentHashHex": "ab12...ff",  // public Poseidon input (hex SHA-256)
  "salt": "1234567890123456789"    // private; optional (auto-generated if missing)
}
```

Authenticity input (Poseidon Merkle, depth 16 by default):

```json
{
  "leafHex": "ab12...ff",
  "rootHex": "cd34...ee",
  "pathElementsHex": ["..."],   // length = DEPTH
  "pathIndices": [0,1,...]      // 0 = leaf on left, 1 = leaf on right
}
```

## Poseidon hashing helper

To match circuit commitments/nullifiers off-chain:

```bash
# CSV inputs (decimal or 0x)
node poseidon-hash.js --inputs 1,2,3

# Or from stdin JSON array
echo '["0x01","0x02","0x03"]' | node poseidon-hash.js
```

## ⚡ Circom Optimization Flags

Level 3 verifiers (verifying level 2 proofs) explode constraints via pairing checks and Poseidon hashes. Use aggressive optimizations:

```
┌──────┬───────────────────────────────┬──────────────────────┬──────────────┐
│ Flag │ Use Case                      │ Constraint Reduction │ Compile Time │
├──────┼───────────────────────────────┼──────────────────────┼──────────────┤
│ -O2  │ Production (required)         │ ~73% vs -O0          │ ~2x longer   │
│ -O1  │ Development (if -O2 chokes)   │ ~40%                 │ ~1.5x        │
│ -O0  │ Debug only                    │ None                 │ Fast         │
└──────┴───────────────────────────────┴──────────────────────┴──────────────┘
```

**Always use `-O2` for production builds** (per ZCLS benchmarks on Groth16 rollups).

### C++ Witness Generation (Required for Large Circuits)

WASM witness gen OOMs on Level 3 circuits (1M+ constraints → 16-64GB RAM). Use C++ witness generator instead:

```bash
# Production build with C++ witness generator (recommended for Level 3)
npx circom circuits/age_level3.circom \
  --r1cs --sym -O2 \
  --c \
  -o artifacts/age_level3 \
  -l node_modules

# Compile the C++ witness generator
cd artifacts/age_level3/age_level3_cpp
make

# Use C++ witness gen instead of WASM
./age_level3 input.json witness.wtns
```

### Memory Settings

For large circuits, crank Node heap and use parallel compilation:

```bash
# Set before compilation/proving
export NODE_OPTIONS="--max-old-space-size=16384"  # 16GB heap

# For extreme cases (recursive verifiers)
export NODE_OPTIONS="--max-old-space-size=32768"  # 32GB heap

# Parallel constraints (circom 2.1.6+)
npx circom ... --parallel 4
```

### Full Production Build Stack

```bash
# Level 3 circuits - full optimization stack
npx circom circuits/age_level3.circom \
  --r1cs --sym -O2 \
  --c \                              # C++ witness (no WASM OOM)
  --parallel 4 \                     # Parallel compilation
  -o artifacts/age_level3 \
  -l node_modules

# Compile C++ witness generator
cd artifacts/age_level3/age_level3_cpp && make && cd ../../..

# Development fallback (if -O2 is too slow)
npx circom circuits/age_level3.circom --r1cs --wasm --sym -O1 -o artifacts/age_level3 -l node_modules
```

### Constraint Counts (with `-O2`)

```
┌─────────────────────┬────────────────┬──────────┬─────────────────────────────────┐
│ Circuit             │ Raw Constraints│ With -O2 │ Notes                           │
├─────────────────────┼────────────────┼──────────┼─────────────────────────────────┤
│ age                 │ ~8K            │ ~3K      │ Simple, WASM OK                 │
│ authenticity        │ ~12K           │ ~4K      │ Simple, WASM OK                 │
│ age_level3          │ ~50K           │ ~14K     │ Use C++ witness                 │
│ level3_inequality   │ ~45K           │ ~12K     │ Use C++ witness                 │
│ Recursive verifier  │ 1M+            │ ~300K    │ C++ witness + 32GB heap required│
└─────────────────────┴────────────────┴──────────┴─────────────────────────────────┘
```

**Quick Reference:**
```bash
# Memory settings by circuit type
export NODE_OPTIONS="--max-old-space-size=4096"   # Simple (age, auth)
export NODE_OPTIONS="--max-old-space-size=16384"  # Level 3
export NODE_OPTIONS="--max-old-space-size=32768"  # Recursive verifiers
```

---

## 🔄 CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/zkp.yml`) handles automated builds:

**Triggers:**
- Push to `main`/`develop` (circuit changes only)
- Weekly schedule (Sunday 2am UTC) - integrity audit
- Manual dispatch with `[rebuild-level3]` commit message

**Jobs:**

```
┌─────────────────────┬─────────────────┬──────────────────────────────────┐
│ Job                 │ Runner          │ Circuits                         │
├─────────────────────┼─────────────────┼──────────────────────────────────┤
│ simple-circuits     │ ubuntu-latest   │ age, authenticity (WASM, -O2)    │
│ level3-circuits     │ ubuntu-latest   │ age_level3, level3_inequality    │
│                     │ + 16GB swap     │ (C++ witness, -O2)               │
│ verify-integrity    │ ubuntu-latest   │ SHA256 hash check + tests        │
│ weekly-audit        │ ubuntu-latest   │ Compare with INTEGRITY.json      │
└─────────────────────┴─────────────────┴──────────────────────────────────┘
```

**Triggering Level 3 rebuilds:**

```bash
# Option 1: Commit message trigger
git commit -m "Update circuits [rebuild-level3]"

# Option 2: Manual dispatch (Actions tab)
# Check "Rebuild Level 3 circuits" checkbox

# Option 3: Automatic on schedule (weekly)
```

**Artifact retention:** 30 days (download from Actions tab)

### Self-Hosted Runners (Recommended for Level 3)

The swap workaround on `ubuntu-latest` works but is slow (~3x longer). For production CI:

**1. Set up a self-hosted runner with 16GB+ RAM:**

```bash
# On your runner machine (Ubuntu 22.04 recommended)
mkdir actions-runner && cd actions-runner
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz
tar xzf ./actions-runner-linux-x64.tar.gz
./config.sh --url https://github.com/YOUR_ORG/honestly --token YOUR_TOKEN --labels self-hosted,linux,x64,16gb
./run.sh
```

**2. Update workflow to use self-hosted:**

```yaml
# .github/workflows/zkp.yml
level3-circuits:
  runs-on: [self-hosted, linux, x64, 16gb]  # Use beefy runner
  env:
    NODE_OPTIONS: "--max-old-space-size=14336"
```

**3. Runner requirements:**

```
┌─────────────────────┬─────────────────────────────────────────────────┐
│ Component           │ Requirement                                     │
├─────────────────────┼─────────────────────────────────────────────────┤
│ RAM                 │ 16GB+ (32GB for recursive verifiers)            │
│ CPU                 │ 4+ cores                                        │
│ Disk                │ 20GB+ free                                      │
│ OS                  │ Ubuntu 22.04 LTS                                │
│ Dependencies        │ Node 20, Rust, build-essential, libgmp-dev      │
└─────────────────────┴─────────────────────────────────────────────────┘
```

**4. GitHub-hosted alternatives:**

| Runner | RAM | Cost | Notes |
|--------|-----|------|-------|
| `ubuntu-latest` | 7GB | Free | Use swap workaround |
| `ubuntu-latest-4-cores` | 16GB | Teams/Enterprise | Good for Level 3 |
| `ubuntu-latest-16-cores` | 64GB | Teams/Enterprise | Recursive verifiers |

---

## ⚡ Rapidsnark Integration

Rapidsnark is a high-performance C++ Groth16 prover from iden3. **5-10x faster than SnarkJS** with sub-8GB RAM for 1M+ constraint circuits.

### When to Use

| Prover | Best For | Speed | Memory |
|--------|----------|-------|--------|
| SnarkJS | Simple circuits (age, auth) | ~5s | 4GB |
| **Rapidsnark** | Level 3, AAIP, recursive | ~2s | 8GB |

### Installation

```bash
# From source (Linux/macOS)
git clone https://github.com/iden3/rapidsnark.git
cd rapidsnark
git submodule init && git submodule update
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
sudo make install

# Verify
rapidsnark --version
```

### Python Integration

The `ZKProofService` automatically uses rapidsnark for Level 3 and AAIP circuits:

```python
from vault.zk_proofs import ZKProofService

zk = ZKProofService()

# Simple circuits → SnarkJS (fast enough)
proof = zk.generate_age_proof(birth_date="1990-01-01", min_age=18, document_hash="0x...")

# Level 3 circuits → Rapidsnark (5-10x faster)
proof = zk.generate_age_level3_proof(birth_date="1990-01-01", min_age=18, document_hash="0x...")

# AAIP circuits → Rapidsnark
proof = zk.generate_agent_reputation_proof(
    reputation_score=75,
    threshold=50,
    agent_did_hash="0x...",
)
```

### CLI Usage

```bash
# Prove with rapidsnark
python rapidsnark_prover.py prove -c age_level3 -i input.json -o proof.json

# Benchmark SnarkJS vs Rapidsnark
python rapidsnark_prover.py benchmark -c age_level3 -i input.json
# Output: ⚡ Speedup: 5.2x faster with Rapidsnark
```

### Environment Variables

```bash
RAPIDSNARK_BIN=/usr/local/bin/rapidsnark  # Path to binary
OMP_NUM_THREADS=8                          # Parallel threads (default: CPU count)
```

### 📊 Benchmark Results

**Hardware**: Intel i9-13900K, 32GB RAM, Ubuntu 22.04, `OMP_NUM_THREADS=8`

```
┌─────────────────────┬──────────────┬──────────────┬─────────────┬───────────┐
│ Circuit             │ SnarkJS      │ Rapidsnark   │ Speedup     │ Memory    │
├─────────────────────┼──────────────┼──────────────┼─────────────┼───────────┤
│ age (simple)        │ 4.2s         │ N/A          │ -           │ 2GB       │
│ authenticity        │ 5.1s         │ N/A          │ -           │ 2GB       │
│ age_level3          │ 12.3s        │ 2.1s         │ 5.9x        │ 6GB       │
│ level3_inequality   │ 11.8s        │ 2.4s         │ 4.9x        │ 6GB       │
│ agent_capability    │ 9.7s         │ 1.8s         │ 5.4x        │ 5GB       │
│ agent_reputation    │ 10.2s        │ 2.0s         │ 5.1x        │ 5GB       │
└─────────────────────┴──────────────┴──────────────┴─────────────┴───────────┘

Average speedup: 5.3x
Verification: <50ms (both backends, cached vkeys)
```

**AMD EPYC (cloud)**: 7-8x speedup with 16+ cores (OMP scales well)

**Batch throughput** (`/ai/verify-proofs-batch`):
- Single 8-core pod: **100+ req/min**
- Rapidsnark server mode (10+ proofs): ~1.5s/proof queued

### 🚀 Production Tips

**Kubernetes Affinity** (pin to high-core nodes):

```yaml
# k8s deployment for ZKP prover pods
spec:
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
        - matchExpressions:
          - key: node.kubernetes.io/instance-type
            operator: In
            values:
            - c6i.4xlarge    # 16 vCPU
            - c6a.4xlarge    # AMD EPYC, 16 vCPU
            - m6i.4xlarge    # 16 vCPU, more RAM
  containers:
  - name: zkp-prover
    resources:
      requests:
        cpu: "8"
        memory: "8Gi"
      limits:
        cpu: "16"
        memory: "16Gi"
    env:
    - name: OMP_NUM_THREADS
      value: "8"
    - name: RAPIDSNARK_BIN
      value: "/usr/local/bin/rapidsnark"
```

**Why not Rapidsnark for simple circuits?**
- SnarkJS bundle: ~1MB (browser-friendly)
- Rapidsnark binary: ~50MB (server-only)
- Simple circuits prove in <5s anyway—not worth the binary size

---

## 🐳 Docker Build

Multi-stage Dockerfile for C++ witness generators (builds native, copies to slim runtime):

```bash
# Build ZKP image with all circuits
docker build -f docker/Dockerfile.zkp -t honestly-zkp .

# Run with resource limits (Level 3 circuits)
docker run --rm \
  --memory=16g \
  --cpus=4 \
  -v zkp_artifacts:/zkp/artifacts \
  honestly-zkp

# Or use docker-compose (recommended)
docker-compose up zkp
```

**docker-compose.yml resource limits:**

```yaml
zkp:
  deploy:
    resources:
      limits:
        memory: 16G    # Level 3 circuits need this
        cpus: '4'
      reservations:
        memory: 8G
        cpus: '2'
  environment:
    - NODE_OPTIONS=--max-old-space-size=16384
```

**Resource requirements by build type:**

```
┌─────────────────────┬──────────┬──────┬─────────────────────────────────┐
│ Build Type          │ Memory   │ CPUs │ Notes                           │
├─────────────────────┼──────────┼──────┼─────────────────────────────────┤
│ Simple circuits     │ 4G       │ 2    │ age, authenticity (WASM)        │
│ Level 3 circuits    │ 16G      │ 4    │ C++ witness, -O2                │
│ Recursive verifiers │ 32G      │ 8    │ C++ witness, -O2, --parallel    │
│ Runtime (API)       │ 8G       │ 2    │ Proving only (pre-built zkeys)  │
└─────────────────────┴──────────┴──────┴─────────────────────────────────┘
```

---

## Notes

- Circuits use Poseidon for constraint efficiency.
- Public signals order matters; the runner returns both the raw `publicSignals` array and a named map.
- If artifacts are missing, the runner returns a clear error directing you to build them.
- Sample inputs/proofs are in `samples/` for quick smoke tests. Replace placeholder vk/proofs with real generated ones for production.
- Heavy circuits (level3) may need a larger Node heap during build/proving: set `NODE_OPTIONS="--max-old-space-size=8192"`; Windows is more likely to need this.
- Property tests: from `backend-python`, run `ZK_TESTS=1 pytest tests/test_zk_properties.py -v` after rebuilding artifacts.
