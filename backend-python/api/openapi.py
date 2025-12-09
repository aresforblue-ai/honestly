"""
OpenAPI/Swagger configuration for the Truth Engine API.

Provides enhanced documentation, security schemes, and example responses.
"""

from typing import Dict, Any

# API Information
API_TITLE = "Truth Engine API"
API_VERSION = "1.0.0"
API_DESCRIPTION = """
# Truth Engine - Personal Proof Vault API

The Truth Engine is a privacy-preserving identity and credential verification system 
powered by **Zero-Knowledge Proofs (ZK-SNARKs)**.

## Features

- **🔐 Zero-Knowledge Proofs**: Generate and verify Groth16 proofs without revealing sensitive data
- **📦 Personal Proof Vault**: Encrypted document storage with blockchain anchoring
- **🔗 Shareable Proof Links**: Time-limited, access-controlled proof bundles
- **📊 GraphQL API**: Flexible querying for entity claims and verification data
- **🛡️ Enterprise Security**: Rate limiting, CORS, CSP, and structured logging

## Authentication

Most endpoints require JWT authentication. Include the token in the `Authorization` header:

```
Authorization: Bearer <your-jwt-token>
```

For development, you can use HS256 tokens. Production deployments should use RS256/ES256 via OIDC.

## Rate Limits

| Endpoint Type | Requests/Minute |
|--------------|-----------------|
| Authenticated | 60 |
| Public Share Links | 20 |
| GraphQL | 60 |

## Zero-Knowledge Circuits

| Circuit | Description | Public Inputs |
|---------|-------------|---------------|
| `age` | Age verification (>= minAge) | minAgeOut, referenceTsOut, documentHashOut, commitment |
| `authenticity` | Document authenticity via Merkle proof | rootOut, leafOut |
| `age_level3` | Enhanced age proof with nullifiers | referenceTs, minAge, userID, documentHash, nullifier |

## Links

- [GitHub Repository](https://github.com/honestly-labs/honestly)
- [Documentation](https://docs.honestly.dev)
- [Security Policy](https://github.com/honestly-labs/honestly/security)
"""

# Tags for grouping endpoints
API_TAGS = [
    {
        "name": "health",
        "description": "Health check and readiness probes for Kubernetes/Docker deployments",
    },
    {
        "name": "vault",
        "description": "Personal Proof Vault operations - document upload, retrieval, and sharing",
    },
    {
        "name": "proofs",
        "description": "Zero-knowledge proof generation and verification",
    },
    {
        "name": "share",
        "description": "Share link management for proof bundles",
    },
    {
        "name": "graphql",
        "description": "GraphQL endpoint for entity queries and mutations",
    },
    {
        "name": "monitoring",
        "description": "Prometheus metrics and observability endpoints",
    },
]

# Security schemes
SECURITY_SCHEMES = {
    "bearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token obtained from authentication service",
    },
    "apiKey": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "API key for service-to-service authentication",
    },
}

# Response examples
RESPONSE_EXAMPLES: Dict[str, Any] = {
    "document_upload": {
        "document_id": "doc_abc123def456",
        "hash": "0x7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "fabric_tx_id": "tx_789xyz",
        "message": "Document uploaded and encrypted successfully",
    },
    "share_bundle": {
        "share_token": "shr_xyzabc123",
        "document_id": "doc_abc123def456",
        "proof_type": "age",
        "access_level": "PROOF_ONLY",
        "document_hash": "0x7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069",
        "issued_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-01-15T11:30:00Z",
        "max_accesses": 5,
        "nonce": "a1b2c3d4e5f6",
        "verification": {
            "circuit": "age",
            "vk_url": "/zkp/artifacts/age/verification_key.json",
            "vk_sha256": "abc123...",
            "attestation": {
                "fabric_tx_id": "tx_789xyz",
                "merkle_root": "0x...",
                "timestamp": "2024-01-15T10:00:00Z",
            },
        },
        "signature": "hmac_signature_here",
    },
    "error_response": {
        "error": {
            "code": "VALIDATION_ERROR",
            "message": "Invalid document type",
            "correlation_id": "abc123",
            "details": {"field": "document_type"},
        }
    },
    "health_ready": {
        "status": "ok",
        "vkeys": True,
        "neo4j": True,
    },
    "capabilities": {
        "service": "Truth Engine - Personal Proof Vault",
        "version": "1.0.0",
        "proofs": [
            {
                "type": "age_proof",
                "circuit": "age",
                "public_inputs": ["minAgeOut", "referenceTsOut", "documentHashOut", "commitment"],
                "endpoint": "/vault/share/{token}/bundle",
                "vk": "/zkp/artifacts/age/verification_key.json",
                "vk_sha256": "abc123...",
            }
        ],
        "hmac": True,
    },
}


def get_openapi_config() -> Dict[str, Any]:
    """Get OpenAPI configuration for FastAPI app."""
    return {
        "title": API_TITLE,
        "version": API_VERSION,
        "description": API_DESCRIPTION,
        "openapi_tags": API_TAGS,
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "swagger_ui_parameters": {
            "defaultModelsExpandDepth": -1,
            "docExpansion": "list",
            "filter": True,
            "showExtensions": True,
            "syntaxHighlight.theme": "monokai",
        },
    }


def customize_openapi_schema(app) -> Dict[str, Any]:
    """
    Customize the OpenAPI schema with additional metadata.
    Call this after app initialization.
    """
    if app.openapi_schema:
        return app.openapi_schema

    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=API_TITLE,
        version=API_VERSION,
        description=API_DESCRIPTION,
        routes=app.routes,
        tags=API_TAGS,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

    # Add server URLs
    openapi_schema["servers"] = [
        {"url": "/", "description": "Current server"},
        {"url": "http://localhost:8000", "description": "Local development"},
        {"url": "https://api.honestly.dev", "description": "Production"},
    ]

    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "Honestly Labs",
        "url": "https://honestly.dev",
        "email": "support@honestly.dev",
    }
    openapi_schema["info"]["license"] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }

    # Add external docs
    openapi_schema["externalDocs"] = {
        "description": "Full Documentation",
        "url": "https://docs.honestly.dev",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
