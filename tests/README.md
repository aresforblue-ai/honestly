# Validation Test Suite

Comprehensive test suite to validate production readiness: Load Testing, Security Audit, Chaos Engineering, and Documentation Review.

## 🎯 Test Goals

1. **Load Testing**: Prove <200ms response time (99th percentile)
2. **Security Audit**: Verify security hardening works
3. **Chaos Engineering**: Test resilience when dependencies fail
4. **Documentation Review**: Ensure docs are complete and accurate

## 🚀 Quick Start

```bash
# Run all tests
bash tests/run-all-tests.sh

# Or run individually:
bash tests/docs/doc-validation.sh      # Documentation
bash tests/security/security-audit.sh # Security
bash tests/chaos/chaos-tests.sh       # Chaos engineering
k6 run tests/load/k6-load-test.js     # Load testing
```

## 📋 Test Suites

### 1. Load Testing

**Tools**: k6, Locust, Artillery

**Tests**:
- Ramp-up to 100 concurrent users, hold for 5 minutes
- Spike test: 10 → 500 users instantly
- Target: 99th percentile < 200ms

**Run**:
```bash
# k6
k6 run tests/load/k6-load-test.js

# Locust
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Artillery
artillery run tests/load/artillery-config.yml
```

### 2. Security Audit

**Tests**:
- Security headers validation
- XSS/injection prevention
- Rate limiting
- Error handling (no stack traces)
- CORS validation
- Request size limits

**Run**:
```bash
bash tests/security/security-audit.sh
```

**OWASP ZAP**:
```bash
# Start ZAP
zap.sh -daemon -host 0.0.0.0 -port 8080

# Run scan
bash tests/security/zap-scan.sh
```

### 3. Chaos Engineering

**Tests**:
- Redis failure (graceful degradation)
- Neo4j failure (health checks)
- Service recovery
- High load during failures

**Run**:
```bash
bash tests/chaos/chaos-tests.sh
```

### 4. Documentation Review

**Tests**:
- Required files exist
- Required sections present
- Environment variables documented
- Code examples valid

**Run**:
```bash
bash tests/docs/doc-validation.sh
```

## 📊 Expected Results

### Load Testing
- ✅ p95 < 200ms
- ✅ p99 < 200ms
- ✅ Error rate < 1%

### Security Audit
- ✅ All security headers present
- ✅ XSS/injection attempts blocked
- ✅ Rate limiting works
- ✅ No stack traces in errors
- ✅ CORS properly configured

### Chaos Engineering
- ✅ Service responds without Redis (fallback)
- ✅ Health checks reflect dependency status
- ✅ Graceful error handling
- ✅ Automatic recovery

### Documentation
- ✅ All required files present
- ✅ All sections documented
- ✅ Environment variables documented
- ✅ Code examples valid

## 🔧 Prerequisites

### Required
- Docker (for chaos tests)
- curl (for security tests)
- bash (for scripts)

### Optional
- k6 (for load testing): `brew install k6`
- Locust (for load testing): `pip install locust`
- Artillery (for load testing): `npm install -g artillery`
- OWASP ZAP (for security scan): Download from [OWASP ZAP](https://www.zaproxy.org/download/)

## 📝 Test Reports

Test results are saved to:
- `load-test-results.json` (k6)
- `zap-report-*.json` (ZAP JSON report)
- `zap-report-*.html` (ZAP HTML report)

## 🎯 Success Criteria

All tests must pass for production deployment:
- ✅ Load tests: p99 < 200ms, error rate < 1%
- ✅ Security audit: No high-risk issues, all checks pass
- ✅ Chaos tests: Graceful degradation, health checks accurate
- ✅ Documentation: Complete and accurate

## 🚨 Troubleshooting

**Service not running**:
```bash
docker compose -f docker-compose.min.yml up -d
```

**k6 not found**:
```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6
```

**ZAP not running**:
```bash
# Download ZAP from https://www.zaproxy.org/download/
# Start ZAP daemon
./zap.sh -daemon -host 0.0.0.0 -port 8080
```

## 📚 Additional Resources

- [k6 Documentation](https://k6.io/docs/)
- [Locust Documentation](https://docs.locust.io/)
- [Artillery Documentation](https://www.artillery.io/docs)
- [OWASP ZAP Documentation](https://www.zaproxy.org/docs/)


