# Performance Guide
# Last updated: 2025-12-06

Targets (p99):
- Share bundle: <200ms (cached)
- Proof verification: <200ms (cached vkeys with ETag/sha256)
- Health live: <50ms
- AI endpoints: <300ms

Key levers:
- Caching: Redis with in-memory fallback. VKeys are immutable and cached; share bundles cached 60s.
- Connection pooling: Neo4j driver pooling; reuse HTTP clients.
- Static assets: Serve zk vkeys with `Cache-Control: public, max-age=31536000, immutable` and ETag.
- Rate limiting: Keep public endpoints cheap; return 429 fast on abuse.
- Avoid cold starts: Warm vkeys on startup (`make zkp-rebuild` + `scripts/verify_key_integrity.py`).
- Payloads: Keep proof/bundle payloads small; gzip at the proxy.

Baseline checks:
```bash
# Health
curl -w "%{time_total}\n" http://localhost:8000/health/live
curl -w "%{time_total}\n" http://localhost:8000/health/ready

# Share bundle hot/cold
curl -w "%{time_total}\n" http://localhost:8000/vault/share/<token>/bundle

# Proof verify (API key required)
curl -X POST -H "X-API-Key: $AI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @samples/age-proof.sample.json \
  http://localhost:8000/ai/verify-proof
```

Load testing:
- k6 ramp/spike scripts in `perf/` (targets bundle and vkey endpoints). Threshold: `p(99)<200ms`, error rate <1%.

Troubleshooting slow paths:
- Check cache hit rate (if instrumented); ensure Redis reachable.
- Confirm vkeys present and ETag served; missing vkeys force 503.
- Verify Neo4j latency; ensure indexes and pool size are tuned.
- Inspect logs for rate-limit hits or 5xx spikes.

