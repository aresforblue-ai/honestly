"""
Monitoring and observability for production system.
Includes metrics, health checks, and audit logging.
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

logger = logging.getLogger(__name__)

# In-memory metrics store (use Prometheus/StatsD in production)
_metrics = defaultdict(lambda: {"count": 0, "total_time": 0.0, "errors": 0})
_health_status = {"status": "healthy", "checks": {}}
_ai_interactions = []


def record_metric(endpoint: str, duration: float, success: bool = True):
    """Record performance metric."""
    _metrics[endpoint]["count"] += 1
    _metrics[endpoint]["total_time"] += duration
    if not success:
        _metrics[endpoint]["errors"] += 1


def log_ai_interaction(
    agent_id: str,
    action: str,
    success: bool,
    duration: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
):
    """Log AI agent interaction for audit trail."""
    interaction = {
        "agent_id": agent_id,
        "action": action,
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_ms": duration * 1000 if duration else None,
        "metadata": metadata or {},
        "error": error,
    }

    _ai_interactions.append(interaction)

    # Keep only last 1000 interactions in memory
    if len(_ai_interactions) > 1000:
        _ai_interactions.pop(0)

    logger.info(
        f"AI interaction: {agent_id} -> {action} ({'success' if success else 'failed'})",
        extra=interaction,
    )


def update_health_check(service: str, status: str, details: Optional[Dict] = None):
    """Update health check status for a service."""
    _health_status["checks"][service] = {
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {},
    }

    # Update overall status
    all_healthy = all(check["status"] == "healthy" for check in _health_status["checks"].values())
    _health_status["status"] = "healthy" if all_healthy else "degraded"


@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint."""
    return JSONResponse(content=_health_status)


@router.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    metrics_summary = {}
    for endpoint, data in _metrics.items():
        avg_time = data["total_time"] / data["count"] if data["count"] > 0 else 0
        error_rate = data["errors"] / data["count"] if data["count"] > 0 else 0

        metrics_summary[endpoint] = {
            "request_count": data["count"],
            "avg_response_time_ms": avg_time * 1000,
            "error_count": data["errors"],
            "error_rate": error_rate,
        }

    return JSONResponse(
        content={"metrics": metrics_summary, "timestamp": datetime.utcnow().isoformat()}
    )


@router.get("/ai-interactions")
async def get_ai_interactions(limit: int = 100):
    """Get recent AI agent interactions (audit trail)."""
    return JSONResponse(
        content={"interactions": _ai_interactions[-limit:], "total": len(_ai_interactions)}
    )


@router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe."""
    # Check critical services
    checks = {
        "neo4j": _check_neo4j(),
        "vault_storage": _check_vault_storage(),
    }

    all_ready = all(checks.values())

    return JSONResponse(
        content={"ready": all_ready, "checks": checks}, status_code=200 if all_ready else 503
    )


@router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe."""
    return JSONResponse(content={"alive": True})


def _check_neo4j() -> bool:
    """Check Neo4j connectivity."""
    try:
        from py2neo import Graph

        NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
        NEO4J_PASS = os.getenv("NEO4J_PASS", "test")
        graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        graph.run("RETURN 1")
        return True
    except (ImportError, Exception):
        return False


def _check_vault_storage() -> bool:
    """Check vault storage availability."""
    try:
        from vault.storage import VaultStorage

        _ = VaultStorage()
        return True
    except (ImportError, Exception):
        return False
