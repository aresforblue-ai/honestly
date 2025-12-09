"""
JWT Authentication & Role-Based Access Control (RBAC)

Implements:
- JWT token generation and validation
- Role-based permissions (admin, verifier, user, anonymous)
- FastAPI dependency injection for protected routes
- Token refresh and revocation

Environment Variables:
- JWT_SECRET: Secret key for signing tokens (REQUIRED in production)
- JWT_ALGORITHM: Algorithm (default: HS256)
- JWT_EXPIRY_HOURS: Token expiry (default: 24)
- JWT_REFRESH_DAYS: Refresh token expiry (default: 7)
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Literal
from functools import wraps

from fastapi import HTTPException, Depends, Request, APIRouter
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))
JWT_REFRESH_DAYS = int(os.getenv("JWT_REFRESH_DAYS", "7"))

# Warn if using default secret
if JWT_SECRET == "CHANGE_ME_IN_PRODUCTION_use_openssl_rand_hex_32":
    logger.warning("⚠️  Using default JWT_SECRET - SET THIS IN PRODUCTION!")

# =============================================================================
# Models
# =============================================================================

Role = Literal["admin", "verifier", "user", "anonymous"]


class TokenPayload(BaseModel):
    """JWT token payload structure"""

    sub: str  # Subject (user ID)
    role: Role  # User role
    exp: datetime  # Expiration time
    iat: datetime  # Issued at
    jti: str  # JWT ID (for revocation)
    permissions: List[str] = []  # Fine-grained permissions


class TokenPair(BaseModel):
    """Access + refresh token pair"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Seconds until access token expires


class User(BaseModel):
    """Authenticated user context"""

    id: str
    role: Role
    permissions: List[str]
    token_id: str


# =============================================================================
# Role Permissions Matrix
# =============================================================================

ROLE_PERMISSIONS = {
    "admin": [
        "read:claims",
        "write:claims",
        "delete:claims",
        "read:users",
        "write:users",
        "delete:users",
        "read:proofs",
        "write:proofs",
        "verify:proofs",
        "admin:config",
        "admin:audit",
    ],
    "verifier": [
        "read:claims",
        "write:claims",
        "read:proofs",
        "write:proofs",
        "verify:proofs",
    ],
    "user": [
        "read:claims",
        "read:proofs",
        "write:proofs",
    ],
    "anonymous": [
        "read:claims",
        "verify:proofs",  # Anyone can verify a proof
    ],
}

# =============================================================================
# Token Management
# =============================================================================

# In-memory token blacklist (use Redis in production)
_revoked_tokens: set = set()


def create_access_token(user_id: str, role: Role, extra_permissions: List[str] = None) -> str:
    """Create a JWT access token"""
    import uuid

    now = datetime.utcnow()
    permissions = ROLE_PERMISSIONS.get(role, []).copy()
    if extra_permissions:
        permissions.extend(extra_permissions)

    payload = {
        "sub": user_id,
        "role": role,
        "permissions": list(set(permissions)),
        "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, role: Role) -> str:
    """Create a JWT refresh token"""
    import uuid

    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(days=JWT_REFRESH_DAYS),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_token_pair(user_id: str, role: Role) -> TokenPair:
    """Create both access and refresh tokens"""
    return TokenPair(
        access_token=create_access_token(user_id, role),
        refresh_token=create_refresh_token(user_id, role),
        expires_in=JWT_EXPIRY_HOURS * 3600,
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # Check if token is revoked
        if payload.get("jti") in _revoked_tokens:
            raise HTTPException(status_code=401, detail="Token has been revoked")

        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


def revoke_token(token: str) -> bool:
    """Revoke a token by adding its JTI to the blacklist"""
    try:
        payload = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALGORITHM], options={"verify_exp": False}
        )
        jti = payload.get("jti")
        if jti:
            _revoked_tokens.add(jti)
            logger.info(f"Token revoked: {jti[:8]}...")
            return True
    except jwt.InvalidTokenError:
        pass
    return False


def refresh_access_token(refresh_token: str) -> TokenPair:
    """Use refresh token to get new token pair"""
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Revoke old refresh token
    revoke_token(refresh_token)

    # Issue new pair
    return create_token_pair(payload["sub"], payload["role"])


