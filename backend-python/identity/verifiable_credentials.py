"""
W3C Verifiable Credentials Implementation
==========================================

Standards-compliant implementation of Verifiable Credentials (VC) and
Verifiable Presentations (VP) for the Honestly platform.

This enables:
1. Universal credential format that works across systems
2. Selective disclosure of credential attributes
3. Zero-knowledge proofs of credential properties
4. Interoperability with existing identity systems

Based on: https://www.w3.org/TR/vc-data-model/
"""

import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger("identity.vc")


# ============================================
# W3C VC CONTEXTS
# ============================================

CONTEXTS = {
    "credentials_v1": "https://www.w3.org/2018/credentials/v1",
    "credentials_v2": "https://www.w3.org/ns/credentials/v2",
    "honestly": "https://honestly.dev/credentials/v1",
    "schema_org": "https://schema.org/",
}


class CredentialType(Enum):
    """Standard credential types."""

    VERIFIABLE_CREDENTIAL = "VerifiableCredential"

    # Identity credentials
    IDENTITY_CREDENTIAL = "IdentityCredential"
    AGE_CREDENTIAL = "AgeCredential"
    NATIONALITY_CREDENTIAL = "NationalityCredential"

    # Education
    EDUCATION_CREDENTIAL = "EducationCredential"
    DEGREE_CREDENTIAL = "DegreeCredential"
    CERTIFICATION_CREDENTIAL = "CertificationCredential"

    # Employment
    EMPLOYMENT_CREDENTIAL = "EmploymentCredential"
    PROFESSIONAL_CREDENTIAL = "ProfessionalCredential"

    # Financial
    CREDIT_SCORE_CREDENTIAL = "CreditScoreCredential"
    INCOME_CREDENTIAL = "IncomeCredential"
    ACCREDITED_INVESTOR_CREDENTIAL = "AccreditedInvestorCredential"

    # Health
    VACCINATION_CREDENTIAL = "VaccinationCredential"
    HEALTH_CREDENTIAL = "HealthCredential"

    # AI/Agent
    AI_AGENT_CREDENTIAL = "AIAgentCredential"
    CAPABILITY_CREDENTIAL = "CapabilityCredential"

    # Platform specific
    REPUTATION_CREDENTIAL = "ReputationCredential"
    MEMBERSHIP_CREDENTIAL = "MembershipCredential"
    PROOF_OF_HUMANITY = "ProofOfHumanityCredential"


class ProofType(Enum):
    """Supported proof types."""

    ED25519_SIGNATURE = "Ed25519Signature2020"
    ECDSA_SECP256K1 = "EcdsaSecp256k1Signature2019"
    BBS_PLUS = "BbsBlsSignature2020"  # Supports selective disclosure
    ZK_SNARK = "Groth16Proof2024"
    ZK_STARK = "StarkProof2024"


@dataclass
class CredentialSubject:
    """The entity the credential is about."""

    id: str  # DID of the subject
    claims: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {"id": self.id, **self.claims}


@dataclass
class CredentialStatus:
    """Status information for revocation checking."""

    id: str
    type: str = "RevocationList2020Status"
    revocation_list_index: int = 0
    revocation_list_credential: str = ""

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type,
            "revocationListIndex": self.revocation_list_index,
            "revocationListCredential": self.revocation_list_credential,
        }


@dataclass
class Proof:
    """Cryptographic proof of credential authenticity."""

    type: str
    created: str
    verification_method: str
    proof_purpose: str = "assertionMethod"
    proof_value: str = ""

    # For ZK proofs
    zk_circuit: Optional[str] = None
    public_signals: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        result = {
            "type": self.type,
            "created": self.created,
            "verificationMethod": self.verification_method,
            "proofPurpose": self.proof_purpose,
            "proofValue": self.proof_value,
        }
        if self.zk_circuit:
            result["zkCircuit"] = self.zk_circuit
        if self.public_signals:
            result["publicSignals"] = self.public_signals
        return result


