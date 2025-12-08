# Monitoring Setup Guide

## Prometheus + Grafana Integration

### Quick Start

```bash
# Start monitoring stack
docker-compose -f docker-compose.monitoring.yml up -d

# Access Grafana
# URL: http://localhost:3000
# Username: admin
# Password: admin (change on first login)

# Access Prometheus
# URL: http://localhost:9090
```

### Configuration

#### Prometheus

Prometheus scrapes metrics from the API at `/metrics/prometheus` every 5 seconds.

**Configuration:** `docker/prometheus.yml`

#### Grafana

Pre-configured dashboard: `docker/grafana/dashboards/honestly-dashboard.json`

**Dashboards Include:**
- P99 Response Time (with alert at 200ms)
- Verification Time
- Request Rate
- Error Rate
- Cache Hit Rate
- Rate Limit Hits
- System Resources

### Metrics Exposed

#### HTTP Metrics

- `http_requests_total` - Total HTTP requests (by method, endpoint, status)
- `http_request_duration_seconds` - Request duration histogram

#### Verification Metrics

- `verification_duration_seconds` - ZK proof verification time (by circuit, result)

#### Cache Metrics

- `cache_hits_total` - Cache hits (by cache type)
- `cache_misses_total` - Cache misses (by cache type)

#### Rate Limiting Metrics

- `rate_limit_hits_total` - Rate limit hits (by endpoint, IP)

#### System Metrics

- `active_connections` - Active database connections
- `system_cpu_percent` - CPU usage
- `system_memory_percent` - Memory usage
- `uptime_seconds` - System uptime

### Alerts

#### P99 Response Time Alert

- **Condition**: P99 > 200ms for 5 minutes
- **Action**: Sends notification (configure in Grafana)

#### Error Rate Alert

- **Condition**: Error rate > 1% for 5 minutes
- **Action**: Sends notification

### Querying Metrics

#### Prometheus Queries

```promql
# P99 Response Time
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))

# Request Rate
rate(http_requests_total[5m])

# Error Rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Cache Hit Rate
rate(cache_hits_total[5m]) / (rate(cache_hits_total[5m]) + rate(cache_misses_total[5m]))
```

### Integration with CI/CD

Metrics are automatically collected during load tests and can be visualized in Grafana.

### Production Deployment

1. **Configure Prometheus:**
   - Update `docker/prometheus.yml` with production targets
   - Set appropriate scrape intervals

2. **Configure Grafana:**
   - Set up data source (Prometheus)
   - Import dashboard
   - Configure alerts

3. **Enable Metrics:**
   - Set `ENABLE_PROMETHEUS=true` in environment
   - Verify `/metrics/prometheus` endpoint

4. **Monitor:**
   - Set up alerting rules
   - Configure notification channels
   - Review dashboards regularly


