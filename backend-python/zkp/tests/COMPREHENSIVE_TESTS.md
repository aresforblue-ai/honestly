# Comprehensive Test Suite Implementation

## Overview

This test suite implements the exact specifications for boundary conditions, overflow protection, leap year handling, and input validation security as requested.

## 1. Boundary Value Analysis

### Implementation
- **Precise calculation**: Uses `minimumAge = 18 * 365.25 * 24 * 60 * 60` seconds
- **Three critical tests**:
  1. Minimum age - 1 second → **FAIL**
  2. Exactly minimum age → **SUCCEED**
  3. Minimum age + 1 second → **SUCCEED**

### What It Verifies
- The `>=` condition is correctly implemented (not `>`)
- Off-by-one errors are prevented
- Circuit correctly enforces `delta >= minAgeSeconds`

### Example Test
```python
reference_date = datetime.datetime(2025, 1, 1)
reference_ts = int(reference_date.timestamp())
min_age_seconds = 18 * 31556952  # Circuit's YEAR_SECONDS

# Test 1: -1 second (FAIL)
birth_ts_fail = reference_ts - min_age_seconds - 1

# Test 2: Exactly (SUCCEED)
birth_ts_exact = reference_ts - min_age_seconds

# Test 3: +1 second (SUCCEED)
birth_ts_pass = reference_ts - min_age_seconds + 1
```

## 2. Overflow Protection

### Implementation
- **Field element tests**: Uses BN254 field modulus `(p-1) = 21888242871839275222246405745257275088548364400416034343698204186575808495616`
- **Attack vectors tested**:
  1. Nonsensically large field element as birth date
  2. Nonsensically large field element as reference date
  3. Field element wrap-around attacks
  4. 32-bit and 64-bit integer limits

### What It Verifies
- Circuit's arithmetic doesn't "wrap around" with extreme values
- Large field elements don't cause false positives
- Input validation rejects nonsensical values

### Example Test
```python
FIELD_MODULUS_MINUS_1 = "21888242871839275222246405745257275088548364400416034343698204186575808495616"

# Attack: Max field element as birth date
overflow_attack = {
    "birthTs": FIELD_MODULUS_MINUS_1,  # Max field element
    "referenceTs": str(reference_ts),
    "minAge": "1",
    ...
}
# Should FAIL: birthTs > referenceTs check
```

## 3. Leap Year Handling

### Implementation
- **Specific edge cases**:
  1. Birth Feb 29, reference Feb 28 (one day short) → **FAIL**
  2. Birth Feb 29, reference Mar 1 (on/after birthday) → **SUCCEED**
  3. Multiple leap year transitions
  4. Century year edge cases (1900 not leap, 2000 leap)

### What It Verifies
- Unix timestamps correctly handle leap years
- Circuit's average year length (31556952 seconds) works correctly
- Feb 29 birthdays are handled properly

### Example Test
```python
# Test: Birth Feb 29, 2004, reference Feb 28, 2022 (one day short)
birth_feb29_2004 = int(datetime.datetime(2004, 2, 29).timestamp())
reference_feb28_2022 = int(datetime.datetime(2022, 2, 28).timestamp())
# Should FAIL: one day short of 18 years

# Test: Birth Feb 29, 2004, reference Mar 1, 2022 (on/after birthday)
reference_mar1_2022 = int(datetime.datetime(2022, 3, 1).timestamp())
# Should SUCCEED: on/after 18th birthday
```

## 4. Input Validation & Security

### Implementation
- **Merkle proof security tests**:
  1. Merkle proof for leaf not in tree → **FAIL**
  2. Path indices out of bounds (999, etc.) → **FAIL**
  3. Path indices with invalid values (2, 3, etc.) → **FAIL**
  4. Wrong number of path elements → **FAIL**
  5. Empty path elements → **FAIL**

### What It Verifies
- Core security assumption: can't prove membership for non-members
- Path indices must be 0 or 1 only
- Proof structure must be correct
- Active tampering is detected

### Example Test
```python
# Test: Fake leaf not in tree
fake_leaf_input = {
    "leafHex": "0000000000000000000000000000000000000000000000000000000000000000",
    "rootHex": "feedface...",
    "pathElementsHex": [...],
    "pathIndices": [0, 1, 0, 1, ...]
}
# Should FAIL: leaf doesn't match root

# Test: Invalid path indices
invalid_indices = {
    ...
    "pathIndices": [999, 0, 1, 2, ...]  # First index is 999 (invalid)
}
# Should FAIL: path indices must be 0 or 1
```

## Test Execution

```bash
cd backend-python/zkp
npm run test
```

## Expected Results

All tests should pass:
- ✅ Boundary tests: Correct pass/fail at exact boundaries
- ✅ Overflow tests: Large values handled correctly or safely rejected
- ✅ Leap year tests: All date combinations handled correctly
- ✅ Security tests: Tampering and invalid inputs rejected

## Security Guarantees

These tests verify:
1. **No off-by-one errors**: Exact boundaries are enforced correctly
2. **No overflow exploits**: Large values don't cause false positives
3. **Leap year robustness**: All date combinations work correctly
4. **Merkle proof integrity**: Can't prove false membership
5. **Input validation**: Nonsensical inputs are rejected

## Continuous Integration

Add to CI/CD:
```yaml
- name: Test ZK Circuits
  run: |
    cd backend-python/zkp
    npm install
    npm run build:age && npm run setup:age && npm run contribute:age && npm run vk:age
    npm run build:auth && npm run setup:auth && npm run contribute:auth && npm run vk:auth
    npm run test
```

## Notes

- Circuit uses `YEAR_SECONDS = 31556952` (average Gregorian year)
- This is correct for long-term calculations (accounts for 400-year leap cycle)
- Tests use both precise (365.25 days) and circuit values to verify correctness
- Field element tests use actual BN254 field modulus for realistic attack scenarios

