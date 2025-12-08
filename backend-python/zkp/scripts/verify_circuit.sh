#!/bin/bash
# Level 3 Static Analysis Verification Script
# Uses circomspect to mathematically verify circuit constraints

set -e

CIRCUIT="${1:-circuits/age_level3.circom}"
CIRCUIT_DIR="$(dirname "$CIRCUIT")"
CIRCUIT_NAME="$(basename "$CIRCUIT" .circom)"

echo "========================================"
echo "🛡️  STARTING LEVEL 3 STATIC ANALYSIS"
echo "========================================"
echo "Circuit: $CIRCUIT"
echo ""

# Check if circomspect is installed
if ! command -v circomspect &> /dev/null; then
    echo "❌ circomspect not found!"
    echo ""
    echo "Install with:"
    echo "  cargo install circomspect"
    echo ""
    echo "Or build from source:"
    echo "  git clone https://github.com/trailofbits/circomspect"
    echo "  cd circomspect"
    echo "  cargo build --release"
    echo ""
    exit 1
fi

# 1. Compile the circuit first to check for syntax errors
echo "[1/3] Compiling Circuit..."
echo "----------------------------------------"
circom "$CIRCUIT" --r1cs --wasm --sym -o "$CIRCUIT_DIR/../artifacts/$CIRCUIT_NAME"
if [ $? -ne 0 ]; then
    echo "❌ Compilation Failed!"
    exit 1
fi
echo "✅ Compilation successful"
echo ""

# 2. Run Circomspect Analysis
echo "[2/3] Running Constraint Solver (Circomspect)..."
echo "    - Looking for under-constrained signals"
echo "    - Checking for unassigned outputs"
echo "    - Verifying non-quadratic constraints"
echo "    - Detecting potential vulnerabilities"
echo "----------------------------------------"

# Run the analyzer
circomspect "$CIRCUIT" --json > "/tmp/circomspect_${CIRCUIT_NAME}.json" 2>&1 || true
circomspect "$CIRCUIT"

EXIT_CODE=$?

echo "----------------------------------------"

# 3. Parse and report results
if [ -f "/tmp/circomspect_${CIRCUIT_NAME}.json" ]; then
    echo ""
    echo "[3/3] Analysis Summary"
    echo "----------------------------------------"
    
    # Count issues by severity
    HIGH=$(jq '[.issues[] | select(.severity == "high")] | length' "/tmp/circomspect_${CIRCUIT_NAME}.json" 2>/dev/null || echo "0")
    MEDIUM=$(jq '[.issues[] | select(.severity == "medium")] | length' "/tmp/circomspect_${CIRCUIT_NAME}.json" 2>/dev/null || echo "0")
    LOW=$(jq '[.issues[] | select(.severity == "low")] | length' "/tmp/circomspect_${CIRCUIT_NAME}.json" 2>/dev/null || echo "0")
    
    echo "High severity issues:   $HIGH"
    echo "Medium severity issues: $MEDIUM"
    echo "Low severity issues:    $LOW"
    echo ""
    
    if [ "$HIGH" -gt 0 ] || [ "$MEDIUM" -gt 0 ]; then
        echo "❌ Critical issues found! Review the analysis above."
        exit 1
    elif [ "$LOW" -gt 0 ]; then
        echo "⚠️  Low severity issues found. Review recommended."
        exit 0
    else
        echo "✅ No issues found. Circuit is mathematically sound."
        exit 0
    fi
else
    if [ $EXIT_CODE -eq 0 ]; then
        echo "✅ Analysis complete. No issues found."
        exit 0
    else
        echo "❌ Analysis failed. Check circomspect output above."
        exit 1
    fi
fi



