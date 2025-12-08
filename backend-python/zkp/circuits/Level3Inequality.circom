pragma circom 2.0.0;

// Level 3: High Assurance Identity-Binding Circuit
// Uses Poseidon hash for SNARK-friendly identity binding
// Prevents proof replay attacks and double-spending

// Import circomlib components
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/bitify.circom";
include "circomlib/circuits/poseidon.circom";

template Level3Inequality(n) {
    // ---------------------------------------------------------
    // 1. SIGNAL DEFINITIONS
    // ---------------------------------------------------------
    signal input val;          // Private: The value (e.g., stake amount, age)
    signal input salt;         // Private: Random noise to prevent dictionary attacks
    signal input threshold;    // Public: The inequality boundary (e.g., 50, 18)
    signal input senderID;     // Public: The Ethereum address or user ID

    signal output nullifier;   // Public: Unique hash binding this proof to user+secret
    signal output out;         // Public: Result of the check (1 if valid, 0 if not)

    // ---------------------------------------------------------
    // 2. RANGE CHECK (Level 2 Protection)
    // ---------------------------------------------------------
    // Force 'val' to be exactly 'n' bits.
    // This physically prevents the "Modular Wraparound" attack.
    component rangeCheck = Num2Bits(n);
    rangeCheck.in <== val;

    // ---------------------------------------------------------
    // 3. INEQUALITY CHECK
    // ---------------------------------------------------------
    // Checks if val > threshold
    component gt = GreaterThan(n);
    gt.in[0] <== val;
    gt.in[1] <== threshold;

    // We strictly enforce the result to be 1 (True).
    // If val <= threshold, proof generation fails immediately.
    gt.out === 1;
    out <== gt.out;

    // ---------------------------------------------------------
    // 4. IDENTITY BINDING (Level 3 Protection)
    // ---------------------------------------------------------
    // We hash (val + salt + senderID).
    // If an attacker intercepts the proof and tries to submit it
    // from their address, the 'senderID' changes, invalidating this hash.
    component hasher = Poseidon(3);
    hasher.inputs[0] <== val;
    hasher.inputs[1] <== salt;
    hasher.inputs[2] <== senderID;

    nullifier <== hasher.out;
}

// Instantiate for 64-bit numbers (covers all reasonable values)
component main {public [threshold, senderID]} = Level3Inequality(64);



