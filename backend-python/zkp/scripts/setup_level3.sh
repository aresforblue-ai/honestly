#!/bin/bash
# Level 3 Setup Script
# Sets up Level 3 circuits with identity binding and static analysis

set -e

echo "🛡️  Level 3 High Assurance Setup"
echo "=================================="
echo ""

# Check prerequisites
echo "Checking prerequisites..."

# Check for circom
if ! command -v circom &> /dev/null; then
    echo "❌ circom not found. Install from https://docs.circom.io/"
    exit 1
fi
echo "✅ circom found"

# Check for snarkjs
if ! command -v snarkjs &> /dev/null; then
    echo "❌ snarkjs not found. Install with: npm install -g snarkjs"
    exit 1
fi
echo "✅ snarkjs found"

# Check for circomspect
if ! command -v circomspect &> /dev/null; then
    echo "⚠️  circomspect not found. Install with: cargo install circomspect"
    echo "   Static analysis will be skipped."
    SKIP_ANALYSIS=true
else
    echo "✅ circomspect found"
    SKIP_ANALYSIS=false
fi

# Check for circomlib
if [ ! -d "node_modules/circomlib" ]; then
    echo "Installing circomlib..."
    npm install circomlib
fi
echo "✅ circomlib found"

echo ""

# Create artifacts directory
mkdir -p artifacts/age_level3
mkdir -p artifacts/level3_inequality

# 1. Compile Level 3 Age Circuit
echo "1. Compiling Level 3 Age Circuit..."
echo "-----------------------------------"
circom circuits/age_level3.circom \
    --r1cs \
    --wasm \
    --sym \
    -o artifacts/age_level3

if [ $? -eq 0 ]; then
    echo "✅ Age circuit compiled"
else
    echo "❌ Age circuit compilation failed"
    exit 1
fi

# 2. Compile Level 3 Inequality Circuit
echo ""
echo "2. Compiling Level 3 Inequality Circuit..."
echo "------------------------------------------"
circom circuits/Level3Inequality.circom \
    --r1cs \
    --wasm \
    --sym \
    -o artifacts/level3_inequality

if [ $? -eq 0 ]; then
    echo "✅ Inequality circuit compiled"
else
    echo "❌ Inequality circuit compilation failed"
    exit 1
fi

# 3. Run static analysis (if circomspect available)
if [ "$SKIP_ANALYSIS" = false ]; then
    echo ""
    echo "3. Running Static Analysis..."
    echo "-----------------------------"
    
    echo "Analyzing age_level3.circom..."
    bash scripts/verify_circuit.sh circuits/age_level3.circom
    
    echo ""
    echo "Analyzing Level3Inequality.circom..."
    bash scripts/verify_circuit.sh circuits/Level3Inequality.circom
else
    echo ""
    echo "3. Skipping Static Analysis (circomspect not available)"
fi

# 4. Generate Groth16 setup (if ptau available)
if [ -f "artifacts/common/pot16_final.ptau" ]; then
    echo ""
    echo "4. Generating Groth16 Setup..."
    echo "------------------------------"
    
    echo "Setting up age_level3..."
    snarkjs groth16 setup \
        artifacts/age_level3/age_level3.r1cs \
        artifacts/common/pot16_final.ptau \
        artifacts/age_level3/age_level3_0000.zkey
    
    snarkjs zkey contribute \
        artifacts/age_level3/age_level3_0000.zkey \
        artifacts/age_level3/age_level3_final.zkey \
        -n "level3_contribution"
    
    snarkjs zkey export verificationkey \
        artifacts/age_level3/age_level3_final.zkey \
        artifacts/age_level3/verification_key.json
    
    echo "✅ Age circuit setup complete"
    
    echo ""
    echo "Setting up level3_inequality..."
    snarkjs groth16 setup \
        artifacts/level3_inequality/Level3Inequality.r1cs \
        artifacts/common/pot16_final.ptau \
        artifacts/level3_inequality/Level3Inequality_0000.zkey
    
    snarkjs zkey contribute \
        artifacts/level3_inequality/Level3Inequality_0000.zkey \
        artifacts/level3_inequality/Level3Inequality_final.zkey \
        -n "level3_contribution"
    
    snarkjs zkey export verificationkey \
        artifacts/level3_inequality/Level3Inequality_final.zkey \
        artifacts/level3_inequality/verification_key.json
    
    echo "✅ Inequality circuit setup complete"
    
    # Export Solidity verifier
    echo ""
    echo "5. Exporting Solidity Verifiers..."
    echo "-----------------------------------"
    
    snarkjs zkey export solidityverifier \
        artifacts/age_level3/age_level3_final.zkey \
        contracts/AgeVerifier.sol
    
    snarkjs zkey export solidityverifier \
        artifacts/level3_inequality/Level3Inequality_final.zkey \
        contracts/InequalityVerifier.sol
    
    echo "✅ Solidity verifiers exported"
else
    echo ""
    echo "4. Skipping Groth16 Setup (ptau file not found)"
    echo "   Download ptau with:"
    echo "   curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau"
fi

echo ""
echo "=================================="
echo "✅ Level 3 Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Review static analysis results"
echo "2. Test circuits with sample inputs"
echo "3. Deploy verifier contracts to blockchain"
echo "4. Integrate nullifier checking in your application"



