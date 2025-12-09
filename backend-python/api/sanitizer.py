"""
Input sanitization and validation utilities.

Provides protection against common injection attacks and ensures
input data meets expected formats.
"""

import re
import html
import unicodedata
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, field_validator
import logging

logger = logging.getLogger("api.sanitizer")

# Regex patterns for validation
PATTERNS = {
    "uuid": re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I),
    "hex_hash": re.compile(r"^(0x)?[0-9a-f]{64}$", re.I),
    "document_id": re.compile(r"^doc_[a-zA-Z0-9]{12,32}$"),
    "share_token": re.compile(r"^shr_[a-zA-Z0-9]{16,48}$"),
    "safe_string": re.compile(r"^[a-zA-Z0-9\s\-_.,!?@#$%&()]+$"),
    "email": re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"),
    "url": re.compile(r"^https?://[a-zA-Z0-9.-]+(/[a-zA-Z0-9._~:/?#\[\]@!$&'()*+,;=-]*)?$"),
}

# Characters that could indicate injection attempts
DANGEROUS_PATTERNS = [
    r"<script",
    r"javascript:",
    r"on\w+\s*=",
    r"data:",
    r"vbscript:",
    r"\x00",
    r"\\x00",
    r"{{",
    r"}}",
    r"\$\{",
    r"`",
]

# Cypher injection patterns
CYPHER_INJECTION_PATTERNS = [
    r"(?i)MATCH\s*\(",
    r"(?i)CREATE\s*\(",
    r"(?i)DELETE\s+",
    r"(?i)DETACH\s+DELETE",
    r"(?i)SET\s+\w+",
    r"(?i)REMOVE\s+",
    r"(?i)MERGE\s*\(",
    r"(?i)CALL\s+\w+",
    r"(?i)LOAD\s+CSV",
    r"--",
    r"//.*$",
    r"/\*.*\*/",
]


