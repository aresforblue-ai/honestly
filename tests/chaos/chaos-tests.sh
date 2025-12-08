#!/bin/bash
# Chaos Engineering Tests
# Tests resilience when dependencies fail

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "🌪️  Starting Chaos Engineering Tests"
echo "====================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# Check if service is healthy before starting
echo "Pre-test: Verifying service is healthy..."
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Service is healthy${NC}"
else
    echo -e "${RED}❌ Service is not healthy. Aborting.${NC}"
    exit 1
fi
echo ""

# Test 1: Kill Redis
echo "Test 1: Redis Failure"
echo "---------------------"
echo "Stopping Redis container..."

if docker ps | grep -q "honestly-redis"; then
    docker stop honestly-redis-min 2>/dev/null || docker stop honestly-redis 2>/dev/null || true
    echo "Redis stopped"
    sleep 2
    
    # Service should still respond (fallback to in-memory)
    echo "Checking service response..."
    RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "200" ]; then
        test_result 0 "Service responds without Redis (fallback working)"
    else
        test_result 1 "Service failed when Redis unavailable"
    fi
    
    # Rate limiting should still work (in-memory fallback)
    echo "Testing rate limiting fallback..."
    RATE_LIMIT_WORKING=0
    for i in {1..25}; do
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/vault/share/test-token/bundle")
        if [ "$HTTP_CODE" = "429" ]; then
            RATE_LIMIT_WORKING=1
            break
        fi
        sleep 0.1
    done
    
    if [ $RATE_LIMIT_WORKING -eq 1 ]; then
        test_result 0 "Rate limiting works without Redis (in-memory fallback)"
    else
        test_result 1 "Rate limiting failed without Redis"
    fi
    
    # Restart Redis
    echo "Restarting Redis..."
    docker start honestly-redis-min 2>/dev/null || docker start honestly-redis 2>/dev/null || true
    sleep 3
    
    # Verify Redis is back
    if docker ps | grep -q "redis"; then
        test_result 0 "Redis recovered successfully"
    else
        test_result 1 "Redis did not recover"
    fi
else
    echo -e "${YELLOW}⚠️  Redis container not found. Skipping Redis test.${NC}"
fi

echo ""

# Test 2: Kill Neo4j
echo "Test 2: Neo4j Failure"
echo "---------------------"
echo "Stopping Neo4j container..."

if docker ps | grep -q "honestly-neo4j"; then
    docker stop honestly-neo4j-min 2>/dev/null || docker stop honestly-neo4j 2>/dev/null || true
    echo "Neo4j stopped"
    sleep 2
    
    # Health check should show not ready
    echo "Checking readiness endpoint..."
    READINESS=$(curl -s "$BASE_URL/health/ready")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health/ready")
    
    if [ "$HTTP_CODE" = "503" ]; then
        test_result 0 "Readiness check correctly reports not ready (503)"
    else
        test_result 1 "Readiness check did not report failure"
    fi
    
    # Basic health should still work
    HEALTH=$(curl -s "$BASE_URL/health")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health")
    
    if [ "$HTTP_CODE" = "200" ]; then
        test_result 0 "Basic health check still works without Neo4j"
    else
        test_result 1 "Basic health check failed without Neo4j"
    fi
    
    # Endpoints that need Neo4j should fail gracefully
    echo "Testing endpoints that require Neo4j..."
    RESPONSE=$(curl -s "$BASE_URL/vault/share/test-token/bundle")
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/vault/share/test-token/bundle")
    
    if [ "$HTTP_CODE" = "503" ] || [ "$HTTP_CODE" = "500" ]; then
        # Check if error message is safe (no stack trace)
        if echo "$RESPONSE" | grep -qiE "(traceback|stack trace|file \"/)"; then
            test_result 1 "Error response leaks stack trace"
        else
            test_result 0 "Endpoints fail gracefully without Neo4j"
        fi
    else
        test_result 1 "Endpoints did not handle Neo4j failure"
    fi
    
    # Restart Neo4j
    echo "Restarting Neo4j..."
    docker start honestly-neo4j-min 2>/dev/null || docker start honestly-neo4j 2>/dev/null || true
    sleep 5  # Neo4j takes longer to start
    
    # Verify Neo4j is back
    if docker ps | grep -q "neo4j"; then
        # Wait for Neo4j to be ready
        sleep 3
        READINESS=$(curl -s "$BASE_URL/health/ready")
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health/ready")
        
        if [ "$HTTP_CODE" = "200" ]; then
            test_result 0 "Neo4j recovered and service is ready"
        else
            test_result 1 "Neo4j recovered but service not ready"
        fi
    else
        test_result 1 "Neo4j did not recover"
    fi
else
    echo -e "${YELLOW}⚠️  Neo4j container not found. Skipping Neo4j test.${NC}"
fi

echo ""

# Test 3: Network latency simulation
echo "Test 3: Network Latency"
echo "------------------------"
echo "Simulating network latency..."

# This would require tc (traffic control) or similar
# For now, we'll just verify the service handles slow responses
echo -e "${YELLOW}⚠️  Network latency simulation requires tc (traffic control).${NC}"
echo -e "${YELLOW}   Manual test: Add latency with 'tc qdisc add dev eth0 root netem delay 500ms'${NC}"

echo ""

# Test 4: High load during failure
echo "Test 4: High Load During Failure"
echo "---------------------------------"
echo "This test requires running load tests while dependencies are down."
echo -e "${YELLOW}⚠️  Manual test: Run 'k6 run tests/load/k6-load-test.js' while Redis/Neo4j are down${NC}"

echo ""

# Summary
echo "=========================="
echo "Chaos Test Summary"
echo "=========================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All chaos tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some chaos tests failed. Review above.${NC}"
    exit 1
fi


