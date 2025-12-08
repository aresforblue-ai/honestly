#!/bin/bash
# Run All Production Validation Tests
# 
# This script runs comprehensive production validation:
# 1. Load Testing (k6) - Prove <200ms response time
# 2. Security Audit - Find vulnerabilities
# 3. Chaos Engineering - Test resilience
# 4. Documentation Review - "New Hire" test

set -e

BASE_URL=${BASE_URL:-"http://localhost:8000"}

echo "=========================================="
echo "PRODUCTION VALIDATION TEST SUITE"
echo "=========================================="
echo "Base URL: $BASE_URL"
echo ""

# Check prerequisites
echo "Checking prerequisites..."
echo ""

# Check k6
if command -v k6 &> /dev/null; then
    echo "✓ k6 installed"
else
    echo "✗ k6 not installed (required for load testing)"
    echo "  Install: https://k6.io/docs/getting-started/installation/"
fi

# Check Python dependencies
if python3 -c "import requests, docker" 2>/dev/null; then
    echo "✓ Python dependencies installed"
else
    echo "✗ Python dependencies missing"
    echo "  Install: pip install requests docker"
fi

echo ""
echo "=========================================="
echo "1. LOAD TESTING"
echo "=========================================="
if command -v k6 &> /dev/null; then
    cd load
    bash run_load_tests.sh
    cd ..
else
    echo "Skipping load tests (k6 not installed)"
fi

echo ""
echo "=========================================="
echo "2. SECURITY AUDIT"
echo "=========================================="
if python3 -c "import requests" 2>/dev/null; then
    cd security
    python3 security_audit.py "$BASE_URL"
    cd ..
else
    echo "Skipping security audit (requests not installed)"
fi

echo ""
echo "=========================================="
echo "3. CHAOS ENGINEERING"
echo "=========================================="
if python3 -c "import docker" 2>/dev/null && docker ps &>/dev/null; then
    cd chaos
    python3 chaos_tests.py "$BASE_URL"
    cd ..
else
    echo "Skipping chaos tests (docker not available)"
fi

echo ""
echo "=========================================="
echo "4. DOCUMENTATION REVIEW"
echo "=========================================="
echo "Please review: tests/documentation/documentation_test.md"
echo "Follow the 'New Hire' test procedure"
echo ""

echo "=========================================="
echo "ALL TESTS COMPLETE"
echo "=========================================="
echo ""
echo "Review results:"
echo "  - Load tests: tests/load/results_*.json"
echo "  - Security audit: tests/security/security_audit_report.json"
echo "  - Chaos tests: See output above"
echo "  - Documentation: Complete documentation_test.md checklist"
echo ""

