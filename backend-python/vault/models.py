"""
Data models for Personal Proof Vault MVP.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class DocumentType(str, Enum):
    """Supported document types."""

    IDENTITY = "identity"
    LICENSE = "license"
    FINANCIAL = "financial"
    CREDENTIAL = "credential"
    OTHER = "other"


class EventType(str, Enum):
    """Timeline event types."""

    DOCUMENT_UPLOADED = "document_uploaded"
    ATTESTATION_CREATED = "attestation_created"
    PROOF_GENERATED = "proof_generated"
    SHARE_LINK_CREATED = "share_link_created"
    DECISION_LOGGED = "decision_logged"
    VERIFICATION_COMPLETED = "verification_completed"


class AccessLevel(str, Enum):
    """Share link access levels."""

    PROOF_ONLY = "proof_only"  # Only ZK proof, no document data
    METADATA = "metadata"  # Document metadata + proof
    FULL = "full"  # Full document access (requires auth)


@dataclass
class ProofDocument:
    """Represents an encrypted document in the vault."""

    id: str
    user_id: str
    document_type: DocumentType
    encrypted_data: bytes
    hash: str  # SHA-256 hash of original document
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None


@dataclass
class Attestation:
    """Represents a blockchain attestation for a document."""

    document_id: str
    fabric_tx_id: str
    merkle_root: str
    timestamp: datetime
    signature: str  # Dilithium signature
    public_key: str  # Public key used for signature
    verified: bool = False
    verified_at: Optional[datetime] = None


@dataclass
class ProofLink:
    """Represents a shareable proof link."""

    share_token: str
    document_id: str
    expires_at: Optional[datetime] = None
    access_level: AccessLevel = AccessLevel.PROOF_ONLY
    proof_type: Optional[str] = None  # e.g., "age_proof", "authenticity_proof"
    created_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    max_accesses: Optional[int] = None


@dataclass
class TimelineEvent:
    """Represents an event in the user's verification timeline."""

    user_id: str
    event_type: EventType
    document_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    attestation_id: Optional[str] = None
    proof_link_id: Optional[str] = None
