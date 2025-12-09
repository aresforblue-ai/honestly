"""
Key loading utilities for Vault encryption.

Attempts to load the master key from (in order):
1) VAULT_ENCRYPTION_KEY (base64-encoded string)
2) VAULT_KEY_FILE (path to base64-encoded key)
3) KMS_ENDPOINT (placeholder for future KMS integration)

Falls back to generated keys only when ALLOW_GENERATED_VAULT_KEY=true
to avoid accidental production boot without a managed secret.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency
    requests = None

logger = logging.getLogger("security")


def _decode_key(value: str, source: str) -> bytes:
    """Decode a base64 key and validate its length."""
    try:
        key = base64.b64decode(value)
    except Exception as exc:
        raise RuntimeError(f"Invalid base64 key from {source}") from exc
    if len(key) != 32:
        raise RuntimeError(f"Key from {source} must be 32 bytes (256 bits)")
    return key


def load_master_key(explicit_key: Optional[str] = None) -> bytes:
    """
    Load the master encryption key with a strict priority order.

    Args:
        explicit_key: Optional base64 key string provided directly.
    Returns:
        32-byte key for AES-256-GCM.
    Raises:
        RuntimeError if no valid key source is available.
    """
    if explicit_key:
        return _decode_key(explicit_key, "explicit parameter")

    env_key = os.getenv("VAULT_ENCRYPTION_KEY")
    if env_key:
        logger.info("Loaded VAULT_ENCRYPTION_KEY from environment.")
        return _decode_key(env_key, "VAULT_ENCRYPTION_KEY")

    kms_endpoint = os.getenv("KMS_ENDPOINT")
    kms_token = os.getenv("KMS_TOKEN")
    if kms_endpoint:
        if not requests:
            raise RuntimeError("KMS_ENDPOINT configured but 'requests' not installed.")
        try:
            headers = {"Authorization": f"Bearer {kms_token}"} if kms_token else {}
            resp = requests.get(kms_endpoint, headers=headers, timeout=5)
            resp.raise_for_status()
            value = resp.text.strip()
            logger.info("Loaded VAULT_ENCRYPTION_KEY from KMS_ENDPOINT.")
            return _decode_key(value, "KMS_ENDPOINT")
        except Exception as exc:
            raise RuntimeError(f"Failed to load key from KMS_ENDPOINT: {exc}") from exc

    key_file = os.getenv("VAULT_KEY_FILE")
    if key_file:
        path = Path(key_file)
        if not path.exists():
            raise RuntimeError(f"VAULT_KEY_FILE path not found: {path}")
        value = path.read_text().strip()
        logger.info("Loaded VAULT_ENCRYPTION_KEY from VAULT_KEY_FILE.")
        return _decode_key(value, "VAULT_KEY_FILE")

    allow_gen = os.getenv("ALLOW_GENERATED_VAULT_KEY", "false").lower() == "true"
    if allow_gen:
        key = AESGCM.generate_key(bit_length=256)
        logger.warning(
            "Generated new encryption key (dev). "
            "Set VAULT_ENCRYPTION_KEY or VAULT_KEY_FILE in production."
        )
        return key

    raise RuntimeError(
        "VAULT_ENCRYPTION_KEY not configured and key generation is disabled. "
        "Set VAULT_ENCRYPTION_KEY (base64) or VAULT_KEY_FILE; "
        "for local dev set ALLOW_GENERATED_VAULT_KEY=true."
    )