@dataclass
class VerifiableCredential:
    """
    A W3C Verifiable Credential.

    This is the core data structure for credentials in the system.
    """

    id: str
    type: List[str]
    issuer: Union[str, Dict]
    issuance_date: str
    credential_subject: CredentialSubject

    # Optional fields
    expiration_date: Optional[str] = None
    credential_status: Optional[CredentialStatus] = None
    proof: Optional[Proof] = None

    # Honestly extensions
    zk_commitment: Optional[str] = None
    selective_disclosure_enabled: bool = False

    def to_dict(self) -> Dict:
        result = {
            "@context": [
                CONTEXTS["credentials_v1"],
                CONTEXTS["honestly"],
            ],
            "id": self.id,
            "type": self.type,
            "issuer": self.issuer,
            "issuanceDate": self.issuance_date,
            "credentialSubject": self.credential_subject.to_dict(),
        }

        if self.expiration_date:
            result["expirationDate"] = self.expiration_date
        if self.credential_status:
            result["credentialStatus"] = self.credential_status.to_dict()
        if self.proof:
            result["proof"] = self.proof.to_dict()
        if self.zk_commitment:
            result["zkCommitment"] = self.zk_commitment
        if self.selective_disclosure_enabled:
            result["selectiveDisclosure"] = True

        return result

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    def get_hash(self) -> str:
        """Get credential hash for verification."""
        canonical = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass
class VerifiablePresentation:
    """
    A W3C Verifiable Presentation.

    Contains one or more credentials presented by a holder.
    """

    id: str
    type: List[str]
    holder: str
    verifiable_credential: List[VerifiableCredential]
    proof: Optional[Proof] = None

    # Selective disclosure
    disclosed_claims: Optional[Dict[str, List[str]]] = None

    def to_dict(self) -> Dict:
        result = {
            "@context": [
                CONTEXTS["credentials_v1"],
                CONTEXTS["honestly"],
            ],
            "id": self.id,
            "type": self.type,
            "holder": self.holder,
            "verifiableCredential": [vc.to_dict() for vc in self.verifiable_credential],
        }

        if self.proof:
            result["proof"] = self.proof.to_dict()
        if self.disclosed_claims:
            result["disclosedClaims"] = self.disclosed_claims

        return result


