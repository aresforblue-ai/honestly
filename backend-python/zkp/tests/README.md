# ZK-SNARK Circuit Test Suite

Comprehensive test suite for validating zkSNARK circuit correctness, security, and edge cases.

## Test Coverage

### ✅ Valid Proofs
- Age proofs with various valid inputs
- Authenticity proofs with valid Merkle paths
- Edge cases (minimum age, maximum timestamps, etc.)

### ❌ Invalid Proofs (Should Fail)
- **Age Circuit:**
  - Birth date after reference date (negative age)
  - Age below minimum threshold
  - Zero age (same timestamps)
  - Exactly 1 day short of minimum age

- **Authenticity Circuit:**
  - Wrong Merkle root (double-spend equivalent)
  - Wrong leaf hash
  - Invalid path indices (out of range)

### 🔒 Security Tests
- Proof tampering detection
- Public signal tampering detection
- Verification integrity checks

### 📊 Boundary Value Analysis
- **Minimum age - 1 second** (should fail)
- **Exactly minimum age** (should succeed)
- **Minimum age + 1 second** (should succeed)
- Tests for off-by-one errors in timestamp arithmetic

### 🔢 Integer Overflow/Underflow Protection
- **32-bit signed integer max** (2^31 - 1)
- **64-bit integer max** (2^63 - 1)
- **Very large age differences** (200+ years)
- **Negative timestamps** (should fail)
- **Nonsensical inputs** (birth after reference)

### 🗓️ Leap Year/Day Edge Cases
- **Birth on Feb 29** (leap year)
- **Reference on Feb 29** (leap year)
- **Feb 28 to Feb 29** (non-leap to leap)
- **Feb 29 to Feb 28** (leap to non-leap)
- **Multiple leap years** in age calculation
- **Century years** (1900 not leap, 2000 leap)
- Tests that circuit handles leap years correctly using average year length

## Running Tests

### Prerequisites

1. **Build circuits:**
   ```bash
   cd backend-python/zkp
   npm install
   
   # Download Powers of Tau
   curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau \
     -o artifacts/common/pot16_final.ptau
   
   # Build and setup circuits
   npm run build:age
   npm run setup:age
   npm run contribute:age
   npm run vk:age
   
   npm run build:auth
   npm run setup:auth
   npm run contribute:auth
   npm run vk:auth
   ```

2. **Run tests:**
   ```bash
   # Python test suite
   npm run test
   
   # Or directly
   python3 tests/test_circuits.py
   
   # Full test suite (includes shell checks)
   npm run test:all
   ```

## Test Structure

### `test_circuits.py`
Main test suite that:
- Tests valid proof generation and verification
- Tests invalid inputs (should fail)
- Tests edge cases
- Tests proof integrity (tampering detection)

### `test_merkle_tree.py`
Merkle tree construction utilities for authenticity circuit tests.

### `run_tests.sh`
Shell script that checks prerequisites and runs the full test suite.

## Expected Results

All tests should pass:
- ✅ Valid proofs generate successfully
- ✅ Valid proofs verify successfully
- ✅ Invalid proofs are rejected during generation
- ✅ Tampered proofs fail verification
- ✅ Edge cases handled correctly

## Example Test Output

```
======================================================================
ZK-SNARK CIRCUIT TEST SUITE
======================================================================

======================================================================
AGE CIRCUIT - VALID PROOFS
======================================================================

✓ Testing: Valid age proof (25 years, >= 18)
  ✓ Proof generated successfully
  ✓ Verifying: Verify valid age proof
  ✓ Verification passed

✓ Testing: Edge case: exactly minimum age
  ✓ Proof generated successfully

======================================================================
AGE CIRCUIT - INVALID PROOFS (SHOULD FAIL)
======================================================================

✓ Testing (should fail): Invalid: birth date after reference date
  ✓ Correctly rejected invalid input

✓ Testing (should fail): Invalid: age below minimum (0.9 years < 18)
  ✓ Correctly rejected invalid input

======================================================================
TEST SUMMARY
======================================================================
Total tests: 15
Passed: 15
Failed: 0
======================================================================
```

## Security Considerations

These tests verify that:
1. **Circuits reject invalid inputs** - Prevents proving false statements
2. **Proofs cannot be tampered with** - Cryptographic integrity
3. **Edge cases are handled** - No unexpected behavior
4. **Verification is strict** - Only valid proofs pass

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
- name: Test ZK Circuits
  run: |
    cd backend-python/zkp
    npm install
    npm run build:age && npm run setup:age && npm run contribute:age && npm run vk:age
    npm run build:auth && npm run setup:auth && npm run contribute:auth && npm run vk:auth
    npm run test
```

## Troubleshooting

### "Runner not found"
Build the circuits first (see Prerequisites).

### "Circuit not built"
Run the build and setup commands for the specific circuit.

### "Proof generation fails"
Check that:
- Input data is valid JSON
- All required fields are present
- Values are within expected ranges
- Circuit artifacts exist

### "Verification fails"
Ensure:
- Proof was generated with the same circuit
- Verification key matches the proving key
- Public signals are correct
- Proof hasn't been tampered with