# =============================================================================
# FastAPI Dependencies
# =============================================================================

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request, credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    FastAPI dependency to get current authenticated user.
    Returns anonymous user if no token provided.
    """
    if not credentials:
        # Anonymous access
        return User(
            id="anonymous",
            role="anonymous",
            permissions=ROLE_PERMISSIONS["anonymous"],
            token_id="none",
        )

    payload = decode_token(credentials.credentials)

    return User(
        id=payload["sub"],
        role=payload["role"],
        permissions=payload.get("permissions", ROLE_PERMISSIONS.get(payload["role"], [])),
        token_id=payload["jti"],
    )


def require_auth(user: User = Depends(get_current_user)) -> User:
    """Require authenticated user (not anonymous)"""
    if user.role == "anonymous":
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


def require_role(*roles: Role):
    """Require user to have one of the specified roles"""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Required role: {' or '.join(roles)}")
        return user

    return dependency


def require_permission(*permissions: str):
    """Require user to have all specified permissions"""

    def dependency(user: User = Depends(get_current_user)) -> User:
        missing = [p for p in permissions if p not in user.permissions]
        if missing:
            raise HTTPException(
                status_code=403, detail=f"Missing permissions: {', '.join(missing)}"
            )
        return user

    return dependency


# =============================================================================
# GraphQL Context Integration
# =============================================================================


def get_graphql_context(request: Request) -> dict:
    """
    Create GraphQL context with authenticated user.
    Use in Ariadne/Strawberry resolvers.
    """
    auth_header = request.headers.get("Authorization", "")
    user = User(
        id="anonymous",
        role="anonymous",
        permissions=ROLE_PERMISSIONS["anonymous"],
        token_id="none",
    )

    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = decode_token(token)
            user = User(
                id=payload["sub"],
                role=payload["role"],
                permissions=payload.get("permissions", []),
                token_id=payload["jti"],
            )
        except HTTPException:
            pass  # Keep anonymous user

    return {"user": user, "request": request}


def graphql_require_permission(*permissions: str):
    """Decorator for GraphQL resolvers requiring permissions"""

    def decorator(resolver):
        @wraps(resolver)
        async def wrapper(*args, info, **kwargs):
            user = info.context.get("user")
            if not user:
                raise Exception("Authentication context not available")

            missing = [p for p in permissions if p not in user.permissions]
            if missing:
                raise Exception(f"Missing permissions: {', '.join(missing)}")

            return await resolver(*args, info, **kwargs)

        return wrapper

    return decorator


# =============================================================================
# Auth Routes (add to FastAPI app)
# =============================================================================

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: dict


@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return token pair.

    In production, validate against your user database.
    """
    # NOTE: Demo users for development/testing
    # For production, integrate with your user store:
    #   - Connect to database (Neo4j, PostgreSQL, etc.)
    #   - Use proper password hashing (bcrypt, argon2)
    #   - Add account lockout after failed attempts

    # Demo users (development only)
    demo_users = {
        "admin": {"password": "admin123", "role": "admin"},
        "verifier": {"password": "verify123", "role": "verifier"},
        "user": {"password": "user123", "role": "user"},
    }

    user_data = demo_users.get(request.username)
    if not user_data or user_data["password"] != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    tokens = create_token_pair(request.username, user_data["role"])

    return LoginResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user={
            "id": request.username,
            "role": user_data["role"],
            "permissions": ROLE_PERMISSIONS[user_data["role"]],
        },
    )


@auth_router.post("/refresh", response_model=TokenPair)
async def refresh(refresh_token: str):
    """Exchange refresh token for new token pair"""
    return refresh_access_token(refresh_token)


@auth_router.post("/logout")
async def logout(user: User = Depends(require_auth)):
    """Revoke current token"""
    # In a real app, you'd revoke from the request's token
    return {"message": "Logged out successfully"}


@auth_router.get("/me")
async def get_me(user: User = Depends(require_auth)):
    """Get current user info"""
    return {
        "id": user.id,
        "role": user.role,
        "permissions": user.permissions,
    }
