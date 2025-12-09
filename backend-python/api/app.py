import os
import json
import time
import logging
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
from py2neo import Graph
from sentence_transformers import SentenceTransformer
from vector_index.faiss_index import FaissIndex

# Import shared utilities (avoids circular imports)
from api.utils import get_vkey_hash, vkeys_ready, load_vkey_hashes, get_artifacts_dir

# Import vault resolvers and routes
from api.vault_resolvers import query as vault_query, mutation as vault_mutation
from api.vault_routes import router as vault_router
from api.auth import decode_authorization_header

# Import monitoring router
from api.monitoring import router as monitoring_router

# Import AI agent routers
try:
    from api.ai_agents import router as ai_agents_router

    AI_AGENTS_AVAILABLE = True
except ImportError:
    AI_AGENTS_AVAILABLE = False
    ai_agents_router = None

try:
    from api.ml_router import router as ml_router

    ML_ROUTER_AVAILABLE = True
except ImportError:
    ML_ROUTER_AVAILABLE = False
    ml_router = None

try:
    from api.websocket_router import router as ws_router

    WS_ROUTER_AVAILABLE = True
except ImportError:
    WS_ROUTER_AVAILABLE = False
    ws_router = None

try:
    from api.alerts import get_alert_service

    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    get_alert_service = None

# Import Prometheus metrics
try:
    from api.prometheus import get_metrics_endpoint

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    get_metrics_endpoint = None
    print("Warning: prometheus_client not installed. Metrics disabled.")

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "test")
_DEFAULT_ORIGIN = "http://localhost:5173"
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("ALLOWED_ORIGINS", _DEFAULT_ORIGIN).split(",") if o.strip()
]
STRICT_CORS = os.getenv("STRICT_CORS", "false").lower() == "true"
ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() != "false"
ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() != "false"
HSTS_MAX_AGE = int(os.getenv("HSTS_MAX_AGE", "31536000"))
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false"
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "60"))  # per window per IP for public/GraphQL
_rate_bucket: dict[str, dict] = {}
logger = logging.getLogger("security")

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
faiss = FaissIndex(index_path="faiss.index")

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.graphql")
with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
    type_defs = f.read()

# Original query resolvers
query = QueryType()


@query.field("claim")
def resolve_claim(_, info, id):
    q = "MATCH (c:Claim {id:$id})<-[:REPORTS]-(s:Source) RETURN c, s LIMIT 1"
    res = graph.run(q, id=id).data()
    if not res:
        raise HTTPException(status_code=404, detail="Claim not found")
    c = res[0]["c"]
    s = res[0]["s"]
    return {
        "id": c["id"],
        "text": c.get("text"),
        "veracity": float(c.get("veracity", 0.5)),
        "state": c.get("state"),
        "timestamp": str(c.get("timestamp")) if c.get("timestamp") else None,
        "source": s.get("name"),
        "provenance": c.get("provenance"),
    }


@query.field("search")
def resolve_search(_, info, query, topK=5):
    vec = embed_model.encode(query)
    results = faiss.search(vec, top_k=topK)
    claims = []
    for r in results:
        # fetch claim metadata from Neo4j
        q = "MATCH (c:Claim {id:$id})<-[:REPORTS]-(s:Source) RETURN c, s LIMIT 1"
        res = graph.run(q, id=r["id"]).data()
        if not res:
            continue
        c = res[0]["c"]
        s = res[0]["s"]
        claims.append(
            {
                "id": c["id"],
                "text": c.get("text"),
                "veracity": float(c.get("veracity", 0.5)),
                "state": c.get("state"),
                "timestamp": str(c.get("timestamp")) if c.get("timestamp") else None,
                "source": s.get("name"),
                "provenance": c.get("provenance"),
            }
        )
    return claims


