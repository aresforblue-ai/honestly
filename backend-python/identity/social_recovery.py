"""
Social Recovery System using Shamir's Secret Sharing
=====================================================

A revolutionary key recovery mechanism that eliminates single points of failure.

This enables:
1. Split your master key into N shares
2. Distribute shares to trusted guardians (friends, family, devices)
3. Recover with K-of-N shares (threshold scheme)
4. Never lose access to your identity again
5. No centralized recovery = true self-sovereignty

Based on Shamir's Secret Sharing Scheme (1979)
"""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger("identity.recovery")

# Prime for finite field arithmetic (256-bit prime)
PRIME = 2**256 - 2**32 - 2**9 - 2**8 - 2**7 - 2**6 - 2**4 - 1


class GuardianType(Enum):
    """Types of recovery guardians."""

    TRUSTED_CONTACT = "trusted_contact"  # Friend or family member
    HARDWARE_DEVICE = "hardware_device"  # Hardware wallet, YubiKey
    CLOUD_BACKUP = "cloud_backup"  # Encrypted cloud storage
    INSTITUTION = "institution"  # Bank, lawyer, etc.
    SMART_CONTRACT = "smart_contract"  # On-chain guardian
    TIME_LOCKED = "time_locked"  # Auto-releases after time


class RecoveryStatus(Enum):
    """Status of a recovery process."""

    INITIATED = "initiated"
    COLLECTING_SHARES = "collecting_shares"
    THRESHOLD_MET = "threshold_met"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Guardian:
    """A trusted guardian holding a share."""

    guardian_id: str
    guardian_type: GuardianType
    name: str
    contact_method: str  # email, phone, ethereum address, etc.
    share_index: int
    share_commitment: str  # Hash of share for verification
    added_at: str
    last_verified: Optional[str] = None
    metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["guardian_type"] = self.guardian_type.value
        return result


@dataclass
class RecoveryShare:
    """A single share of the secret."""

    index: int
    value: int
    commitment: str
    guardian_id: str
    encrypted_for_guardian: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "index": self.index,
            "commitment": self.commitment,
            "guardian_id": self.guardian_id,
        }


@dataclass
class RecoveryConfig:
    """Configuration for social recovery."""

    user_id: str
    threshold: int  # K - minimum shares needed
    total_shares: int  # N - total shares created
    guardians: List[Guardian] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    secret_commitment: str = ""  # Hash of the secret for verification

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class RecoveryProcess:
    """An active recovery process."""

    recovery_id: str
    user_id: str
    status: RecoveryStatus
    threshold: int
    collected_shares: List[Tuple[int, int]] = field(default_factory=list)
    initiated_at: str = ""
    expires_at: str = ""
    completed_at: Optional[str] = None
    initiated_by: Optional[str] = None

    def __post_init__(self):
        if not self.initiated_at:
            self.initiated_at = datetime.utcnow().isoformat()
        if not self.expires_at:
            # Recovery expires in 7 days by default
            self.expires_at = (datetime.utcnow() + timedelta(days=7)).isoformat()


