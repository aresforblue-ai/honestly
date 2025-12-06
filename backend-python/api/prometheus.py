"""
Prometheus metrics exporter for monitoring.
Exposes metrics for Grafana dashboard integration.
"""
import time
from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST
)

router = APIRouter(prefix="/metrics", tags=["prometheus"])

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

verification_duration_seconds = Histogram(
    'verification_duration_seconds',
    'ZK proof verification duration in seconds',
    ['circuit', 'result'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)

cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type']
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type']
)

rate_limit_hits_total = Counter(
    'rate_limit_hits_total',
    'Total rate limit hits',
    ['endpoint', 'ip']
)

active_connections = Gauge(
    'active_connections',
    'Active database connections'
)

system_cpu_percent = Gauge(
    'system_cpu_percent',
    'System CPU usage percentage'
)

system_memory_percent = Gauge(
    'system_memory_percent',
    'System memory usage percentage'
)

uptime_seconds = Gauge(
    'uptime_seconds',
    'System uptime in seconds'
)

_start_time = time.time()


@router.get("/prometheus")
async def prometheus_metrics():
    """Prometheus metrics endpoint."""
    # Update uptime
    uptime_seconds.set(time.time() - _start_time)
    
    # Update system metrics
    try:
        import psutil
        system_cpu_percent.set(psutil.cpu_percent(interval=0.1))
        system_memory_percent.set(psutil.virtual_memory().percent)
    except Exception:
        pass
    
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


def record_request(method: str, endpoint: str, status: int, duration: float):
    """Record HTTP request metrics."""
    http_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_verification(circuit: str, result: str, duration: float):
    """Record verification metrics."""
    verification_duration_seconds.labels(circuit=circuit, result=result).observe(duration)


def record_cache_hit(cache_type: str):
    """Record cache hit."""
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """Record cache miss."""
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_rate_limit(endpoint: str, ip: str):
    """Record rate limit hit."""
    rate_limit_hits_total.labels(endpoint=endpoint, ip=ip).inc()

