"""
Production middleware for security, performance, and monitoring.
"""
import os
import time
import json
import hashlib
import logging
from typing import Callable
from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from api.security import add_security_headers, get_client_identifier, RateLimiter
from api.prometheus import metrics

logger = logging.getLogger(__name__)

# Global rate limiter for all requests
_global_rate_limiter = RateLimiter(calls=1000, period=60)  # 1000 req/min per client


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        response = await call_next(request)
        return add_security_headers(response)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        identifier = get_client_identifier(request)
        
        if not _global_rate_limiter.check(identifier):
            remaining = _global_rate_limiter.get_remaining(identifier)
            # Record rate limit hit
            metrics.record_rate_limit_hit(request.url.path, identifier)
            return Response(
                content=json.dumps({"detail": "Rate limit exceeded"}),
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                media_type="application/json",
                headers={
                    'X-RateLimit-Remaining': str(remaining),
                    'X-RateLimit-Reset': str(int(time.time()) + 60)
                }
            )
        
        response = await call_next(request)
        remaining = _global_rate_limiter.get_remaining(identifier)
        response.headers['X-RateLimit-Remaining'] = str(remaining)
        return response


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Monitor request performance and log slow requests."""
    
    def __init__(self, app, slow_request_threshold: float = 0.2):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Record Prometheus metrics
        endpoint = request.url.path
        metrics.record_request(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
            duration=duration
        )
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} took {duration:.3f}s",
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'duration': duration,
                    'client': get_client_identifier(request)
                }
            )
        
        # Add performance headers
        response.headers['X-Response-Time'] = f"{duration:.3f}"
        response.headers['X-Request-ID'] = request.headers.get('X-Request-ID', '')
        
        return response


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests for audit trail."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        client_id = get_client_identifier(request)
        
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'client': client_id,
                'user_agent': request.headers.get('user-agent', ''),
                'timestamp': time.time()
            }
        )
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} {response.status_code}",
            extra={
                'method': request.method,
                'path': request.url.path,
                'status_code': response.status_code,
                'duration': duration,
                'client': client_id
            }
        )
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Handle errors gracefully and prevent information leakage."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
                extra={
                    'method': request.method,
                    'path': request.url.path,
                    'client': get_client_identifier(request)
                }
            )
            
            # Don't leak internal error details in production
            is_dev = os.getenv('ENVIRONMENT', 'production') == 'development'
            
            return Response(
                content=json.dumps({
                    "detail": str(e) if is_dev else "Internal server error",
                    "error_id": hashlib.sha256(f"{time.time()}{request.url.path}".encode()).hexdigest()[:16]
                }),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )

