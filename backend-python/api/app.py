import os
from fastapi import FastAPI, HTTPException
from ariadne import QueryType, MutationType, make_executable_schema
from ariadne.asgi import GraphQL
from py2neo import Graph
from sentence_transformers import SentenceTransformer
from vector_index.faiss_index import FaissIndex

# Import vault resolvers and routes
from api.vault_resolvers import query as vault_query, mutation as vault_mutation
from api.vault_routes import router as vault_router

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

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

# Import vault resolvers
from api.vault_resolvers import query as vault_query, mutation as vault_mutation

# Create mutation type
mutation = MutationType()

# Copy vault query resolvers to main query
# Ariadne QueryType stores resolvers in _resolvers dict
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

# Mount GraphQL endpoint
app.mount("/graphql", GraphQL(schema, debug=True))

# Mount vault REST routes
app.include_router(vault_router)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Truth Engine - Personal Proof Vault API",
        "graphql": "/graphql",
        "vault": "/vault"
    }