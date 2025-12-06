# Rebuild Circuits After Nullifier Changes

## ⚠️ Breaking Changes

The circuits have been updated with nullifier patterns. **You must rebuild all circuits** before using them.

## Changes Made

### Age Circuit
- ✅ Added `epoch` input (private)
- ✅ Added `nullifier` output (public)
- ✅ Removed `nonce` input/output

### Authenticity Circuit
- ✅ Added `salt` input (private)
- ✅ Added `epoch` input (public)
- ✅ Added `epochOut` output (public)
- ✅ Added `nullifier` output (public)
- ✅ Removed `nonce` input/output

## Rebuild Steps

### 1. Navigate to ZKP Directory

```bash
cd backend-python/zkp
```

### 2. Install Dependencies (if needed)

```bash
npm install
```

### 3. Download Powers of Tau

```bash
mkdir -p artifacts/common
curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau \
  -o artifacts/common/pot16_final.ptau
```

### 4. Build Age Circuit

```bash
# Compile circuit
npm run build:age

# Setup (creates initial zkey)
npm run setup:age

# Contribute (creates final zkey)
npm run contribute:age

# Export verification key
npm run vk:age
```

### 5. Build Authenticity Circuit

```bash
# Compile circuit
npm run build:auth

# Setup (creates initial zkey)
npm run setup:auth

# Contribute (creates final zkey)
npm run contribute:auth

# Export verification key
npm run vk:auth
```

### 6. Verify Build

```bash
# Check artifacts exist
ls -la artifacts/age/verification_key.json
ls -la artifacts/authenticity/verification_key.json

# Run tests
npm test
```

## Update Application Code

### Proof Generation

**Age Proof** (now requires `epoch`):
```python
input = {
    "birthTs": "631152000",
    "referenceTs": "1733443200",
    "minAge": "18",
    "documentHashHex": "abc123...",
    "salt": str(secrets.randbits(128)),
    "epoch": "0"  # NEW: Private epoch
}
```

**Authenticity Proof** (now requires `salt` and `epoch`):
```python
input = {
    "leafHex": "abc123...",
    "rootHex": "def456...",
    "pathElementsHex": [...],
    "pathIndices": [...],
    "salt": str(secrets.randbits(128)),  # NEW: Private salt
    "epoch": "0"  # NEW: Public epoch
}
```

### Proof Verification

**Age Proof** (extract nullifier):
```python
public_signals = proof["publicSignals"]
nullifier = public_signals[-1]  # Last signal

# Check if nullifier was already used
if nullifier in used_nullifiers:
    return False

# Verify proof
if not verify_proof(proof):
    return False

# Mark nullifier as used
used_nullifiers.add(nullifier)
```

**Authenticity Proof** (extract epoch and nullifier):
```python
public_signals = proof["publicSignals"]
epoch_out = int(public_signals[-2])  # Second-to-last signal
nullifier = public_signals[-1]  # Last signal

# Enforce freshness
if epoch_out < current_epoch:
    return False

# Check if nullifier was already used
epoch_nullifiers = used_nullifiers_by_epoch.get(epoch_out, set())
if nullifier in epoch_nullifiers:
    return False

# Verify proof
if not verify_proof(proof):
    return False

# Mark nullifier as used
epoch_nullifiers.add(nullifier)
used_nullifiers_by_epoch[epoch_out] = epoch_nullifiers
```

## Public Signal Order

### Age Circuit Public Signals

1. `minAgeOut`
2. `referenceTsOut`
3. `documentHashOut`
4. `commitment`
5. `nullifier` ← **NEW**

### Authenticity Circuit Public Signals

1. `rootOut`
2. `leafOut`
3. `epochOut` ← **NEW**
4. `nullifier` ← **NEW**

## Testing

After rebuilding, run the test suite:

```bash
cd backend-python/zkp/tests
python3 test_circuits.py
```

Tests should verify:
- ✅ Nullifier computation is correct
- ✅ Nullifier constraints are enforced
- ✅ Epoch constraints are enforced (authenticity circuit)
- ✅ Output constraints are enforced

## Rollback Plan

If you need to rollback:

1. Revert circuit files to previous version
2. Rebuild circuits
3. Update application code to match old circuit interface

## Notes

- **Breaking Change**: Old proofs won't work with new circuits
- **Storage Required**: Verifier must store used nullifiers (Redis/database)
- **Epoch Management**: Authenticity circuit requires epoch management (increment on document updates)

---

**Last Updated**: 2024-12-19  
**Status**: ⚠️ **REBUILD REQUIRED**

