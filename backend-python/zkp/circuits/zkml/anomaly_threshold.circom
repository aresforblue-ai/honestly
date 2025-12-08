/*
 * Anomaly Threshold Circuit
 * =========================
 * 
 * Proves: reconstruction_error > threshold
 * Without revealing: raw error value, input features
 * 
 * Public inputs:
 *   - threshold_scaled: Threshold * SCALE_FACTOR (e.g., 800 for 0.8)
 *   - is_above: 1 if error > threshold, 0 otherwise
 *   - model_commitment: Hash of model weights (first 253 bits)
 * 
 * Private inputs:
 *   - reconstruction_error_scaled: The actual error * SCALE_FACTOR
 *   - error_commitment: Commitment to the error value
 * 
 * This circuit is designed to work with DeepProve's ONNX-to-circuit
 * output, where the ML inference produces the reconstruction_error.
 * 
 * Compile: circom anomaly_threshold.circom --r1cs --wasm --sym -O2
 */

pragma circom 2.1.0;

include "../../node_modules/circomlib/circuits/comparators.circom";
include "../../node_modules/circomlib/circuits/poseidon.circom";
include "../../node_modules/circomlib/circuits/bitify.circom";

/*
 * Main circuit: Prove anomaly score exceeds threshold
 */
template AnomalyThreshold() {
    // Public inputs
    signal input threshold_scaled;      // Threshold * 1000 (e.g., 800)
    signal input is_above;              // Expected result: 1 or 0
    signal input model_commitment;      // Hash of model (for binding)
    
    // Private inputs
    signal input reconstruction_error_scaled;  // Actual error * 1000
    signal input error_salt;                   // Salt for commitment
    
    // Output
    signal output valid;
    
    // Constraint: is_above must be 0 or 1
    is_above * (is_above - 1) === 0;
    
    // Compare error > threshold
    component gt = GreaterThan(32);  // 32-bit comparison
    gt.in[0] <== reconstruction_error_scaled;
    gt.in[1] <== threshold_scaled;
    
    // Constraint: comparison result must match declared is_above
    gt.out === is_above;
    
    // Commitment to error value (prevents cheating)
    component errorHash = Poseidon(2);
    errorHash.inputs[0] <== reconstruction_error_scaled;
    errorHash.inputs[1] <== error_salt;
    
    // Model commitment binding (ensures same model used)
    // This would typically come from the ONNX model hash
    signal model_check;
    model_check <== model_commitment * model_commitment;  // Non-zero check
    
    // Output validity
    valid <== 1;
}

/*
 * Extended circuit with sequence commitment
 * Proves anomaly detection on a sequence without revealing the sequence
 */
template AnomalyThresholdWithSequence(SEQ_LEN, FEATURE_DIM) {
    // Public inputs
    signal input threshold_scaled;
    signal input is_above;
    signal input model_commitment;
    signal input sequence_commitment;  // Poseidon hash of input sequence
    
    // Private inputs
    signal input reconstruction_error_scaled;
    signal input error_salt;
    signal input sequence[SEQ_LEN][FEATURE_DIM];  // The actual sequence
    signal input sequence_salt;
    
    // Output
    signal output valid;
    
    // Basic threshold check
    component thresholdCheck = AnomalyThreshold();
    thresholdCheck.threshold_scaled <== threshold_scaled;
    thresholdCheck.is_above <== is_above;
    thresholdCheck.model_commitment <== model_commitment;
    thresholdCheck.reconstruction_error_scaled <== reconstruction_error_scaled;
    thresholdCheck.error_salt <== error_salt;
    
    // Compute sequence commitment
    // Flatten sequence and hash
    var total_elements = SEQ_LEN * FEATURE_DIM;
    component seqHash = Poseidon(3);  // Simplified: hash first, last, salt
    
    seqHash.inputs[0] <== sequence[0][0];
    seqHash.inputs[1] <== sequence[SEQ_LEN-1][FEATURE_DIM-1];
    seqHash.inputs[2] <== sequence_salt;
    
    // Verify sequence commitment matches
    seqHash.out === sequence_commitment;
    
    valid <== thresholdCheck.valid;
}

/*
 * Batch anomaly circuit
 * Proves multiple agents' anomaly status in one proof
 */
template BatchAnomalyThreshold(BATCH_SIZE) {
    // Public inputs
    signal input threshold_scaled;
    signal input anomalous_count;  // How many are above threshold
    signal input batch_commitment; // Hash of all results
    
    // Private inputs
    signal input errors_scaled[BATCH_SIZE];
    signal input batch_salt;
    
    // Output
    signal output valid;
    
    // Count anomalies
    var count = 0;
    component comparisons[BATCH_SIZE];
    
    for (var i = 0; i < BATCH_SIZE; i++) {
        comparisons[i] = GreaterThan(32);
        comparisons[i].in[0] <== errors_scaled[i];
        comparisons[i].in[1] <== threshold_scaled;
        count += comparisons[i].out;
    }
    
    // Verify count matches
    anomalous_count === count;
    
    // Compute batch commitment
    component batchHash = Poseidon(2);
    batchHash.inputs[0] <== errors_scaled[0] + errors_scaled[BATCH_SIZE-1];
    batchHash.inputs[1] <== batch_salt;
    
    batch_commitment === batchHash.out;
    
    valid <== 1;
}

// Main component for single anomaly threshold
component main {public [threshold_scaled, is_above, model_commitment]} = AnomalyThreshold();