# App/Entity resolvers for Frontend Dashboard
@query.field("apps")
def resolve_apps(_, info):
    """Get all apps/entities from Neo4j."""
    q = """
    MATCH (a:App)
    OPTIONAL MATCH (a)-[:HAS_CLAIM]->(c:Claim)
    OPTIONAL MATCH (a)-[:HAS_REVIEW]->(r:Review)
    RETURN a, collect(DISTINCT c) as claims, collect(DISTINCT r) as reviews
    """
    results = graph.run(q).data()
    apps = []
    for record in results:
        app_node = record["a"]
        if not app_node:
            continue
        apps.append(
            {
                "id": app_node.get("id"),
                "name": app_node.get("name", "Unknown"),
                "whistlerScore": float(app_node.get("whistlerScore", 0)),
                "metadata": {
                    "zkProofVerified": app_node.get("zkProofVerified", False),
                    "category": app_node.get("category"),
                    "description": app_node.get("description"),
                },
                "claims": [dict(c) for c in record.get("claims", []) if c],
                "reviews": [dict(r) for r in record.get("reviews", []) if r],
            }
        )
    return apps


@query.field("app")
def resolve_app(_, info, id):
    """Get a specific app by ID."""
    q = """
    MATCH (a:App {id: $id})
    OPTIONAL MATCH (a)-[:HAS_CLAIM]->(c:Claim)
    OPTIONAL MATCH (c)<-[:REPORTS]-(s:Source)
    OPTIONAL MATCH (c)-[:HAS_VERDICT]->(v:Verdict)
    OPTIONAL MATCH (a)-[:HAS_REVIEW]->(r:Review)
    RETURN a, 
           collect(DISTINCT {claim: c, source: s, verdicts: collect(DISTINCT v)}) as claims,
           collect(DISTINCT r) as reviews
    """
    results = graph.run(q, id=id).data()
    if not results or not results[0].get("a"):
        return None

    record = results[0]
    app_node = record["a"]

    claims = []
    for claim_data in record.get("claims", []):
        c = claim_data.get("claim")
        if not c:
            continue
        verdicts = claim_data.get("verdicts", [])
        claims.append(
            {
                "id": c.get("id"),
                "statement": c.get("text") or c.get("statement"),
                "claimHash": c.get("hash") or c.get("claimHash", ""),
                "verdicts": [
                    {
                        "outcome": v.get("outcome", "UNKNOWN"),
                        "confidence": float(v.get("confidence", 0.5)),
                    }
                    for v in verdicts
                    if v
                ],
            }
        )

    reviews = []
    for r in record.get("reviews", []):
        if r:
            reviews.append(
                {
                    "id": r.get("id"),
                    "rating": float(r.get("rating", 0)),
                    "sentiment": r.get("sentiment", "NEUTRAL"),
                    "text": r.get("text"),
                }
            )

    return {
        "id": app_node.get("id"),
        "name": app_node.get("name", "Unknown"),
        "whistlerScore": float(app_node.get("whistlerScore", 0)),
        "metadata": {
            "zkProofVerified": app_node.get("zkProofVerified", False),
            "category": app_node.get("category"),
            "description": app_node.get("description"),
        },
        "claims": claims,
        "reviews": reviews,
    }


@query.field("scoreApp")
def resolve_score_app(_, info, appId):
    """Calculate and return app score breakdown."""
    q = """
    MATCH (a:App {id: $id})
    OPTIONAL MATCH (a)-[:HAS_SCORE]->(s:Score)
    RETURN a, s
    """
    results = graph.run(q, id=appId).data()
    if not results or not results[0].get("a"):
        return None

    app_node = results[0]["a"]
    score_node = results[0].get("s")

    # Calculate grade from whistlerScore
    score = float(app_node.get("whistlerScore", 0))
    if score >= 90:
        grade = "A"
    elif score >= 80:
        grade = "B"
    elif score >= 70:
        grade = "C"
    elif score >= 60:
        grade = "D"
    else:
        grade = "F"

    # Get breakdown from score node or calculate defaults
    if score_node:
        breakdown = {
            "privacy": {"value": float(score_node.get("privacy", 50)), "label": "Privacy"},
            "financial": {"value": float(score_node.get("financial", 50)), "label": "Financial"},
            "security": {"value": float(score_node.get("security", 50)), "label": "Security"},
            "transparency": {
                "value": float(score_node.get("transparency", 50)),
                "label": "Transparency",
            },
        }
    else:
        # Default breakdown based on overall score
        breakdown = {
            "privacy": {"value": score * 0.9, "label": "Privacy"},
            "financial": {"value": score * 0.85, "label": "Financial"},
            "security": {"value": score * 0.95, "label": "Security"},
            "transparency": {"value": score * 0.8, "label": "Transparency"},
        }

    return {
        "grade": grade,
        "breakdown": breakdown,
    }


