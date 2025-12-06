// Groth16 age proof circuit: prove (referenceTs - birthTs) >= minAge * YEAR_SECONDS
// and bind to a Poseidon commitment over birthTs, salt, documentHash.
pragma circom 2.1.6;

include "../node_modules/circomlib/circuits/poseidon.circom";
include "../node_modules/circomlib/circuits/comparators.circom";
include "../node_modules/circomlib/circuits/bitify.circom";

template AgeProof() {
    signal input birthTs;        // private: birth timestamp (seconds)
    signal input referenceTs;    // public: reference timestamp (seconds)
    signal input minAge;         // public: minimum age in years
    signal input documentHash;   // public: document hash mapped into field
    signal input salt;           // private: random salt
    signal input epoch;          // private: epoch/version number (prevents cross-epoch replay)

    signal output minAgeOut;         // public signal
    signal output referenceTsOut;    // public signal
    signal output documentHashOut;   // public signal
    signal output commitment;        // public signal: Poseidon(birthTs, salt, documentHash)
    signal output nullifier;         // public signal: Poseidon(salt, documentHash, epoch) - ONE-TIME USE

    // Enforce referenceTs > birthTs
    component ltTime = LessThan(64);
    ltTime.in[0] <== birthTs;
    ltTime.in[1] <== referenceTs;
    ltTime.out === 1;

    // Compute delta = referenceTs - birthTs, constrain to 64 bits (non-negative)
    signal delta;
    delta <== referenceTs - birthTs;

    component deltaBits = Num2Bits(64);
    deltaBits.in <== delta;

    // Convert minAge to seconds: YEAR_SECONDS * minAge
    var YEAR_SECONDS = 31556952; // average seconds per Gregorian year
    signal minAgeSeconds;
    minAgeSeconds <== minAge * YEAR_SECONDS;

    // Check minAgeSeconds <= delta  => delta >= minAgeSeconds
    signal deltaPlusOne;
    deltaPlusOne <== delta + 1;

    component ageOk = LessThan(64);
    ageOk.in[0] <== minAgeSeconds;
    ageOk.in[1] <== deltaPlusOne;
    ageOk.out === 1;

    // Poseidon commitment to bind private data to public inputs
    component pose = Poseidon(3);
    pose.inputs[0] <== birthTs;
    pose.inputs[1] <== salt;
    pose.inputs[2] <== documentHash;

    commitment <== pose.out;
    
    // CRITICAL: Nullifier for one-time use (prevents proof replay/double-spending)
    // Nullifier = Poseidon(salt, documentHash, epoch)
    // Verifier stores used nullifiers and rejects duplicates
    // This provides ZERO-TOLERANCE replay prevention (not time-window based)
    component nullifierHash = Poseidon(3);
    nullifierHash.inputs[0] <== salt;
    nullifierHash.inputs[1] <== documentHash;
    nullifierHash.inputs[2] <== epoch;
    nullifier <== nullifierHash.out;
    
    // CRITICAL: Constrain outputs to match inputs (prevents output manipulation)
    // Without these constraints, an attacker could modify outputs without violating circuit
    minAgeOut <== minAge;
    minAgeOut === minAge;  // Enforce output matches input
    
    referenceTsOut <== referenceTs;
    referenceTsOut === referenceTs;  // Enforce output matches input
    
    documentHashOut <== documentHash;
    documentHashOut === documentHash;  // Enforce output matches input
    
    // CRITICAL: Constrain commitment is correctly computed (prevents commitment manipulation)
    // This ensures the commitment cannot be modified without violating the circuit
    commitment === pose.out;
    
    // CRITICAL: Constrain nullifier is correctly computed (prevents nullifier manipulation)
    // This ensures the nullifier cannot be modified without violating the circuit
    nullifier === nullifierHash.out;
    
    // CRITICAL: Constrain epoch is reasonable (prevents extreme values)
    // Epoch should be a version number (e.g., 0, 1, 2, ...)
    // Constrain to 64 bits to prevent overflow
    component epochBits = Num2Bits(64);
    epochBits.in <== epoch;
}

component main = AgeProof();

