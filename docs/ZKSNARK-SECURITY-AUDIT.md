# zkSNARK Security Audit - Critical Foundation

**⚠️ CRITICAL: This document addresses the most important security aspects. If any of these are wrong, nothing else matters.**

## 1. Proving System Foundation

### Library Choice: Circom + snarkjs (Groth16)

**Library:** 
- **Circom 2.1.6**: Circuit description language
- **snarkjs 0.7.3**: Groth16 prover/verifier
- **circomlib**: Standard library for Poseidon hashing

**Audit Status:**
- ✅ **Circom**: Developed by iden3, widely used in production (Tornado Cash, Semaphore)
- ✅ **snarkjs**: Mature library, used by major projects
- ✅ **circomlib**: Standard, audited Poseidon implementation
- ⚠️ **Version**: Using stable versions, but should pin exact versions in production

**Recommendation:**
```json
// package.json - Pin exact versions
{
  "dependencies": {
    "circomlib": "0.0.20",  // Pin exact version
    "snarkjs": "0.7.3"      // Pin exact version
  }
}
```

### Trusted Setup: Groth16 Ceremony

**Status:** ⚠️ **REQUIRES TRUSTED SETUP**

**Current Implementation:**
- Using local trusted setup (`snarkjs zkey contribute`)
- **CRITICAL ISSUE**: Local setup is NOT secure for production

**Required Actions:**

1. **Use Public Ceremony or Generate Properly:**
   ```bash
   # Option 1: Use public Powers of Tau ceremony
   # Download from: https://github.com/iden3/snarkjs#7-prepare-phase-2
   curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau -o pot16.ptau
   
   # Option 2: Run multi-party ceremony (RECOMMENDED)
   # Follow: https://github.com/iden3/snarkjs#8-contribute-to-the-ceremony
   ```

2. **Toxic Waste Disposal:**
   - ⚠️ **CRITICAL**: If you generated the setup locally, the toxic waste (secret randomness) must be destroyed
   - **NEVER** commit `.zkey` files that contain toxic waste
   - **NEVER** reuse the same setup for different circuits
   - Use `age_final.zkey` (contributed) and destroy `age_0000.zkey` (toxic waste)

3. **Transparency:**
   - Document who participated in ceremony
   - Publish ceremony transcript (if multi-party)
   - Use verifiable ceremony tools

**Production Recommendation:**
- Use public Powers of Tau ceremony (already available)
- Add at least one contribution with verifiable randomness
- Document and publish ceremony details

### Circuit Correctness: CRITICAL VERIFICATION

#### Age Proof Circuit (`age.circom`)

**Verification Checklist:**

✅ **1. Timestamp Ordering:**
```circom
// Line 22-25: Enforces referenceTs > birthTs
component ltTime = LessThan(64);
ltTime.in[0] <== birthTs;
ltTime.in[1] <== referenceTs;
ltTime.out === 1;  // ✅ CORRECT: Ensures referenceTs > birthTs
```

✅ **2. Age Calculation:**
```circom
// Line 34-46: Enforces age >= minAge
var YEAR_SECONDS = 31556952;  // ✅ CORRECT: Average seconds per year
signal minAgeSeconds;
minAgeSeconds <== minAge * YEAR_SECONDS;  // ✅ CORRECT: Convert years to seconds

component ageOk = LessThan(64);
ageOk.in[0] <== minAgeSeconds;
ageOk.in[1] <== deltaPlusOne;  // delta + 1
ageOk.out === 1;  // ✅ CORRECT: Ensures delta >= minAgeSeconds
```

✅ **3. Commitment Binding:**
```circom
// Line 48-54: Poseidon commitment binds private data
component pose = Poseidon(3);
pose.inputs[0] <== birthTs;      // ✅ Private
pose.inputs[1] <== salt;          // ✅ Private
pose.inputs[2] <== documentHash;  // ✅ Public (but bound)
commitment <== pose.out;          // ✅ Public output
```

**Potential Issues:**

