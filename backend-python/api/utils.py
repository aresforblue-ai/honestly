"""
Shared utility functions for the API.
Extracted to avoid circular imports between app.py and vault_routes.py.
"""

import os
import json
import hashlib
import hmac
import base64
from pathlib import Path
from typing import Dict

# Configuration
HMAC_SECRET = os.getenv("BUNDLE_HMAC_SECRET")

# Verification key hashes cache
_VERIFICATION_KEY_HASHES: Dict[str, str] = {}


def get_artifacts_dir() -> Path:
    """Get the path to ZK artifacts directory."""
    return Path(__file__).resolve().parent.parent / "zkp" / "artifacts"


def load_verification_key_hashes() -> None:
    """Compute SHA-256 hashes of verification keys and ensure presence."""
    artifacts_dir = get_artifacts_dir()
    required_verification_keys = {
        "age": artifacts_dir / "age" / "verification_key.json",
        "authenticity": artifacts_dir / "authenticity" / "verification_key.json",
    }
    missing_keys = [
        str(key_path) for key_path in required_verification_keys.values() if not key_path.exists()
    ]
    if missing_keys:
        raise RuntimeError(
            f"Missing verification keys: {missing_keys}. Run zkp build to generate real vkeys."
        )
    for circuit, key_path in required_verification_keys.items():
        key_data = key_path.read_bytes()
        _VERIFICATION_KEY_HASHES[circuit] = hashlib.sha256(key_data).hexdigest()


def get_verification_key_hash(circuit: str) -> str:
    """Get the SHA-256 hash of a verification key."""
    return _VERIFICATION_KEY_HASHES.get(circuit, "")


def hmac_sign(payload: dict) -> str:
    """Sign a payload with HMAC-SHA256."""
    if not HMAC_SECRET:
        return ""
    payload_body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    hmac_digest = hmac.new(HMAC_SECRET.encode(), payload_body, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(hmac_digest).decode()


def verification_keys_ready() -> bool:
    """Check if all verification keys are loaded."""
    return all(_VERIFICATION_KEY_HASHES.get(circuit) for circuit in ("age", "authenticity"))
