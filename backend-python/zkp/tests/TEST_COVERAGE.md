# Comprehensive Test Coverage Documentation

## Overview

This document details the comprehensive test coverage for zkSNARK circuits, ensuring correctness, security, and robustness.

## Test Categories

### 1. Boundary Value Analysis

**Purpose**: Detect off-by-one errors in timestamp arithmetic.

**Tests**:
- ✅ Minimum age - 1 second → **Should FAIL**
- ✅ Exactly minimum age → **Should SUCCEED**
- ✅ Minimum age + 1 second → **Should SUCCEED**

**Why Critical**: 
- Prevents proving false statements by exploiting boundary conditions
- Ensures circuit correctly enforces `delta >= minAgeSeconds`
- Validates that `LessThan(64)` comparator works correctly

**Example**:
```python
# For minAge = 18, YEAR_SECONDS = 31556952
min_age_seconds = 18 * 31556952  # 567,985,136 seconds

# Test cases:
birthTs = 631152000  # Jan 1, 1990
referenceTs_fail = birthTs + min_age_seconds - 1    # 1 second short → FAIL
referenceTs_exact = birthTs + min_age_seconds      # Exactly 18 years → SUCCEED
referenceTs_pass = birthTs + min_age_seconds + 1    # 1 second over → SUCCEED
```

### 2. Integer Overflow/Underflow Protection

**Purpose**: Ensure circuit handles large values correctly and rejects nonsensical inputs.

**Tests**:
- ✅ 32-bit signed integer max (2^31 - 1 = 2,147,483,647)
- ✅ 64-bit integer max (2^63 - 1 = 9,223,372,036,854,775,807)
- ✅ Very large age differences (200+ years)
- ✅ Negative timestamps → **Should FAIL**
- ✅ Nonsensical inputs (birthTs > referenceTs) → **Should FAIL**

**Why Critical**:
- Prevents integer overflow from causing false positives
- Ensures circuit constraints (64-bit) are properly enforced
- Validates that `Num2Bits(64)` prevents overflow
- Rejects malicious inputs that could exploit arithmetic

**Circuit Protection**:
```circom
// Circuit uses 64-bit constraints
component deltaBits = Num2Bits(64);
deltaBits.in <== delta;  // Enforces delta fits in 64 bits
```

### 3. Leap Year/Day Edge Cases

**Purpose**: Verify circuit handles leap years correctly using average year length.

**Tests**:
- ✅ Birth on Feb 29, 2000 (leap year)
- ✅ Reference on Feb 29, 2024 (leap year)
- ✅ Feb 28 (non-leap) to Feb 29 (leap)
- ✅ Feb 29 (leap) to Feb 28 (non-leap)
- ✅ Multiple leap years in calculation (2000-2024)
- ✅ Century years (1900 not leap, 2000 leap)

**Why Critical**:
- Circuit uses average year length (31556952 seconds/year)
- This is correct for long-term calculations
- Tests ensure no edge cases cause failures
- Validates that Unix timestamps handle leap years correctly

**Circuit Design**:
```circom
var YEAR_SECONDS = 31556952; // Average seconds per Gregorian year
// This accounts for leap years over long periods
```

**Leap Year Facts**:
- Every 4 years is a leap year (2000, 2004, 2008, ...)
- Century years are NOT leap unless divisible by 400 (1900 no, 2000 yes)
- Average year length ≈ 365.25 days = 31,556,952 seconds

### 4. Valid Proof Tests

**Purpose**: Ensure legitimate proofs generate and verify correctly.

**Tests**:
- ✅ Standard age proofs (25 years proving >= 18)
- ✅ Exactly minimum age proofs
- ✅ Large age differences
- ✅ Various timestamp combinations

### 5. Invalid Proof Tests

**Purpose**: Ensure circuit rejects invalid inputs.

**Tests**:
- ✅ Birth date after reference date
- ✅ Age below minimum threshold
- ✅ Zero age (same timestamps)
- ✅ Wrong Merkle root
- ✅ Wrong leaf hash
- ✅ Invalid path indices

### 6. Security/Integrity Tests

**Purpose**: Verify cryptographic integrity.

**Tests**:
- ✅ Proof tampering detection
- ✅ Public signal tampering detection
- ✅ Verification integrity checks

## Test Execution

Run all tests:
```bash
cd backend-python/zkp
npm run test
```

Run specific test category:
```python
python3 tests/test_circuits.py
# Modify main() to call specific test functions
```

## Expected Results

All tests should pass:
- ✅ Valid proofs: Generate and verify successfully
- ✅ Invalid proofs: Rejected during generation
- ✅ Boundary tests: Correct pass/fail at boundaries
- ✅ Overflow tests: Handled correctly or safely rejected
- ✅ Leap year tests: All pass (circuit uses average year)
- ✅ Security tests: Tampering detected

## Circuit Robustness

The age circuit is designed to be robust:

1. **64-bit constraints** prevent overflow
2. **Average year length** handles leap years correctly
3. **Strict comparisons** prevent off-by-one errors
4. **Poseidon commitments** ensure cryptographic integrity

## Continuous Integration

These tests should run in CI/CD:
- On every commit
- Before releases
- After circuit changes
- With different Powers of Tau files

## Reporting Issues

If any test fails:
1. Check circuit compilation
2. Verify Powers of Tau file
3. Check input format
4. Review circuit constraints
5. Check for circuit bugs

