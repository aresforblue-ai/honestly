/**
 * Client-side Poseidon hash generation for Level 3 identity binding
 * Matches the circuit's Poseidon hash computation
 */
const { buildPoseidon } = require("circomlibjs");

/**
 * Generate Poseidon hash for identity binding (4 inputs)
 * Matches: Poseidon(birthTs, salt, userID, documentHash)
 * 
 * @param {bigint|string} birthTs - Birth timestamp
 * @param {bigint|string} salt - Random salt
 * @param {bigint|string} userID - User identifier
 * @param {bigint|string} documentHash - Document hash (field element)
 * @returns {Promise<string>} Poseidon hash as hex string
 */
async function generateIdentityNullifier(birthTs, salt, userID, documentHash) {
    const poseidon = await buildPoseidon();
    
    // Convert inputs to BigInt
    const inputs = [
        BigInt(birthTs),
        BigInt(salt),
        BigInt(userID),
        BigInt(documentHash)
    ];
    
    // Compute Poseidon hash
    const hash = poseidon(inputs);
    
    // Convert to hex string (remove 0x prefix for consistency)
    const hashHex = poseidon.F.toString(hash, 16);
    
    return hashHex;
}

/**
 * Generate Poseidon hash for document hash (single input)
 * Used to convert document hash to field element
 * 
 * @param {string} documentHashHex - Document hash as hex string
 * @returns {Promise<bigint>} Field element representation
 */
async function hashDocumentHash(documentHashHex) {
    const poseidon = await buildPoseidon();
    
    // Convert hex to BigInt
    const hashBigInt = BigInt("0x" + documentHashHex.replace(/^0x/, ""));
    
    // Hash it (single input Poseidon)
    const hash = poseidon([hashBigInt]);
    
    return poseidon.F.toObject(hash);
}

/**
 * Verify nullifier matches expected value
 * 
 * @param {string} nullifier - Nullifier from proof
 * @param {object} inputs - Input values used in proof
 * @returns {Promise<boolean>} True if nullifier is valid
 */
async function verifyNullifier(nullifier, inputs) {
    const { birthTs, salt, userID, documentHashHex } = inputs;
    
    // Hash document hash first
    const docHashField = await hashDocumentHash(documentHashHex);
    
    // Generate expected nullifier
    const expectedNullifier = await generateIdentityNullifier(
        birthTs,
        salt,
        userID,
        docHashField
    );
    
    // Compare (case-insensitive)
    return nullifier.toLowerCase() === expectedNullifier.toLowerCase();
}

module.exports = {
    generateIdentityNullifier,
    hashDocumentHash,
    verifyNullifier
};

// Example usage
if (require.main === module) {
    (async () => {
        const birthTs = "631152000"; // Example timestamp
        const salt = "1234567890123456789";
        const userID = "0x1234567890123456789012345678901234567890";
        const documentHashHex = "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yzab5678cdef";
        
        const docHashField = await hashDocumentHash(documentHashHex);
        const nullifier = await generateIdentityNullifier(
            birthTs,
            salt,
            userID,
            docHashField
        );
        
        console.log("Document Hash (field element):", docHashField.toString());
        console.log("Nullifier:", nullifier);
        
        // Verify
        const isValid = await verifyNullifier(nullifier, {
            birthTs,
            salt,
            userID,
            documentHashHex
        });
        
        console.log("Nullifier valid:", isValid);
    })();
}