# Import vault resolvers (already imported at top)
# Create mutation type
mutation = MutationType()

# Copy vault query resolvers to main query
for field_name, resolver in vault_query._resolvers.items():
    query.field(field_name)(resolver)

# Copy vault mutation resolvers to main mutation
for field_name, resolver in vault_mutation._resolvers.items():
    mutation.field(field_name)(resolver)

schema = make_executable_schema(type_defs, query, mutation)

# Create FastAPI app
app = FastAPI(
    title="Truth Engine - Personal Proof Vault",
    description="Blockchain-verified identity and credential verification system",
    version="1.0.0",
)

if STRICT_CORS and (not ALLOWED_ORIGINS or ALLOWED_ORIGINS == [_DEFAULT_ORIGIN]):
    raise RuntimeError("STRICT_CORS enabled but ALLOWED_ORIGINS not set to explicit domains.")

if ENABLE_CORS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Security headers middleware (best-effort, configurable)
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response: Response = await call_next(request)
        # Enforce no sniff, frame options, referrer policy
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        # Basic CSP; adjust allowed connect-src to backend domains
        connect_src = " ".join({request.url.scheme + "://" + request.url.netloc, *ALLOWED_ORIGINS})
        csp = (
            "default-src 'self'; "
            f"connect-src 'self' {connect_src}; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "frame-ancestors 'none'"
        )
        response.headers.setdefault("Content-Security-Policy", csp)
        # HSTS only makes sense behind HTTPS/termination; keep configurable
        if request.url.scheme == "https":
            response.headers.setdefault(
                "Strict-Transport-Security", f"max-age={HSTS_MAX_AGE}; includeSubDomains"
            )
        return response


if ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

# Serve zk artifacts (verification keys) statically
artifacts_dir = get_artifacts_dir()
artifacts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/zkp/artifacts", StaticFiles(directory=str(artifacts_dir)), name="zk-artifacts")


def _log_security(event: str, request: Request | None = None, **kwargs):
    """Lightweight structured security logging."""
    payload = {"event": event, **kwargs}
    if request:
        payload["path"] = request.url.path
        payload["client"] = request.client.host if request.client else None
    try:
        logger.warning(json.dumps(payload))
    except Exception:
        logger.warning("%s %s", event, payload)


def _rate_check(key: str):
    if not RATE_LIMIT_ENABLED:
        return
    now = time.time()
    bucket = _rate_bucket.get(key, {"count": 0, "window_start": now})
    if now - bucket["window_start"] > RATE_LIMIT_WINDOW:
        bucket = {"count": 0, "window_start": now}
    bucket["count"] += 1
    _rate_bucket[key] = bucket
    if bucket["count"] > RATE_LIMIT_MAX:
        _log_security("rate_limit_exceeded", key=key, count=bucket["count"])
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


@app.middleware("http")
async def integrity_middleware(request, call_next):
    path = request.url.path
    if path.startswith(("/graphql", "/vault/share", "/vault/qr")):
        _rate_check(f"{path}:{request.client.host}")
    # Fail fast if vkeys missing for critical endpoints
    if path.startswith("/vault/share") or path.startswith("/zkp/artifacts"):
        if not vkeys_ready():
            return Response(
                content='{"detail":"Verification keys unavailable"}',
                status_code=503,
                media_type="application/json",
            )
    response: Response = await call_next(request)
    # Add immutable caching and ETag for vkeys
    if path.startswith("/zkp/artifacts") and path.endswith("verification_key.json"):
        parts = path.strip("/").split("/")
        circuit = parts[-2] if len(parts) >= 2 else ""
        etag = get_vkey_hash(circuit)
        if etag:
            response.headers.setdefault("ETag", etag)
        response.headers.setdefault("Cache-Control", "public, max-age=31536000, immutable")
    return response