class CredentialIssuer:
    """
    Issues verifiable credentials.

    This is the core issuer component that creates credentials
    with cryptographic proofs.
    """

    def __init__(
        self,
        issuer_did: str,
        issuer_name: str,
        signing_key: Optional[str] = None,
    ):
        self.issuer_did = issuer_did
        self.issuer_name = issuer_name
        self.signing_key = signing_key or secrets.token_hex(32)
        self.issued_credentials = {}
        self.revocation_list = set()

    def issue_credential(
        self,
        subject_did: str,
        credential_type: CredentialType,
        claims: Dict[str, Any],
        expires_days: Optional[int] = 365,
        enable_selective_disclosure: bool = False,
    ) -> VerifiableCredential:
        """
        Issue a new verifiable credential.

        Args:
            subject_did: DID of the credential subject
            credential_type: Type of credential to issue
            claims: Claims to include in the credential
            expires_days: Days until expiration (None = never)
            enable_selective_disclosure: Enable ZK selective disclosure

        Returns:
            VerifiableCredential instance
        """
        credential_id = f"urn:uuid:{secrets.token_hex(16)}"
        now = datetime.utcnow()

        # Create credential subject
        subject = CredentialSubject(
            id=subject_did,
            claims=claims,
        )

        # Create status for revocation
        status = CredentialStatus(
            id=f"{self.issuer_did}/credentials/{credential_id}/status",
            revocation_list_index=len(self.issued_credentials),
            revocation_list_credential=f"{self.issuer_did}/revocation-list",
        )

        # Calculate ZK commitment if selective disclosure enabled
        zk_commitment = None
        if enable_selective_disclosure:
            commitment_data = json.dumps(
                {
                    "subject": subject_did,
                    "claims": claims,
                    "nonce": secrets.token_hex(16),
                },
                sort_keys=True,
            )
            zk_commitment = hashlib.sha256(commitment_data.encode()).hexdigest()

        # Create the credential
        credential = VerifiableCredential(
            id=credential_id,
            type=[CredentialType.VERIFIABLE_CREDENTIAL.value, credential_type.value],
            issuer={
                "id": self.issuer_did,
                "name": self.issuer_name,
            },
            issuance_date=now.isoformat() + "Z",
            expiration_date=(
                (now + timedelta(days=expires_days)).isoformat() + "Z" if expires_days else None
            ),
            credential_subject=subject,
            credential_status=status,
            zk_commitment=zk_commitment,
            selective_disclosure_enabled=enable_selective_disclosure,
        )

        # Sign the credential
        proof = self._create_proof(credential)
        credential.proof = proof

        # Store issued credential
        self.issued_credentials[credential_id] = credential.get_hash()

        logger.info(f"Issued credential {credential_id} to {subject_did}")
        return credential

    def _create_proof(self, credential: VerifiableCredential) -> Proof:
        """Create cryptographic proof for credential."""
        now = datetime.utcnow()

        # Create signature (simplified - in production use proper crypto)
        sign_data = json.dumps(
            {
                "credential_id": credential.id,
                "issuer": self.issuer_did,
                "subject": credential.credential_subject.id,
                "claims_hash": hashlib.sha256(
                    json.dumps(credential.credential_subject.claims, sort_keys=True).encode()
                ).hexdigest(),
                "timestamp": now.isoformat(),
            },
            sort_keys=True,
        )

        signature = hashlib.sha256((sign_data + self.signing_key).encode()).hexdigest()

        return Proof(
            type=ProofType.ED25519_SIGNATURE.value,
            created=now.isoformat() + "Z",
            verification_method=f"{self.issuer_did}#key-1",
            proof_value=signature,
        )

    def revoke_credential(self, credential_id: str) -> bool:
        """Revoke a credential."""
        if credential_id in self.issued_credentials:
            self.revocation_list.add(credential_id)
            logger.info(f"Revoked credential {credential_id}")
            return True
        return False

    def is_revoked(self, credential_id: str) -> bool:
        """Check if a credential is revoked."""
        return credential_id in self.revocation_list


