/*
 * Document Authenticity Circuit (PLONK-optimized)
 * 
 * Proves: A document hash is included in a Merkle tree of verified documents
 * Uses PLONK-optimized Poseidon hash for Merkle path verification
 * 
 * Curve: BLS12-381 (universal SRS)
 * Depth: 16 levels (supports ~65k documents)
 */

pragma circom 2.1.6;

include "../../../node_modules/circomlib/circuits/poseidon.circom";
include "../../../node_modules/circomlib/circuits/switcher.circom";
include "../../../node_modules/circomlib/circuits/bitify.circom";

/*
 * MerklePathPoseidon: Verify Merkle inclusion using Poseidon hash
 * PLONK-optimized version with reduced constraint count
 */
template MerklePathPoseidon(depth) {
    signal input leaf;
    signal input root;
    signal input path[depth];         // Sibling hashes
    signal input indices[depth];      // 0 = left, 1 = right
    
    signal output isValid;
    
    // Intermediate hashes
    signal hashes[depth + 1];
    hashes[0] <== leaf;
    
    // Traverse the Merkle tree
    component hashers[depth];
    component switchers[depth];
    
    for (var i = 0; i < depth; i++) {
        // Ensure index is binary
        indices[i] * (1 - indices[i]) === 0;
        
        // Switch inputs based on index
        switchers[i] = Switcher();
        switchers[i].sel <== indices[i];
        switchers[i].L <== hashes[i];
        switchers[i].R <== path[i];
        
        // Hash the pair
        hashers[i] = Poseidon(2);
        hashers[i].inputs[0] <== switchers[i].outL;
        hashers[i].inputs[1] <== switchers[i].outR;
        
        hashes[i + 1] <== hashers[i].out;
    }
    
    // Check if computed root matches expected root
    component rootCheck = IsEqual();
    rootCheck.in[0] <== hashes[depth];
    rootCheck.in[1] <== root;
    
    isValid <== rootCheck.out;
}

/*
 * IsEqual: Check if two values are equal
 */
template IsEqual() {
    signal input in[2];
    signal output out;
    
    signal diff <== in[0] - in[1];
    signal isZero <== diff * diff;
    
    // If diff is 0, isZero is 0, out is 1
    // If diff is non-zero, we need inverse
    signal inv;
    inv <-- diff != 0 ? 1/diff : 0;
    
    signal diffTimesInv <== diff * inv;
    out <== 1 - diffTimesInv;
    
    // Constraint: out is 1 iff diff is 0
    out * diff === 0;
}

/*
 * Switcher: Swap two values based on selector
 */
template Switcher() {
    signal input sel;
    signal input L;
    signal input R;
    signal output outL;
    signal output outR;
    
    signal aux <== (R - L) * sel;
    outL <== L + aux;
    outR <== R - aux;
}

/*
 * AuthenticityPLONK: Main circuit for document authenticity proofs
 */
template AuthenticityPLONK(depth) {
    // Private inputs
    signal input document_hash;           // Hash of the document
    signal input merkle_path[depth];      // Sibling hashes in Merkle tree
    signal input merkle_indices[depth];   // Path direction (0=left, 1=right)
    signal input timestamp;               // When document was registered
    signal input issuer_id;               // ID of document issuer
    
    // Public inputs
    signal input merkle_root;             // Public Merkle root
    signal input min_timestamp;           // Prove document existed before this time
    
    // Outputs
    signal output is_authentic;           // 1 if document is in the tree
    signal output document_commitment;    // Commitment to document details

    // ========== Merkle Inclusion Proof ==========
    
    component merkleVerifier = MerklePathPoseidon(depth);
    merkleVerifier.leaf <== document_hash;
    merkleVerifier.root <== merkle_root;
    
    for (var i = 0; i < depth; i++) {
        merkleVerifier.path[i] <== merkle_path[i];
        merkleVerifier.indices[i] <== merkle_indices[i];
    }

    // ========== Timestamp Verification ==========
    
    // Prove document was registered before min_timestamp
    component timestampCheck = LessThan(64);
    timestampCheck.in[0] <== timestamp;
    timestampCheck.in[1] <== min_timestamp;
    
    signal timestamp_valid <== timestampCheck.out;

    // ========== Combined Validity ==========
    
    is_authentic <== merkleVerifier.isValid * timestamp_valid;

    // ========== Document Commitment ==========
    
    // Create commitment that binds document to issuer and time
    component commitHash = Poseidon(3);
    commitHash.inputs[0] <== document_hash;
    commitHash.inputs[1] <== timestamp;
    commitHash.inputs[2] <== issuer_id;
    
    document_commitment <== commitHash.out;
}

/*
 * LessThan: Check if in[0] < in[1]
 */
template LessThan(n) {
    signal input in[2];
    signal output out;
    
    component n2b = Num2Bits(n + 1);
    n2b.in <== in[0] + (1 << n) - in[1];
    
    out <== 1 - n2b.out[n];
}

/*
 * Num2Bits: Convert number to bits
 */
template Num2Bits(n) {
    signal input in;
    signal output out[n];
    
    var lc = 0;
    var bit_value = 1;
    
    for (var i = 0; i < n; i++) {
        out[i] <-- (in >> i) & 1;
        out[i] * (out[i] - 1) === 0;
        lc += out[i] * bit_value;
        bit_value *= 2;
    }
    
    lc === in;
}

// Main component with 16-level depth (65,536 documents)
component main {public [merkle_root, min_timestamp]} = AuthenticityPLONK(16);

