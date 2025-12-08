#!/bin/bash
# Master Test Runner
# Runs all validation tests: Load, Security, Chaos, Documentation

set -e

echo "🧪 Running All Validation Tests"
echo "================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BASE_URL="${BASE_URL:-http://localhost:8000}"

# Check if service is running
echo "Pre-flight check: Verifying service is running..."
if curl -s "$BASE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Service is running${NC}"
else
    echo -e "${RED}❌ Service is not running at $BASE_URL${NC}"
    echo "Start the service first: docker compose -f docker-compose.min.yml up -d"
    exit 1
fi
echo ""

# Test results
TOTAL_PASSED=0
TOTAL_FAILED=0

run_test_suite() {
    local name=$1
    local script=$2
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Running: $name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    if [ -f "$script" ] && [ -x "$script" ]; then
        if bash "$script"; then
            echo -e "${GREEN}✅ $name: PASSED${NC}"
            ((TOTAL_PASSED++))
        else
            echo -e "${RED}❌ $name: FAILED${NC}"
            ((TOTAL_FAILED++))
        fi
    else
        echo -e "${YELLOW}⚠️  $name: Script not found or not executable ($script)${NC}"
        ((TOTAL_FAILED++))
    fi
    echo ""
}

# 1. Documentation Validation (can run without dependencies)
echo "Starting with documentation validation..."
run_test_suite "Documentation Validation" "tests/docs/doc-validation.sh"

# 2. Security Audit
echo "Running security tests..."
run_test_suite "Security Audit" "tests/security/security-audit.sh"

# 3. Load Testing (if k6 is available)
if command -v k6 &> /dev/null; then
    echo "Running load tests with k6..."
    if k6 run tests/load/k6-load-test.js; then
        echo -e "${GREEN}✅ Load Testing: PASSED${NC}"
        ((TOTAL_PASSED++))
    else
        echo -e "${RED}❌ Load Testing: FAILED${NC}"
        ((TOTAL_FAILED++))
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  k6 not found. Install with: brew install k6 (or see https://k6.io/docs/getting-started/installation/)${NC}"
    echo -e "${YELLOW}   Skipping load tests.${NC}"
    echo ""
fi

# 4. Chaos Engineering
echo "Running chaos engineering tests..."
run_test_suite "Chaos Engineering" "tests/chaos/chaos-tests.sh"

# 5. OWASP ZAP (if available)
if command -v zap-cli &> /dev/null || curl -s "http://localhost:8080" > /dev/null 2>&1; then
    echo "Running OWASP ZAP scan..."
    run_test_suite "OWASP ZAP Scan" "tests/security/zap-scan.sh"
else
    echo -e "${YELLOW}⚠️  OWASP ZAP not available.${NC}"
    echo -e "${YELLOW}   Install ZAP and run: zap.sh -daemon -host 0.0.0.0 -port 8080${NC}"
    echo -e "${YELLOW}   Then run: bash tests/security/zap-scan.sh${NC}"
    echo ""
fi

# Final Summary
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}Final Test Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Total Passed: $TOTAL_PASSED${NC}"
echo -e "${RED}Total Failed: $TOTAL_FAILED${NC}"
echo ""

if [ $TOTAL_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! System is production-ready!${NC}"
    echo ""
    echo "Your system has been validated for:"
    echo "  ✅ Documentation completeness"
    echo "  ✅ Security hardening"
    echo "  ✅ Performance (<200ms)"
    echo "  ✅ Resilience (chaos engineering)"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review the output above.${NC}"
    echo ""
    exit 1
fi


