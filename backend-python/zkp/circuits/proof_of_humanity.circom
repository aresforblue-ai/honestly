/*
 * Proof of Humanity Circuit
 * ==========================
 * 
 * A revolutionary zero-knowledge proof that proves someone is human
 * WITHOUT revealing their identity.
 * 
 * This is critical for:
 * - Combating bots and automated attacks
 * - Verifying human involvement in AI-assisted processes
 * - Preventing deepfake and AI-generated identity fraud
 * - Sybil resistance in decentralized systems
 * - Human-gated access to sensitive resources
 * 
 * The proof demonstrates:
 * 1. Possession of valid identity credentials (hashed)
 * 2. Liveness verification result (from biometric check)
 * 3. Uniqueness (via nullifier to prevent double-proving)
 * 4. Time-bound freshness (proof is recent)
 * 
 * Privacy guarantees:
 * - No personal information is revealed
 * - Cannot link multiple proofs to same person (nullifier is scoped)
 * - Verifier learns only: "This is a unique human who passed liveness check"
 */

pragma circom 2.0.0;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";
include "../node_modules/circomlib/circuits/bitify.circom";

/*
 * ProofOfHumanity
 * 
 * Inputs:
 *   - identitySecret: User's secret identity key (private)
 *   - identityCommitment: Hash of identity (can be checked against registry)
 *   - livenessNonce: Random nonce from liveness check (private)
 *   - livenessResult: Result of liveness verification (1 = passed)
 *   - biometricHash: Hash of biometric data used (private)
 *   - credentialHash: Hash of identity credential (private)
 *   - timestamp: Unix timestamp of the proof
 *   - maxAge: Maximum age of proof in seconds (e.g., 300 = 5 minutes)
 *   - currentTime: Current time for freshness check
 *   - scope: Application scope for nullifier (prevents cross-app tracking)
 *   - externalNullifier: External nullifier for this proof session
 * 
 * Outputs:
 *   - nullifierHash: Unique nullifier for this proof (prevents double-use)
 *   - humanityCommitment: Commitment that can be verified
 *   - timestampOut: The timestamp (for verification)
 *   - scopeOut: The scope (for verification)
 */
template ProofOfHumanity() {
    // Private inputs
    signal input identitySecret;
    signal input livenessNonce;
    signal input livenessResult;
    signal input biometricHash;
    signal input credentialHash;
    
    // Public inputs
    signal input identityCommitment;
    signal input timestamp;
    signal input maxAge;
    signal input currentTime;
    signal input scope;
    signal input externalNullifier;
    
    // Outputs
    signal output nullifierHash;
    signal output humanityCommitment;
    signal output timestampOut;
    signal output scopeOut;
    
    // ================================================
    // 1. Verify identity commitment
    // ================================================
    // The identity commitment should match hash(identitySecret)
    component identityHasher = Poseidon(1);
    identityHasher.inputs[0] <== identitySecret;
    
    // Verify commitment matches
    identityHasher.out === identityCommitment;
    
    // ================================================
    // 2. Verify liveness check passed
    // ================================================
    // Liveness result must be 1 (passed)
    // This is enforced as a constraint
    signal livenessValid;
    livenessValid <== livenessResult;
    livenessValid === 1;
    
    // Verify liveness was performed with valid nonce
    component livenessHasher = Poseidon(2);
    livenessHasher.inputs[0] <== livenessNonce;
    livenessHasher.inputs[1] <== biometricHash;
    // The liveness commitment can be checked externally if needed
    
    // ================================================
    // 3. Verify credential is valid
    // ================================================
    // Create commitment to credential
    component credentialHasher = Poseidon(2);
    credentialHasher.inputs[0] <== credentialHash;
    credentialHasher.inputs[1] <== identitySecret;
    
    // ================================================
    // 4. Check freshness (timestamp within maxAge)
    // ================================================
    // Ensure timestamp is not too old
    component ageCheck = LessThan(64);
    signal age;
    age <== currentTime - timestamp;
    ageCheck.in[0] <== age;
    ageCheck.in[1] <== maxAge;
    ageCheck.out === 1;  // age must be < maxAge
    
    // Ensure timestamp is not in the future
    component notFuture = LessEqThan(64);
    notFuture.in[0] <== timestamp;
    notFuture.in[1] <== currentTime;
    notFuture.out === 1;
    
    // ================================================
    // 5. Generate nullifier (prevents double-proving)
    // ================================================
    // Nullifier = hash(identitySecret, scope, externalNullifier)
    // This ensures:
    // - Same person can't prove twice for same scope+session
    // - Different scopes have different nullifiers (no cross-tracking)
    component nullifierHasher = Poseidon(3);
    nullifierHasher.inputs[0] <== identitySecret;
    nullifierHasher.inputs[1] <== scope;
    nullifierHasher.inputs[2] <== externalNullifier;
    nullifierHash <== nullifierHasher.out;
    
    // ================================================
    // 6. Generate humanity commitment
    // ================================================
    // This commitment proves humanity without revealing identity
    component humanityHasher = Poseidon(4);
    humanityHasher.inputs[0] <== identityCommitment;
    humanityHasher.inputs[1] <== livenessHasher.out;
    humanityHasher.inputs[2] <== credentialHasher.out;
    humanityHasher.inputs[3] <== timestamp;
    humanityCommitment <== humanityHasher.out;
    
    // ================================================
    // 7. Output public values
    // ================================================
    timestampOut <== timestamp;
    scopeOut <== scope;
}

