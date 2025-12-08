"""
Redis-backed rate limiting with fallback to in-memory storage.

Provides configurable rate limits per endpoint category with
sliding window algorithm for accurate limiting.
"""
import os
import time
import hashlib
import logging
from typing import Optional, Tuple
from functools import wraps
from fastapi import Request, HTTPException, status

logger = logging.getLogger("api.rate_limit")

# Configuration
RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() != "false"
REDIS_URL = os.getenv("REDIS_URL", "")

# Rate limit configurations by category
RATE_LIMITS = {
    "default": {"requests": 60, "window": 60},      # 60/min for authenticated
    "public": {"requests": 20, "window": 60},       # 20/min for public endpoints
    "graphql": {"requests": 60, "window": 60},      # 60/min for GraphQL
    "upload": {"requests": 10, "window": 60},       # 10/min for uploads
    "proof": {"requests": 5, "window": 60},         # 5/min for proof generation (expensive)
    "share": {"requests": 30, "window": 60},        # 30/min for share links
}

# Redis client (lazy initialization)
_redis_client = None


def _get_redis():
    """Get Redis client with lazy initialization."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    
    if not REDIS_URL:
        return None
    
    try:
        import redis
        _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        _redis_client.ping()
        logger.info("Redis rate limiter initialized")
        return _redis_client
    except Exception as e:
        logger.warning(f"Redis unavailable, using in-memory rate limiter: {e}")
        return None


# In-memory fallback storage
_memory_store: dict = {}


def _get_client_key(request: Request) -> str:
    """Generate a unique key for the client."""
    # Use forwarded IP if behind proxy, otherwise use direct IP
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    
    # Include user ID if authenticated
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    
    # Hash IP for privacy in logs
    ip_hash = hashlib.sha256(ip.encode()).hexdigest()[:12]
    return f"ip:{ip_hash}"


class RateLimiter:
    """
    Sliding window rate limiter with Redis backend and in-memory fallback.
    """
    
    def __init__(self, category: str = "default"):
        self.category = category
        config = RATE_LIMITS.get(category, RATE_LIMITS["default"])
        self.max_requests = config["requests"]
        self.window_seconds = config["window"]
    
    def _redis_check(self, key: str) -> Tuple[bool, int, int]:
        """Check rate limit using Redis sliding window."""
        redis_client = _get_redis()
        if not redis_client:
            return self._memory_check(key)
        
        now = time.time()
        window_start = now - self.window_seconds
        redis_key = f"ratelimit:{self.category}:{key}"
        
        try:
            pipe = redis_client.pipeline()
            
            # Remove old entries outside window
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count entries in current window
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {str(now): now})
            
            # Set expiry on the key
            pipe.expire(redis_key, self.window_seconds + 1)
            
            results = pipe.execute()
            count = results[1]  # zcard result
            
            remaining = max(0, self.max_requests - count - 1)
            reset_time = int(now + self.window_seconds)
            
            if count >= self.max_requests:
                return False, 0, reset_time
            
            return True, remaining, reset_time
            
        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}")
            return self._memory_check(key)
    
    def _memory_check(self, key: str) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory storage (fallback)."""
        now = time.time()
        memory_key = f"{self.category}:{key}"
        
        # Clean up old entries
        if memory_key in _memory_store:
            window_start = now - self.window_seconds
            _memory_store[memory_key] = [
                ts for ts in _memory_store[memory_key] 
                if ts > window_start
            ]
        else:
            _memory_store[memory_key] = []
        
        count = len(_memory_store[memory_key])
        remaining = max(0, self.max_requests - count - 1)
        reset_time = int(now + self.window_seconds)
        
        if count >= self.max_requests:
            return False, 0, reset_time
        
        _memory_store[memory_key].append(now)
        return True, remaining, reset_time
    
    def check(self, request: Request) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limits.
        
        Returns:
            Tuple of (allowed, remaining, reset_timestamp)
        """
        if not RATE_LIMIT_ENABLED:
            return True, self.max_requests, int(time.time() + self.window_seconds)
        
        key = _get_client_key(request)
        return self._redis_check(key)
    
    async def __call__(self, request: Request):
        """Dependency for FastAPI routes."""
        allowed, remaining, reset_time = self.check(request)
        
        # Add rate limit headers
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = reset_time
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                extra={
                    "category": self.category,
                    "client": _get_client_key(request),
                    "path": request.url.path,
                }
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time())),
                },
            )
        
        return True


def rate_limit(category: str = "default"):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @app.get("/api/resource")
        @rate_limit("public")
        async def get_resource():
            ...
    """
    limiter = RateLimiter(category)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, request: Request = None, **kwargs):
            # Find request in args if not in kwargs
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                await limiter(request)
            
            return await func(*args, request=request, **kwargs)
        return wrapper
    return decorator


# Pre-configured rate limiters as dependencies
public_rate_limit = RateLimiter("public")
upload_rate_limit = RateLimiter("upload")
proof_rate_limit = RateLimiter("proof")
share_rate_limit = RateLimiter("share")
graphql_rate_limit = RateLimiter("graphql")

