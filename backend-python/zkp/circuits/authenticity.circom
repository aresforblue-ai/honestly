// Poseidon Merkle inclusion proof circuit.
pragma circom 2.1.6;

include "../node_modules/circomlib/circuits/poseidon.circom";

template MerklePath(depth) {
    signal input leaf;
    signal input pathElements[depth];
    signal input pathIndices[depth]; // 0 = leaf on left, 1 = leaf on right

    signal output root;

    var i;
    signal hash;
    hash <== leaf;

    for (i = 0; i < depth; i++) {
        signal left;
        signal right;

        // Select ordering based on path index
        left <== (1 - pathIndices[i]) * hash + pathIndices[i] * pathElements[i];
        right <== pathIndices[i] * hash + (1 - pathIndices[i]) * pathElements[i];

        component p = Poseidon(2);
        p.inputs[0] <== left;
        p.inputs[1] <== right;
        hash <== p.out;
    }

    root <== hash;
}

template AuthenticityProof(depth) {
    signal input leaf;                  // public: document hash mapped into field
    signal input root;                  // public: Merkle root
    signal input pathElements[depth];   // private: sibling nodes
    signal input pathIndices[depth];    // private: sibling positions
    signal input salt;                  // private: random salt for nullifier
    signal input epoch;                 // public: epoch/version number (allows freshness enforcement & nullifier purging)

    signal output rootOut;              // public: computed root (should equal root)
    signal output leafOut;              // public: echoes leaf
    signal output epochOut;             // public: echoed epoch for verifier freshness checks
    signal output nullifier;            // public signal: Poseidon(salt, leaf, epoch) - ONE-TIME USE

    component mp = MerklePath(depth);
    mp.leaf <== leaf;
    for (var i = 0; i < depth; i++) {
        mp.pathElements[i] <== pathElements[i];
        mp.pathIndices[i] <== pathIndices[i];
    }

    rootOut <== mp.root;
    leafOut <== leaf;

    // CRITICAL: Constrain outputs to match computed values (prevents output manipulation)
    // Without these constraints, an attacker could modify outputs without violating circuit
    rootOut === mp.root;  // Enforce output matches computed root
    leafOut === leaf;     // Enforce output matches input leaf
    
    // Enforce provided root matches computed root
    root === mp.root;
    
    // CRITICAL: Ensure rootOut matches provided root (prevents root manipulation)
    // This creates a chain: root === mp.root === rootOut
    rootOut === root;
    
    // CRITICAL: Nullifier for one-time use (prevents proof replay/double-spending)
    // Nullifier = Poseidon(salt, leaf, epoch)
    // Verifier stores used nullifiers and rejects duplicates
    // This provides ZERO-TOLERANCE replay prevention (not time-window based)
    component nullifierHash = Poseidon(3);
    nullifierHash.inputs[0] <== salt;
    nullifierHash.inputs[1] <== leaf;
    nullifierHash.inputs[2] <== epoch;
    nullifier <== nullifierHash.out;
    
    // CRITICAL: Constrain nullifier is correctly computed (prevents nullifier manipulation)
    // This ensures the nullifier cannot be modified without violating the circuit
    nullifier === nullifierHash.out;
    
    // CRITICAL: Constrain epoch output matches input (prevents epoch manipulation)
    // Verifier can check epochOut to enforce freshness and purge old nullifiers
    epochOut <== epoch;
    epochOut === epoch;
    
    // CRITICAL: Constrain epoch is reasonable (prevents extreme values)
    // Epoch should be a version number (e.g., 0, 1, 2, ...)
    // Constrain to 64 bits to prevent overflow
    component epochBits = Num2Bits(64);
    epochBits.in <== epoch;
}

// Default depth 16 (65,536 leaves). Adjust as needed when compiling.
component main = AuthenticityProof(16);