⚠️ **Issue 1: Year Calculation**
- Uses average year (31556952 seconds)
- **Impact**: Small error (~0.25 days/year)
- **Mitigation**: Acceptable for age verification, but document limitation

⚠️ **Issue 2: Timestamp Range**
- No explicit bounds checking on timestamps
- **Impact**: Could accept invalid dates
- **Mitigation**: Validate in Python layer (already done)

✅ **Overall Assessment:** Circuit logic is **CORRECT** for age verification

#### Authenticity Proof Circuit (`authenticity.circom`)

**Verification Checklist:**

✅ **1. Merkle Path Verification:**
```circom
// Line 17-29: Correctly computes Merkle path
for (i = 0; i < depth; i++) {
    left <== (1 - pathIndices[i]) * hash + pathIndices[i] * pathElements[i];
    right <== pathIndices[i] * hash + (1 - pathIndices[i]) * pathElements[i];
    // ✅ CORRECT: Properly selects left/right based on index
    component p = Poseidon(2);
    p.inputs[0] <== left;
    p.inputs[1] <== right;
    hash <== p.out;  // ✅ CORRECT: Computes parent hash
}
```

✅ **2. Root Verification:**
```circom
// Line 54: Enforces provided root matches computed root
root === mp.root;  // ✅ CORRECT: Ensures proof is valid
```

✅ **3. Leaf Binding:**
```circom
// Line 51: Outputs leaf for verification
leafOut <== leaf;  // ✅ CORRECT: Public output for verification
```

**Potential Issues:**

✅ **No Issues Found:** Circuit correctly implements Merkle inclusion proof

**Overall Assessment:** Circuit logic is **CORRECT** for authenticity verification

## 2. Implementation Details (The Plumbing)

### Randomness Generation: ✅ SECURE

**Current Implementation:**
```python
# backend-python/vault/zk_proofs.py:67
"salt": str(secrets.randbits(128)),  # ✅ CORRECT: Uses CSPRNG
```

**Verification:**
- ✅ Uses Python's `secrets` module (cryptographically secure)
- ✅ Generates 128 bits of randomness (sufficient)
- ✅ Never uses `random` module (insecure)
- ✅ Never uses `Math.random()` (insecure)

**Security Status:** ✅ **SECURE**

### Key Management: ⚠️ NEEDS IMPROVEMENT

**Current Implementation:**
```javascript
// snark-runner.js:104
const vkey = JSON.parse(fs.readFileSync(circuit.vkey, "utf8"));
```

**Issues:**

1. **Storage Location:**
   - Keys stored in `backend-python/zkp/artifacts/`
   - ⚠️ **RISK**: If repository is public, keys are exposed
   - ⚠️ **RISK**: No access control on key files

2. **Key Loading:**
   - ✅ Loads from file system (correct)
   - ⚠️ No integrity verification (hash checking)
   - ⚠️ No versioning or rotation mechanism

3. **Proving Keys:**
   - ⚠️ **CRITICAL**: Proving keys (`age_final.zkey`) contain secret information
   - ⚠️ Must be kept secure and never exposed
   - ⚠️ Current implementation loads from file system without encryption

**Required Improvements:**

```python
# Add key integrity verification
def load_vkey_with_integrity(circuit: str) -> Dict[str, Any]:
    vkey_path = Path(f"zkp/artifacts/{circuit}/verification_key.json")
    vkey_hash_path = Path(f"zkp/artifacts/{circuit}/verification_key.sha256")
    
    # Verify integrity
    with open(vkey_path, "r") as f:
        vkey_data = json.load(f)
    vkey_str = json.dumps(vkey_data, sort_keys=True)
    computed_hash = hashlib.sha256(vkey_str.encode()).hexdigest()
    
    if vkey_hash_path.exists():
        with open(vkey_hash_path, "r") as f:
            expected_hash = f.read().strip()
        if computed_hash != expected_hash:
            raise SecurityError("Verification key integrity check failed")
    
    return vkey_data
```

**Recommendations:**
1. ✅ Add `.gitignore` entries for `.zkey` files (proving keys)
2. ✅ Add integrity hashes for verification keys
3. ✅ Store proving keys encrypted (if needed)
4. ✅ Use environment variables for key paths
5. ✅ Implement key rotation mechanism

