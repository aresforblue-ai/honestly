# Circuit Security Constraints

This document explains the **NEW constraints** added to prevent output manipulation and proof replay attacks.

## Problem: Unconstrained Outputs

### Before (Vulnerable)

The circuits output public signals but didn't constrain them:

```circom
// Age circuit - VULNERABLE
minAgeOut <== minAge;  // Assignment, but no constraint
referenceTsOut <== referenceTs;  // Assignment, but no constraint
documentHashOut <== documentHash;  // Assignment, but no constraint
commitment <== pose.out;  // Assignment, but no constraint
```

**Attack Vector**: An attacker could modify the public signals after proof generation without violating circuit constraints, potentially:
- Changing `minAgeOut` to a different value
- Modifying `referenceTsOut` to an old timestamp
- Altering `documentHashOut` to match a different document
- Manipulating `commitment` to break binding

### After (Secure)

All outputs are now constrained to match inputs/computed values:

```circom
// Age circuit - SECURE
minAgeOut <== minAge;
minAgeOut === minAge;  // CRITICAL: Constraint ensures output matches input

referenceTsOut <== referenceTs;
referenceTsOut === referenceTs;  // CRITICAL: Constraint ensures output matches input

documentHashOut <== documentHash;
documentHashOut === documentHash;  // CRITICAL: Constraint ensures output matches input

commitment === pose.out;  // CRITICAL: Constraint ensures commitment is correctly computed
```

## New Constraints Added

### 1. Output Matching Constraints

**Age Circuit**:
- `minAgeOut === minAge` - Prevents minAge manipulation
- `referenceTsOut === referenceTs` - Prevents timestamp manipulation
- `documentHashOut === documentHash` - Prevents document hash manipulation
- `commitment === pose.out` - Prevents commitment manipulation

**Authenticity Circuit**:
- `rootOut === mp.root` - Prevents root manipulation
- `rootOut === root` - Creates chain: root === mp.root === rootOut
- `leafOut === leaf` - Prevents leaf manipulation

### 2. Nonce/Timestamp Freshness Constraints

**Both Circuits**:
- Added `nonce` input (public signal)
- Added `nonceOut` output (public signal)
- Constraint: `nonceOut === nonce` - Prevents nonce manipulation
- Constraint: `Num2Bits(64)` on nonce - Ensures nonce fits in 64 bits

**Purpose**: Prevent proof replay attacks. Verifier checks `nonceOut` is recent (application-layer).

## Security Guarantees

### Before
- ✅ Circuit enforced age requirement
- ✅ Circuit enforced Merkle tree integrity
- ❌ Outputs could be manipulated
- ❌ No replay prevention

### After
- ✅ Circuit enforced age requirement
- ✅ Circuit enforced Merkle tree integrity
- ✅ **Outputs are cryptographically constrained**
- ✅ **Nonce prevents replay (with application-layer freshness check)**

## Attack Prevention

### Output Manipulation Attack

**Before**: Attacker modifies `minAgeOut` from 18 to 21 after proof generation
- **Result**: Proof still verifies (no constraint violation)

**After**: Attacker tries to modify `minAgeOut`
- **Result**: Proof fails verification (constraint violation: `minAgeOut !== minAge`)

### Proof Replay Attack

**Before**: Attacker reuses old proof with old `referenceTs`
- **Result**: Proof verifies (no freshness check)

**After**: Attacker tries to reuse old proof
- **Result**: Application-layer checks `nonceOut` is recent, rejects old proofs

## Migration Notes

### Breaking Changes

1. **Age Circuit**: Now requires `nonce` input
   - Old proofs won't work with new circuit
   - Must regenerate proofs with nonce

2. **Authenticity Circuit**: Now requires `nonce` input
   - Old proofs won't work with new circuit
   - Must regenerate proofs with nonce

### Application Changes Required

1. **Proof Generation**: Include `nonce` (Unix timestamp) in inputs
2. **Proof Verification**: Check `nonceOut` is recent (e.g., within 1 hour)
3. **Public Signals**: Verify all outputs match expected values

## Example Usage

### Age Proof with Nonce

```javascript
const input = {
    birthTs: "631152000",
    referenceTs: "1733443200",
    minAge: "18",
    documentHashHex: "abc123...",
    salt: "1234567890123456789",
    nonce: Math.floor(Date.now() / 1000).toString()  // NEW: Unix timestamp
};

const proof = await generateProof("age", input);

// Verification
const publicSignals = proof.publicSignals;
const nonceOut = publicSignals[4];  // nonceOut is 5th public signal

// Check freshness (application-layer)
const now = Math.floor(Date.now() / 1000);
const age = now - parseInt(nonceOut);
if (age > 3600) {  // Reject if > 1 hour old
    throw new Error("Proof expired");
}
```

## Testing

New tests verify:
1. Output constraints are enforced (circuit-level)
2. Nonce constraints are enforced (circuit-level)
3. Output manipulation fails (application-layer)
4. Replay attacks fail (application-layer)

See `test_circuits.py` for circuit-level constraint tests.

---

**Last Updated**: 2024-12-19  
**Version**: 2.0.0 (Breaking changes)  
**Security Level**: Enhanced (output constraints + replay prevention)