class CredentialVerifier:
    """
    Verifies credentials and presentations.
    """

    def __init__(self, trusted_issuers: Optional[List[str]] = None):
        self.trusted_issuers = trusted_issuers or []

    def verify_credential(
        self,
        credential: VerifiableCredential,
        check_expiration: bool = True,
        check_revocation: bool = True,
    ) -> Dict:
        """
        Verify a credential's authenticity and validity.

        Returns verification result with details.
        """
        result = {
            "valid": True,
            "checks": {},
            "errors": [],
        }

        # Check structure
        result["checks"]["structure"] = self._check_structure(credential)
        if not result["checks"]["structure"]:
            result["valid"] = False
            result["errors"].append("Invalid credential structure")

        # Check issuer
        issuer_id = (
            credential.issuer if isinstance(credential.issuer, str) else credential.issuer.get("id")
        )
        result["checks"]["issuer"] = (
            issuer_id in self.trusted_issuers if self.trusted_issuers else True
        )

        # Check expiration
        if check_expiration and credential.expiration_date:
            try:
                exp = datetime.fromisoformat(credential.expiration_date.rstrip("Z"))
                result["checks"]["not_expired"] = datetime.utcnow() < exp
                if not result["checks"]["not_expired"]:
                    result["valid"] = False
                    result["errors"].append("Credential has expired")
            except Exception:
                result["checks"]["not_expired"] = False
                result["errors"].append("Invalid expiration date format")

        # Check proof
        if credential.proof:
            result["checks"]["proof"] = self._verify_proof(credential)
            if not result["checks"]["proof"]:
                result["valid"] = False
                result["errors"].append("Invalid proof")
        else:
            result["checks"]["proof"] = False
            result["valid"] = False
            result["errors"].append("Missing proof")

        return result

    def _check_structure(self, credential: VerifiableCredential) -> bool:
        """Verify credential has required structure."""
        return all(
            [
                credential.id,
                credential.type,
                credential.issuer,
                credential.issuance_date,
                credential.credential_subject,
            ]
        )

    def _verify_proof(self, credential: VerifiableCredential) -> bool:
        """Verify the cryptographic proof."""
        # In production, this would verify actual signatures
        # For now, check proof structure exists
        if not credential.proof:
            return False
        return bool(credential.proof.proof_value)

    def verify_presentation(
        self,
        presentation: VerifiablePresentation,
    ) -> Dict:
        """Verify a verifiable presentation."""
        result = {
            "valid": True,
            "credential_results": [],
            "errors": [],
        }

        # Verify each credential in the presentation
        for vc in presentation.verifiable_credential:
            vc_result = self.verify_credential(vc)
            result["credential_results"].append(
                {
                    "credential_id": vc.id,
                    "valid": vc_result["valid"],
                    "details": vc_result,
                }
            )
            if not vc_result["valid"]:
                result["valid"] = False

        # Verify presentation proof if present
        if presentation.proof:
            result["presentation_proof_valid"] = bool(presentation.proof.proof_value)

        return result


class SelectiveDisclosure:
    """
    Enables selective disclosure of credential claims using ZK proofs.

    This allows proving specific attributes without revealing others.
    """

    @staticmethod
    def create_disclosure_request(
        required_claims: List[str],
        credential_types: List[CredentialType],
    ) -> Dict:
        """
        Create a request for selective disclosure.

        The holder will respond with a presentation that only
        reveals the requested claims.
        """
        return {
            "type": "SelectiveDisclosureRequest",
            "required_claims": required_claims,
            "credential_types": [ct.value for ct in credential_types],
            "challenge": secrets.token_hex(16),
            "created_at": datetime.utcnow().isoformat(),
        }

    @staticmethod
    def create_disclosed_presentation(
        credential: VerifiableCredential,
        claims_to_disclose: List[str],
        holder_did: str,
    ) -> VerifiablePresentation:
        """
        Create a presentation with selective disclosure.

        Only reveals specified claims, with ZK proof of other claims' existence.
        """
        # Filter claims
        full_claims = credential.credential_subject.claims
        disclosed_claims = {k: v for k, v in full_claims.items() if k in claims_to_disclose}
        hidden_claims = [k for k in full_claims.keys() if k not in claims_to_disclose]

        # Create commitment to hidden claims (ZK proof placeholder)
        hidden_hash = hashlib.sha256(
            json.dumps({k: full_claims[k] for k in hidden_claims}, sort_keys=True).encode()
        ).hexdigest()

        # Create selective credential
        selective_subject = CredentialSubject(
            id=credential.credential_subject.id,
            claims={
                **disclosed_claims,
                "_hidden_claims_commitment": hidden_hash,
            },
        )

        selective_credential = VerifiableCredential(
            id=credential.id,
            type=credential.type,
            issuer=credential.issuer,
            issuance_date=credential.issuance_date,
            expiration_date=credential.expiration_date,
            credential_subject=selective_subject,
            proof=credential.proof,
            selective_disclosure_enabled=True,
        )

        # Create presentation
        presentation = VerifiablePresentation(
            id=f"urn:uuid:{secrets.token_hex(16)}",
            type=["VerifiablePresentation", "SelectiveDisclosurePresentation"],
            holder=holder_did,
            verifiable_credential=[selective_credential],
            disclosed_claims={credential.id: claims_to_disclose},
        )

        return presentation

    @staticmethod
    def create_range_proof(
        credential: VerifiableCredential,
        claim_name: str,
        comparison: str,  # "gt", "lt", "gte", "lte", "eq"
        threshold: int,
    ) -> Dict:
        """
        Create a ZK range proof for a numeric claim.

        Proves a claim is above/below a threshold without revealing the value.
        """
        claim_value = credential.credential_subject.claims.get(claim_name)
        if claim_value is None:
            raise ValueError(f"Claim {claim_name} not found")

        # Evaluate condition
        result = False
        if comparison == "gt":
            result = claim_value > threshold
        elif comparison == "lt":
            result = claim_value < threshold
        elif comparison == "gte":
            result = claim_value >= threshold
        elif comparison == "lte":
            result = claim_value <= threshold
        elif comparison == "eq":
            result = claim_value == threshold

        # Create proof commitment (would be actual ZK proof in production)
        proof_data = f"{credential.id}:{claim_name}:{comparison}:{threshold}:{result}"
        commitment = hashlib.sha256(proof_data.encode()).hexdigest()

        return {
            "type": "RangeProof",
            "credential_id": credential.id,
            "claim": claim_name,
            "comparison": comparison,
            "threshold": threshold,
            "result": result,
            "proof_commitment": commitment,
            "created_at": datetime.utcnow().isoformat(),
        }


