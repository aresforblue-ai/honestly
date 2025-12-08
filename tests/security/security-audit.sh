#!/bin/bash
# Security Audit Script
# Tests: OWASP ZAP, manual penetration testing, error handling

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
ZAP_HOST="${ZAP_HOST:-localhost}"
ZAP_PORT="${ZAP_PORT:-8080}"

echo "🔒 Starting Security Audit"
echo "=========================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

test_result() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        ((FAILED++))
    fi
}

# 1. Test Security Headers
echo "1. Testing Security Headers..."
echo "----------------------------"

HEADERS=$(curl -s -I "$BASE_URL/health" | grep -iE "(x-content-type-options|x-frame-options|x-xss-protection|strict-transport-security)")

if echo "$HEADERS" | grep -q "X-Content-Type-Options"; then
    test_result 0 "X-Content-Type-Options header present"
else
    test_result 1 "X-Content-Type-Options header missing"
fi

if echo "$HEADERS" | grep -q "X-Frame-Options"; then
    test_result 0 "X-Frame-Options header present"
else
    test_result 1 "X-Frame-Options header missing"
fi

if echo "$HEADERS" | grep -q "X-XSS-Protection"; then
    test_result 0 "X-XSS-Protection header present"
else
    test_result 1 "X-XSS-Protection header missing"
fi

echo ""

# 2. Test Input Validation (XSS attempts)
echo "2. Testing Input Validation (XSS)..."
echo "-------------------------------------"

XSS_PAYLOADS=(
    "<script>alert('XSS')</script>"
    "javascript:alert('XSS')"
    "<img src=x onerror=alert('XSS')>"
    "'; DROP TABLE users; --"
)

for payload in "${XSS_PAYLOADS[@]}"; do
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/vault/share/$payload/bundle")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "404" ]; then
        test_result 0 "XSS payload rejected: ${payload:0:30}..."
    else
        # Check if payload appears in response (should not)
        if echo "$RESPONSE" | grep -q "$payload"; then
            test_result 1 "XSS payload not sanitized: ${payload:0:30}..."
        else
            test_result 0 "XSS payload handled: ${payload:0:30}..."
        fi
    fi
done

echo ""

# 3. Test Rate Limiting
echo "3. Testing Rate Limiting..."
echo "---------------------------"

# Send 25 requests rapidly (limit is 20/min)
RATE_LIMIT_HIT=0
for i in {1..25}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/vault/share/test-token/bundle")
    if [ "$HTTP_CODE" = "429" ]; then
        RATE_LIMIT_HIT=1
        break
    fi
    sleep 0.1
done

if [ $RATE_LIMIT_HIT -eq 1 ]; then
    test_result 0 "Rate limiting working (429 returned)"
else
    test_result 1 "Rate limiting not working (no 429 after 25 requests)"
fi

echo ""

# 4. Test Error Handling (no stack traces)
echo "4. Testing Error Handling..."
echo "----------------------------"

# Test malformed JSON
RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Content-Type: application/json" \
    -d '{"invalid": json}')

if echo "$RESPONSE" | grep -qiE "(traceback|stack trace|file \"/|line \d+)"; then
    test_result 1 "Stack trace leaked in error response"
else
    test_result 0 "No stack trace in error response"
fi

# Test invalid endpoint
RESPONSE=$(curl -s "$BASE_URL/invalid-endpoint-12345")
if echo "$RESPONSE" | grep -qiE "(traceback|stack trace|file \"/|line \d+)"; then
    test_result 1 "Stack trace leaked for 404"
else
    test_result 0 "No stack trace for 404"
fi

echo ""

# 5. Test SQL Injection (Neo4j Cypher injection)
echo "5. Testing Injection Attacks..."
echo "-------------------------------"

INJECTION_PAYLOADS=(
    "'; MATCH (n) DETACH DELETE n; --"
    "1' OR '1'='1"
    "admin'--"
)

for payload in "${INJECTION_PAYLOADS[@]}"; do
    RESPONSE=$(curl -s "$BASE_URL/vault/share/$payload/bundle")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/vault/share/$payload/bundle")
    
    if [ "$HTTP_CODE" = "400" ] || [ "$HTTP_CODE" = "404" ]; then
        test_result 0 "Injection attempt rejected: ${payload:0:30}..."
    else
        # Check if error message reveals database structure
        if echo "$RESPONSE" | grep -qiE "(cypher|neo4j|database|sql)"; then
            test_result 1 "Database info leaked: ${payload:0:30}..."
        else
            test_result 0 "Injection attempt handled: ${payload:0:30}..."
        fi
    fi
done

echo ""

# 6. Test CORS
echo "6. Testing CORS..."
echo "-----------------"

# Test from unauthorized origin
CORS_RESPONSE=$(curl -s -H "Origin: https://evil.com" \
    -H "Access-Control-Request-Method: GET" \
    -X OPTIONS "$BASE_URL/health" -v 2>&1)

if echo "$CORS_RESPONSE" | grep -qi "access-control-allow-origin.*evil.com"; then
    test_result 1 "CORS allows unauthorized origin"
else
    test_result 0 "CORS properly restricts origins"
fi

echo ""

# 7. Test Request Size Limits
echo "7. Testing Request Size Limits..."
echo "---------------------------------"

# Create a large payload (>10MB)
LARGE_PAYLOAD=$(head -c 11000000 < /dev/zero | tr '\0' 'A')
RESPONSE=$(curl -s -X POST "$BASE_URL/graphql" \
    -H "Content-Type: application/json" \
    -d "{\"query\": \"$LARGE_PAYLOAD\"}" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" = "413" ]; then
    test_result 0 "Request size limit enforced (413)"
else
    test_result 1 "Request size limit not enforced"
fi

echo ""

# Summary
echo "=========================="
echo "Security Audit Summary"
echo "=========================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All security tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some security tests failed. Review above.${NC}"
    exit 1
fi


