import os
import json
import hashlib
import hmac
import base64
import time
from pathlib import Path
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
from py2neo import Graph
from sentence_transformers import SentenceTransformer
from vector_index.faiss_index import FaissIndex

# Import vault resolvers and routes
from api.vault_resolvers import query as vault_query, mutation as vault_mutation
from api.vault_routes import router as vault_router

# Import Prometheus metrics
try:
    from api.prometheus import metrics, get_metrics_endpoint
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    print("Warning: prometheus_client not installed. Metrics disabled.")

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')
_DEFAULT_ORIGIN = 'http://localhost:5173'
ALLOWED_ORIGINS = [o.strip() for o in os.getenv('ALLOWED_ORIGINS', _DEFAULT_ORIGIN).split(',') if o.strip()]
STRICT_CORS = os.getenv('STRICT_CORS', 'false').lower() == 'true'
ENABLE_CORS = os.getenv('ENABLE_CORS', 'true').lower() != 'false'
ENABLE_SECURITY_HEADERS = os.getenv('ENABLE_SECURITY_HEADERS', 'true').lower() != 'false'
HSTS_MAX_AGE = int(os.getenv('HSTS_MAX_AGE', '31536000'))
HMAC_SECRET = os.getenv('BUNDLE_HMAC_SECRET')
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() != 'false'
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '60'))
RATE_LIMIT_MAX = int(os.getenv('RATE_LIMIT_MAX', '60'))  # per window per IP for public/GraphQL
_VKEY_HASHES = {}  # circuit -> sha256 hex
_rate_bucket: dict[str, dict] = {}

graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
embed_model = SentenceTransformer('all-MiniLM-L6-v2')
faiss = FaissIndex(index_path='faiss.index')

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
    c = res[0]['c']
    s = res[0]['s']
    return {
        "id": c['id'],
        "text": c.get('text'),
        "veracity": float(c.get('veracity', 0.5)),
        "state": c.get('state'),
        "timestamp": str(c.get('timestamp')) if c.get('timestamp') else None,
        "source": s.get('name'),
        "provenance": c.get('provenance')
    }

@query.field("search")
def resolve_search(_, info, query, topK=5):
    vec = embed_model.encode(query)
    results = faiss.search(vec, top_k=topK)
    claims = []
    for r in results:
        # fetch claim metadata from Neo4j
        q = "MATCH (c:Claim {id:$id})<-[:REPORTS]-(s:Source) RETURN c, s LIMIT 1"
        res = graph.run(q, id=r['id']).data()
        if not res:
            continue
        c = res[0]['c']
        s = res[0]['s']
        claims.append({
            "id": c['id'],
            "text": c.get('text'),
            "veracity": float(c.get('veracity', 0.5)),
            "state": c.get('state'),
            "timestamp": str(c.get('timestamp')) if c.get('timestamp') else None,
            "source": s.get('name'),
            "provenance": c.get('provenance')
        })
    return claims

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
    version="1.0.0"
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
            response.headers.setdefault("Strict-Transport-Security", f"max-age={HSTS_MAX_AGE}; includeSubDomains")
        return response

if ENABLE_SECURITY_HEADERS:
    app.add_middleware(SecurityHeadersMiddleware)

# Serve zk artifacts (verification keys) statically
artifacts_dir = Path(__file__).resolve().parent.parent / "zkp" / "artifacts"
artifacts_dir.mkdir(parents=True, exist_ok=True)
app.mount("/zkp/artifacts", StaticFiles(directory=str(artifacts_dir)), name="zk-artifacts")


def _load_vkey_hashes():
    """Compute SHA-256 hashes of verification keys and ensure presence."""
    required = {
        "age": artifacts_dir / "age" / "verification_key.json",
        "authenticity": artifacts_dir / "authenticity" / "verification_key.json",
    }
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing verification keys: {missing}. Run zkp build to generate real vkeys.")
    for circuit, path in required.items():
        data = path.read_bytes()
        _VKEY_HASHES[circuit] = hashlib.sha256(data).hexdigest()


def get_vkey_hash(circuit: str) -> str:
    return _VKEY_HASHES.get(circuit, "")


def hmac_sign(payload: dict) -> str:
    if not HMAC_SECRET:
        return ""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()


def vkeys_ready() -> bool:
    return all(_VKEY_HASHES.get(c) for c in ("age", "authenticity"))


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

def _ensure_vkeys_loaded():
    if not vkeys_ready():
        raise RuntimeError("Verification keys are not loaded; startup gating failed.")

# Mount GraphQL endpoint
app.mount("/graphql", GraphQL(schema, debug=True))

# Mount vault REST routes
app.include_router(vault_router)

# Prometheus metrics endpoint
if PROMETHEUS_AVAILABLE:
    @app.get("/metrics")
    async def prometheus_metrics():
        """Prometheus metrics endpoint."""
        return get_metrics_endpoint()


@app.on_event("startup")
async def startup_event():
    """Load critical artifacts on startup."""
    _load_vkey_hashes()
    _ensure_vkeys_loaded()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Truth Engine - Personal Proof Vault API",
        "graphql": "/graphql",
        "vault": "/vault",
        "metrics": "/metrics" if PROMETHEUS_AVAILABLE else None
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