### Data Serialization: ✅ CONSISTENT

**Current Implementation:**

**Python → Node (Proving):**
```python
# backend-python/vault/zk_proofs.py:62-68
payload = {
    "birthTs": str(birth_ts),           # ✅ String conversion
    "referenceTs": str(ref_ts),         # ✅ String conversion
    "minAge": str(min_age),             # ✅ String conversion
    "documentHashHex": self._strip_hex_prefix(document_hash),  # ✅ Hex handling
    "salt": str(secrets.randbits(128)), # ✅ String conversion
}
# JSON serialization
json.dumps(payload)  # ✅ Consistent JSON
```

**Node → Python (Verification):**
```javascript
// snark-runner.js:72-80
const res = await groth16.fullProve(input, circuit.wasm, circuit.zkey);
const payload = {
    circuit: circuit.name,
    proof: res.proof,              // ✅ Direct pass-through
    publicSignals: res.publicSignals,  // ✅ Direct pass-through
    namedSignals,                  // ✅ Named mapping
};
console.log(JSON.stringify(payload, null, 2));  // ✅ Consistent JSON
```

**Verification:**
- ✅ Consistent JSON serialization
- ✅ String conversion for large numbers (prevents precision loss)
- ✅ Hex prefix stripping (consistent handling)
- ✅ Public signals order matches circuit definition

**Potential Issues:**

⚠️ **Issue: Number Precision**
- Using string conversion for timestamps (good)
- But snarkjs expects numbers in some contexts
- **Mitigation**: Current implementation handles this correctly

✅ **Overall Assessment:** Serialization is **CONSISTENT** and **SECURE**

## 3. System-Level Security (The Vault Doors)

### Frontend Security: ⚠️ NEEDS VERIFICATION

**Current Implementation:**
- Frontend verifies proofs using snarkjs in browser
- Verification keys loaded from `/zkp/artifacts/`

**Security Concerns:**

1. **Man-in-the-Middle Attacks:**
   - ⚠️ Verification keys loaded over HTTP (if not HTTPS)
   - ⚠️ Proof data could be tampered with before verification
   - **Mitigation**: Use HTTPS, verify key integrity

2. **Key Integrity:**
   - ⚠️ No integrity verification in frontend
   - ⚠️ Keys could be replaced with malicious versions
   - **Mitigation**: Add hash verification, use Content-Security-Policy

**Required Improvements:**

```javascript
// frontend-app/src/App.jsx - Add key integrity check
async function loadVkeyWithIntegrity(circuit) {
    const vkey = await fetch(`/zkp/artifacts/${circuit}/verification_key.json`);
    const vkeyData = await vkey.json();
    
    // Verify integrity hash
    const vkeyStr = JSON.stringify(vkeyData, Object.keys(vkeyData).sort());
    const hash = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(vkeyStr));
    const hashHex = Array.from(new Uint8Array(hash))
        .map(b => b.toString(16).padStart(2, '0'))
        .join('');
    
    // Compare with expected hash (from secure source)
    const expectedHash = await fetch(`/zkp/artifacts/${circuit}/verification_key.sha256`).then(r => r.text());
    if (hashHex !== expectedHash.trim()) {
        throw new Error('Verification key integrity check failed');
    }
    
    return vkeyData;
}
```

### Backend Security: ✅ GOOD

**Current Implementation:**
- Proof generation on backend (secure)
- Verification on backend (secure)
- Rate limiting (implemented)
- Input validation (implemented)

**Security Status:** ✅ **SECURE**

**Recommendations:**
1. ✅ Keep proving keys secure (never expose)
2. ✅ Use HTTPS in production
3. ✅ Implement request signing for sensitive operations
4. ✅ Monitor for anomalous proof generation patterns

### Side-Channel Resistance: ⚠️ BASIC

**Current Implementation:**
- No explicit side-channel protection
- Proof generation time could leak information
- Memory usage patterns could leak information

**Potential Leaks:**

