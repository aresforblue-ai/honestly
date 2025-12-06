# Circuit-Level Constraint Tests

This document explains the circuit-level constraint tests that verify R1CS constraints are properly enforced by the zkSNARK circuits themselves, not just application-layer validation.

## Why Circuit-Level Tests Matter

Application-layer validation can be bypassed. Circuit-level constraints cannot. These tests verify that:

1. **The R1CS constraints themselves enforce correctness** - Even if someone bypasses application validation, the circuit will reject invalid proofs
2. **Mathematical guarantees** - The constraints encode mathematical properties that must hold
3. **Security guarantees** - These are cryptographic guarantees, not just code checks

## Age Circuit Constraints

### Constraint 1: `referenceTs > birthTs`

**Circuit Implementation**:
```circom
component ltTime = LessThan(64);
ltTime.in[0] <== birthTs;
ltTime.in[1] <== referenceTs;
ltTime.out === 1;  // This constraint MUST be satisfied
```

**Test**: `test_circuit_level_constraints_age()` - Test 1
- **Input**: `birthTs = 1733443200`, `referenceTs = 631152000` (violates constraint)
- **Expected**: Circuit constraint violation (R1CS unsatisfiable)
- **Guarantee**: Even if application validation is bypassed, circuit rejects invalid timestamp order

### Constraint 2: `delta >= minAgeSeconds`

**Circuit Implementation**:
```circom
signal delta;
delta <== referenceTs - birthTs;
signal minAgeSeconds;
minAgeSeconds <== minAge * YEAR_SECONDS;
component ageOk = LessThan(64);
ageOk.in[0] <== minAgeSeconds;
ageOk.in[1] <== deltaPlusOne;
ageOk.out === 1;  // This constraint MUST be satisfied
```

**Test**: `test_circuit_level_constraints_age()` - Test 2
- **Input**: `delta = 100 seconds`, `minAge = 18 years` (~568M seconds)
- **Expected**: Circuit constraint violation (ageOk.out cannot be 1)
- **Guarantee**: Circuit enforces age requirement mathematically

### Constraint 3: `delta fits in 64 bits`

**Circuit Implementation**:
```circom
component deltaBits = Num2Bits(64);
deltaBits.in <== delta;
```

**Test**: `test_circuit_level_constraints_age()` - Test 3
- **Input**: `delta = 2^64 + 1` (overflows 64 bits)
- **Expected**: Circuit constraint violation (Num2Bits cannot represent value)
- **Guarantee**: Prevents integer overflow attacks

## Authenticity Circuit Constraints

### Constraint 1: `root === mp.root`

**Circuit Implementation**:
```circom
component mp = MerklePath(depth);
// ... compute root ...
rootOut <== mp.root;
root === mp.root;  // This constraint MUST be satisfied
```

**Test**: `test_circuit_level_constraints_authenticity()` - Test 1
- **Input**: Wrong root that doesn't match computed Merkle path root
- **Expected**: Circuit constraint violation (root !== mp.root)
- **Guarantee**: Circuit enforces Merkle tree integrity

### Constraint 2: Path indices affect Merkle computation

**Circuit Implementation**:
```circom
left <== (1 - pathIndices[i]) * hash + pathIndices[i] * pathElements[i];
right <== pathIndices[i] * hash + (1 - pathIndices[i]) * pathElements[i];
```

**Test**: `test_circuit_level_constraints_authenticity()` - Test 2
- **Input**: Non-binary path indices (e.g., 2, 3 instead of 0, 1)
- **Expected**: Wrong Merkle path computation, root mismatch
- **Guarantee**: Circuit enforces correct Merkle path structure

### Constraint 3: Merkle path computation structure

**Circuit Implementation**:
```circom
component p = Poseidon(2);
p.inputs[0] <== left;
p.inputs[1] <== right;
hash <== p.out;
```

**Test**: `test_circuit_level_constraints_authenticity()` - Test 3
- **Input**: Wrong path elements (all zeros)
- **Expected**: Computed root doesn't match provided root
- **Guarantee**: Circuit enforces correct Merkle path computation

## How to Verify Circuit-Level Enforcement

When a test fails at the circuit level, you should see errors like:

- `"Error: Error: Error: Invalid witness generated"`
- `"Error: Constraint doesn't match"`
- `"Error: R1CS constraint not satisfied"`
- `"Error: Witness generation failed"`

These indicate the circuit itself rejected the input, not just the application layer.

## Application-Layer vs Circuit-Level

| Test Type | What It Tests | Can Be Bypassed? |
|-----------|---------------|------------------|
| Application-Layer | Input validation, format checks | Yes (if code is modified) |
| Circuit-Level | R1CS constraint satisfaction | No (cryptographic guarantee) |

## Running Circuit-Level Tests

```bash
cd backend-python/zkp/tests
python3 test_circuits.py
```

Look for tests prefixed with `CIRCUIT-LEVEL CONSTRAINT TESTS` in the output.

## Security Implications

These circuit-level tests verify that:

1. **Even if an attacker bypasses application validation**, the circuit will reject invalid proofs
2. **The mathematical properties are enforced cryptographically**, not just by code
3. **The security guarantees hold even if the application code is compromised**

This is the difference between "secure code" and "cryptographically secure proofs."

---

**Last Updated**: 2024-12-19  
**Test Coverage**: Age circuit (3 constraints), Authenticity circuit (3 constraints)

