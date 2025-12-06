#!/bin/bash
# Test runner script for zkSNARK circuits

set -e

echo "=========================================="
echo "ZK-SNARK Circuit Test Suite"
echo "=========================================="

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "ERROR: Node.js is not installed"
    exit 1
fi

# Check if circuits are built
ZKP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACTS_DIR="$ZKP_DIR/artifacts"

if [ ! -f "$ARTIFACTS_DIR/age/age.wasm" ] || [ ! -f "$ARTIFACTS_DIR/age/age_final.zkey" ]; then
    echo "ERROR: Age circuit not built"
    echo "Run: cd $ZKP_DIR && npm install && npm run build:age && npm run setup:age && npm run contribute:age"
    exit 1
fi

if [ ! -f "$ARTIFACTS_DIR/authenticity/authenticity.wasm" ] || [ ! -f "$ARTIFACTS_DIR/authenticity/authenticity_final.zkey" ]; then
    echo "ERROR: Authenticity circuit not built"
    echo "Run: cd $ZKP_DIR && npm install && npm run build:auth && npm run setup:auth && npm run contribute:auth"
    exit 1
fi

# Run Python tests
echo ""
echo "Running Python test suite..."
python3 "$ZKP_DIR/tests/test_circuits.py"

echo ""
echo "=========================================="
echo "Tests completed"
echo "=========================================="