async def graphql_context_value(request: Request):
    """Attach authenticated user (if provided) to GraphQL context."""
    auth_header = request.headers.get("authorization")
    user = None
    if auth_header:
        user = decode_authorization_header(auth_header)
    return {
        "request": request,
        "user": user,
        "user_id": user["user_id"] if user else None,
    }


# Mount GraphQL endpoint with context-aware auth
app.mount("/graphql", GraphQL(schema, debug=False, context_value=graphql_context_value))

# Mount vault REST routes
app.include_router(vault_router)

# Mount monitoring routes
app.include_router(monitoring_router)

# Mount AI agent routes
if AI_AGENTS_AVAILABLE and ai_agents_router:
    app.include_router(ai_agents_router)

# Mount ML anomaly detection routes
if ML_ROUTER_AVAILABLE and ml_router:
    app.include_router(ml_router)

# Mount WebSocket routes for real-time anomaly streaming
if WS_ROUTER_AVAILABLE and ws_router:
    app.include_router(ws_router)

# Mount AAIP Swarm routes
try:
    from api.swarm_routes import router as swarm_router

    app.include_router(swarm_router)
except ImportError:
    pass  # Swarm router optional

# Mount Cross-Chain Anomaly Federation routes
try:
    from api.cross_chain_routes import router as cross_chain_router

    app.include_router(cross_chain_router)
except ImportError:
    pass  # Cross-chain router optional

# Mount Quantum Computing routes
try:
    from api.quantum_routes import router as quantum_router

    app.include_router(quantum_router)
except ImportError:
    pass  # Quantum router optional

# Prometheus metrics endpoint
if PROMETHEUS_AVAILABLE:

    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint."""
        return get_metrics_endpoint()


@app.on_event("startup")
async def startup_event():
    """Load critical artifacts on startup."""
    load_vkey_hashes()
    if not vkeys_ready():
        raise RuntimeError("Verification keys are not loaded; startup gating failed.")


# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Truth Engine - Personal Proof Vault API",
        "graphql": "/graphql",
        "vault": "/vault",
        "metrics": "/metrics" if PROMETHEUS_AVAILABLE else None,
    }


@app.get("/health/live")
async def health_live():
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready():
    """Readiness probe: checks vkeys and Neo4j connectivity."""
    vkeys_ok = vkeys_ready()
    neo4j_ok = False
    try:
        graph.run("RETURN 1").evaluate()
        neo4j_ok = True
    except Exception:
        neo4j_ok = False
    status_code = 200 if (vkeys_ok and neo4j_ok) else 503
    return Response(
        content=json.dumps(
            {
                "status": "ok" if status_code == 200 else "degraded",
                "vkeys": vkeys_ok,
                "neo4j": neo4j_ok,
            }
        ),
        media_type="application/json",
        status_code=status_code,
    )


@app.get("/capabilities")
async def capabilities():
    from api.utils import HMAC_SECRET

    return {
        "service": "Truth Engine - Personal Proof Vault",
        "version": "1.0.0",
        "proofs": [
            {
                "type": "age_proof",
                "circuit": "age",
                "public_inputs": ["minAgeOut", "referenceTsOut", "documentHashOut", "commitment"],
                "endpoint": "/vault/share/{token}/bundle",
                "vk": "/zkp/artifacts/age/verification_key.json",
                "vk_sha256": get_vkey_hash("age"),
            },
            {
                "type": "authenticity_proof",
                "circuit": "authenticity",
                "public_inputs": ["rootOut", "leafOut"],
                "endpoint": "/vault/share/{token}/bundle",
                "vk": "/zkp/artifacts/authenticity/verification_key.json",
                "vk_sha256": get_vkey_hash("authenticity"),
            },
        ],
        "hmac": bool(HMAC_SECRET),
    }
