# Production Deployment Guide

## 🚀 Production-Ready Features

This system has been hardened for production with:

### Security
- ✅ JWT authentication with refresh tokens
- ✅ Rate limiting (configurable, Redis-ready)
- ✅ Security headers (HSTS, CSP, X-Frame-Options, etc.)
- ✅ Input validation and sanitization
- ✅ AI agent signature verification
- ✅ Audit logging for all interactions
- ✅ Error handling without information leakage

### Performance (<0.2s target)
- ✅ In-memory caching with LRU eviction
- ✅ Connection pooling for Neo4j
- ✅ Lazy loading of heavy models
- ✅ Pre-warmed verification key cache
- ✅ Optimized database queries
- ✅ Response time monitoring

### AI Agent Support
- ✅ Dedicated `/ai` endpoints
- ✅ Request signature verification
- ✅ Rate limiting per agent
- ✅ Complete audit trail
- ✅ Structured request/response models

### Monitoring & Observability
- ✅ Health checks (`/monitoring/health`)
- ✅ Metrics endpoint (`/monitoring/metrics`)
- ✅ AI interaction logs (`/monitoring/ai-interactions`)
- ✅ Kubernetes-ready probes (`/monitoring/ready`, `/monitoring/live`)
- ✅ Performance tracking
- ✅ Slow request detection

## 📋 Environment Variables

Create a `.env` file with:

```bash
# Required in Production
ENVIRONMENT=production
JWT_SECRET=<32-byte-hex-random>
AI_AGENT_SECRET=<32-byte-hex-random>
NEO4J_PASS=<strong-password>

# Optional Configuration
JWT_ACCESS_EXPIRY=3600
JWT_REFRESH_EXPIRY=604800
AI_AGENT_RATE_LIMIT=100
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REDIS_URL=redis://localhost:6379/0
SLOW_REQUEST_THRESHOLD=0.2
ALLOWED_ORIGINS=https://yourdomain.com
```

## 🔐 Security Best Practices

1. **Never commit secrets** - Use environment variables or secret management
2. **Rotate JWT secrets** regularly
3. **Use HTTPS** in production (TLS termination at load balancer)
4. **Monitor rate limits** - Adjust based on traffic patterns
5. **Review audit logs** regularly for suspicious activity
6. **Keep dependencies updated** - Run security scans

## 🤖 AI Agent Integration

### Authentication

AI agents must sign requests with HMAC-SHA256:

```python
import hmac
import hashlib
import json

payload = json.dumps(request_data, sort_keys=True)
signature = hmac.new(
    AI_AGENT_SECRET.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

headers = {
    'X-AI-Signature': signature,
    'Content-Type': 'application/json'
}
```

### Available Endpoints

- `POST /ai/verify-proof` - Verify zkSNARK proofs
- `POST /ai/get-document-hash` - Get document hash (no content)
- `POST /ai/create-share-link` - Create shareable links
- `GET /ai/health` - Health check

### Example Request

```python
import requests

request_data = {
    "agent_id": "my_agent_001",
    "action": "verify_proof",
    "parameters": {
        "proof_data": "...",
        "proof_type": "age_proof"
    },
    "timestamp": 1234567890.0
}

# Sign request
signature = create_signature(request_data, AI_AGENT_SECRET)

response = requests.post(
    "https://api.example.com/ai/verify-proof",
    json=request_data,
    headers={"X-AI-Signature": signature}
)
```

## 📊 Monitoring

### Health Checks

```bash
# Overall health
curl https://api.example.com/monitoring/health

# Kubernetes readiness
curl https://api.example.com/monitoring/ready

# Kubernetes liveness
curl https://api.example.com/monitoring/live
```

### Metrics

```bash
curl https://api.example.com/monitoring/metrics
```

Returns:
```json
{
  "metrics": {
    "/vault/share/{token}/bundle": {
      "request_count": 1234,
      "avg_response_time_ms": 45.2,
      "error_count": 2,
      "error_rate": 0.0016
    }
  }
}
```

### AI Interactions

```bash
curl https://api.example.com/monitoring/ai-interactions?limit=100
```

## ⚡ Performance Optimization

### Caching

- Verification keys: Pre-warmed on startup, never expire
- Share bundles: 60s TTL
- Document metadata: 300s TTL (configurable)

### Database

- Connection pooling: Max 50 connections
- Query optimization: Indexed lookups only
- Lazy loading: Heavy models loaded on demand

### Response Times

Target: <0.2s for all endpoints
- Share bundle: ~50ms (cached)
- Proof verification: ~100ms (cached vkeys)
- Document hash: ~30ms

## 🚨 Error Handling

- All errors logged with request context
- No internal details leaked in production
- Error IDs for tracking
- Graceful degradation for non-critical services

## 🔄 Deployment

### Docker

```bash
docker build -f docker/Dockerfile.api -t honestly-api .
docker run -p 8000:8000 --env-file .env honestly-api
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: honestly-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: honestly-api:latest
        env:
        - name: ENVIRONMENT
          value: "production"
        livenessProbe:
          httpGet:
            path: /monitoring/live
            port: 8000
        readinessProbe:
          httpGet:
            path: /monitoring/ready
            port: 8000
```

## 📈 Scaling

### Horizontal Scaling

- Stateless API: Scale horizontally
- Use Redis for distributed rate limiting
- Load balancer with health checks

### Vertical Scaling

- Increase Neo4j connection pool
- Increase cache size
- Add more workers (uvicorn workers)

## 🛡️ Security Checklist

- [ ] JWT_SECRET set to random 32-byte hex
- [ ] AI_AGENT_SECRET set to random 32-byte hex
- [ ] NEO4J_PASS changed from default
- [ ] HTTPS enabled (TLS termination)
- [ ] CORS origins restricted
- [ ] Rate limits configured
- [ ] Security headers enabled
- [ ] Audit logging enabled
- [ ] Error details hidden in production
- [ ] Dependencies scanned for vulnerabilities

## 🐛 Troubleshooting

### Slow Requests

Check `/monitoring/metrics` for slow endpoints. Common causes:
- Cache misses
- Database queries
- External API calls

### High Error Rate

Check logs for patterns:
```bash
grep ERROR /var/log/honestly-api.log
```

### Rate Limit Issues

Adjust `RATE_LIMIT_*` environment variables or use Redis for distributed limiting.

## 📞 Support

For production issues:
1. Check `/monitoring/health`
2. Review `/monitoring/metrics`
3. Check application logs
4. Review AI interaction logs if applicable


