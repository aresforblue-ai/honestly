# Production Validation Test Suite

Comprehensive test suite for validating production readiness, security, performance, and resilience.

## Test Categories

### 1. Load Testing (`load/`)

**Goal**: Prove <200ms response time under load

**Tests**:
- **Ramp Test**: Ramp up to 100 concurrent users, hold for 5 minutes
- **Spike Test**: Jump from 10 to 500 users instantly

**Requirements**:
- k6 installed: https://k6.io/docs/getting-started/installation/

**Run**:
```bash
cd tests/load
bash run_load_tests.sh
```

**Metrics**:
- p(95) response time < 200ms
- p(99) response time < 200ms
- Error rate < 1%

### 2. Security Audit (`security/`)

**Goal**: Find vulnerabilities before attackers do

**Tests**:
- Rate limiting bypass attempts
- SQL injection
- XSS vulnerabilities
- Security headers
- Error handling (information leakage)
- Authentication bypass

**Requirements**:
```bash
pip install requests
```

**Run**:
```bash
cd tests/security
python3 security_audit.py http://localhost:8000
```

**Output**: `security_audit_report.json`

### 3. Chaos Engineering (`chaos/`)

**Goal**: Test resilience when things break

**Tests**:
- Redis failure (graceful degradation)
- Neo4j failure (readiness checks)
- API failure (monitoring detection)

**Requirements**:
```bash
pip install docker
```

**Run**:
```bash
cd tests/chaos
python3 chaos_tests.py http://localhost:8000
```

**What It Tests**:
- System degrades gracefully
- Health checks reflect actual state
- Automatic recovery when services return

### 4. Documentation Review (`documentation/`)

**Goal**: "New Hire" test - can someone set up from scratch?

**Procedure**:
1. Give documentation to a colleague
2. Have them set up the system from scratch
3. Track time, blockers, confusion
4. Document improvements needed

**Checklist**: `documentation/documentation_test.md`

## Running All Tests

```bash
cd tests
bash run_all_tests.sh
```

Or run individually:

```bash
# Load testing
cd tests/load && bash run_load_tests.sh

# Security audit
cd tests/security && python3 security_audit.py http://localhost:8000

# Chaos engineering
cd tests/chaos && python3 chaos_tests.py http://localhost:8000

# Documentation review
# Follow checklist in tests/documentation/documentation_test.md
```

## CI/CD Integration

Add to your CI/CD pipeline:

```yaml
# Load Testing (periodic, not on every commit)
- name: Load Test
  run: |
    cd tests/load
    k6 run load_test.js --out json=results.json

# Security Audit (on every commit)
- name: Security Audit
  run: |
    cd tests/security
    python3 security_audit.py ${{ secrets.STAGING_URL }}

# Chaos Tests (on staging deployments)
- name: Chaos Tests
  run: |
    cd tests/chaos
    python3 chaos_tests.py ${{ secrets.STAGING_URL }}
```

## Success Criteria

### Load Testing
- ✅ p(95) response time < 200ms
- ✅ p(99) response time < 200ms
- ✅ Error rate < 1% under normal load
- ✅ Error rate < 5% during spike

### Security Audit
- ✅ No critical vulnerabilities
- ✅ No high-severity vulnerabilities
- ✅ All security headers present
- ✅ Rate limiting cannot be bypassed
- ✅ Error handling doesn't leak information

### Chaos Engineering
- ✅ System degrades gracefully
- ✅ Health checks reflect actual state
- ✅ System recovers automatically
- ✅ Monitoring detects failures

### Documentation
- ✅ System can be set up in < 30 minutes
- ✅ All steps are clear
- ✅ No external knowledge required
- ✅ Troubleshooting guide resolves issues

## Interpreting Results

### Load Test Results

Check `results_load_test.json`:
```json
{
  "metrics": {
    "http_req_duration": {
      "values": {
        "p(95)": 150,  // Should be < 200
        "p(99)": 180   // Should be < 200
      }
    },
    "http_req_failed": {
      "values": {
        "rate": 0.001  // Should be < 0.01 (1%)
      }
    }
  }
}
```

### Security Audit Results

Check `security_audit_report.json`:
- Review all vulnerabilities
- Fix critical and high-severity issues
- Document acceptable medium/low issues

### Chaos Test Results

Review output:
- System should remain functional (degraded) when Redis fails
- Readiness should reflect Neo4j failure
- System should recover when services return

## Troubleshooting

### Load Tests Failing

- Check if API is running
- Verify BASE_URL is correct
- Check rate limiting settings
- Review server logs

### Security Audit Failing

- Review vulnerabilities in report
- Fix critical issues immediately
- Document acceptable risks
- Update security headers/config

### Chaos Tests Failing

- Verify Docker is running
- Check container names match
- Review health check endpoints
- Verify monitoring is working

## Continuous Improvement

After running tests:
1. Fix identified issues
2. Update documentation
3. Improve error handling
4. Enhance monitoring
5. Re-run tests to verify fixes


