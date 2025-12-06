# AI Endpoints Guide

Structured API endpoints for programmatic access to Honestly's verification services. Designed for AI agents, automation, and integration.

## 🔑 Authentication

All AI endpoints require API key authentication via the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" https://api.honestly.dev/ai/status
```

Set the API key via environment variable:
```bash
export AI_API_KEY=your-secure-api-key
```

## 📋 Endpoints Overview

| Endpoint | Method | Description | Rate Limit |
|----------|--------|-------------|------------|
| `/ai/verify-proof` | POST | Verify single proof | 100/min |
| `/ai/verify-proofs-batch` | POST | Batch verify proofs | 10/min |
| `/ai/share-link` | POST | Create shareable link | 50/min |
| `/ai/share/{token}/info` | GET | Get share link info | 100/min |
| `/ai/status` | GET | API status | 100/min |

## 📝 Standard Response Format

All endpoints return a standardized format:

```json
{
  "success": true,
  "data": {...},
  "error": null,
  "metadata": {
    "timestamp": "2024-12-19T10:00:00Z",
    "request_id": "abc123"
  }
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": "Error message here",
  "metadata": {
    "timestamp": "2024-12-19T10:00:00Z",
    "request_id": "abc123"
  }
}
```

## 🔍 Endpoint Details

### POST `/ai/verify-proof`

Verify a single zero-knowledge proof.

**Request Body**:
```json
{
  "proof_data": "{\"proof\": {...}, \"publicSignals\": [...]}",
  "public_inputs": "{\"min_age\": 18, \"document_hash\": \"...\"}",
  "proof_type": "age_proof"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "verified": true
  },
  "metadata": {
    "proof_type": "age_proof",
    "verification_time_ms": "<200"
  }
}
```

**Example**:
```bash
curl -X POST https://api.honestly.dev/ai/verify-proof \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "proof_data": "...",
    "public_inputs": "...",
    "proof_type": "age_proof"
  }'
```

**Proof Types**:
- `age_proof`: Age verification proof
- `authenticity_proof`: Document authenticity proof

---

### POST `/ai/verify-proofs-batch`

Batch verify multiple proofs (up to 100).

**Request Body**:
```json
{
  "proofs": [
    {
      "proof_data": "...",
      "public_inputs": "...",
      "proof_type": "age_proof"
    },
    {
      "proof_data": "...",
      "public_inputs": "...",
      "proof_type": "authenticity_proof"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "index": 0,
        "verified": true,
        "proof_type": "age_proof"
      },
      {
        "index": 1,
        "verified": false,
        "proof_type": "authenticity_proof"
      }
    ],
    "errors": [],
    "total": 2,
    "verified": 1,
    "failed": 1
  },
  "metadata": {
    "batch_size": 2
  }
}
```

**Example**:
```bash
curl -X POST https://api.honestly.dev/ai/verify-proofs-batch \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @proofs-batch.json
```

**Limits**:
- Maximum 100 proofs per batch
- Rate limit: 10 requests/minute

---

### POST `/ai/share-link`

Create a shareable proof link.

**Request Body**:
```json
{
  "document_id": "doc_123456",
  "proof_type": "age_proof",
  "expires_hours": 24,
  "max_accesses": 10
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "share_token": "abc123def456",
    "share_url": "https://app.honestly.dev/verify/abc123def456",
    "expires_at": "2024-12-20T10:00:00Z",
    "max_accesses": 10
  },
  "metadata": {
    "document_id": "doc_123456",
    "proof_type": "age_proof"
  }
}
```

**Parameters**:
- `document_id` (required): Document identifier
- `proof_type` (optional): Type of proof
- `expires_hours` (optional, default: 24): Expiration in hours (1-720)
- `max_accesses` (optional): Maximum access count (1-1000)

**Example**:
```bash
curl -X POST https://api.honestly.dev/ai/share-link \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "document_id": "doc_123456",
    "expires_hours": 48,
    "max_accesses": 5
  }'
