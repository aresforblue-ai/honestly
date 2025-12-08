pragma circom 2.0.0;

/**
 * Agent Capability Proof Circuit
 * ==============================
 * 
 * Proves an AI agent has a specific capability without revealing:
 * - The full list of agent capabilities
 * - The agent's internal state
 * - Other sensitive agent metadata
 * 
 * Uses Poseidon hash for SNARK-friendly commitments and nullifier generation.
 * 
 * Public Inputs:
 * - capabilityHash: Hash of the capability being proven
 * - agentCommitment: Public commitment to agent identity
 * - timestamp: Proof timestamp (for freshness)
 * 
 * Public Outputs:
 * - nullifier: Unique hash preventing replay attacks
 * - verified: 1 if capability is valid, 0 otherwise
 */

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/comparators.circom";

template AgentCapability() {
    // ---------------------------------------------------------
    // 1. PRIVATE INPUTS (not revealed in proof)
    // ---------------------------------------------------------
    signal input agentID;           // Private: Agent's unique identifier
    signal input capabilityIndex;   // Private: Index of capability in agent's list
    signal input salt;              // Private: Random salt for nullifier
    signal input capabilities[8];   // Private: Agent's capability hashes (fixed size array)
    
    // ---------------------------------------------------------
    // 2. PUBLIC INPUTS (known to verifier)
    // ---------------------------------------------------------
    signal input capabilityHash;    // Public: Hash of capability to prove
    signal input agentCommitment;   // Public: Commitment to agent identity
    signal input timestamp;         // Public: Proof timestamp
    
    // ---------------------------------------------------------
    // 3. PUBLIC OUTPUTS
    // ---------------------------------------------------------
    signal output nullifier;        // Prevents proof reuse
    signal output verified;         // 1 = capability proven, 0 = failed
    
    // ---------------------------------------------------------
    // 4. AGENT IDENTITY VERIFICATION
    // ---------------------------------------------------------
    // Verify the agent commitment matches the private agent ID
    // This prevents agents from claiming false capabilities
    component agentHasher = Poseidon(2);
    agentHasher.inputs[0] <== agentID;
    agentHasher.inputs[1] <== salt;
    
    // CRITICAL: Enforce agent identity binding
    // Without this constraint, any agent could claim any capability
    agentHasher.out === agentCommitment;
    
    // ---------------------------------------------------------
    // 5. CAPABILITY LOOKUP
    // ---------------------------------------------------------
    // Check if the capability at capabilityIndex matches capabilityHash
    // Using a simple equality check with selector
    
    signal selectedCapability;
    component selectors[8];
    component eq[8];
    
    signal capMatch[8];
    signal capSum;
    
    var sumTemp = 0;
    
    for (var i = 0; i < 8; i++) {
        // Check if this index is selected
        eq[i] = IsEqual();
        eq[i].in[0] <== capabilityIndex;
        eq[i].in[1] <== i;
        
        // If selected, check capability matches
        capMatch[i] <== eq[i].out * (capabilities[i] - capabilityHash);
    }
    
    // Sum all matches (should be 0 if capability found)
    capSum <== capMatch[0] + capMatch[1] + capMatch[2] + capMatch[3] 
             + capMatch[4] + capMatch[5] + capMatch[6] + capMatch[7];
    
    // Verify capability matches (sum must be 0)
    component isZero = IsZero();
    isZero.in <== capSum;
    verified <== isZero.out;
    
    // ---------------------------------------------------------
    // 6. NULLIFIER GENERATION
    // ---------------------------------------------------------
    // Nullifier = Poseidon(agentID, capabilityHash, salt, timestamp)
    // This binds the proof to the specific agent, capability, and time
    component nullifierHasher = Poseidon(4);
    nullifierHasher.inputs[0] <== agentID;
    nullifierHasher.inputs[1] <== capabilityHash;
    nullifierHasher.inputs[2] <== salt;
    nullifierHasher.inputs[3] <== timestamp;
    
    nullifier <== nullifierHasher.out;
    
    // ---------------------------------------------------------
    // 7. VALIDITY CONSTRAINT
    // ---------------------------------------------------------
    // Force verification to succeed (proof generation fails if not verified)
    verified === 1;
}

component main {public [capabilityHash, agentCommitment, timestamp]} = AgentCapability();


