# Security Testing Guide

## Prerequisites

```bash
pip install requests
```

## Running Tests

### Automated Security Tests

```bash
cd tests/security
python security_test.py
```

**Tests Include:**
- XSS injection attempts
- Rate limiting bypass attempts
- Error handling (stack trace leaks)
- SQL/Cypher injection attempts
- Security headers verification

### OWASP ZAP Testing

```bash
# Install OWASP ZAP
# macOS
brew install --cask owasp-zap

# Linux
wget https://github.com/zaproxy/zaproxy/releases/download/v2.14.0/ZAP_2.14.0_Linux.tar.gz
tar -xzf ZAP_2.14.0_Linux.tar.gz

# Run ZAP
./zap.sh -quickurl http://localhost:8000 -quickprogress
```

### Manual Penetration Testing

#### Test Rate Limiting Bypass

```bash
# Rapid requests
for i in {1..30}; do
  curl http://localhost:8000/vault/share/test_token/bundle
  sleep 0.1
done

# Should see 429 after ~20 requests
```

#### Test Error Handling

```bash
# Malformed JSON
curl -X POST http://localhost:8000/vault/upload \
  -H "Content-Type: application/json" \
  -d "invalid json"

# Should return 422, not 500 with stack trace
```

#### Test Input Validation

```bash
# XSS attempt
curl "http://localhost:8000/vault/share/<script>alert('XSS')</script>"

# Should sanitize or reject, not execute
```

## Expected Results

### ✅ All Tests Should Pass

- **XSS Tests**: All payloads rejected/sanitized
- **Rate Limiting**: Bypass attempts fail
- **Error Handling**: No stack traces leaked
- **Injection Tests**: All payloads rejected
- **Security Headers**: All headers present

## Continuous Security Testing

### CI/CD Integration

```yaml
# .github/workflows/security-test.yml
name: Security Test
on: [push]
jobs:
  security-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install requests
      - name: Run security tests
        run: python tests/security/security_test.py
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: security-results
          path: security-test-results.json
```

## OWASP ZAP Integration

### Automated Scan

```bash
# Start ZAP daemon
zap.sh -daemon -port 8080

# Run quick scan
zap-cli quick-scan http://localhost:8000

# Generate report
zap-cli report -o zap-report.html -f html
```

## Remediation

### If Tests Fail

1. **XSS Vulnerabilities:**
   - Review input validation
   - Check sanitization functions
   - Verify CSP headers

2. **Rate Limiting Bypass:**
   - Review rate limit implementation
   - Check IP detection
   - Verify cleanup logic

3. **Error Handling Leaks:**
   - Review error handlers
   - Remove stack traces in production
   - Use structured error responses

4. **Missing Security Headers:**
   - Review security middleware
   - Verify header configuration
   - Test in production


