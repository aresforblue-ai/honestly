"""
Property tests for zk circuits using the Node snark-runner.

These tests require:
- node available on PATH
- built artifacts in backend-python/zkp/artifacts
- a vectors file providing payloads: env ZK_TEST_VECTORS or default backend-python/zkp/test_vectors.json
- enable with ZK_TESTS=1 (otherwise skipped)
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
ZKP_DIR = BASE_DIR / "zkp"
ARTIFACTS_DIR = ZKP_DIR / "artifacts"
RUNNER = ZKP_DIR / "snark-runner.js"


def _skip_if_not_enabled():
    if os.getenv("ZK_TESTS", "0") != "1":
        pytest.skip("ZK_TESTS not enabled", allow_module_level=True)
    if not shutil.which("node"):
        pytest.skip("node not available", allow_module_level=True)
    required = [
        ARTIFACTS_DIR / "age" / "verification_key.json",
        ARTIFACTS_DIR / "authenticity" / "verification_key.json",
        ARTIFACTS_DIR / "age_level3" / "verification_key.json",
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        pytest.skip(f"zk artifacts missing: {missing}", allow_module_level=True)
    if not RUNNER.exists():
        pytest.skip("snark-runner.js not found", allow_module_level=True)


_skip_if_not_enabled()


def load_vectors() -> dict:
    path = Path(os.getenv("ZK_TEST_VECTORS", ZKP_DIR / "test_vectors.json"))
    if not path.exists():
        pytest.skip(f"Vectors file missing: {path}", allow_module_level=True)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


VECTORS = load_vectors()


def run_runner(action: str, circuit: str, payload: dict) -> dict:
    """Invoke snark-runner.js and return parsed JSON."""
    cmd = ["node", str(RUNNER), action, circuit]
    proc = subprocess.run(
        cmd,
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip())
    try:
        return json.loads(proc.stdout)
    except Exception as exc:  # pragma: no cover - unexpected output
        raise RuntimeError(f"Invalid runner output: {proc.stdout}") from exc


def _skip_on_wasm_memory(exc: RuntimeError, circuit: str):
    msg = str(exc)
    if sys.platform.startswith("win") and "Could not allocate" in msg:
        pytest.skip(f"{circuit} proving skipped on Windows due to wasm memory limits")


def test_age_level3_nullifier_identity_binding():
    if sys.platform.startswith("win"):
        pytest.skip("age_level3 proving skipped on Windows due to wasm memory limits")
    vectors = VECTORS.get("age_level3_nullifier")
    if not vectors:
        pytest.skip("age_level3_nullifier vectors not provided")
    bundle_a = run_runner("prove", "age_level3", vectors["payload_a"])
    bundle_b = run_runner("prove", "age_level3", vectors["payload_b"])
    null_a = bundle_a.get("publicSignals", [])[-1]
    null_b = bundle_b.get("publicSignals", [])[-1]
    assert null_a != null_b, "Nullifier should bind to identity commitment"


def test_authenticity_merkle_valid_then_invalid():
    vectors = VECTORS.get("authenticity_merkle")
    if not vectors:
        pytest.skip("authenticity_merkle vectors not provided")
    valid_payload = vectors["valid_prove"]
    try:
        bundle = run_runner("prove", "authenticity", valid_payload)
    except RuntimeError as exc:
        _skip_on_wasm_memory(exc, "authenticity")
        raise
    verify_result = run_runner("verify", "authenticity", bundle)
    assert bool(verify_result.get("verified")), "Valid merkle proof should verify"

    invalid_payload = vectors.get("invalid_prove")
    if not invalid_payload:
        pytest.skip("invalid_prove vector not provided")
    with pytest.raises(RuntimeError):
        run_runner("prove", "authenticity", invalid_payload)


def test_field_overflow_rejected():
    vectors = VECTORS.get("field_overflow")
    if not vectors:
        pytest.skip("field_overflow vectors not provided")
    with pytest.raises(RuntimeError):
        run_runner("prove", vectors["circuit"], vectors["payload"])
