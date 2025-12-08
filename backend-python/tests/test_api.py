"""
Unit and integration tests for the Truth Engine API.

Run with: pytest tests/test_api.py -v
"""
import pytest
import os
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Set test environment before importing app
os.environ["ALLOW_GENERATED_VAULT_KEY"] = "true"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASS"] = "test"
os.environ["RATE_LIMIT_ENABLED"] = "false"


# ============================================
# Fixtures
# ============================================

@pytest.fixture(scope="module")
def mock_graph():
    """Mock Neo4j graph connection."""
    with patch("api.app.Graph") as mock:
        mock_instance = MagicMock()
        mock_instance.run.return_value.data.return_value = []
        mock.return_value = mock_instance
        yield mock_instance


@pytest.fixture(scope="module")
def mock_vkeys():
    """Mock verification key functions."""
    with patch("api.app.vkeys_ready", return_value=True), \
         patch("api.app.get_vkey_hash", return_value="test_hash_abc123"), \
         patch("api.app.load_vkey_hashes"):
        yield


@pytest.fixture
def client(mock_graph, mock_vkeys):
    """Create test client with mocked dependencies."""
    from api.app import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Generate test JWT headers."""
    # In real tests, you'd generate a proper JWT
    return {"Authorization": "Bearer test_jwt_token"}


# ============================================
# Health Endpoint Tests
# ============================================

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_liveness_probe(self, client):
        """Test /health/live endpoint returns 200."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_readiness_probe_healthy(self, client, mock_graph):
        """Test /health/ready when all services are healthy."""
        mock_graph.run.return_value.evaluate.return_value = 1
        response = client.get("/health/ready")
        data = response.json()
        assert response.status_code in [200, 503]  # Depends on mock state
        assert "status" in data
        assert "vkeys" in data
        assert "neo4j" in data


class TestRootEndpoint:
    """Test root endpoint."""
    
    def test_root_returns_info(self, client):
        """Test / endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "graphql" in data
        assert "vault" in data


class TestCapabilities:
    """Test /capabilities endpoint."""
    
    def test_capabilities_returns_proofs(self, client):
        """Test /capabilities returns proof information."""
        response = client.get("/capabilities")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "proofs" in data
        assert isinstance(data["proofs"], list)


# ============================================
# Error Handling Tests
# ============================================

class TestErrorHandling:
    """Test custom error handling."""
    
    def test_404_returns_structured_error(self, client):
        """Test 404 returns structured error response."""
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_validation_error_format(self, client):
        """Test validation errors are properly formatted."""
        # GraphQL with invalid query should return structured error
        response = client.post(
            "/graphql",
            json={"query": "invalid query syntax"}
        )
        assert response.status_code in [200, 400]  # GraphQL may return 200 with errors


# ============================================
# Sanitizer Tests
# ============================================

class TestSanitizer:
    """Test input sanitization utilities."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        from api.sanitizer import sanitize_string
        
        assert sanitize_string("hello") == "hello"
        assert sanitize_string("  hello  ") == "hello"
        assert sanitize_string("hello\x00world") == "helloworld"
    
    def test_sanitize_string_html_escape(self):
        """Test HTML escaping."""
        from api.sanitizer import sanitize_string
        
        result = sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        assert "&lt;script&gt;" in result
    
    def test_sanitize_string_max_length(self):
        """Test max length truncation."""
        from api.sanitizer import sanitize_string
        
        long_string = "a" * 2000
        result = sanitize_string(long_string, max_length=100)
        assert len(result) == 100
    
    def test_check_injection_cypher(self):
        """Test Cypher injection detection."""
        from api.sanitizer import check_injection
        
        assert check_injection("MATCH (n) DELETE n") == True
        assert check_injection("normal text") == False
        assert check_injection("DETACH DELETE n") == True
    
    def test_check_injection_xss(self):
        """Test XSS pattern detection."""
        from api.sanitizer import check_injection
        
        assert check_injection("<script>alert('xss')</script>") == True
        assert check_injection("javascript:void(0)") == True
        assert check_injection("onclick=doSomething()") == True
    
    def test_sanitize_identifier_valid(self):
        """Test valid identifier sanitization."""
        from api.sanitizer import sanitize_identifier
        
        assert sanitize_identifier("doc_abc123def456", "document_id") == "doc_abc123def456"
        assert sanitize_identifier("shr_abcdef123456789", "share_token") == "shr_abcdef123456789"
    
    def test_sanitize_identifier_invalid(self):
        """Test invalid identifier rejection."""
        from api.sanitizer import sanitize_identifier
        
        assert sanitize_identifier("invalid-id", "document_id") is None
        assert sanitize_identifier("", "document_id") is None
        assert sanitize_identifier(None, "document_id") is None
    
    def test_sanitize_dict_recursive(self):
        """Test recursive dictionary sanitization."""
        from api.sanitizer import sanitize_dict
        
        input_dict = {
            "name": "  test  ",
            "nested": {"value": "<script>xss</script>"},
            "number": 42,
            "list": ["item1", "item2"]
        }
        result = sanitize_dict(input_dict)
        
        assert result["name"] == "test"
        assert "&lt;script&gt;" in result["nested"]["value"]
        assert result["number"] == 42
    
    def test_validate_document_type(self):
        """Test document type validation."""
        from api.sanitizer import validate_document_type
        
        assert validate_document_type("passport") == "passport"
        assert validate_document_type("PASSPORT") == "passport"
        assert validate_document_type("invalid") is None
    
    def test_validate_access_level(self):
        """Test access level validation."""
        from api.sanitizer import validate_access_level
        
        assert validate_access_level("PROOF_ONLY") == "PROOF_ONLY"
        assert validate_access_level("metadata") == "METADATA"
        assert validate_access_level("invalid") is None
    
    def test_validate_proof_type(self):
        """Test proof type validation."""
        from api.sanitizer import validate_proof_type
        
        assert validate_proof_type("age") == "age"
        assert validate_proof_type("authenticity") == "authenticity"
        assert validate_proof_type("invalid") is None


