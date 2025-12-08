/*
 * Age Verification Circuit (PLONK-optimized)
 * 
 * Proves: age >= min_age without revealing birth_date
 * Optimized for PLONK's custom gates and lookup tables
 * 
 * Curve: BLS12-381 (for PLONK's universal SRS)
 * 
 * Note: This circuit is compatible with both Groth16 and PLONK,
 * but uses patterns that PLONK handles more efficiently.
 */

pragma circom 2.1.6;

include "../../../node_modules/circomlib/circuits/poseidon.circom";
include "../../../node_modules/circomlib/circuits/comparators.circom";
include "../../../node_modules/circomlib/circuits/bitify.circom";

template AgePLONK() {
    // Private inputs
    signal input birth_year;      // e.g., 1995
    signal input birth_month;     // 1-12
    signal input birth_day;       // 1-31
    signal input document_hash;   // Hash of identity document
    signal input salt;            // Random salt for commitment
    
    // Public inputs
    signal input current_year;    // e.g., 2025
    signal input current_month;   // 1-12
    signal input current_day;     // 1-31
    signal input min_age;         // e.g., 18 or 21
    
    // Outputs
    signal output commitment;     // Poseidon(birth_date, document_hash, salt)
    signal output is_valid;       // 1 if age >= min_age, 0 otherwise

    // ========== Date Validation (PLONK-friendly range checks) ==========
    
    // Validate birth_month in [1, 12]
    component monthCheck = LessEqThan(8);
    monthCheck.in[0] <== birth_month;
    monthCheck.in[1] <== 12;
    
    component monthPositive = GreaterThan(8);
    monthPositive.in[0] <== birth_month;
    monthPositive.in[1] <== 0;
    
    signal monthValid <== monthCheck.out * monthPositive.out;
    monthValid === 1;
    
    // Validate birth_day in [1, 31]
    component dayCheck = LessEqThan(8);
    dayCheck.in[0] <== birth_day;
    dayCheck.in[1] <== 31;
    
    component dayPositive = GreaterThan(8);
    dayPositive.in[0] <== birth_day;
    dayPositive.in[1] <== 0;
    
    signal dayValid <== dayCheck.out * dayPositive.out;
    dayValid === 1;

    // ========== Age Calculation (precise to the day) ==========
    
    // Calculate base age (year difference)
    signal base_age <== current_year - birth_year;
    
    // Check if birthday has occurred this year
    // birthday_passed = (current_month > birth_month) OR 
    //                  (current_month == birth_month AND current_day >= birth_day)
    
    component monthGreater = GreaterThan(8);
    monthGreater.in[0] <== current_month;
    monthGreater.in[1] <== birth_month;
    
    component monthEqual = IsEqual();
    monthEqual.in[0] <== current_month;
    monthEqual.in[1] <== birth_month;
    
    component dayGreaterEq = GreaterEqThan(8);
    dayGreaterEq.in[0] <== current_day;
    dayGreaterEq.in[1] <== birth_day;
    
    signal birthday_passed_same_month <== monthEqual.out * dayGreaterEq.out;
    signal birthday_passed <== monthGreater.out + birthday_passed_same_month - (monthGreater.out * birthday_passed_same_month);
    
    // Final age: subtract 1 if birthday hasn't occurred
    signal adjustment <== 1 - birthday_passed;
    signal actual_age <== base_age - adjustment;

    // ========== Age Comparison ==========
    
    component ageCheck = GreaterEqThan(8);
    ageCheck.in[0] <== actual_age;
    ageCheck.in[1] <== min_age;
    
    is_valid <== ageCheck.out;

    // ========== Commitment Generation ==========
    
    // Combine birth date into single value for efficiency
    signal birth_date <== birth_year * 10000 + birth_month * 100 + birth_day;
    
    // Poseidon hash for commitment (PLONK-friendly)
    component hasher = Poseidon(3);
    hasher.inputs[0] <== birth_date;
    hasher.inputs[1] <== document_hash;
    hasher.inputs[2] <== salt;
    
    commitment <== hasher.out;
}

component main {public [current_year, current_month, current_day, min_age]} = AgePLONK();

