# Trusted Setup Ceremony Guide

## ⚠️ CRITICAL: Trusted Setup Security

Groth16 requires a trusted setup ceremony. If the setup is compromised, **all proofs can be forged**.

## Option 1: Use Public Powers of Tau (Recommended for MVP)

### Step 1: Download Public Ceremony

```bash
cd backend-python/zkp
mkdir -p artifacts/common

# Download Powers of Tau (16 depth - supports up to 2^16 = 65,536 constraints)
curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau \
  -o artifacts/common/pot16_final.ptau

# Verify download integrity (optional but recommended)
# Check file size: should be ~67MB
ls -lh artifacts/common/pot16_final.ptau
```

### Step 2: Generate Circuit-Specific Setup

```bash
# Build circuit
npm run build:age

# Generate initial zkey (contains toxic waste - DO NOT USE)
npx snarkjs groth16 setup \
  artifacts/age/age.r1cs \
  artifacts/common/pot16_final.ptau \
  artifacts/age/age_0000.zkey

# Contribute randomness (destroys toxic waste)
npx snarkjs zkey contribute \
  artifacts/age/age_0000.zkey \
  artifacts/age/age_final.zkey \
  -n "YourContributionName"

# ⚠️ CRITICAL: DELETE THE TOXIC WASTE
rm artifacts/age/age_0000.zkey

# Export verification key (safe to share)
npx snarkjs zkey export verificationkey \
  artifacts/age/age_final.zkey \
  artifacts/age/verification_key.json
```

### Step 3: Generate Integrity Hash

```bash
python scripts/verify_key_integrity.py generate
```

This creates `verification_key.sha256` files for integrity verification.

## Option 2: Multi-Party Ceremony (Recommended for Production)

### Why Multi-Party?

- **Security**: Requires collusion of all participants to compromise
- **Transparency**: Public ceremony transcript
- **Trust**: Distributed trust model

### Ceremony Process

1. **Initial Setup:**
   ```bash
   # Generate initial zkey (toxic waste)
   npx snarkjs groth16 setup circuit.r1cs pot.ptau circuit_0000.zkey
   ```

2. **Each Participant Contributes:**
   ```bash
   # Participant 1
   npx snarkjs zkey contribute circuit_0000.zkey circuit_0001.zkey -n "Participant1"
   
   # Participant 2 (uses previous contribution)
   npx snarkjs zkey contribute circuit_0001.zkey circuit_0002.zkey -n "Participant2"
   
   # ... continue for N participants
   ```

3. **Finalize:**
   ```bash
   # Last participant finalizes
   npx snarkjs zkey contribute circuit_00N.zkey circuit_final.zkey -n "FinalParticipant"
   
   # ⚠️ CRITICAL: DELETE ALL INTERMEDIATE ZKEYS
   rm circuit_000*.zkey
   
   # Export verification key
   npx snarkjs zkey export verificationkey circuit_final.zkey verification_key.json
   ```

### Ceremony Requirements

- **Minimum Participants**: 3-5 recommended
- **Verification**: Each participant should verify previous contributions
- **Transparency**: Publish ceremony transcript
- **Security**: Each participant must destroy their randomness

## Security Checklist

### ✅ Before Ceremony

- [ ] Verify Powers of Tau source (if using public)
- [ ] Document all participants
- [ ] Set up secure communication channels
- [ ] Prepare verification procedures

### ✅ During Ceremony

- [ ] Verify each contribution before proceeding
- [ ] Document all steps
- [ ] Record timestamps
- [ ] Verify file integrity at each step

### ✅ After Ceremony

- [ ] **CRITICAL**: Delete all intermediate `.zkey` files
- [ ] **CRITICAL**: Verify final zkey doesn't match any intermediate
- [ ] Generate integrity hashes
- [ ] Publish ceremony transcript
- [ ] Store final zkey securely (encrypted if needed)
- [ ] Distribute verification keys

## Verification

### Verify Setup Integrity

```bash
# Check that toxic waste is deleted
find . -name "*_0000.zkey" -o -name "*_0001.zkey"  # Should return nothing

# Verify final zkey exists
ls -lh artifacts/age/age_final.zkey

# Verify verification key integrity
python scripts/verify_key_integrity.py
```

### Test Proof Generation

```bash
# Generate test proof
node snark-runner.js prove age < samples/age-input.sample.json > test_proof.json

# Verify proof
node snark-runner.js verify age < test_proof.json
# Should output: {"verified": true}
```

## Production Recommendations

1. **Use Public Powers of Tau**: Already trusted by many projects
2. **Add Your Contribution**: Adds one layer of security
3. **Document Everything**: Keep ceremony transcript
4. **Verify Integrity**: Always verify keys before use
5. **Rotate Periodically**: Consider re-running ceremony annually

## Emergency Procedures

### If Setup is Compromised

1. **IMMEDIATE**: Stop accepting new proofs
2. **IMMEDIATE**: Revoke all existing proofs
3. **IMMEDIATE**: Generate new setup ceremony
4. **IMMEDIATE**: Notify all users
5. **IMMEDIATE**: Document incident

### Key Recovery

- **Proving Keys**: Cannot be recovered if lost (must regenerate)
- **Verification Keys**: Can be regenerated from proving key
- **Backup**: Store proving keys encrypted in secure location

## References

- [snarkjs Documentation](https://github.com/iden3/snarkjs)
- [Powers of Tau Ceremony](https://github.com/iden3/snarkjs#7-prepare-phase-2)
- [Trusted Setup Best Practices](https://vitalik.ca/general/2022/03/14/trustedsetup.html)