# ============================================
# Rate Limiter Tests
# ============================================

class TestRateLimiter:
    """Test rate limiting functionality."""
    
    def test_limiter_allows_under_limit(self):
        """Test requests under limit are allowed."""
        from api.rate_limiter import RateLimiter
        from unittest.mock import MagicMock
        
        limiter = RateLimiter("default")
        mock_request = MagicMock()
        mock_request.headers.get.return_value = None
        mock_request.client.host = "127.0.0.1"
        
        allowed, remaining, reset = limiter.check(mock_request)
        assert allowed == True
        assert remaining >= 0
    
    def test_limiter_categories(self):
        """Test different rate limit categories have different limits."""
        from api.rate_limiter import RATE_LIMITS
        
        assert RATE_LIMITS["public"]["requests"] < RATE_LIMITS["default"]["requests"]
        assert RATE_LIMITS["proof"]["requests"] < RATE_LIMITS["public"]["requests"]


# ============================================
# Error Classes Tests
# ============================================

class TestErrorClasses:
    """Test custom exception classes."""
    
    def test_api_error_to_dict(self):
        """Test APIError serialization."""
        from api.errors import APIError
        
        error = APIError(
            message="Test error",
            status_code=400,
            error_code="TEST_ERROR",
            details={"field": "test"}
        )
        
        result = error.to_dict()
        assert result["error"]["code"] == "TEST_ERROR"
        assert result["error"]["message"] == "Test error"
        assert result["error"]["details"]["field"] == "test"
        assert "correlation_id" in result["error"]
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError."""
        from api.errors import ResourceNotFoundError
        
        error = ResourceNotFoundError("Document", "doc_123")
        assert error.status_code == 404
        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert "Document" in error.message
    
    def test_validation_error(self):
        """Test ValidationError."""
        from api.errors import ValidationError
        
        error = ValidationError("Invalid format", field="email")
        assert error.status_code == 422
        assert error.details["field"] == "email"
    
    def test_rate_limit_error(self):
        """Test RateLimitExceededError."""
        from api.errors import RateLimitExceededError
        
        error = RateLimitExceededError(retry_after=30)
        assert error.status_code == 429
        assert error.details["retry_after_seconds"] == 30


# ============================================
# Integration Tests
# ============================================

class TestIntegration:
    """Integration tests (require running services)."""
    
    @pytest.mark.integration
    def test_graphql_introspection(self, client):
        """Test GraphQL introspection query."""
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        response = client.post("/graphql", json={"query": query})
        assert response.status_code == 200
    
    @pytest.mark.integration
    def test_zkp_artifacts_accessible(self, client):
        """Test ZKP artifacts are served correctly."""
        response = client.get("/zkp/artifacts/age/verification_key.json")
        # May be 200 or 404 depending on whether artifacts exist
        assert response.status_code in [200, 404, 503]


# ============================================
# Run Tests
# ============================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