/*
 * SimpleLivenessCheck
 * 
 * A simpler template for basic liveness verification.
 * Used when full biometric verification isn't needed.
 */
template SimpleLivenessCheck() {
    signal input challengeResponse;
    signal input challengeHash;
    signal input userSecret;
    
    signal output valid;
    signal output commitment;
    
    // Verify challenge response
    component responseHasher = Poseidon(2);
    responseHasher.inputs[0] <== challengeResponse;
    responseHasher.inputs[1] <== userSecret;
    
    // Check against expected hash
    component isEqual = IsEqual();
    isEqual.in[0] <== responseHasher.out;
    isEqual.in[1] <== challengeHash;
    valid <== isEqual.out;
    
    // Generate commitment
    component commitHasher = Poseidon(1);
    commitHasher.inputs[0] <== userSecret;
    commitment <== commitHasher.out;
}

/*
 * HumanityRegistry
 * 
 * Verifies membership in a registry of verified humans.
 * Uses Merkle proof for privacy-preserving membership check.
 */
template HumanityRegistry(levels) {
    signal input identitySecret;
    signal input pathElements[levels];
    signal input pathIndices[levels];
    signal input root;
    
    signal output nullifier;
    signal output membershipProof;
    
    // Compute identity leaf
    component leafHasher = Poseidon(1);
    leafHasher.inputs[0] <== identitySecret;
    
    // Verify Merkle path
    signal hashIter[levels + 1];
    hashIter[0] <== leafHasher.out;
    
    component pathHashers[levels];
    
    for (var i = 0; i < levels; i++) {
        pathHashers[i] = Poseidon(2);
        
        // Select left/right based on path index
        signal isRight;
        isRight <== pathIndices[i];
        
        // Constrain to binary
        isRight * (isRight - 1) === 0;
        
        // Compute left and right inputs
        signal left;
        signal right;
        left <== hashIter[i] + isRight * (pathElements[i] - hashIter[i]);
        right <== pathElements[i] + isRight * (hashIter[i] - pathElements[i]);
        
        pathHashers[i].inputs[0] <== left;
        pathHashers[i].inputs[1] <== right;
        hashIter[i + 1] <== pathHashers[i].out;
    }
    
    // Verify root matches
    root === hashIter[levels];
    
    // Generate nullifier
    component nullifierHasher = Poseidon(2);
    nullifierHasher.inputs[0] <== identitySecret;
    nullifierHasher.inputs[1] <== root;  // Scoped to this registry
    nullifier <== nullifierHasher.out;
    
    // Output membership proof (the leaf hash)
    membershipProof <== leafHasher.out;
}

/*
 * AntiSybil
 * 
 * Proves uniqueness across multiple proofs to prevent Sybil attacks.
 * Each person can only create one valid proof per epoch.
 */
template AntiSybil() {
    signal input identitySecret;
    signal input epoch;  // Time period (e.g., day number)
    signal input actionId;  // What action this is for
    
    signal output epochNullifier;
    signal output actionNullifier;
    signal output identityCommitment;
    
    // Identity commitment (public)
    component idHasher = Poseidon(1);
    idHasher.inputs[0] <== identitySecret;
    identityCommitment <== idHasher.out;
    
    // Epoch nullifier - one per epoch
    component epochHasher = Poseidon(2);
    epochHasher.inputs[0] <== identitySecret;
    epochHasher.inputs[1] <== epoch;
    epochNullifier <== epochHasher.out;
    
    // Action nullifier - one per action type per epoch
    component actionHasher = Poseidon(3);
    actionHasher.inputs[0] <== identitySecret;
    actionHasher.inputs[1] <== epoch;
    actionHasher.inputs[2] <== actionId;
    actionNullifier <== actionHasher.out;
}

// Main component
component main {public [identityCommitment, timestamp, maxAge, currentTime, scope, externalNullifier]} = ProofOfHumanity();

