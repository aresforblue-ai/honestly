"""
Custom exceptions and error handling for the Truth Engine API.

Provides structured error responses with correlation IDs for debugging.
"""

import uuid
import logging
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_422_UNPROCESSABLE_ENTITY,
    HTTP_429_TOO_MANY_REQUESTS,
    HTTP_500_INTERNAL_SERVER_ERROR,
    HTTP_502_BAD_GATEWAY,
    HTTP_503_SERVICE_UNAVAILABLE,
)

logger = logging.getLogger("api.errors")


class APIError(Exception):
    """Base API exception with structured error details."""

    def __init__(
        self,
        message: str,
        status_code: int = HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())[:8]

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API response format."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "correlation_id": self.correlation_id,
            }
        }
        if self.details:
            response["error"]["details"] = self.details
        return response


# ============================================
# Authentication Errors
# ============================================


class AuthenticationError(APIError):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication required", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=HTTP_401_UNAUTHORIZED,
            error_code="AUTHENTICATION_REQUIRED",
            details=details,
        )


class InvalidTokenError(APIError):
    """JWT or API token is invalid."""

    def __init__(self, message: str = "Invalid or expired token", details: Optional[Dict] = None):
        super().__init__(
            message=message,
            status_code=HTTP_401_UNAUTHORIZED,
            error_code="INVALID_TOKEN",
            details=details,
        )


class InsufficientPermissionsError(APIError):
    """User lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions", required: Optional[str] = None):
        details = {"required_permission": required} if required else None
        super().__init__(
            message=message,
            status_code=HTTP_403_FORBIDDEN,
            error_code="INSUFFICIENT_PERMISSIONS",
            details=details,
        )


# ============================================
# Resource Errors
# ============================================


class ResourceNotFoundError(APIError):
    """Requested resource does not exist."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found",
            status_code=HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class ResourceConflictError(APIError):
    """Resource already exists or conflicts with existing state."""

    def __init__(self, message: str, resource_type: str, resource_id: str):
        super().__init__(
            message=message,
            status_code=HTTP_409_CONFLICT,
            error_code="RESOURCE_CONFLICT",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


# ============================================
# Validation Errors
# ============================================


class ValidationError(APIError):
    """Request validation failed."""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict] = None):
        error_details = details or {}
        if field:
            error_details["field"] = field
        super().__init__(
            message=message,
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR",
            details=error_details,
        )


class InvalidInputError(APIError):
    """Invalid input provided."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            status_code=HTTP_400_BAD_REQUEST,
            error_code="INVALID_INPUT",
            details={"field": field} if field else None,
        )


# ============================================
# Rate Limiting Errors
# ============================================


class RateLimitExceededError(APIError):
    """Request rate limit exceeded."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message="Rate limit exceeded. Please try again later.",
            status_code=HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after},
        )


# ============================================
# ZK Proof Errors
# ============================================


class ProofGenerationError(APIError):
    """Failed to generate ZK proof."""

    def __init__(self, circuit: str, reason: str):
        super().__init__(
            message=f"Failed to generate proof for circuit: {circuit}",
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="PROOF_GENERATION_FAILED",
            details={"circuit": circuit, "reason": reason},
        )


class ProofVerificationError(APIError):
    """ZK proof verification failed."""

    def __init__(self, circuit: str, reason: str = "Invalid proof"):
        super().__init__(
            message=f"Proof verification failed for circuit: {circuit}",
            status_code=HTTP_400_BAD_REQUEST,
            error_code="PROOF_VERIFICATION_FAILED",
            details={"circuit": circuit, "reason": reason},
        )


class VerificationKeyUnavailableError(APIError):
    """Verification key is not available."""

    def __init__(self, circuit: str):
        super().__init__(
            message=f"Verification key unavailable for circuit: {circuit}",
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            error_code="VKEY_UNAVAILABLE",
            details={"circuit": circuit},
        )


# ============================================
# External Service Errors
# ============================================


class DatabaseConnectionError(APIError):
    """Database connection failed."""

    def __init__(self, database: str = "neo4j"):
        super().__init__(
            message=f"Database connection failed: {database}",
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            error_code="DATABASE_UNAVAILABLE",
            details={"database": database},
        )


class BlockchainError(APIError):
    """Blockchain operation failed."""

    def __init__(self, operation: str, reason: str):
        super().__init__(
            message=f"Blockchain operation failed: {operation}",
            status_code=HTTP_502_BAD_GATEWAY,
            error_code="BLOCKCHAIN_ERROR",
            details={"operation": operation, "reason": reason},
        )


class ExternalServiceError(APIError):
    """External service call failed."""

    def __init__(self, service: str, reason: str):
        super().__init__(
            message=f"External service error: {service}",
            status_code=HTTP_502_BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, "reason": reason},
        )


# ============================================
# Error Handlers
# ============================================


async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
    """Handle custom API errors with structured responses."""
    logger.error(
        "api_error",
        extra={
            "error_code": exc.error_code,
            "message": exc.message,
            "correlation_id": exc.correlation_id,
            "path": request.url.path,
            "method": request.method,
            "client": request.client.host if request.client else None,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
        headers={"X-Correlation-ID": exc.correlation_id},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Convert HTTPException to structured format."""
    correlation_id = str(uuid.uuid4())[:8]
    logger.warning(
        "http_exception",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "correlation_id": correlation_id,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "correlation_id": correlation_id,
            }
        },
        headers={"X-Correlation-ID": correlation_id},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with generic error response."""
    correlation_id = str(uuid.uuid4())[:8]
    logger.exception(
        "unhandled_exception",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method,
        },
    )
    return JSONResponse(
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "correlation_id": correlation_id,
            }
        },
        headers={"X-Correlation-ID": correlation_id},
    )


def register_error_handlers(app):
    """Register all error handlers with the FastAPI application."""
    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
