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
HMAC_SECRET = os.getenv('BUNDLE_HMAC_SECRET')

# Verification key hashes cache
_VKEY_HASHES: Dict[str, str] = {}


def get_artifacts_dir() -> Path:
    """Get the path to ZK artifacts directory."""
    return Path(__file__).resolve().parent.parent / "zkp" / "artifacts"


def load_vkey_hashes() -> None:
    """Compute SHA-256 hashes of verification keys and ensure presence."""
    artifacts_dir = get_artifacts_dir()
    required = {
        "age": artifacts_dir / "age" / "verification_key.json",
        "authenticity": artifacts_dir / "authenticity" / "verification_key.json",
    }
    missing = [str(p) for p in required.values() if not p.exists()]
    if missing:
        raise RuntimeError(f"Missing verification keys: {missing}. Run zkp build to generate real vkeys.")
    for circuit, path in required.items():
        data = path.read_bytes()
        _VKEY_HASHES[circuit] = hashlib.sha256(data).hexdigest()


def get_vkey_hash(circuit: str) -> str:
    """Get the SHA-256 hash of a verification key."""
    return _VKEY_HASHES.get(circuit, "")


def hmac_sign(payload: dict) -> str:
    """Sign a payload with HMAC-SHA256."""
    if not HMAC_SECRET:
        return ""
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    digest = hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode()


def vkeys_ready() -> bool:
    """Check if all verification keys are loaded."""
    return all(_VKEY_HASHES.get(c) for c in ("age", "authenticity"))

