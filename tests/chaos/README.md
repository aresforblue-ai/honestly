# Chaos Engineering Guide

## Purpose

Test system resilience when dependencies fail or under extreme load.

## Prerequisites

```bash
pip install requests
```

## Running Tests

### Basic Chaos Tests

```bash
cd tests/chaos
python chaos_test.py
```

**Tests Include:**
- Graceful degradation
- High load during failures
- Health check accuracy
- Recovery testing

### Network Partition Tests (ToxiProxy)

**Prerequisites:**
```bash
# Start ToxiProxy (via Docker Compose)
docker-compose -f docker-compose.monitoring.yml up -d toxiproxy
```

**Run Network Partition Tests:**
```bash
cd tests/chaos
python network_partition.py
```

**Tests Include:**
- Network partition (complete disconnection)
- Latency injection (slow network)
- Bandwidth limitation
- Reconnection behavior

### Manual Chaos Tests

#### Test Neo4j Failure

```bash
# Stop Neo4j
docker stop honestly-neo4j

# Check health endpoint
curl http://localhost:8000/monitoring/health

# Should show Neo4j as unhealthy but system still responds

# Restart Neo4j
docker start honestly-neo4j

# Wait for recovery
sleep 10

# Check health again
curl http://localhost:8000/monitoring/health

# Should show Neo4j as healthy
```

#### Test Network Partition (ToxiProxy)

```bash
# Create proxy for Neo4j
curl -X POST http://localhost:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{
    "name": "neo4j_partition",
    "listen": "0.0.0.0:7688",
    "upstream": "neo4j:7687",
    "enabled": true
  }'

# Add timeout toxic (simulates partition)
curl -X POST http://localhost:8474/proxies/neo4j_partition/toxics \
  -H "Content-Type: application/json" \
  -d '{
    "type": "timeout",
    "attributes": {"timeout": 0}
  }'

# Test system behavior
curl http://localhost:8000/monitoring/health

# Remove toxic (restore connection)
curl -X DELETE http://localhost:8474/proxies/neo4j_partition/toxics/timeout_downstream

# Verify recovery
curl http://localhost:8000/monitoring/health
```

## Expected Behavior

### ✅ Graceful Degradation

- System continues operating
- Health checks reflect failures
- Error responses are user-friendly
- No stack traces leaked

### ✅ Recovery

- System recovers automatically
- Health checks update
- Services resume normal operation
- No manual intervention needed

## Continuous Chaos Testing

### CI/CD Integration

```yaml
# .github/workflows/chaos-test.yml
name: Chaos Test
on: [schedule]
jobs:
  chaos-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install requests
      - name: Run chaos tests
        run: python tests/chaos/chaos_test.py
```

## Monitoring During Chaos

### Key Metrics

1. **Response Times:**
   - Should remain reasonable even during failures
   - May increase but shouldn't timeout

2. **Error Rates:**
   - Should increase but remain manageable
   - Should decrease after recovery

3. **Health Checks:**
   - Should accurately reflect system state
   - Should update in real-time

## Remediation

### If Tests Fail

1. **No Graceful Degradation:**
   - Add fallback mechanisms
   - Improve error handling
   - Add circuit breakers

2. **Health Checks Inaccurate:**
   - Review health check logic
   - Add dependency checks
   - Improve monitoring

3. **No Recovery:**
   - Add retry logic
   - Improve connection pooling
   - Add health check retries
