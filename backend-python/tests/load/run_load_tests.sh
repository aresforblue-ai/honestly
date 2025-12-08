#!/bin/bash
# Load Testing Script
# Requires: k6 (https://k6.io/docs/getting-started/installation/)

set -e

BASE_URL=${BASE_URL:-"http://localhost:8000"}

echo "=========================================="
echo "Load Testing Suite"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Check if k6 is installed
if ! command -v k6 &> /dev/null; then
    echo "ERROR: k6 is not installed"
    echo "Install: https://k6.io/docs/getting-started/installation/"
    exit 1
fi

# Test 1: Ramp up to 100 concurrent users, hold for 5 minutes
echo "Test 1: Ramp up to 100 concurrent users (5 minute hold)"
echo "--------------------------------------------------------"
k6 run --out json=results_load_test.json \
       -e BASE_URL="$BASE_URL" \
       load_test.js

echo ""
echo "Results saved to: results_load_test.json"
echo ""

# Test 2: Spike test (10 to 500 users instantly)
echo "Test 2: Spike test (10 to 500 users instantly)"
echo "--------------------------------------------------------"
k6 run --out json=results_spike_test.json \
       -e BASE_URL="$BASE_URL" \
       spike_test.js

echo ""
echo "Results saved to: results_spike_test.json"
echo ""

# Summary
echo "=========================================="
echo "Load Testing Complete"
echo "=========================================="
echo "Review results:"
echo "  - results_load_test.json"
echo "  - results_spike_test.json"
echo ""
echo "Key metrics to check:"
echo "  - p(95) response time < 200ms"
echo "  - p(99) response time < 200ms"
echo "  - Error rate < 1%"
echo ""


