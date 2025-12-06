# Epoch Design: Private vs Public

## Design Decision

We use **different epoch visibility** for different circuit types based on their use cases:

| Circuit | Epoch Visibility | Rationale |
|---------|------------------|-----------|
| **Age Circuit** | **Private** | Age verification is a permanent fact. No need for freshness enforcement or epoch-based invalidation. |
| **Authenticity Circuit** | **Public** | Documents can be updated. Need freshness enforcement and nullifier purging. |

## Trade-offs

### Private Epoch (Age Circuit)

**Advantages**:
- ✅ **Proof unlinkable across epochs** - Verifier can't tell which epoch proof was generated in
- ✅ **Privacy-preserving** - Epoch doesn't leak information about when proof was created
- ✅ **Permanent facts** - Age verification doesn't expire or need freshness

**Disadvantages**:
- ❌ **No freshness enforcement** - Verifier can't require proofs from current epoch
- ❌ **Can't purge old nullifiers** - Don't know which epoch nullifiers belong to
- ❌ **Storage grows indefinitely** - Must keep all nullifiers forever

**Use Case**: Age verification
- "I was 18+ at time X" is a permanent fact
- Doesn't need freshness checks
- Privacy is more important than storage efficiency

### Public Epoch (Authenticity Circuit)

**Advantages**:
- ✅ **Freshness enforcement** - Verifier can require `epochOut >= currentEpoch`
- ✅ **Nullifier purging** - Can delete nullifiers for `epoch < currentEpoch - N`
- ✅ **Document invalidation** - Can invalidate all proofs when document updated (increment epoch)
- ✅ **Storage efficiency** - Can clean up old epoch nullifiers

**Disadvantages**:
- ❌ **Proof linkable across epochs** - Verifier can see which epoch proof was generated in
- ❌ **Privacy trade-off** - Epoch leaks timing information

**Use Case**: Document authenticity
- Documents can be updated (need to invalidate old proofs)
- Need to enforce freshness (require current epoch)
- Storage efficiency matters (can purge old nullifiers)

## Implementation

### Age Circuit (Private Epoch)

```circom
signal input epoch;  // private: epoch/version number
signal output nullifier;  // public: Poseidon(salt, documentHash, epoch)

// Epoch is private - verifier can't see it
// Nullifier computation uses private epoch
component nullifierHash = Poseidon(3);
nullifierHash.inputs[0] <== salt;
nullifierHash.inputs[1] <== documentHash;
nullifierHash.inputs[2] <== epoch;  // Private input
nullifier <== nullifierHash.out;
```

**Verifier Behavior**:
- Stores all nullifiers (can't purge by epoch)
- Can't enforce freshness (doesn't know epoch)
- Accepts proofs from any epoch

### Authenticity Circuit (Public Epoch)

```circom
signal input epoch;  // public: epoch/version number
signal output epochOut;  // public: echoed epoch
signal output nullifier;  // public: Poseidon(salt, leaf, epoch)

// Epoch is public - verifier can see it
epochOut <== epoch;
epochOut === epoch;  // Constrain output matches input

// Nullifier computation uses public epoch
component nullifierHash = Poseidon(3);
nullifierHash.inputs[0] <== salt;
nullifierHash.inputs[1] <== leaf;
nullifierHash.inputs[2] <== epoch;  // Public input
nullifier <== nullifierHash.out;
```

**Verifier Behavior**:
- Can enforce freshness: `if epochOut < currentEpoch: REJECT`
- Can purge old nullifiers: `delete nullifiers where epoch < currentEpoch - 10`
- Can invalidate proofs: Increment `currentEpoch` when document updated

## Verifier Implementation

### Age Circuit Verifier (Private Epoch)

```python
# Global set of used nullifiers (all epochs mixed together)
used_nullifiers = set()

def verify_age_proof(proof, public_signals):
    nullifier = public_signals[-1]  # Last public signal
    
    # Check if nullifier was already used
    if nullifier in used_nullifiers:
        return False  # REJECT: Proof already used
    
    # Verify proof
    if not snarkjs.verify(vkey, public_signals, proof):
        return False
    
    # Mark nullifier as used
    used_nullifiers.add(nullifier)
    
    return True

# Note: Can't purge by epoch (don't know epoch)
# Storage grows indefinitely
```

### Authenticity Circuit Verifier (Public Epoch)

```python
# Per-epoch sets of used nullifiers
used_nullifiers_by_epoch = {}  # {epoch: set(nullifiers)}
current_epoch = 0

def verify_authenticity_proof(proof, public_signals):
    # Extract epoch (second-to-last public signal)
    epoch_out = int(public_signals[-2])
    nullifier = public_signals[-1]  # Last public signal
    
    # Enforce freshness: require current epoch
    if epoch_out < current_epoch:
        return False  # REJECT: Proof from old epoch
    
    # Get nullifier set for this epoch
    epoch_nullifiers = used_nullifiers_by_epoch.get(epoch_out, set())
    
    # Check if nullifier was already used
    if nullifier in epoch_nullifiers:
        return False  # REJECT: Proof already used
    
    # Verify proof
    if not snarkjs.verify(vkey, public_signals, proof):
        return False
    
    # Mark nullifier as used
    epoch_nullifiers.add(nullifier)
    used_nullifiers_by_epoch[epoch_out] = epoch_nullifiers
    
    return True

def purge_old_nullifiers(keep_last_n=10):
    """Purge nullifiers from epochs older than current_epoch - keep_last_n"""
    min_epoch = current_epoch - keep_last_n
    for epoch in list(used_nullifiers_by_epoch.keys()):
        if epoch < min_epoch:
            del used_nullifiers_by_epoch[epoch]

def invalidate_all_proofs():
    """Invalidate all proofs by incrementing epoch"""
    global current_epoch
    current_epoch += 1
    # Old proofs will be rejected due to freshness check
```

## When to Increment Epoch

### Age Circuit
- **Never** (or very rarely)
- Age verification is permanent
- Only increment if circuit security is compromised

### Authenticity Circuit
- **Document updated** - Increment epoch to invalidate old proofs
- **Security update** - Increment epoch after security fix
- **Key rotation** - Increment epoch after key change
- **Policy change** - Increment epoch after policy update

## Migration Considerations

### Age Circuit
- Epoch remains private
- No changes needed to verifier logic
- Storage grows over time (acceptable for permanent facts)

### Authenticity Circuit
- Epoch is now public
- Verifier must check `epochOut >= currentEpoch`
- Verifier can purge old epoch nullifiers
- Breaking change: Old proofs won't work (must regenerate)

## Summary

| Aspect | Age Circuit (Private) | Authenticity Circuit (Public) |
|--------|----------------------|------------------------------|
| **Epoch Visibility** | Private | Public |
| **Freshness Enforcement** | ❌ No | ✅ Yes |
| **Nullifier Purging** | ❌ No | ✅ Yes |
| **Proof Unlinkability** | ✅ Yes | ❌ No |
| **Storage Efficiency** | ❌ Grows indefinitely | ✅ Can purge old epochs |
| **Use Case** | Permanent facts | Updatable documents |

---

**Last Updated**: 2024-12-19  
**Design Decision**: Hybrid approach (private for age, public for authenticity)

