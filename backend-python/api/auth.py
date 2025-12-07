"""
JWT/OIDC authentication helpers.
- Prefer RS/ES via OIDC JWKS.
- HS256 fallback only when explicitly allowed (ALLOW_HS_FALLBACK=true).
"""
import os
import time
from functools import lru_cache
from typing import Optional

import jwt
from fastapi import HTTPException, Depends
import logging
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGO = os.getenv("JWT_ALGO", "HS256")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE")
JWT_ISSUER = os.getenv("JWT_ISSUER")
OIDC_JWKS_URL = os.getenv("OIDC_JWKS_URL")
OIDC_ALGS = [alg.strip() for alg in os.getenv("OIDC_ALGS", "RS256,ES256").split(",") if alg.strip()]
ALLOW_HS_FALLBACK = os.getenv("ALLOW_HS_FALLBACK", "false").lower() == "true"
OIDC_REQUIRED = os.getenv("OIDC_REQUIRED", "false").lower() == "true"

security = HTTPBearer(auto_error=False)
logger = logging.getLogger("security")


@lru_cache(maxsize=1)
def _jwks_client():
    if not OIDC_JWKS_URL:
        return None
    return jwt.PyJWKClient(OIDC_JWKS_URL)


def _decode_token(token: str) -> dict:
    options = {"verify_aud": bool(JWT_AUDIENCE)}

    client = _jwks_client()
    if client:
        try:
            signing_key = client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=OIDC_ALGS or None,
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options=options,
            )
        except jwt.PyJWTError as exc:
            logger.warning("oidc_token_invalid", extra={"error": str(exc)})
            raise HTTPException(status_code=401, detail="Invalid token") from exc
    else:
        if OIDC_REQUIRED:
            raise HTTPException(status_code=503, detail="OIDC required but OIDC_JWKS_URL is not configured")
        if not ALLOW_HS_FALLBACK:
            raise HTTPException(status_code=503, detail="JWKS not configured and HS fallback disabled")
        if not JWT_SECRET:
            raise HTTPException(status_code=500, detail="JWT_SECRET not configured")
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGO],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options=options,
            )
        except jwt.PyJWTError as exc:
            logger.warning("hs_token_invalid", extra={"error": str(exc)})
            raise HTTPException(status_code=401, detail="Invalid token") from exc

    exp = payload.get("exp")
    if exp and exp < time.time():
        raise HTTPException(status_code=401, detail="Token expired")
    return payload


def get_current_user(
    creds: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    payload = _decode_token(creds.credentials)
    if "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": payload["sub"], "claims": payload}


def decode_authorization_header(auth_header: Optional[str]) -> dict:
    """
    Decode a Bearer token from an Authorization header.
    Raises HTTPException on failure.
    """
    if not auth_header or not auth_header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = auth_header.split(" ", 1)[1].strip()
    payload = _decode_token(token)
    if "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"user_id": payload["sub"], "claims": payload}


def get_optional_user(auth_header: Optional[str]) -> Optional[dict]:
    """
    Best-effort user resolution for contexts where auth is optional.
    Returns None if no header is present; raises for invalid tokens.
    """
    if not auth_header:
        return None
    return decode_authorization_header(auth_header)


