"""
Production configuration and environment variable management.
"""

import os
from typing import List


class ProductionConfig:
    """Production configuration with validation."""

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    DEBUG = ENVIRONMENT == "development"

    # Security
    JWT_SECRET = os.getenv("JWT_SECRET", os.urandom(32).hex())
    JWT_ALGORITHM = "HS256"
    JWT_ACCESS_EXPIRY = int(os.getenv("JWT_ACCESS_EXPIRY", 3600))
    JWT_REFRESH_EXPIRY = int(os.getenv("JWT_REFRESH_EXPIRY", 604800))
    AI_AGENT_SECRET = os.getenv("AI_AGENT_SECRET", os.urandom(32).hex())
    AI_AGENT_RATE_LIMIT = int(os.getenv("AI_AGENT_RATE_LIMIT", 100))

    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REDIS_URL = os.getenv("RATE_LIMIT_REDIS_URL", None)

    # Database
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASS = os.getenv("NEO4J_PASS", "test")

    # CORS
    ENABLE_CORS = os.getenv("ENABLE_CORS", "true").lower() != "false"
    ALLOWED_ORIGINS: List[str] = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]

    # Performance
    SLOW_REQUEST_THRESHOLD = float(os.getenv("SLOW_REQUEST_THRESHOLD", "0.2"))
    CACHE_TTL = int(os.getenv("CACHE_TTL", 300))

    # Feature Flags
    DISABLE_KAFKA = os.getenv("DISABLE_KAFKA", "false").lower() == "true"
    DISABLE_FAISS = os.getenv("DISABLE_FAISS", "false").lower() == "true"
    DISABLE_FABRIC = os.getenv("DISABLE_FABRIC", "false").lower() == "true"

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls):
        """Validate configuration."""
        if cls.ENVIRONMENT == "production":
            # Check if JWT_SECRET is set via environment variable
            if not os.getenv("JWT_SECRET"):
                raise ValueError("JWT_SECRET must be set in production")
            # Check if AI_AGENT_SECRET is set via environment variable
            if not os.getenv("AI_AGENT_SECRET"):
                raise ValueError("AI_AGENT_SECRET must be set in production")
            if cls.NEO4J_PASS == "test":
                raise ValueError("NEO4J_PASS must be changed in production")
