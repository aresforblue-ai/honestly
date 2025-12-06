#!/usr/bin/env python3
"""
Verify integrity of verification keys.
Generates SHA-256 hashes for verification key files.
"""
import json
import hashlib
from pathlib import Path

def compute_vkey_hash(vkey_path: Path) -> str:
    """Compute SHA-256 hash of verification key."""
    with open(vkey_path, "r") as f:
        vkey_data = json.load(f)
    
    # Sort keys for consistent hashing
    vkey_str = json.dumps(vkey_data, sort_keys=True)
    return hashlib.sha256(vkey_str.encode()).hexdigest()

def verify_integrity(circuit: str, artifacts_dir: Path) -> bool:
    """Verify verification key integrity."""
    vkey_path = artifacts_dir / circuit / "verification_key.json"
    hash_path = artifacts_dir / circuit / "verification_key.sha256"
    
    if not vkey_path.exists():
        print(f"❌ Verification key not found: {vkey_path}")
        return False
    
    computed_hash = compute_vkey_hash(vkey_path)
    
    if hash_path.exists():
        with open(hash_path, "r") as f:
            expected_hash = f.read().strip()
        
        if computed_hash != expected_hash:
            print(f"❌ Integrity check FAILED for {circuit}")
            print(f"   Expected: {expected_hash}")
            print(f"   Computed: {computed_hash}")
            return False
        else:
            print(f"✅ Integrity check PASSED for {circuit}")
            return True
    else:
        print(f"⚠️  No hash file found for {circuit}, generating...")
        with open(hash_path, "w") as f:
            f.write(computed_hash)
        print(f"✅ Generated hash: {computed_hash}")
        return True

def generate_hashes(artifacts_dir: Path):
    """Generate integrity hashes for all verification keys."""
    circuits = ["age", "authenticity"]
    
    for circuit in circuits:
        vkey_path = artifacts_dir / circuit / "verification_key.json"
        hash_path = artifacts_dir / circuit / "verification_key.sha256"
        
        if vkey_path.exists():
            hash_value = compute_vkey_hash(vkey_path)
            with open(hash_path, "w") as f:
                f.write(hash_value)
            print(f"✅ Generated hash for {circuit}: {hash_value[:16]}...")
        else:
            print(f"⚠️  Verification key not found for {circuit}")

if __name__ == "__main__":
    import sys
    
    artifacts_dir = Path(__file__).parent.parent / "artifacts"
    
    if len(sys.argv) > 1 and sys.argv[1] == "generate":
        generate_hashes(artifacts_dir)
    else:
        circuits = ["age", "authenticity"]
        all_passed = True
        for circuit in circuits:
            if not verify_integrity(circuit, artifacts_dir):
                all_passed = False
        
        sys.exit(0 if all_passed else 1)

