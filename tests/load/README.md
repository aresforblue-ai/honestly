# Load Testing Guide

## Prerequisites

### k6 Installation

```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

### Locust Installation

```bash
pip install locust
```

## Running Tests

### Test 1: Ramp-up to 100 Concurrent Users

```bash
# Set environment variables
export BASE_URL=http://localhost:8000
export TEST_TOKEN=your_test_token

# Run k6 test
k6 run k6_test.js

# Or with custom options
k6 run --vus 100 --duration 5m k6_test.js
```

**Expected Results:**
- ✅ P99 response time < 200ms
- ✅ Error rate < 1%
- ✅ All thresholds pass

### Test 2: Spike Test (10 → 500 users)

```bash
k6 run k6_spike_test.js
```

**Expected Results:**
- ✅ System handles spike gracefully
- ✅ Rate limiting activates
- ✅ P99 response time < 500ms during spike
- ✅ Recovery after spike

### Test 3: Locust (Alternative)

```bash
# Start Locust web UI
locust -f locustfile.py --host=http://localhost:8000

# Or headless
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
```

## Interpreting Results

### Key Metrics

1. **Response Time Percentiles:**
   - P50 (median): Should be < 100ms
   - P95: Should be < 150ms
   - P99: **MUST be < 200ms** (target)

2. **Error Rate:**
   - Should be < 1% under normal load
   - May spike to 5% during spike test

3. **Throughput:**
   - Requests per second
   - Should remain stable

### Success Criteria

✅ **All tests pass if:**
- P99 response time < 200ms
- Error rate < 1% (normal) or < 5% (spike)
- No memory leaks
- System recovers after spike

## Continuous Testing

### CI/CD Integration

```yaml
# .github/workflows/load-test.yml
name: Load Test
on: [push]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install k6
        run: |
          sudo gpg -k
          sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
          echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
          sudo apt-get update
          sudo apt-get install k6
      - name: Run load test
        run: k6 run tests/load/k6_test.js
```

## Troubleshooting

### High Response Times

1. Check database connection pooling
2. Verify cache is working (check hit rate)
3. Monitor system resources (CPU, memory)
4. Check for slow queries

### High Error Rates

1. Check rate limiting configuration
2. Verify all dependencies are healthy
3. Check logs for errors
4. Verify capacity limits

### Rate Limiting Issues

1. Verify rate limit middleware is active
2. Check rate limit configuration
3. Test with different IP addresses
4. Verify headers are returned


