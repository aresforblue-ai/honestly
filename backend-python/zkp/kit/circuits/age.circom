pragma circom 2.0.0;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/comparators.circom";

template AgeProof() {
    // Private Inputs
    signal input birthTs;
    signal input salt;

    // Public Inputs
    signal input referenceTs;
    signal input minAgeSeconds;
    signal input documentHash;

    // Compute age in seconds (assume referenceTs >= birthTs)
    signal age;
    age <== referenceTs - birthTs;

    // Enforce minimum age
    component ageOk = LessThan(64);
    ageOk.in[0] <== minAgeSeconds;
    ageOk.in[1] <== age + 1; // allow equality
    ageOk.out === 1;

    // Poseidon commitment to bind birthTs+salt to documentHash
    component commit = Poseidon(2);
    commit.inputs[0] <== birthTs;
    commit.inputs[1] <== salt;
    signal commitment;
    commitment <== commit.out;

    // Enforce commitment matches provided documentHash
    signal diff;
    diff <== commitment - documentHash;
    diff === 0;
}

component main = AgeProof();


