# Monitoring Guide
# Last updated: 2025-12-06

Complete guide to monitoring, health checks, and observability in Honestly.

## 🎯 Overview

Honestly provides lightweight probes and Prometheus metrics:
- Liveness: `GET /health/live`
- Readiness: `GET /health/ready` (vkeys + Neo4j)
- Metrics: `GET /metrics` (Prometheus format, if enabled)

## 🏥 Health Checks

### Liveness

**Endpoint**: `GET /health/live`

Fast check for load balancers and k8s liveness.

**Response**:
```json
{ "status": "ok" }
```

### Readiness

**Endpoint**: `GET /health/ready`

Checks verification keys presence and Neo4j connectivity. Returns `503` if degraded.

**Example**:
```bash
curl http://localhost:8000/health/ready
```

Response includes booleans for vkeys and Neo4j.

---

### Metrics (Prometheus)

**Endpoint**: `GET /metrics`

Scrape with Prometheus; import into Grafana. Includes app, request, and security counters (if enabled).

---

## 📊 Performance Metrics

### Security events

If enabled, security events are emitted to structured logs (logger `security`). Tail logs or ship to your SIEM. The public endpoint for events is not exposed by default.

---

## 🔒 Security Monitoring

### Security Events

**Endpoint**: `GET /monitoring/security/events?limit=100`

Get recent security events.

**Query Parameters**:
- `limit` (optional, default: 100): Number of events to return

**Response**:
```json
{
  "events": [
    {
      "timestamp": "2024-12-19T10:00:00Z",
      "type": "suspicious_input",
      "severity": "warning",
      "details": {
        "ip": "192.168.1.100",
        "path": "/vault/share/abc123",
        "pattern": "XSS attempt"
      }
    },
    {
      "timestamp": "2024-12-19T09:55:00Z",
      "type": "rate_limit_exceeded",
      "severity": "info",
      "details": {
        "ip": "192.168.1.101",
        "endpoint": "/vault/share/abc123/bundle",
        "limit": 20
      }
    }
  ],
  "total": 12,
  "limit": 100
}
```

**Event Types**:
- `suspicious_input`: Suspicious input detected
- `rate_limit_exceeded`: Rate limit violation
- `ip_blocked`: IP address blocked
- `authentication_failed`: Failed authentication attempt

**Severity Levels**:
- `info`: Informational events
- `warning`: Warning events
- `error`: Error events

**Example**:
```bash
curl http://localhost:8000/monitoring/security/events?limit=50
```

---

### Threat Summary

**Endpoint**: `GET /monitoring/security/threats`

Get threat detection summary.

**Response**:
```json
{
  "total_threats": 5,
  "recent_threats": [
    {
      "timestamp": "2024-12-19T10:00:00Z",
      "type": "suspicious_input",
      "severity": "warning",
      "details": {...}
    }
  ],
  "timestamp": "2024-12-19T10:00:00Z"
}
```

**Example**:
```bash
curl http://localhost:8000/monitoring/security/threats
```

---

## 📈 Cache Statistics

Cache statistics are included in the comprehensive health check and can be accessed via:

**Endpoint**: `GET /monitoring/health`

**Cache Metrics**:
```json
{
  "cache": {
    "hits": 1234,
    "misses": 567,
    "sets": 1801,
    "hit_rate": "68.5%",
    "backend": "redis",
    "memory_size": 1024
  }
}
```

**Metrics Explained**:
- `hits`: Cache hits
- `misses`: Cache misses
- `sets`: Cache sets
- `hit_rate`: Cache hit rate percentage
- `backend`: Cache backend (redis or memory)
- `memory_size`: Number of entries in memory cache

---

## 🔔 Setting Up Alerts

### Health Check Alerts

Monitor the `/health` endpoint:

```yaml
# Prometheus alert rule
groups:
  - name: honestly_health
    rules:
      - alert: HonestlyUnhealthy
        expr: up{job="honestly"} == 0
        for: 1m
        annotations:
          summary: "Honestly service is down"
```

### Performance Alerts

Alert on high response times:

```yaml
- alert: HighResponseTime
  expr: honestly_avg_response_time > 0.5
  for: 5m
  annotations:
    summary: "Average response time is high"
```

### Security Alerts

Alert on security threats:

```yaml
- alert: SecurityThreats
  expr: increase(honestly_security_events_total[5m]) > 10
  for: 1m
  annotations:
    summary: "High number of security events"
```

---

## 📊 Monitoring Dashboards

### Grafana Dashboard Example

```json
{
  "dashboard": {
    "title": "Honestly Monitoring",
    "panels": [
      {
        "title": "Response Time",
        "targets": [
          {
            "expr": "honestly_avg_response_time"
          }
        ]
      },
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(honestly_request_count[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "targets": [
          {
            "expr": "rate(honestly_error_count[5m])"
          }
        ]
      },
      {
        "title": "Cache Hit Rate",
        "targets": [
          {
            "expr": "honestly_cache_hit_rate"
          }
        ]
      }
    ]
  }
}
```

---

## 🛠️ Integration Examples

### Prometheus Scraping

```yaml
scrape_configs:
  - job_name: 'honestly'
    metrics_path: '/monitoring/metrics'
    static_configs:
      - targets: ['localhost:8000']
```

### Health Check Script

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8000/health"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $response -eq 200 ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
```

### Python Monitoring Client

```python
import requests
import time

def check_health(base_url):
    """Check service health."""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def get_metrics(base_url):
    """Get performance metrics."""
    try:
        response = requests.get(f"{base_url}/monitoring/metrics")
        return response.json()
    except Exception as e:
        print(f"Failed to get metrics: {e}")
        return None

# Example usage
if check_health("http://localhost:8000"):
    metrics = get_metrics("http://localhost:8000")
    print(f"Average response time: {metrics['performance']['avg_response_time']}s")
```

---

## 📋 Monitoring Checklist

- [ ] Set up health check monitoring
- [ ] Configure performance alerts
- [ ] Set up security event monitoring
- [ ] Create monitoring dashboards
- [ ] Configure log aggregation
- [ ] Set up uptime monitoring
- [ ] Configure error tracking
- [ ] Set up cache monitoring

---

## 🔗 Related Documentation

- [Production Deployment](../backend-python/PRODUCTION.md)
- [AI Endpoints Guide](ai-endpoints.md)
- [Security Policy](../SECURITY.md)

---

**Last Updated**: 2024-12-19  
**Version**: 1.0.0