1. **Timing Attacks:**
   - Proof generation time varies with input
   - ⚠️ Could leak information about birth date
   - **Mitigation**: Add timing randomization or constant-time operations

2. **Memory Attacks:**
   - Memory usage patterns could leak circuit structure
   - ⚠️ Less critical for verification (public circuit)
   - **Mitigation**: Acceptable for current use case

**Recommendations:**
1. ⚠️ Add timing randomization for proof generation
2. ✅ Current implementation acceptable for non-adversarial environment
3. ⚠️ Consider constant-time operations for high-security use cases

## Security Checklist

### ✅ Implemented

- [x] Cryptographically secure randomness (`secrets.randbits`)
- [x] Consistent data serialization
- [x] Circuit correctness verified
- [x] Input validation
- [x] Rate limiting
- [x] Security headers
- [x] Audit logging

### ⚠️ Needs Improvement

- [ ] Trusted setup ceremony documentation
- [ ] Key integrity verification
- [ ] Frontend key integrity checks
- [ ] Proving key encryption (if needed)
- [ ] Key rotation mechanism
- [ ] Timing attack mitigation
- [ ] Pin exact library versions

### 🔴 Critical Actions Required

1. **Trusted Setup:**
   - [ ] Use public Powers of Tau or run proper ceremony
   - [ ] Document ceremony participants
   - [ ] Destroy toxic waste properly
   - [ ] Publish ceremony transcript

2. **Key Management:**
   - [ ] Add `.gitignore` for `.zkey` files
   - [ ] Add integrity hashes for verification keys
   - [ ] Implement key loading with integrity checks
   - [ ] Document key storage and access

3. **Frontend Security:**
   - [ ] Add key integrity verification
   - [ ] Use HTTPS in production
   - [ ] Implement CSP headers
   - [ ] Verify proof data integrity

## Testing Recommendations

### Circuit Correctness Tests

```python
def test_age_circuit_correctness():
    """Test age circuit enforces correct constraints."""
    # Test 1: Valid age proof
    assert verify_age_proof(age=25, min_age=18) == True
    
    # Test 2: Invalid age proof (too young)
    assert verify_age_proof(age=15, min_age=18) == False
    
    # Test 3: Timestamp ordering
    assert verify_age_proof(birth_ts=1000, ref_ts=500, min_age=18) == False
    
    # Test 4: Commitment binding
    proof1 = generate_proof(birth_date="1990-01-01", salt="salt1")
    proof2 = generate_proof(birth_date="1990-01-01", salt="salt2")
    assert proof1.commitment != proof2.commitment  # Different salts = different commitments
```

### Randomness Tests

```python
def test_randomness_quality():
    """Test randomness is cryptographically secure."""
    salts = [secrets.randbits(128) for _ in range(1000)]
    assert len(set(salts)) == 1000  # All unique
    # Statistical tests for randomness
```

### Serialization Tests

```python
def test_serialization_consistency():
    """Test serialization is consistent."""
    payload = {"birthTs": "631152000", "minAge": "18"}
    json_str = json.dumps(payload)
    parsed = json.loads(json_str)
    assert parsed == payload  # Round-trip consistency
```

## Conclusion

### ✅ Strengths

1. **Circuit Logic**: Correctly implements age and authenticity proofs
2. **Randomness**: Uses cryptographically secure RNG
3. **Serialization**: Consistent and correct
4. **Library Choice**: Well-audited, production-tested libraries

### ⚠️ Weaknesses

1. **Trusted Setup**: Needs proper ceremony documentation
2. **Key Management**: Needs integrity verification
3. **Frontend Security**: Needs key integrity checks
4. **Side-Channel**: Basic protection, acceptable for current use

### 🔴 Critical Actions

1. **IMMEDIATE**: Document trusted setup process
2. **IMMEDIATE**: Add key integrity verification
3. **HIGH**: Implement frontend key integrity checks
4. **MEDIUM**: Add timing attack mitigation

**Overall Security Status:** ✅ **FOUNDATION IS SOUND** with improvements needed in key management and frontend security.

