"""
Unit tests for JWT authentication and RBAC

Run with: pytest tests/unit/test_auth.py -v
"""

import pytest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

# Set test environment before imports
os.environ["JWT_SECRET"] = "test_secret_key_for_unit_tests_only_32chars"
os.environ["JWT_EXPIRY_HOURS"] = "1"
os.environ["JWT_REFRESH_DAYS"] = "1"

# Import after setting env vars
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend-python'))

from api.auth import (
    create_access_token,
    create_refresh_token,
    create_token_pair,
    decode_token,
    revoke_token,
    refresh_access_token,
    ROLE_PERMISSIONS,
    User,
)


class TestTokenCreation:
    """Test JWT token generation"""
    
    def test_create_access_token(self):
        """Access token should contain correct claims"""
        token = create_access_token("user123", "user")
        payload = decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["role"] == "user"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Refresh token should be valid and have correct type"""
        token = create_refresh_token("user123", "user")
        payload = decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"
    
    def test_create_token_pair(self):
        """Token pair should contain both tokens"""
        pair = create_token_pair("user123", "admin")
        
        assert pair.access_token
        assert pair.refresh_token
        assert pair.token_type == "bearer"
        assert pair.expires_in > 0
    
    def test_token_contains_permissions(self):
        """Access token should include role permissions"""
        token = create_access_token("admin1", "admin")
        payload = decode_token(token)
        
        assert "admin:config" in payload["permissions"]
        assert "read:claims" in payload["permissions"]
    
    def test_extra_permissions(self):
        """Extra permissions should be added to token"""
        token = create_access_token("user1", "user", ["special:permission"])
        payload = decode_token(token)
        
        assert "special:permission" in payload["permissions"]
        assert "read:claims" in payload["permissions"]


class TestTokenValidation:
    """Test JWT token validation"""
    
    def test_valid_token(self):
        """Valid token should decode successfully"""
        token = create_access_token("user123", "user")
        payload = decode_token(token)
        
        assert payload["sub"] == "user123"
    
    def test_expired_token(self):
        """Expired token should raise exception"""
        import jwt
        
        payload = {
            "sub": "user123",
            "role": "user",
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iat": datetime.utcnow() - timedelta(hours=2),
            "jti": "test-jti",
            "type": "access",
        }
        token = jwt.encode(payload, os.environ["JWT_SECRET"], algorithm="HS256")
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail.lower()
    
    def test_invalid_signature(self):
        """Token with wrong signature should be rejected"""
        import jwt
        
        payload = {"sub": "user123", "role": "user", "exp": datetime.utcnow() + timedelta(hours=1)}
        token = jwt.encode(payload, "wrong_secret", algorithm="HS256")
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert exc_info.value.status_code == 401
    
    def test_malformed_token(self):
        """Malformed token should be rejected"""
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            decode_token("not.a.valid.token")
        
        assert exc_info.value.status_code == 401


class TestTokenRevocation:
    """Test token revocation"""
    
    def test_revoke_token(self):
        """Revoked token should fail validation"""
        token = create_access_token("user123", "user")
        
        # Token should be valid initially
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        
        # Revoke the token
        assert revoke_token(token) == True
        
        # Token should now be invalid
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            decode_token(token)
        
        assert "revoked" in exc_info.value.detail.lower()
    
    def test_revoke_invalid_token(self):
        """Revoking invalid token should return False"""
        assert revoke_token("invalid.token") == False


class TestTokenRefresh:
    """Test token refresh flow"""
    
    def test_refresh_token_flow(self):
        """Refresh token should generate new token pair"""
        # Create initial pair
        pair = create_token_pair("user123", "verifier")
        
        # Refresh
        new_pair = refresh_access_token(pair.refresh_token)
        
        assert new_pair.access_token != pair.access_token
        assert new_pair.refresh_token != pair.refresh_token
        
        # New access token should be valid
        payload = decode_token(new_pair.access_token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "verifier"
    
    def test_refresh_with_access_token_fails(self):
        """Using access token for refresh should fail"""
        token = create_access_token("user123", "user")
        
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            refresh_access_token(token)
        
        assert "Invalid refresh token" in exc_info.value.detail


class TestRolePermissions:
    """Test role-based permissions"""
    
    def test_admin_has_all_permissions(self):
        """Admin role should have comprehensive permissions"""
        perms = ROLE_PERMISSIONS["admin"]
        
        assert "admin:config" in perms
        assert "write:users" in perms
        assert "delete:claims" in perms
    
    def test_user_has_limited_permissions(self):
        """User role should have limited permissions"""
        perms = ROLE_PERMISSIONS["user"]
        
        assert "read:claims" in perms
        assert "write:proofs" in perms
        assert "admin:config" not in perms
        assert "delete:claims" not in perms
    
    def test_anonymous_can_verify(self):
        """Anonymous users should be able to verify proofs"""
        perms = ROLE_PERMISSIONS["anonymous"]
        
        assert "verify:proofs" in perms
        assert "read:claims" in perms
        assert "write:proofs" not in perms


class TestUserModel:
    """Test User model"""
    
    def test_user_creation(self):
        """User model should hold correct data"""
        user = User(
            id="test123",
            role="verifier",
            permissions=["read:claims", "write:proofs"],
            token_id="jti-123"
        )
        
        assert user.id == "test123"
        assert user.role == "verifier"
        assert "read:claims" in user.permissions


# Integration tests would go in tests/integration/test_auth_endpoints.py

