pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";

template MerkleProof(depth) {
    signal input leaf;
    signal input pathElements[depth];
    signal input pathIndices[depth];
    signal output root;

    var i;
    signal hash;
    hash <== leaf;

    for (i = 0; i < depth; i++) {
        signal left;
        signal right;
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
    // Private Inputs
    signal input leaf;

    // Public Inputs
    signal input root;
    signal input pathElements[depth];
    signal input pathIndices[depth];

    // Compute root
    component mp = MerkleProof(depth);
    mp.leaf <== leaf;
    for (var i = 0; i < depth; i++) {
        mp.pathElements[i] <== pathElements[i];
        mp.pathIndices[i] <== pathIndices[i];
    }

    // Enforce equality
    signal diff;
    diff <== mp.root - root;
    diff === 0;
}

component main = AuthenticityProof(16);


