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

def generate_hashes(artifacts_dir: Path, circuits):
    """Generate integrity hashes for all verification keys."""
    integrity = {}
    for circuit in circuits:
        vkey_path = artifacts_dir / circuit / "verification_key.json"
        hash_path = artifacts_dir / circuit / "verification_key.sha256"
        if vkey_path.exists():
            hash_value = compute_vkey_hash(vkey_path)
            integrity[circuit] = hash_value
            with open(hash_path, "w") as f:
                f.write(hash_value)
            print(f"✅ Generated hash for {circuit}: {hash_value[:16]}...")
        else:
            print(f"⚠️  Verification key not found for {circuit}")
    if integrity:
        with open(artifacts_dir / "INTEGRITY.json", "w") as f:
            json.dump(integrity, f, indent=2)
        print("✅ Wrote INTEGRITY.json")

if __name__ == "__main__":
    import sys
    
    artifacts_dir = Path(__file__).parent.parent / "artifacts"
    
    # Core circuits (always required)
    CORE_CIRCUITS = ["age", "authenticity", "age_level3", "level3_inequality"]
    
    # AAIP circuits (optional, for AI agent identity)
    AAIP_CIRCUITS = ["agent_capability", "agent_reputation"]
    
    # All circuits
    ALL_CIRCUITS = CORE_CIRCUITS + AAIP_CIRCUITS

    if len(sys.argv) > 1:
        if sys.argv[1] == "generate":
            # Generate hashes for all existing vkeys
            generate_hashes(artifacts_dir, ALL_CIRCUITS)
        elif sys.argv[1] == "--check":
            # Strict check against INTEGRITY.json (for CI)
            integrity_path = artifacts_dir / "INTEGRITY.json"
            if not integrity_path.exists():
                print("❌ INTEGRITY.json not found")
                sys.exit(1)
            with open(integrity_path) as f:
                expected = json.load(f)
            all_passed = True
            for circuit, expected_hash in expected.items():
                vkey_path = artifacts_dir / circuit / "verification_key.json"
                if vkey_path.exists():
                    computed = compute_vkey_hash(vkey_path)
                    if computed != expected_hash:
                        print(f"❌ MISMATCH {circuit}: expected {expected_hash[:16]}..., got {computed[:16]}...")
                        all_passed = False
                    else:
                        print(f"✅ {circuit}: {computed[:16]}...")
                else:
                    print(f"⚠️  {circuit}: vkey not found (skipping)")
            sys.exit(0 if all_passed else 1)
        elif sys.argv[1] == "--aaip":
            # Generate hashes for AAIP circuits only
            generate_hashes(artifacts_dir, AAIP_CIRCUITS)
    else:
        # Default: verify core circuits
        all_passed = True
        for circuit in CORE_CIRCUITS:
            if not verify_integrity(circuit, artifacts_dir):
                all_passed = False
        sys.exit(0 if all_passed else 1)