def sanitize_string(value: str, max_length: int = 1000, allow_html: bool = False) -> str:
    """
    Sanitize a string input.

    Args:
        value: Input string to sanitize
        max_length: Maximum allowed length
        allow_html: Whether to allow HTML (default False - escapes HTML)

    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        value = str(value)

    # Normalize unicode
    value = unicodedata.normalize("NFKC", value)

    # Remove null bytes
    value = value.replace("\x00", "")

    # Truncate to max length
    value = value[:max_length]

    # Strip leading/trailing whitespace
    value = value.strip()

    # Escape HTML unless explicitly allowed
    if not allow_html:
        value = html.escape(value)

    return value


def sanitize_identifier(value: str, pattern: str = "safe_string") -> Optional[str]:
    """
    Sanitize and validate an identifier (ID, token, etc.).

    Args:
        value: Input identifier
        pattern: Regex pattern name from PATTERNS dict

    Returns:
        Validated identifier or None if invalid
    """
    if not value or not isinstance(value, str):
        return None

    value = value.strip()

    regex = PATTERNS.get(pattern)
    if regex and regex.match(value):
        return value

    return None


def check_injection(value: str) -> bool:
    """
    Check if a string contains potential injection patterns.

    Returns:
        True if potentially dangerous, False if safe
    """
    if not value:
        return False

    value_lower = value.lower()

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, value_lower, re.I):
            logger.warning(f"Potential injection detected: {pattern}")
            return True

    # Check for Cypher injection
    for pattern in CYPHER_INJECTION_PATTERNS:
        if re.search(pattern, value, re.I | re.M):
            logger.warning(f"Potential Cypher injection detected: {pattern}")
            return True

    return False


def sanitize_dict(data: Dict[str, Any], max_depth: int = 5) -> Dict[str, Any]:
    """
    Recursively sanitize a dictionary.

    Args:
        data: Input dictionary
        max_depth: Maximum recursion depth

    Returns:
        Sanitized dictionary
    """
    if max_depth <= 0:
        return {}

    result = {}
    for key, value in data.items():
        # Sanitize key
        clean_key = sanitize_string(str(key), max_length=100)
        if check_injection(clean_key):
            continue

        # Sanitize value based on type
        if isinstance(value, str):
            clean_value = sanitize_string(value)
            if not check_injection(value):
                result[clean_key] = clean_value
        elif isinstance(value, dict):
            result[clean_key] = sanitize_dict(value, max_depth - 1)
        elif isinstance(value, list):
            result[clean_key] = sanitize_list(value, max_depth - 1)
        elif isinstance(value, (int, float, bool)) or value is None:
            result[clean_key] = value
        else:
            # Convert other types to string and sanitize
            result[clean_key] = sanitize_string(str(value))

    return result


def sanitize_list(data: List[Any], max_depth: int = 5) -> List[Any]:
    """
    Recursively sanitize a list.
    """
    if max_depth <= 0:
        return []

    result = []
    for item in data[:1000]:  # Limit list length
        if isinstance(item, str):
            clean = sanitize_string(item)
            if not check_injection(item):
                result.append(clean)
        elif isinstance(item, dict):
            result.append(sanitize_dict(item, max_depth - 1))
        elif isinstance(item, list):
            result.append(sanitize_list(item, max_depth - 1))
        elif isinstance(item, (int, float, bool)) or item is None:
            result.append(item)

    return result


def validate_document_type(doc_type: str) -> Optional[str]:
    """Validate document type enum."""
    valid_types = {
        "passport",
        "drivers_license",
        "national_id",
        "birth_certificate",
        "other",
        "credential",
    }
    doc_type = doc_type.lower().strip()
    return doc_type if doc_type in valid_types else None


def validate_access_level(level: str) -> Optional[str]:
    """Validate access level enum."""
    valid_levels = {"PROOF_ONLY", "METADATA", "FULL"}
    level = level.upper().strip()
    return level if level in valid_levels else None


def validate_proof_type(proof_type: str) -> Optional[str]:
    """Validate proof circuit type."""
    valid_types = {"age", "authenticity", "age_level3", "level3_inequality"}
    proof_type = proof_type.lower().strip()
    return proof_type if proof_type in valid_types else None


class SanitizedInput(BaseModel):
    """Base model for sanitized inputs with automatic validation."""

    @field_validator("*", mode="before")
    @classmethod
    def sanitize_strings(cls, v):
        if isinstance(v, str):
            sanitized = sanitize_string(v)
            if check_injection(v):
                raise ValueError("Input contains potentially dangerous content")
            return sanitized
        return v


class DocumentUploadInput(SanitizedInput):
    """Validated input for document upload."""

    document_type: str
    metadata: Optional[Dict[str, Any]] = None

    @field_validator("document_type")
    @classmethod
    def validate_doc_type(cls, v):
        validated = validate_document_type(v)
        if not validated:
            raise ValueError("Invalid document type")
        return validated

    @field_validator("metadata")
    @classmethod
    def sanitize_metadata(cls, v):
        if v:
            return sanitize_dict(v)
        return v


class ShareLinkInput(SanitizedInput):
    """Validated input for share link creation."""

    document_id: str
    proof_type: str
    access_level: str
    max_accesses: Optional[int] = None
    expires_hours: Optional[int] = None

    @field_validator("document_id")
    @classmethod
    def validate_doc_id(cls, v):
        if not sanitize_identifier(v, "document_id"):
            raise ValueError("Invalid document ID format")
        return v

    @field_validator("proof_type")
    @classmethod
    def validate_circuit(cls, v):
        validated = validate_proof_type(v)
        if not validated:
            raise ValueError("Invalid proof type")
        return validated

    @field_validator("access_level")
    @classmethod
    def validate_access(cls, v):
        validated = validate_access_level(v)
        if not validated:
            raise ValueError("Invalid access level")
        return validated

    @field_validator("max_accesses")
    @classmethod
    def validate_max_accesses(cls, v):
        if v is not None and (v < 1 or v > 1000):
            raise ValueError("max_accesses must be between 1 and 1000")
        return v

    @field_validator("expires_hours")
    @classmethod
    def validate_expires(cls, v):
        if v is not None and (v < 1 or v > 8760):  # Max 1 year
            raise ValueError("expires_hours must be between 1 and 8760")
        return v


def sanitize_graphql_variables(variables: Optional[Dict]) -> Dict:
    """Sanitize GraphQL query variables."""
    if not variables:
        return {}
    return sanitize_dict(variables)