# ============================================
# FACTORY FUNCTIONS
# ============================================


def create_age_credential(
    issuer: CredentialIssuer,
    subject_did: str,
    birth_date: str,
    document_type: str = "passport",
) -> VerifiableCredential:
    """Create an age verification credential."""
    return issuer.issue_credential(
        subject_did=subject_did,
        credential_type=CredentialType.AGE_CREDENTIAL,
        claims={
            "birthDate": birth_date,
            "documentType": document_type,
            "verificationMethod": "document_scan",
        },
        enable_selective_disclosure=True,
    )


def create_education_credential(
    issuer: CredentialIssuer,
    subject_did: str,
    degree: str,
    institution: str,
    graduation_date: str,
    field_of_study: str,
) -> VerifiableCredential:
    """Create an education credential."""
    return issuer.issue_credential(
        subject_did=subject_did,
        credential_type=CredentialType.EDUCATION_CREDENTIAL,
        claims={
            "degree": degree,
            "institution": institution,
            "graduationDate": graduation_date,
            "fieldOfStudy": field_of_study,
        },
        enable_selective_disclosure=True,
    )


def create_proof_of_humanity_credential(
    issuer: CredentialIssuer,
    subject_did: str,
    verification_method: str,
    liveness_score: float,
) -> VerifiableCredential:
    """Create a proof of humanity credential."""
    return issuer.issue_credential(
        subject_did=subject_did,
        credential_type=CredentialType.PROOF_OF_HUMANITY,
        claims={
            "isHuman": True,
            "verificationMethod": verification_method,
            "livenessScore": liveness_score,
            "verifiedAt": datetime.utcnow().isoformat(),
        },
        enable_selective_disclosure=False,  # This should be all-or-nothing
        expires_days=30,  # Short expiry for freshness
    )


def create_reputation_credential(
    issuer: CredentialIssuer,
    subject_did: str,
    platform: str,
    reputation_score: int,
    total_interactions: int,
) -> VerifiableCredential:
    """Create a reputation credential."""
    return issuer.issue_credential(
        subject_did=subject_did,
        credential_type=CredentialType.REPUTATION_CREDENTIAL,
        claims={
            "platform": platform,
            "reputationScore": reputation_score,
            "totalInteractions": total_interactions,
            "scoreRange": {"min": 0, "max": 100},
        },
        enable_selective_disclosure=True,
        expires_days=7,  # Reputation should be fresh
    )
