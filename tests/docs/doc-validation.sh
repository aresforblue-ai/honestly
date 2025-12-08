#!/bin/bash
# Documentation Validation Script
# Tests: Can a new user follow the docs to get the system running?

set -e

echo "📚 Documentation Validation Test"
echo "================================="
echo ""
echo "This script validates that the documentation is complete and accurate."
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

# Check if required documentation files exist
echo "1. Checking Documentation Files..."
echo "----------------------------------"

DOCS=(
    "SETUP.md"
    "PRODUCTION.md"
    "PRODUCTION-READY.md"
    "README.md"
    "backend-python/zkp/README.md"
)

for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        test_result 0 "Documentation file exists: $doc"
    else
        test_result 1 "Documentation file missing: $doc"
    fi
done

echo ""

# Check if SETUP.md has all required sections
echo "2. Validating SETUP.md Content..."
echo "-----------------------------------"

if [ -f "SETUP.md" ]; then
    REQUIRED_SECTIONS=(
        "Prerequisites"
        "Quick Start"
        "Installation"
        "Configuration"
        "Running"
    )
    
    SETUP_CONTENT=$(cat SETUP.md)
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if echo "$SETUP_CONTENT" | grep -qi "$section"; then
            test_result 0 "SETUP.md contains section: $section"
        else
            test_result 1 "SETUP.md missing section: $section"
        fi
    done
else
    test_result 1 "SETUP.md not found"
fi

echo ""

# Check if PRODUCTION.md has all required sections
echo "3. Validating PRODUCTION.md Content..."
echo "--------------------------------------"

if [ -f "PRODUCTION.md" ]; then
    REQUIRED_SECTIONS=(
        "Security"
        "Performance"
        "Monitoring"
        "Deployment"
        "Environment Variables"
    )
    
    PROD_CONTENT=$(cat PRODUCTION.md)
    for section in "${REQUIRED_SECTIONS[@]}"; do
        if echo "$PROD_CONTENT" | grep -qi "$section"; then
            test_result 0 "PRODUCTION.md contains section: $section"
        else
            test_result 1 "PRODUCTION.md missing section: $section"
        fi
    done
else
    test_result 1 "PRODUCTION.md not found"
fi

echo ""

# Check if docker-compose files are documented
echo "4. Validating Docker Compose Documentation..."
echo "---------------------------------------------"

if [ -f "docker-compose.min.yml" ]; then
    if grep -q "docker-compose.min.yml" SETUP.md || grep -q "docker-compose.min.yml" PRODUCTION.md; then
        test_result 0 "docker-compose.min.yml is documented"
    else
        test_result 1 "docker-compose.min.yml not documented"
    fi
else
    test_result 1 "docker-compose.min.yml not found"
fi

echo ""

# Check if environment variables are documented
echo "5. Validating Environment Variables Documentation..."
echo "-----------------------------------------------------"

ENV_VARS=(
    "NEO4J_URI"
    "NEO4J_USER"
    "NEO4J_PASS"
    "REDIS_HOST"
    "ALLOWED_ORIGINS"
)

DOCS_CONTENT=$(cat SETUP.md PRODUCTION.md 2>/dev/null || echo "")
for var in "${ENV_VARS[@]}"; do
    if echo "$DOCS_CONTENT" | grep -q "$var"; then
        test_result 0 "Environment variable documented: $var"
    else
        test_result 1 "Environment variable not documented: $var"
    fi
done

echo ""

# Check if health endpoints are documented
echo "6. Validating Health Endpoints Documentation..."
echo "-----------------------------------------------"

HEALTH_ENDPOINTS=(
    "/health"
    "/health/ready"
    "/health/live"
    "/health/metrics"
)

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
    if echo "$DOCS_CONTENT" | grep -q "$endpoint"; then
        test_result 0 "Health endpoint documented: $endpoint"
    else
        test_result 1 "Health endpoint not documented: $endpoint"
    fi
done

echo ""

# Check if code examples are valid (basic syntax check)
echo "7. Validating Code Examples..."
echo "------------------------------"

# Check if bash scripts are executable and have shebang
SCRIPTS=(
    "tests/security/security-audit.sh"
    "tests/chaos/chaos-tests.sh"
    "tests/docs/doc-validation.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ]; then
        if head -n1 "$script" | grep -q "#!/bin/bash"; then
            test_result 0 "Script has shebang: $script"
        else
            test_result 1 "Script missing shebang: $script"
        fi
        
        if [ -x "$script" ]; then
            test_result 0 "Script is executable: $script"
        else
            test_result 1 "Script not executable: $script"
        fi
    fi
done

echo ""

# Check if README has quick start
echo "8. Validating README Quick Start..."
echo "------------------------------------"

if [ -f "README.md" ]; then
    README_CONTENT=$(cat README.md)
    if echo "$README_CONTENT" | grep -qiE "(quick start|getting started|install)"; then
        test_result 0 "README contains quick start section"
    else
        test_result 1 "README missing quick start section"
    fi
else
    test_result 1 "README.md not found"
fi

echo ""

# Summary
echo "=========================="
echo "Documentation Validation Summary"
echo "=========================="
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All documentation checks passed!${NC}"
    echo ""
    echo "Next step: Have a colleague (or yourself on a fresh machine) follow"
    echo "the documentation to set up the system from scratch."
    exit 0
else
    echo -e "${RED}❌ Some documentation checks failed. Review above.${NC}"
    exit 1
fi


