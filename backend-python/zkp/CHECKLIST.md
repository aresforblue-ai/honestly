# Nullifier Implementation Checklist

## ✅ Completed

- [x] **Circuits updated** - Added nullifier pattern to age and authenticity circuits
- [x] **snark-runner.js updated** - Added nullifier to public signals list
- [x] **Nullifier storage (Python)** - Implemented `nullifier_storage.py` with Redis/in-memory support
- [x] **zk_proofs.py updated** - Added epoch support and nullifier extraction
- [x] **AUDIT.md updated** - Added artifact hash instructions and public signal order

## ⚠️ Remaining Tasks

### 1. Rebuild Circuits

**Status**: ⚠️ **REQUIRED** - Circuits must be rebuilt with new nullifier constraints

**Steps**:
```bash
cd backend-python/zkp

# Install dependencies
npm install

# Download Powers of Tau
mkdir -p artifacts/common
curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau \
  -o artifacts/common/pot16_final.ptau

# Build Age Circuit
npm run build:age
npm run setup:age
npm run contribute:age
npm run vk:age

# Build Authenticity Circuit
npm run build:auth
npm run setup:auth
npm run contribute:auth
npm run vk:auth
```

**See**: `REBUILD_CIRCUITS.md` for detailed instructions

### 2. Compute Artifact Hashes

**Status**: ⚠️ **REQUIRED** - After rebuilding, compute SHA256 checksums

**Steps**:
```bash
cd backend-python/zkp

# Linux/macOS
sha256sum artifacts/common/pot16_final.ptau
sha256sum artifacts/age/age.r1cs
sha256sum artifacts/age/age_final.zkey
sha256sum artifacts/age/verification_key.json
sha256sum artifacts/authenticity/authenticity.r1cs
sha256sum artifacts/authenticity/authenticity_final.zkey
sha256sum artifacts/authenticity/verification_key.json

# Windows PowerShell
Get-FileHash artifacts\common\pot16_final.ptau -Algorithm SHA256
Get-FileHash artifacts\age\age.r1cs -Algorithm SHA256
# ... etc
```

**Update**: Fill in checksums in `AUDIT.md`

### 3. Update Sample Input Files

**Status**: ⚠️ **REQUIRED** - Update sample input files with epoch

**Files to update**:
- `backend-python/zkp/samples/age-input.sample.json` - Add `epoch` field
- `backend-python/zkp/samples/authenticity-input.sample.json` - Add `salt` and `epoch` fields

**Example**:
```json
// age-input.sample.json
{
  "birthTs": "631152000",
  "referenceTs": "1733443200",
  "minAge": "18",
  "documentHashHex": "abcdef0123456789...",
  "salt": "1234567890123456789",
  "epoch": "0"  // NEW
}
```

### 4. Configure Redis (Production)

**Status**: ⚠️ **RECOMMENDED** - For production deployment

**Steps**:
1. Install Redis: `pip install redis`
2. Set environment variable: `REDIS_URL=redis://localhost:6379/0`
3. Verify connection: `redis-cli ping`

**Note**: In-memory storage works for development but not recommended for production

### 5. Update Application Code

**Status**: ⚠️ **REQUIRED** - Update code that calls proof generation/verification

**Changes needed**:
1. Add `epoch` parameter to proof generation calls
2. Extract `nullifier` from proof results
3. Use nullifier storage in verification
4. For authenticity: Check epoch freshness

**Example**:
```python
from vault.zk_proofs import ZKProofService
from vault.nullifier_storage import get_nullifier_storage

zk_service = ZKProofService()

# Generate proof with epoch
proof = zk_service.generate_age_proof(
    birth_date="2000-01-01",
    min_age=18,
    document_hash="abc123...",
    epoch=0  # NEW
)

# Verify proof (automatically checks nullifier)
verified = zk_service.verify_age_proof(
    proof_data=proof["proof_data"],
    check_nullifier=True  # NEW
)
```

### 6. Test Nullifier Functionality

**Status**: ⚠️ **REQUIRED** - Verify nullifier prevents replay

**Test cases**:
1. Generate proof → Verify succeeds
2. Verify same proof again → Should fail (nullifier already used)
3. Generate new proof → Verify succeeds (different nullifier)
4. For authenticity: Test epoch freshness enforcement

**Run tests**:
```bash
cd backend-python/zkp/tests
python3 test_circuits.py
```

### 7. Update Documentation

**Status**: ✅ **DONE** - Documentation created

**Files created**:
- `NULLIFIER_PATTERN.md` - Nullifier pattern explanation
- `EPOCH_DESIGN.md` - Epoch visibility design decisions
- `REBUILD_CIRCUITS.md` - Rebuild instructions
- `CIRCUIT_SECURITY_CONSTRAINTS.md` - Security constraints documentation

## Summary

| Task | Status | Priority |
|------|--------|----------|
| Rebuild circuits | ⚠️ Required | **HIGH** |
| Compute artifact hashes | ⚠️ Required | **HIGH** |
| Update sample inputs | ⚠️ Required | **MEDIUM** |
| Configure Redis | ⚠️ Recommended | **MEDIUM** |
| Update application code | ⚠️ Required | **HIGH** |
| Test nullifier | ⚠️ Required | **HIGH** |
| Documentation | ✅ Done | - |

---

**Last Updated**: 2024-12-19  
**Next Step**: Rebuild circuits (see `REBUILD_CIRCUITS.md`)