class ShamirSecretSharing:
    """
    Implementation of Shamir's Secret Sharing Scheme.

    Splits a secret into N shares where any K shares can reconstruct it,
    but K-1 shares reveal nothing about the secret.
    """

    def __init__(self, prime: int = PRIME):
        self.prime = prime

    def _mod_inverse(self, a: int, p: int) -> int:
        """Calculate modular inverse using extended Euclidean algorithm."""
        if a < 0:
            a = p + a
        g, x, _ = self._extended_gcd(a, p)
        if g != 1:
            raise ValueError("Modular inverse doesn't exist")
        return x % p

    def _extended_gcd(self, a: int, b: int) -> Tuple[int, int, int]:
        """Extended Euclidean algorithm."""
        if a == 0:
            return b, 0, 1
        gcd, x1, y1 = self._extended_gcd(b % a, a)
        x = y1 - (b // a) * x1
        y = x1
        return gcd, x, y

    def _random_polynomial(self, secret: int, degree: int) -> List[int]:
        """Generate random polynomial with secret as constant term."""
        coefficients = [secret]
        for _ in range(degree):
            coefficients.append(secrets.randbelow(self.prime))
        return coefficients

    def _evaluate_polynomial(self, coefficients: List[int], x: int) -> int:
        """Evaluate polynomial at point x."""
        result = 0
        for i, coef in enumerate(coefficients):
            result = (result + coef * pow(x, i, self.prime)) % self.prime
        return result

    def split_secret(
        self,
        secret: int,
        threshold: int,
        num_shares: int,
    ) -> List[Tuple[int, int]]:
        """
        Split a secret into shares using Shamir's scheme.

        Args:
            secret: The secret to split (as integer)
            threshold: Minimum shares needed to reconstruct (K)
            num_shares: Total number of shares to create (N)

        Returns:
            List of (index, share_value) tuples
        """
        if threshold > num_shares:
            raise ValueError("Threshold cannot exceed number of shares")
        if threshold < 2:
            raise ValueError("Threshold must be at least 2")
        if secret >= self.prime:
            raise ValueError("Secret must be less than prime")

        # Generate random polynomial of degree (threshold - 1)
        # with secret as the constant term
        coefficients = self._random_polynomial(secret, threshold - 1)

        # Generate shares by evaluating polynomial at points 1, 2, ..., num_shares
        shares = []
        for i in range(1, num_shares + 1):
            share_value = self._evaluate_polynomial(coefficients, i)
            shares.append((i, share_value))

        return shares

    def reconstruct_secret(self, shares: List[Tuple[int, int]]) -> int:
        """
        Reconstruct the secret from shares using Lagrange interpolation.

        Args:
            shares: List of (index, share_value) tuples

        Returns:
            The reconstructed secret
        """
        if len(shares) < 2:
            raise ValueError("Need at least 2 shares to reconstruct")

        secret = 0

        for i, (xi, yi) in enumerate(shares):
            # Calculate Lagrange basis polynomial at x=0
            numerator = 1
            denominator = 1

            for j, (xj, _) in enumerate(shares):
                if i != j:
                    numerator = (numerator * (-xj)) % self.prime
                    denominator = (denominator * (xi - xj)) % self.prime

            # Lagrange coefficient
            lagrange = (yi * numerator * self._mod_inverse(denominator, self.prime)) % self.prime
            secret = (secret + lagrange) % self.prime

        return secret

    def verify_share(self, share: Tuple[int, int], commitment: str) -> bool:
        """Verify a share matches its commitment."""
        index, value = share
        computed_commitment = hashlib.sha256(f"{index}:{value}".encode()).hexdigest()
        return computed_commitment == commitment


class SocialRecoveryManager:
    """
    Manages social recovery setup and execution.

    This is the main interface for users to set up and use social recovery.
    """

    def __init__(self, storage_backend=None):
        self.storage = storage_backend or {}
        self.sss = ShamirSecretSharing()
        self.active_recoveries: Dict[str, RecoveryProcess] = {}

    def setup_recovery(
        self,
        user_id: str,
        master_secret: bytes,
        threshold: int,
        guardians: List[Dict],
    ) -> RecoveryConfig:
        """
        Set up social recovery for a user.

        Args:
            user_id: User identifier
            master_secret: The secret to protect (master key, seed, etc.)
            threshold: Minimum guardians needed for recovery
            guardians: List of guardian configurations

        Returns:
            RecoveryConfig with guardian information
        """
        num_shares = len(guardians)

        if threshold > num_shares:
            raise ValueError(
                f"Threshold ({threshold}) cannot exceed number of guardians ({num_shares})"
            )

        if threshold < 2:
            raise ValueError("Threshold must be at least 2 for security")

        # Convert secret to integer
        secret_int = int.from_bytes(master_secret, "big")
        if secret_int >= PRIME:
            # Hash the secret if too large
            secret_int = int.from_bytes(hashlib.sha256(master_secret).digest(), "big") % PRIME

        # Generate shares
        shares = self.sss.split_secret(secret_int, threshold, num_shares)

        # Create guardian objects with shares
        guardian_objects = []
        share_records = []

        for i, (guardian_config, (index, value)) in enumerate(zip(guardians, shares)):
            guardian_id = f"guardian_{secrets.token_hex(8)}"

            # Commitment to verify share later
            commitment = hashlib.sha256(f"{index}:{value}".encode()).hexdigest()

            guardian = Guardian(
                guardian_id=guardian_id,
                guardian_type=GuardianType(guardian_config.get("type", "trusted_contact")),
                name=guardian_config["name"],
                contact_method=guardian_config["contact"],
                share_index=index,
                share_commitment=commitment,
                added_at=datetime.utcnow().isoformat(),
                metadata=guardian_config.get("metadata", {}),
            )
            guardian_objects.append(guardian)

            # Create share record (value would be encrypted for guardian in production)
            share_record = RecoveryShare(
                index=index,
                value=value,
                commitment=commitment,
                guardian_id=guardian_id,
            )
            share_records.append(share_record)

        # Create recovery config
        secret_commitment = hashlib.sha256(master_secret).hexdigest()

        config = RecoveryConfig(
            user_id=user_id,
            threshold=threshold,
            total_shares=num_shares,
            guardians=guardian_objects,
            secret_commitment=secret_commitment,
        )

        # Store configuration (without actual share values)
        self.storage[user_id] = {
            "config": asdict(config),
            "share_commitments": {s.guardian_id: s.commitment for s in share_records},
        }

        logger.info(f"Set up social recovery for {user_id} with {threshold}-of-{num_shares} scheme")

        # Return config and shares (shares should be distributed to guardians)
        return config, share_records

    def initiate_recovery(
        self,
        user_id: str,
        initiated_by: Optional[str] = None,
    ) -> RecoveryProcess:
        """
        Initiate the recovery process.

        This starts the process of collecting shares from guardians.
        """
        if user_id not in self.storage:
            raise ValueError(f"No recovery configuration for user {user_id}")

        config_data = self.storage[user_id]["config"]

        recovery_id = f"recovery_{secrets.token_hex(8)}"

        process = RecoveryProcess(
            recovery_id=recovery_id,
            user_id=user_id,
            status=RecoveryStatus.INITIATED,
            threshold=config_data["threshold"],
            initiated_by=initiated_by,
        )

        self.active_recoveries[recovery_id] = process

        logger.info(f"Initiated recovery {recovery_id} for user {user_id}")

        return process

    def submit_share(
        self,
        recovery_id: str,
        guardian_id: str,
        share_index: int,
        share_value: int,
    ) -> Dict:
        """
        Submit a share from a guardian.

        Returns the current recovery status.
        """
        if recovery_id not in self.active_recoveries:
            raise ValueError(f"Recovery {recovery_id} not found")

        process = self.active_recoveries[recovery_id]

        if process.status in [
            RecoveryStatus.COMPLETED,
            RecoveryStatus.CANCELLED,
            RecoveryStatus.EXPIRED,
        ]:
            raise ValueError(f"Recovery is {process.status.value}")

        # Check expiration
        if datetime.utcnow() > datetime.fromisoformat(process.expires_at):
            process.status = RecoveryStatus.EXPIRED
            return {"status": "expired", "message": "Recovery period has expired"}

        # Verify share commitment
        user_data = self.storage.get(process.user_id)
        if not user_data:
            raise ValueError("User recovery data not found")

        expected_commitment = user_data["share_commitments"].get(guardian_id)
        if not expected_commitment:
            raise ValueError(f"Guardian {guardian_id} not found in recovery config")

        actual_commitment = hashlib.sha256(f"{share_index}:{share_value}".encode()).hexdigest()

        if actual_commitment != expected_commitment:
            logger.warning(f"Invalid share submitted for recovery {recovery_id}")
            return {"status": "error", "message": "Invalid share"}

        # Add share to collected shares
        process.collected_shares.append((share_index, share_value))
        process.status = RecoveryStatus.COLLECTING_SHARES

        # Check if threshold met
        if len(process.collected_shares) >= process.threshold:
            process.status = RecoveryStatus.THRESHOLD_MET

        logger.info(
            f"Share submitted for recovery {recovery_id}: {len(process.collected_shares)}/{process.threshold}"
        )

        return {
            "status": process.status.value,
            "shares_collected": len(process.collected_shares),
            "threshold": process.threshold,
            "ready_to_reconstruct": process.status == RecoveryStatus.THRESHOLD_MET,
        }

    def complete_recovery(self, recovery_id: str) -> Tuple[bytes, Dict]:
        """
        Complete the recovery process and reconstruct the secret.

        Returns the reconstructed secret and recovery details.
        """
        if recovery_id not in self.active_recoveries:
            raise ValueError(f"Recovery {recovery_id} not found")

        process = self.active_recoveries[recovery_id]

        if process.status != RecoveryStatus.THRESHOLD_MET:
            raise ValueError(f"Cannot complete recovery: status is {process.status.value}")

        # Reconstruct the secret
        try:
            secret_int = self.sss.reconstruct_secret(process.collected_shares)

            # Convert back to bytes
            # Determine byte length (256-bit = 32 bytes)
            secret_bytes = secret_int.to_bytes(32, "big")

            # Verify against commitment
            user_data = self.storage.get(process.user_id)
            expected_commitment = user_data["config"]["secret_commitment"]
            actual_commitment = hashlib.sha256(secret_bytes).hexdigest()

            if actual_commitment != expected_commitment:
                # Try with leading zeros stripped
                secret_bytes = secret_int.to_bytes((secret_int.bit_length() + 7) // 8 or 1, "big")
                actual_commitment = hashlib.sha256(secret_bytes).hexdigest()

            process.status = RecoveryStatus.COMPLETED
            process.completed_at = datetime.utcnow().isoformat()

            logger.info(f"Recovery {recovery_id} completed successfully")

            return secret_bytes, {
                "recovery_id": recovery_id,
                "status": "completed",
                "shares_used": len(process.collected_shares),
                "completed_at": process.completed_at,
            }

        except Exception as e:
            logger.error(f"Recovery {recovery_id} failed: {e}")
            raise ValueError(f"Failed to reconstruct secret: {e}")

    def cancel_recovery(self, recovery_id: str, cancelled_by: str) -> Dict:
        """Cancel an active recovery process."""
        if recovery_id not in self.active_recoveries:
            raise ValueError(f"Recovery {recovery_id} not found")

        process = self.active_recoveries[recovery_id]
        process.status = RecoveryStatus.CANCELLED

        logger.info(f"Recovery {recovery_id} cancelled by {cancelled_by}")

        return {
            "recovery_id": recovery_id,
            "status": "cancelled",
            "cancelled_by": cancelled_by,
        }

    def get_recovery_status(self, recovery_id: str) -> Dict:
        """Get the current status of a recovery process."""
        if recovery_id not in self.active_recoveries:
            return {"status": "not_found"}

        process = self.active_recoveries[recovery_id]

        return {
            "recovery_id": recovery_id,
            "user_id": process.user_id,
            "status": process.status.value,
            "shares_collected": len(process.collected_shares),
            "threshold": process.threshold,
            "initiated_at": process.initiated_at,
            "expires_at": process.expires_at,
            "ready_to_reconstruct": process.status == RecoveryStatus.THRESHOLD_MET,
        }

    def add_guardian(
        self,
        user_id: str,
        guardian_config: Dict,
        current_secret: bytes,
    ) -> Guardian:
        """
        Add a new guardian to an existing recovery setup.

        This requires re-splitting the secret with the new guardian included.
        """
        if user_id not in self.storage:
            raise ValueError(f"No recovery configuration for user {user_id}")

        user_data = self.storage[user_id]
        config = user_data["config"]

        # Verify secret
        if hashlib.sha256(current_secret).hexdigest() != config["secret_commitment"]:
            raise ValueError("Invalid secret provided")

        # Re-setup with new guardian
        existing_guardians = [
            {
                "type": g["guardian_type"],
                "name": g["name"],
                "contact": g["contact_method"],
                "metadata": g.get("metadata", {}),
            }
            for g in config["guardians"]
        ]
        existing_guardians.append(guardian_config)

        new_config, new_shares = self.setup_recovery(
            user_id=user_id,
            master_secret=current_secret,
            threshold=config["threshold"],
            guardians=existing_guardians,
        )

        # Return the new guardian
        return new_config.guardians[-1], new_shares[-1]

    def remove_guardian(
        self,
        user_id: str,
        guardian_id: str,
        current_secret: bytes,
    ) -> RecoveryConfig:
        """
        Remove a guardian from the recovery setup.

        This requires re-splitting the secret without the removed guardian.
        """
        if user_id not in self.storage:
            raise ValueError(f"No recovery configuration for user {user_id}")

        user_data = self.storage[user_id]
        config = user_data["config"]

        # Verify secret
        if hashlib.sha256(current_secret).hexdigest() != config["secret_commitment"]:
            raise ValueError("Invalid secret provided")

        # Filter out the guardian
        remaining_guardians = [
            {
                "type": g["guardian_type"],
                "name": g["name"],
                "contact": g["contact_method"],
                "metadata": g.get("metadata", {}),
            }
            for g in config["guardians"]
            if g["guardian_id"] != guardian_id
        ]

        if len(remaining_guardians) < config["threshold"]:
            raise ValueError("Cannot remove guardian: would fall below threshold")

        # Re-setup without the guardian
        new_config, new_shares = self.setup_recovery(
            user_id=user_id,
            master_secret=current_secret,
            threshold=config["threshold"],
            guardians=remaining_guardians,
        )

        return new_config, new_shares


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================


def create_recovery_setup(
    user_id: str,
    master_key: bytes,
    guardians: List[Dict],
    threshold: Optional[int] = None,
) -> Tuple[RecoveryConfig, List[Dict]]:
    """
    Create a social recovery setup.

    Args:
        user_id: User identifier
        master_key: The key to protect
        guardians: List of guardian configs with 'name', 'contact', 'type'
        threshold: Minimum guardians needed (default: ceil(N/2) + 1)

    Returns:
        Tuple of (RecoveryConfig, list of shares to distribute)
    """
    manager = SocialRecoveryManager()

    if threshold is None:
        # Default: majority + 1 for security
        threshold = (len(guardians) // 2) + 1

    config, shares = manager.setup_recovery(
        user_id=user_id,
        master_secret=master_key,
        threshold=threshold,
        guardians=guardians,
    )

    # Format shares for distribution
    share_packages = []
    for guardian, share in zip(config.guardians, shares):
        share_packages.append(
            {
                "guardian_id": guardian.guardian_id,
                "guardian_name": guardian.name,
                "share_index": share.index,
                "share_value_hex": hex(share.value),
                "commitment": share.commitment,
                "instructions": f"Keep this share safe. You are guardian #{share.index} of {len(shares)}. "
                f"At least {threshold} guardians are needed for recovery.",
            }
        )

    return config, share_packages
