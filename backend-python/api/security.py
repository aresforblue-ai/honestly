"""
Production-grade security middleware and utilities.
Implements JWT authentication, rate limiting, input validation, security headers.
"""
import os
import time
import hashlib
import hmac
from typing import Optional, Dict, Any, Callable
from datetime import datetime, timedelta
from functools import wraps
from fastapi import HTTPException, Request, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import Response
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

# Configuration
JWT_SECRET = os.getenv('JWT_SECRET', os.urandom(32).hex())
JWT_ALGORITHM = 'HS256'
JWT_ACCESS_EXPIRY = int(os.getenv('JWT_ACCESS_EXPIRY', 3600))  # 1 hour
JWT_REFRESH_EXPIRY = int(os.getenv('JWT_REFRESH_EXPIRY', 604800))  # 7 days
RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
RATE_LIMIT_REDIS_URL = os.getenv('RATE_LIMIT_REDIS_URL', None)  # Optional Redis for distributed rate limiting

# In-memory rate limiter (fallback if Redis not available)
_rate_limit_store: Dict[str, Dict[str, Any]] = {}
_rate_limit_cleanup_interval = 300  # Clean up old entries every 5 minutes
_last_cleanup = time.time()

# Security headers
SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
}

security = HTTPBearer(auto_error=False)


class RateLimiter:
    """Production-grade rate limiter with sliding window."""
    
    def __init__(self, calls: int = 100, period: int = 60):
        self.calls = calls
        self.period = period
    
    def _get_key(self, identifier: str) -> str:
        return f"rate_limit:{identifier}"
    
    def _cleanup_old_entries(self):
        """Periodic cleanup of expired rate limit entries."""
        global _last_cleanup
        now = time.time()
        if now - _last_cleanup < _rate_limit_cleanup_interval:
            return
        
        expired_keys = [
            k for k, v in _rate_limit_store.items()
            if now - v.get('window_start', 0) > self.period * 2
        ]
        for key in expired_keys:
            _rate_limit_store.pop(key, None)
        _last_cleanup = now
    
    def check(self, identifier: str) -> bool:
        """Check if request should be allowed. Returns True if allowed."""
        if not RATE_LIMIT_ENABLED:
            return True
        
        self._cleanup_old_entries()
        key = self._get_key(identifier)
        now = time.time()
        
        entry = _rate_limit_store.get(key, {'count': 0, 'window_start': now})
        
        # Reset window if expired
        if now - entry['window_start'] > self.period:
            entry = {'count': 0, 'window_start': now}
        
        entry['count'] += 1
        _rate_limit_store[key] = entry
        
        return entry['count'] <= self.calls
    
    def get_remaining(self, identifier: str) -> int:
        """Get remaining requests in current window."""
        key = self._get_key(identifier)
        entry = _rate_limit_store.get(key, {'count': 0, 'window_start': time.time()})
        return max(0, self.calls - entry['count'])


def create_access_token(user_id: str, additional_claims: Optional[Dict] = None) -> str:
    """Create JWT access token."""
    payload = {
        'sub': user_id,
        'type': 'access',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=JWT_ACCESS_EXPIRY),
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(seconds=JWT_REFRESH_EXPIRY),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    
    payload = verify_token(credentials.credentials)
    if payload.get('type') != 'access':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    
    return payload.get('sub')


def get_client_identifier(request: Request) -> str:
    """Get client identifier for rate limiting."""
    # Try to get user ID from auth token first
    auth_header = request.headers.get('authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            token = auth_header.split(' ')[1]
            payload = verify_token(token)
            return f"user:{payload.get('sub')}"
        except:
            pass
    
    # Fallback to IP address
    forwarded = request.headers.get('x-forwarded-for')
    if forwarded:
        return f"ip:{forwarded.split(',')[0].strip()}"
    return f"ip:{request.client.host}"


def rate_limit(calls: int = 100, period: int = 60):
    """Decorator for rate limiting endpoints."""
    limiter = RateLimiter(calls=calls, period=period)
    
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            identifier = get_client_identifier(request)
            if not limiter.check(identifier):
                remaining = limiter.get_remaining(identifier)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again later.",
                    headers={'X-RateLimit-Remaining': str(remaining)}
                )
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


def add_security_headers(response: Response) -> Response:
    """Add security headers to response."""
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response


def validate_input(data: Any, schema: Dict[str, Any]) -> bool:
    """Validate input data against schema."""
    # Basic validation - extend with pydantic or jsonschema for production
    if not isinstance(data, dict):
        return False
    
    for key, rules in schema.items():
        if rules.get('required', False) and key not in data:
            return False
        
        if key in data:
            value = data[key]
            expected_type = rules.get('type')
            if expected_type and not isinstance(value, expected_type):
                return False
            
            if 'max_length' in rules and len(str(value)) > rules['max_length']:
                return False
            
            if 'pattern' in rules:
                import re
                if not re.match(rules['pattern'], str(value)):
                    return False
    
    return True


def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    # Remove null bytes
    data = data.replace('\x00', '')
    # Remove control characters except newlines and tabs
    import re
    data = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', data)
    return data.strip()


def hash_sensitive_data(data: str, salt: Optional[str] = None) -> str:
    """Hash sensitive data with optional salt."""
    if salt is None:
        salt = os.urandom(16).hex()
    
    h = hmac.new(salt.encode(), data.encode(), hashlib.sha256)
    return f"{salt}:{h.hexdigest()}"


def verify_ai_agent_signature(payload: str, signature: str, secret: str) -> bool:
    """Verify signature from AI agent requests."""
    expected_signature = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected_signature)