```

---

### GET `/ai/share/{token}/info`

Get share link information (cached for performance).

**Response**:
```json
{
  "success": true,
  "data": {
    "share_token": "abc123def456",
    "document_id": "doc_123456",
    "proof_type": "age_proof",
    "access_level": "proof_only",
    "expires_at": "2024-12-20T10:00:00Z",
    "access_count": 3,
    "max_accesses": 10,
    "document_hash": "abc123..."
  },
  "metadata": {
    "cached": true
  }
}
```

**Example**:
```bash
curl -H "X-API-Key: your-api-key" \
  https://api.honestly.dev/ai/share/abc123def456/info
```

**Caching**: Results are cached for 60 seconds for performance.

---

### GET `/ai/status`

Get API status and capabilities.

**Response**:
```json
{
  "success": true,
  "data": {
    "api_version": "1.0.0",
    "endpoints": {
      "verify_proof": "/ai/verify-proof",
      "verify_proofs_batch": "/ai/verify-proofs-batch",
      "create_share_link": "/ai/share-link",
      "get_share_info": "/ai/share/{token}/info"
    },
    "cache": {
      "backend": "redis",
      "hit_rate": "85.5%"
    },
    "rate_limits": {
      "verify_proof": "100/min",
      "batch_verify": "10/min",
      "share_link": "50/min"
    }
  }
}
```

**Example**:
```bash
curl -H "X-API-Key: your-api-key" \
  https://api.honestly.dev/ai/status
```

---

## 🚦 Rate Limiting

Rate limits are enforced per endpoint:

- `verify_proof`: 100 requests/minute
- `verify_proofs_batch`: 10 requests/minute
- `share_link`: 50 requests/minute
- `share_info`: 100 requests/minute
- `status`: 100 requests/minute

**Rate Limit Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703001600
```

**Rate Limit Exceeded Response**:
```json
{
  "success": false,
  "error": "Rate limit exceeded",
  "metadata": {
    "retry_after": 30
  }
}
```

## ⚠️ Error Handling

### Common Errors

**Invalid API Key** (401):
```json
{
  "success": false,
  "error": "Invalid API key"
}
```

**Invalid Input** (400):
```json
{
  "success": false,
  "error": "Invalid token format"
}
```

**Not Found** (404):
```json
{
  "success": false,
  "error": "Share link not found or expired"
}
```

**Rate Limit Exceeded** (429):
```json
{
  "success": false,
  "error": "Rate limit exceeded"
}
```

**Server Error** (500):
```json
{
  "success": false,
  "error": "Internal server error"
}
```

## 💡 Best Practices

### 1. Use Batch Endpoints

For multiple verifications, use batch endpoints:
```python
# Good: Batch verify
response = requests.post('/ai/verify-proofs-batch', json={
    'proofs': [proof1, proof2, proof3]
})

# Avoid: Multiple single requests
for proof in proofs:
    requests.post('/ai/verify-proof', json=proof)
```

### 2. Handle Caching

Share info endpoints are cached. Check `metadata.cached`:
```python
response = requests.get('/ai/share/{token}/info')
if response.json()['metadata']['cached']:
    # Result was served from cache
    pass
```

### 3. Error Handling

Always check `success` field:
```python
response = requests.post('/ai/verify-proof', json=data)
result = response.json()

if result['success']:
    verified = result['data']['verified']
else:
    error = result['error']
    # Handle error
```

### 4. Rate Limiting

Respect rate limits and implement exponential backoff:
```python
import time

def make_request_with_retry(url, data, max_retries=3):
    for attempt in range(max_retries):
        response = requests.post(url, json=data)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

## 📊 Performance

**Target Response Times**:
- `verify_proof`: <0.2s
- `verify_proofs_batch`: <0.5s per proof
- `share_link`: <0.2s
- `share_info`: <0.1s (cached)
- `status`: <0.05s

## 🔗 Related Documentation

- [Vault API Reference](vault-api.md)
- [Monitoring Guide](monitoring.md)
- [Production Deployment](../backend-python/PRODUCTION.md)

---

**Last Updated**: 2024-12-19  
**API Version**: 1.0.0


