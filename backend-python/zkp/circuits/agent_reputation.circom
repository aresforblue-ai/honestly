pragma circom 2.0.0;

/**
 * Agent Reputation Proof Circuit
 * ==============================
 * 
 * Proves an AI agent's reputation exceeds a threshold without revealing:
 * - The exact reputation score
 * - The agent's interaction history
 * - Other agents' feedback
 * 
 * Built specifically for AAIP (AI Agent Identity Protocol).
 * 
 * Security Features:
 * - Level 3 identity binding (agent ID bound to proof)
 * - Nullifier for replay attack prevention
 * - Range check to prevent modular wraparound
 * - Timestamp for proof freshness
 * 
 * Public Inputs:
 * - threshold: Minimum reputation required
 * - agentDIDHash: Hash of agent's DID
 * - timestamp: Proof timestamp
 * 
 * Public Outputs:
 * - nullifier: Unique, non-reusable identifier
 * - verified: 1 if reputation >= threshold
 */

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/comparators.circom";
include "circomlib/circuits/bitify.circom";

template AgentReputation(n) {
    // ---------------------------------------------------------
    // 1. PRIVATE INPUTS
    // ---------------------------------------------------------
    signal input reputationScore;   // Private: Actual reputation (0-100)
    signal input salt;              // Private: Random salt for nullifier
    signal input interactionCount;  // Private: Total interactions
    signal input positiveCount;     // Private: Positive interactions
    
    // ---------------------------------------------------------
    // 2. PUBLIC INPUTS
    // ---------------------------------------------------------
    signal input threshold;         // Public: Minimum reputation to prove
    signal input agentDIDHash;      // Public: Hash of agent's DID
    signal input timestamp;         // Public: Proof timestamp
    
    // ---------------------------------------------------------
    // 3. PUBLIC OUTPUTS
    // ---------------------------------------------------------
    signal output nullifier;        // Prevents proof reuse
    signal output verified;         // 1 if reputation >= threshold
    signal output reputationCommitment;  // Commitment to reputation data
    
    // ---------------------------------------------------------
    // 4. RANGE CHECK (Prevent Overflow)
    // ---------------------------------------------------------
    // Ensure reputation score is within valid range (0-100)
    // Use n bits for the comparison (7 bits covers 0-127)
    component rangeCheck = Num2Bits(n);
    rangeCheck.in <== reputationScore;
    
    // Also ensure threshold is valid
    component thresholdRange = Num2Bits(n);
    thresholdRange.in <== threshold;
    
    // ---------------------------------------------------------
    // 5. REPUTATION THRESHOLD CHECK
    // ---------------------------------------------------------
    // Check: reputationScore >= threshold
    component gte = GreaterEqThan(n);
    gte.in[0] <== reputationScore;
    gte.in[1] <== threshold;
    
    verified <== gte.out;
    
    // ---------------------------------------------------------
    // 6. REPUTATION COMMITMENT
    // ---------------------------------------------------------
    // Commit to reputation data without revealing exact values
    component repCommitment = Poseidon(4);
    repCommitment.inputs[0] <== reputationScore;
    repCommitment.inputs[1] <== interactionCount;
    repCommitment.inputs[2] <== positiveCount;
    repCommitment.inputs[3] <== salt;
    
    reputationCommitment <== repCommitment.out;
    
    // ---------------------------------------------------------
    // 7. IDENTITY-BOUND NULLIFIER
    // ---------------------------------------------------------
    // Nullifier binds this proof to the specific agent and time
    // Prevents replaying the same proof from different contexts
    component nullifierHasher = Poseidon(4);
    nullifierHasher.inputs[0] <== agentDIDHash;
    nullifierHasher.inputs[1] <== threshold;
    nullifierHasher.inputs[2] <== salt;
    nullifierHasher.inputs[3] <== timestamp;
    
    nullifier <== nullifierHasher.out;
    
    // ---------------------------------------------------------
    // 8. VALIDITY CONSTRAINT
    // ---------------------------------------------------------
    // Proof generation fails if reputation < threshold
    verified === 1;
}

// Instantiate with 7-bit range (covers 0-127, sufficient for 0-100 reputation)
component main {public [threshold, agentDIDHash, timestamp]} = AgentReputation(7);


