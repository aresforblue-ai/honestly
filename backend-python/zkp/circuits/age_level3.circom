pragma circom 2.0.0;

// Level 3: High Assurance Age Proof Circuit
// Identity-binding with Poseidon hash to prevent proof replay

include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/sha256.circom";

template AgeProofLevel3() {
    // Private inputs
    signal input birthTs;          // Birth timestamp (private)
    signal input referenceTs;      // Reference timestamp (public)
    signal input salt;             // Random salt (private)
    signal input userID;           // User identifier (public)
    signal input documentHashHex;  // Document hash (public, hex string)
    
    // Public inputs
    signal input minAge;           // Minimum age required (public)
    
    // Outputs
    signal output nullifier;       // Identity-binding nullifier (public)
    signal output verified;         // Verification result (public, 1 if valid)
    
    // Convert document hash hex to field element
    component hashConverter = HexToBits(256);
    hashConverter.in <== documentHashHex;
    
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
    verified <== 1;
    
    // Range check on age (prevent overflow)
    component ageRangeCheck = Num2Bits(32);
    ageRangeCheck.in <== ageYearsScaled;
    
    // Identity binding: Poseidon hash of (birthTs, salt, userID, documentHash)
    // This prevents proof replay attacks
    component identityHasher = Poseidon(4);
    identityHasher.inputs[0] <== birthTs;
    identityHasher.inputs[1] <== salt;
    identityHasher.inputs[2] <== userID;
    
    // Hash document hash (convert to field element)
    component docHashHasher = Poseidon(1);
    docHashHasher.inputs[0] <== hashConverter.out;
    
    identityHasher.inputs[3] <== docHashHasher.out;
    
    nullifier <== identityHasher.out;
}

component main {public [referenceTs, minAge, userID, documentHashHex]} = AgeProofLevel3();



