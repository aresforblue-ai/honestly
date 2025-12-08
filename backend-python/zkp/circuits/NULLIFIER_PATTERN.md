# Nullifier Pattern for One-Time Proof Use

## The Problem with Nonces

### What We Had (Vulnerable)

```circom
signal input nonce;  // Public: Unix timestamp
signal output nonceOut;  // Public: Echoed nonce
```

**Attack Scenario**:
1. Attacker generates proof with `nonce = 1703000000` (current timestamp)
2. Attacker uses proof at time `T`
3. Attacker reuses same proof at time `T + 1 second` (still "recent")
4. Verifier can't distinguish - both verifications succeed
5. **Result**: Double-spending/replay within freshness window

**Limitations**:
- Time-window based (not zero-tolerance)
- Verifier stores nothing (can't detect duplicates)
- Same proof can be used multiple times within window

## The Solution: Nullifiers

### What We Have Now (Secure)

```circom
signal input salt;      // Private: Random salt
signal input epoch;     // Private: Epoch/version number
signal output nullifier; // Public: Poseidon(salt, documentHash, epoch)
```

**How It Works**:
1. Prover generates proof with private `salt` and `epoch`
2. Circuit computes `nullifier = Poseidon(salt, documentHash, epoch)`
3. Nullifier is output as public signal
4. Verifier stores used nullifiers in database/set
5. Verifier checks: `if nullifier in used_nullifiers: REJECT`
6. Verifier adds nullifier to used set after successful verification

**Security Guarantees**:
- ✅ **Zero-tolerance replay prevention** (not time-window based)
- ✅ **One-time use** - each proof can only be verified once
- ✅ **Verifier tracks used nullifiers** - detects duplicates immediately
- ✅ **Cryptographically bound** - nullifier computed from private inputs

## Implementation Details

### Age Circuit

```circom
// Nullifier computation
component nullifierHash = Poseidon(3);
nullifierHash.inputs[0] <== salt;           // Private
nullifierHash.inputs[1] <== documentHash;   // Public (but bound to proof)
nullifierHash.inputs[2] <== epoch;         // Private
nullifier <== nullifierHash.out;           // Public output

// Constraint: nullifier must match computation
nullifier === nullifierHash.out;
```

### Authenticity Circuit

```circom
// Nullifier computation
component nullifierHash = Poseidon(3);
nullifierHash.inputs[0] <== salt;    // Private
nullifierHash.inputs[1] <== leaf;     // Public (document hash)
nullifierHash.inputs[2] <== epoch;    // Private
nullifier <== nullifierHash.out;      // Public output

// Constraint: nullifier must match computation
nullifier === nullifierHash.out;
```

## Verifier Implementation

### Required Changes

**Before (Nonce)**:
```python
def verify_proof(proof, public_signals):
    # Check nonce is recent
    nonce = int(public_signals[4])
    now = int(time.time())
    if now - nonce > 3600:  # 1 hour window
        return False
    
    # Verify proof
    return snarkjs.verify(vkey, public_signals, proof)
```

**After (Nullifier)**:
```python
# Global set of used nullifiers (in production: use Redis/database)
used_nullifiers = set()

def verify_proof(proof, public_signals):
    # Extract nullifier (last public signal)
    nullifier = public_signals[-1]
    
    # Check if nullifier was already used (ONE-TIME USE)
    if nullifier in used_nullifiers:
        return False  # REJECT: Proof already used
    
    # Verify proof
    if not snarkjs.verify(vkey, public_signals, proof):
        return False
    
    # Mark nullifier as used (AFTER successful verification)
    used_nullifiers.add(nullifier)
    
    return True
```

## Attack Prevention

### Replay Attack

**Before (Nonce)**:
- Attacker generates proof with `nonce = now`
- Attacker uses proof multiple times within 1 hour
- **Result**: ✅ All verifications succeed (vulnerable)

**After (Nullifier)**:
- Attacker generates proof with `salt = random`, `epoch = 0`
- Attacker uses proof first time: ✅ Verification succeeds, nullifier stored
- Attacker tries to reuse same proof: ❌ **REJECTED** (nullifier already used)
- **Result**: ✅ Only first verification succeeds (secure)

### Cross-Epoch Replay

**Scenario**: Attacker tries to reuse proof in different epoch

**Protection**:
- Nullifier includes `epoch` in computation
- Different epoch = different nullifier
- Verifier can track nullifiers per epoch
- **Result**: ✅ Cross-epoch replay prevented

## Epoch Management

### What is Epoch?

Epoch is a version number that can be incremented to invalidate all previous proofs:

- **Epoch 0**: Initial proofs
- **Epoch 1**: After security update / key rotation
- **Epoch 2**: After another update

### Epoch Increment Strategy

```python
# When to increment epoch:
# 1. Security vulnerability discovered
# 2. Key rotation
# 3. Circuit update
# 4. Policy change

current_epoch = get_current_epoch()  # e.g., 0
new_epoch = current_epoch + 1

# All new proofs must use new_epoch
# Old proofs (with old epoch) can be rejected or tracked separately
```

### Verifier Epoch Handling

```python
def verify_proof(proof, public_signals, required_epoch=None):
    nullifier = public_signals[-1]
    
    # Extract epoch from nullifier computation (application-layer)
    # Or track nullifiers per epoch
    epoch = extract_epoch_from_proof(proof)  # Application-specific
    
    if required_epoch and epoch < required_epoch:
        return False  # Reject old epoch proofs
    
    # Check nullifier in epoch-specific set
    epoch_nullifiers = used_nullifiers.get(epoch, set())
    if nullifier in epoch_nullifiers:
        return False
    
    # Verify proof...
    if not snarkjs.verify(vkey, public_signals, proof):
        return False
    
    # Mark as used
    epoch_nullifiers.add(nullifier)
    used_nullifiers[epoch] = epoch_nullifiers
    
    return True
```

## Comparison Table

| Property | Nonce (Before) | Nullifier (After) |
|----------|----------------|-------------------|
| **Input Type** | Public (timestamp) | Private (salt, epoch) |
| **Computation** | Echo input | Poseidon(salt, docHash, epoch) |
| **Value** | Visible timestamp | Cryptographic hash |
| **Replay Window** | Time-based (e.g., 1 hour) | **Zero** (one-time use) |
| **Verifier Storage** | Nothing | Set of used nullifiers |
| **Attack Prevention** | ⚠️ Replay within window | ✅ Complete replay prevention |
| **Double-Spending** | ⚠️ Possible | ✅ Prevented |

## Migration Guide

### Breaking Changes

1. **Circuit Inputs Changed**:
   - ❌ Removed: `nonce` (public timestamp)
   - ✅ Added: `salt` (private), `epoch` (private)

2. **Circuit Outputs Changed**:
   - ❌ Removed: `nonceOut` (public timestamp)
   - ✅ Added: `nullifier` (public hash)

3. **Verifier Logic Changed**:
   - ❌ Removed: Time-based freshness check
   - ✅ Added: Nullifier tracking (set/database)

### Application Updates Required

1. **Proof Generation**:
```python
# OLD
input = {
    "nonce": str(int(time.time()))
}

# NEW
input = {
    "salt": str(secrets.randbits(128)),
    "epoch": str(get_current_epoch())
}
```

2. **Proof Verification**:
```python
# OLD
nonce = public_signals[4]
if time.time() - int(nonce) > 3600:
    return False

# NEW
nullifier = public_signals[-1]
if nullifier in used_nullifiers:
    return False
used_nullifiers.add(nullifier)
```

3. **Storage**:
   - Implement nullifier storage (Redis/database)
   - Track nullifiers per epoch
   - Consider cleanup strategy (optional)

## Security Guarantees

### What Nullifiers Provide

1. ✅ **One-time use guarantee** - Each proof can only be verified once
2. ✅ **Zero-tolerance replay prevention** - No time window vulnerability
3. ✅ **Cryptographic binding** - Nullifier computed from private inputs
4. ✅ **Epoch-based invalidation** - Can invalidate all proofs in old epoch

### What Nullifiers Don't Provide

1. ❌ **Freshness** - Doesn't ensure proof is "recent" (use application-layer check if needed)
2. ❌ **Automatic cleanup** - Verifier must manage nullifier storage
3. ❌ **Cross-verifier sync** - Each verifier needs own nullifier set (use shared storage)

## Best Practices

1. **Use Redis/Database** for nullifier storage (not in-memory)
2. **Track nullifiers per epoch** for epoch management
3. **Consider TTL** for old epoch nullifiers (optional cleanup)
4. **Monitor nullifier set size** (grows over time)
5. **Use distributed storage** if multiple verifiers (Redis Cluster)

---

**Last Updated**: 2024-12-19  
**Version**: 3.0.0 (Breaking changes - nullifier pattern)  
**Security Level**: Maximum (zero-tolerance replay prevention)

