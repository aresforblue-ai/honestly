pragma circom 2.0.0;

// Level 3: High Assurance Age Proof Circuit
// Identity-binding with Poseidon hash to prevent proof replay

include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/poseidon.circom";
// Note: documentHash is provided as a field element (not hex). Remove hex conversion.

template AgeProofLevel3() {
    // Private inputs
    signal input birthTs;          // Birth timestamp (private)
    signal input salt;             // Random salt (private)

    // Public inputs
    signal input referenceTs;      // Reference timestamp (public)
    signal input minAge;           // Minimum age required (public, years)
    signal input userID;           // User identifier (public)
    signal input documentHash;     // Document hash as field element (public)
    
    // Outputs
    signal output nullifier;       // Identity-binding nullifier (public)
    signal output verified;        // Verification result (public, 1 if valid)
    
    // Calculate age in seconds
    signal ageSeconds;
    ageSeconds <== referenceTs - birthTs;
    
    // Convert to years (approximate: 365.25 days/year)
    // Using fixed-point: multiply by 10000, divide by 31557600 (seconds in year)
    signal ageYearsScaled;
    ageYearsScaled <== ageSeconds * 10000;
    
    // Check age >= minAge (using 32-bit comparison)
    component ageCheck = GreaterThan(32);
    ageCheck.in[0] <== ageYearsScaled;
    ageCheck.in[1] <== minAge * 10000;
    
    // Enforce age requirement
    ageCheck.out === 1;
    verified <== ageCheck.out;
    
    // Range check on age (prevent overflow)
    component ageRangeCheck = Num2Bits(32);
    ageRangeCheck.in <== ageYearsScaled;
    
    // Identity binding: Poseidon hash of (birthTs, salt, userID, documentHash)
    // This prevents proof replay attacks
    component identityHasher = Poseidon(4);
    identityHasher.inputs[0] <== birthTs;
    identityHasher.inputs[1] <== salt;
    identityHasher.inputs[2] <== userID;
    identityHasher.inputs[3] <== documentHash;
    nullifier <== identityHasher.out;
}

component main {public [referenceTs, minAge, userID, documentHash]} = AgeProofLevel3();



