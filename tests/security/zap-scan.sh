#!/bin/bash
# OWASP ZAP Security Scan Script
# Requires: ZAP running on ZAP_HOST:ZAP_PORT

set -e

BASE_URL="${BASE_URL:-http://localhost:8000}"
ZAP_HOST="${ZAP_HOST:-localhost}"
ZAP_PORT="${ZAP_PORT:-8080}"
ZAP_API="http://${ZAP_HOST}:${ZAP_PORT}"

echo "🔒 Starting OWASP ZAP Security Scan"
echo "===================================="
echo ""

# Check if ZAP is running
if ! curl -s "${ZAP_API}/JSON/core/view/version/" > /dev/null; then
    echo "❌ ZAP is not running at ${ZAP_API}"
    echo "Start ZAP with: zap.sh -daemon -host 0.0.0.0 -port ${ZAP_PORT}"
    exit 1
fi

echo "✅ ZAP is running"
echo ""

# Start spider scan
echo "1. Starting spider scan..."
SPIDER_ID=$(curl -s "${ZAP_API}/JSON/spider/action/scan/?url=${BASE_URL}" | jq -r '.scan')
echo "   Spider scan ID: $SPIDER_ID"

# Wait for spider to complete
while true; do
    STATUS=$(curl -s "${ZAP_API}/JSON/spider/view/status/?scanId=${SPIDER_ID}" | jq -r '.status')
    echo "   Spider status: ${STATUS}%"
    if [ "$STATUS" = "100" ]; then
        break
    fi
    sleep 2
done

echo "✅ Spider scan complete"
echo ""

# Start active scan
echo "2. Starting active scan (this may take a while)..."
ACTIVE_SCAN_ID=$(curl -s "${ZAP_API}/JSON/ascan/action/scan/?url=${BASE_URL}" | jq -r '.scan')
echo "   Active scan ID: $ACTIVE_SCAN_ID"

# Wait for active scan to complete
while true; do
    STATUS=$(curl -s "${ZAP_API}/JSON/ascan/view/status/?scanId=${ACTIVE_SCAN_ID}" | jq -r '.status')
    echo "   Active scan status: ${STATUS}%"
    if [ "$STATUS" = "100" ]; then
        break
    fi
    sleep 5
done

echo "✅ Active scan complete"
echo ""

# Generate report
echo "3. Generating security report..."
REPORT=$(curl -s "${ZAP_API}/JSON/core/view/alerts/?baseurl=${BASE_URL}")

# Count alerts by risk level
HIGH=$(echo "$REPORT" | jq '[.alerts[] | select(.risk == "High")] | length')
MEDIUM=$(echo "$REPORT" | jq '[.alerts[] | select(.risk == "Medium")] | length')
LOW=$(echo "$REPORT" | jq '[.alerts[] | select(.risk == "Low")] | length')
INFO=$(echo "$REPORT" | jq '[.alerts[] | select(.risk == "Informational")] | length')

echo ""
echo "=========================="
echo "ZAP Scan Results"
echo "=========================="
echo "High Risk:      $HIGH"
echo "Medium Risk:    $MEDIUM"
echo "Low Risk:       $LOW"
echo "Informational:  $INFO"
echo ""

# Save detailed report
REPORT_FILE="zap-report-$(date +%Y%m%d-%H%M%S).json"
echo "$REPORT" | jq '.' > "$REPORT_FILE"
echo "Detailed report saved to: $REPORT_FILE"

# Export HTML report
HTML_REPORT="zap-report-$(date +%Y%m%d-%H%M%S).html"
curl -s "${ZAP_API}/OTHER/core/other/htmlreport/" > "$HTML_REPORT"
echo "HTML report saved to: $HTML_REPORT"

# Fail if high-risk issues found
if [ "$HIGH" -gt 0 ]; then
    echo ""
    echo "❌ High-risk security issues found! Review the reports."
    exit 1
else
    echo ""
    echo "✅ No high-risk security issues found!"
    exit 0
fi


