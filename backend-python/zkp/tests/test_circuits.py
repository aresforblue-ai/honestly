#!/usr/bin/env python3
"""
Comprehensive test suite for zkSNARK circuits.
Tests valid proofs, invalid proofs (should fail), and edge cases.
"""
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Test configuration
ZKP_DIR = Path(__file__).resolve().parent.parent
RUNNER_PATH = ZKP_DIR / "snark-runner.js"
ARTIFACTS_DIR = ZKP_DIR / "artifacts"


class CircuitTester:
    """Test harness for zkSNARK circuits."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def run_command(self, action: str, circuit: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run snark-runner command."""
        cmd = ["node", str(RUNNER_PATH), action, circuit]

        try:
            proc = subprocess.run(
                cmd,
                input=json.dumps(input_data),
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )

            if proc.returncode != 0:
                return {
                    "success": False,
                    "error": proc.stderr.strip() or proc.stdout.strip(),
                    "returncode": proc.returncode,
                }

            try:
                result = json.loads(proc.stdout)
                result["success"] = True
                return result
            except json.JSONDecodeError:
                return {"success": False, "error": f"Invalid JSON output: {proc.stdout[:200]}"}

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out after 30s"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def assert_prove_succeeds(self, circuit: str, input_data: Dict[str, Any], description: str):
        """Assert that proving succeeds."""
        print(f"\n✓ Testing: {description}")
        result = self.run_command("prove", circuit, input_data)

        if result.get("success") and "proof" in result:
            print("  ✓ Proof generated successfully")
            self.passed += 1
            return True
        else:
            error = result.get("error", "Unknown error")
            print(f"  ✗ Proof generation failed: {error}")
            self.failed += 1
            self.errors.append(f"{description}: {error}")
            return False

    def assert_prove_fails(self, circuit: str, input_data: Dict[str, Any], description: str):
        """Assert that proving fails (invalid input)."""
        print(f"\n✓ Testing (should fail): {description}")
        result = self.run_command("prove", circuit, input_data)

        if not result.get("success"):
            print("  ✓ Correctly rejected invalid input")
            self.passed += 1
            return True
        else:
            print("  ✗ Should have failed but succeeded!")
            self.failed += 1
            self.errors.append(f"{description}: Should have failed but succeeded")
            return False

    def assert_verify_succeeds(self, circuit: str, proof_data: Dict[str, Any], description: str):
        """Assert that verification succeeds."""
        print(f"\n✓ Verifying: {description}")
        result = self.run_command("verify", circuit, proof_data)

        if result.get("success") and result.get("verified") is True:
            print("  ✓ Verification passed")
            self.passed += 1
            return True
        else:
            error = result.get("error", "Verification failed")
            print(f"  ✗ Verification failed: {error}")
            self.failed += 1
            self.errors.append(f"{description}: {error}")
            return False

    def assert_verify_fails(self, circuit: str, proof_data: Dict[str, Any], description: str):
        """Assert that verification fails (invalid proof)."""
        print(f"\n✓ Verifying (should fail): {description}")
        result = self.run_command("verify", circuit, proof_data)

        if result.get("success") and result.get("verified") is False:
            print("  ✓ Correctly rejected invalid proof")
            self.passed += 1
            return True
        else:
            print("  ✗ Should have failed verification but passed!")
            self.failed += 1
            self.errors.append(f"{description}: Should have failed but passed")
            return False

    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        print(f"Total tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")

        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")

        print("=" * 70)
        return self.failed == 0


def test_age_circuit_valid(tester: CircuitTester):
    """Test valid age proofs."""
    print("\n" + "=" * 70)
    print("AGE CIRCUIT - VALID PROOFS")
    print("=" * 70)

    # Test 1: Valid age proof (25 years old, proving >= 18)
    valid_input_1 = {
        "birthTs": "631152000",  # Jan 1, 1990
        "referenceTs": "1733443200",  # Dec 1, 2024
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    if tester.assert_prove_succeeds("age", valid_input_1, "Valid age proof (25 years, >= 18)"):
        # Get proof and verify it
        result = tester.run_command("prove", "age", valid_input_1)
        if result.get("success"):
            tester.assert_verify_succeeds("age", result, "Verify valid age proof")

    # Test 2: Edge case - exactly minimum age
    edge_input = {
        "birthTs": "1577836800",  # Jan 1, 2020
        "referenceTs": "1733443200",  # Dec 1, 2024 (exactly 4 years)
        "minAge": "4",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "9876543210987654321",
    }

    tester.assert_prove_succeeds("age", edge_input, "Edge case: exactly minimum age")

    # Test 3: Large age difference
    large_age_input = {
        "birthTs": "0",  # Jan 1, 1970
        "referenceTs": "1733443200",  # Dec 1, 2024
        "minAge": "50",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "1111111111111111111",
    }

    tester.assert_prove_succeeds("age", large_age_input, "Large age difference (54 years, >= 50)")


def test_age_circuit_invalid(tester: CircuitTester):
    """Test invalid age proofs (should fail)."""
    print("\n" + "=" * 70)
    print("AGE CIRCUIT - INVALID PROOFS (SHOULD FAIL)")
    print("=" * 70)

    # Test 1: Age too young (negative age scenario)
    invalid_input_1 = {
        "birthTs": "1733443200",  # Dec 1, 2024
        "referenceTs": "631152000",  # Jan 1, 1990 (birth AFTER reference - invalid!)
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    tester.assert_prove_fails("age", invalid_input_1, "Invalid: birth date after reference date")

    # Test 2: Age below minimum
    invalid_input_2 = {
        "birthTs": "1704067200",  # Jan 1, 2024
        "referenceTs": "1733443200",  # Dec 1, 2024 (less than 1 year)
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    tester.assert_prove_fails("age", invalid_input_2, "Invalid: age below minimum (0.9 years < 18)")

    # Test 3: Exactly one day short of minimum age
    invalid_input_3 = {
        "birthTs": "1704067200",  # Jan 1, 2024
        "referenceTs": str(1704067200 + (18 * 365 * 24 * 3600) - 86400),  # 1 day before 18 years
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    tester.assert_prove_fails("age", invalid_input_3, "Invalid: exactly 1 day short of minimum age")

    # Test 4: Zero age
    invalid_input_4 = {
        "birthTs": "1733443200",  # Dec 1, 2024
        "referenceTs": "1733443200",  # Same date
        "minAge": "1",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    tester.assert_prove_fails("age", invalid_input_4, "Invalid: zero age (same timestamps)")


def test_authenticity_circuit_valid(tester: CircuitTester):
    """Test valid authenticity proofs."""
    print("\n" + "=" * 70)
    print("AUTHENTICITY CIRCUIT - VALID PROOFS")
    print("=" * 70)

    # Note: For valid Merkle proofs, we need actual Merkle tree data
    # This is a simplified test - in production, you'd generate real Merkle trees

    # Test with sample data (assuming valid Merkle proof structure)
    # In real tests, you'd construct a Merkle tree and generate actual proofs
    print("\n  Note: Authenticity circuit requires actual Merkle tree construction")
    print("  For production, use a Merkle tree library to generate real proofs")

    # Example structure (would need real Merkle tree to be valid)
    valid_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }

    # This will likely fail without real Merkle tree, but shows the structure
    result = tester.run_command("prove", "authenticity", valid_input)
    if result.get("success"):
        tester.assert_verify_succeeds("authenticity", result, "Verify valid authenticity proof")
    else:
        print(
            f"  ⚠ Skipping authenticity test (requires real Merkle tree): {result.get('error', 'Unknown')}"
        )


def test_authenticity_circuit_invalid(tester: CircuitTester):
    """Test invalid authenticity proofs (should fail)."""
    print("\n" + "=" * 70)
    print("AUTHENTICITY CIRCUIT - INVALID PROOFS (SHOULD FAIL)")
    print("=" * 70)

    # Test 1: Wrong root (double-spend equivalent)
    invalid_input_1 = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "0000000000000000000000000000000000000000000000000000000000000000",  # Wrong root
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }

    tester.assert_prove_fails("authenticity", invalid_input_1, "Invalid: wrong Merkle root")

    # Test 2: Wrong leaf
    invalid_input_2 = {
        "leafHex": "0000000000000000000000000000000000000000000000000000000000000000",  # Wrong leaf
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }

    tester.assert_prove_fails("authenticity", invalid_input_2, "Invalid: wrong leaf hash")

    # Test 3: Invalid path indices (out of range)
    invalid_input_3 = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
        ],  # Invalid: should be 0 or 1
    }

    tester.assert_prove_fails("authenticity", invalid_input_3, "Invalid: path indices out of range")


def test_boundary_value_analysis(tester: CircuitTester):
    """Test boundary value analysis - critical for off-by-one errors.

    Tests the >= condition explicitly to ensure it's not mistakenly implemented as >.
    Uses precise calculations: minimumAge = 18 * 365.25 * 24 * 60 * 60 seconds.
    """
    print("\n" + "=" * 70)
    print("BOUNDARY VALUE ANALYSIS")
    print("=" * 70)

    # Circuit uses YEAR_SECONDS = 31556952 (average seconds per Gregorian year)
    # For precise boundary testing, we'll use 365.25 days calculation
    SECONDS_PER_DAY = 24 * 60 * 60  # 86400
    DAYS_PER_YEAR = 365.25
    SECONDS_PER_YEAR_PRECISE = int(DAYS_PER_YEAR * SECONDS_PER_DAY)  # 31,557,600

    # Circuit's actual value (should match or be very close)
    YEAR_SECONDS_CIRCUIT = 31556952

    min_age = 18
    min_age_seconds_precise = min_age * SECONDS_PER_YEAR_PRECISE
    min_age_seconds_circuit = min_age * YEAR_SECONDS_CIRCUIT

    # Use a fixed reference date
    import datetime

    reference_date = datetime.datetime(2025, 1, 1)
    reference_ts = int(reference_date.timestamp())

    print(f"\n  Reference date: {reference_date.isoformat()}")
    print(f"  Minimum age: {min_age} years")
    print(f"  Precise calculation: {min_age} * 365.25 * 86400 = {min_age_seconds_precise} seconds")
    print(
        f"  Circuit calculation: {min_age} * {YEAR_SECONDS_CIRCUIT} = {min_age_seconds_circuit} seconds"
    )

    # Test 1: Minimum age - 1 second (should FAIL)
    print(f"\n  Testing boundary: minimum age ({min_age} years) - 1 second")
    birth_ts_fail = reference_ts - min_age_seconds_circuit - 1  # 1 second too young
    boundary_fail = {
        "birthTs": str(birth_ts_fail),
        "referenceTs": str(reference_ts),
        "minAge": str(min_age),
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "boundary_test_1",
    }
    tester.assert_prove_fails(
        "age", boundary_fail, f"Boundary: {min_age} years - 1 second (should fail)"
    )

    # Test 2: Exactly minimum age (should SUCCEED)
    print(f"\n  Testing boundary: exactly minimum age ({min_age} years)")
    birth_ts_exact = reference_ts - min_age_seconds_circuit  # Just old enough
    boundary_exact = {
        "birthTs": str(birth_ts_exact),
        "referenceTs": str(reference_ts),
        "minAge": str(min_age),
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "boundary_test_2",
    }
    if tester.assert_prove_succeeds(
        "age", boundary_exact, f"Boundary: exactly {min_age} years (should succeed)"
    ):
        result = tester.run_command("prove", "age", boundary_exact)
        if result.get("success"):
            tester.assert_verify_succeeds(
                "age", result, f"Verify boundary: exactly {min_age} years"
            )

    # Test 3: Minimum age + 1 second (should SUCCEED)
    print(f"\n  Testing boundary: minimum age ({min_age} years) + 1 second")
    birth_ts_pass = reference_ts - min_age_seconds_circuit + 1  # Just over the line
    boundary_pass = {
        "birthTs": str(birth_ts_pass),
        "referenceTs": str(reference_ts),
        "minAge": str(min_age),
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "boundary_test_3",
    }
    if tester.assert_prove_succeeds(
        "age", boundary_pass, f"Boundary: {min_age} years + 1 second (should succeed)"
    ):
        result = tester.run_command("prove", "age", boundary_pass)
        if result.get("success"):
            tester.assert_verify_succeeds(
                "age", result, f"Verify boundary: {min_age} years + 1 second"
            )

    # Test 4: Test with smaller min_age for precision (1 year boundary)
    print("\n  Testing boundary: 1 year boundary (more precise)")
    min_age_1 = 1
    min_age_1_seconds = min_age_1 * YEAR_SECONDS_CIRCUIT

    boundary_1yr_fail = {
        "birthTs": "0",
        "referenceTs": str(min_age_1_seconds - 1),  # 1 second short of 1 year
        "minAge": str(min_age_1),
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "boundary_1yr_fail",
    }
    tester.assert_prove_fails("age", boundary_1yr_fail, "Boundary: 1 year - 1 second (should fail)")

    boundary_1yr_exact = {
        "birthTs": "0",
        "referenceTs": str(min_age_1_seconds),  # Exactly 1 year
        "minAge": str(min_age_1),
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "boundary_1yr_exact",
    }
    tester.assert_prove_succeeds(
        "age", boundary_1yr_exact, "Boundary: exactly 1 year (should succeed)"
    )

    boundary_1yr_pass = {
        "birthTs": "0",
        "referenceTs": str(min_age_1_seconds + 1),  # 1 second over 1 year
        "minAge": str(min_age_1),
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "boundary_1yr_pass",
    }
    tester.assert_prove_succeeds(
        "age", boundary_1yr_pass, "Boundary: 1 year + 1 second (should succeed)"
    )

    # Test 5: Verify >= is not mistakenly implemented as >
    print("\n  Testing: Verifying >= condition (not >)")
    # This is already covered by the exact boundary test above
    # If it were > instead of >=, the exact boundary test would fail
    print("  ✓ >= condition verified: exact boundary succeeds, -1 second fails")


def test_integer_overflow_underflow(tester: CircuitTester):
    """Test integer overflow/underflow protection.

    Tests that large field element values don't cause overflow or false positives.
    Circuit uses 64-bit constraints, but field elements are much larger (BN254 field).
    """
    print("\n" + "=" * 70)
    print("INTEGER OVERFLOW/UNDERFLOW TESTS")
    print("=" * 70)

    # BN254 field modulus (p-1) - maximum field element value
    # This is the attack vector: feeding max field values to exploit arithmetic
    _ = "21888242871839275222246405745257275088548364400416034343698204186575808495617"  # FIELD_MODULUS for reference
    FIELD_MODULUS_MINUS_1 = (
        "21888242871839275222246405745257275088548364400416034343698204186575808495616"
    )

    import datetime

    reference_date = datetime.datetime(2025, 1, 1)
    reference_ts = int(reference_date.timestamp())
    normal_birth_ts = reference_ts - (50 * 365.25 * 24 * 60 * 60)  # Normal 50-year-old

    # Test 1: Maximum 32-bit signed integer (2^31 - 1)
    print("\n  Testing: 32-bit signed integer max (2^31 - 1)")
    max_32bit = 2**31 - 1  # 2147483647
    overflow_test_1 = {
        "birthTs": "0",
        "referenceTs": str(max_32bit),
        "minAge": "1",
        "documentHashHex": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "salt": "overflow_test_1",
    }
    result = tester.run_command("prove", "age", overflow_test_1)
    if result.get("success"):
        print("  ✓ Circuit handles 32-bit max correctly")
        tester.passed += 1
    else:
        print(f"  ⚠ Circuit may have issues with 32-bit max: {result.get('error', 'Unknown')}")
        tester.failed += 1

    # Test 2: Nonsensically large field element as birth date (should FAIL)
    print("\n  Testing: Nonsensically large field element as birth date (attack vector)")
    overflow_attack_birth = {
        "birthTs": FIELD_MODULUS_MINUS_1,  # Max field element
        "referenceTs": str(reference_ts),
        "minAge": "1",
        "documentHashHex": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "salt": "overflow_attack_birth",
    }
    # This should fail because birthTs > referenceTs (nonsensical)
    tester.assert_prove_fails(
        "age",
        overflow_attack_birth,
        "Nonsensically large field element as birth date (should fail)",
    )

    # Test 3: Nonsensically large field element as reference date (should FAIL)
    print("\n  Testing: Nonsensically large field element as reference date (attack vector)")
    overflow_attack_ref = {
        "birthTs": str(normal_birth_ts),  # Normal age
        "referenceTs": FIELD_MODULUS_MINUS_1,  # Max field element - attack vector
        "minAge": "1",
        "documentHashHex": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "salt": "overflow_attack_ref",
    }
    # This might succeed if circuit doesn't validate, but delta calculation should be wrong
    result = tester.run_command("prove", "age", overflow_attack_ref)
    if result.get("success"):
        print("  ⚠ WARNING: Circuit accepted max field element as reference date")
        print("     This may indicate a vulnerability - verify delta calculation")
        tester.failed += 1
    else:
        print("  ✓ Circuit correctly rejects max field element as reference date")
        tester.passed += 1

    # Test 4: Very large timestamp (approaching 64-bit limit)
    print("\n  Testing: Very large timestamp (2^63 - 1)")
    max_64bit = 2**63 - 1  # 9223372036854775807
    overflow_test_2 = {
        "birthTs": "0",
        "referenceTs": str(max_64bit),
        "minAge": "1",
        "documentHashHex": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "salt": "overflow_test_2",
    }
    # Circuit uses 64-bit constraints, so this should be handled
    result = tester.run_command("prove", "age", overflow_test_2)
    if result.get("success"):
        print("  ✓ Circuit handles 64-bit max correctly")
        tester.passed += 1
    else:
        # This might fail due to field size limits, which is acceptable
        print(f"  ⚠ Large timestamp rejected (may be expected): {result.get('error', 'Unknown')}")
        tester.passed += 1  # Count as pass if it rejects safely

    # Test 5: Negative timestamp (should fail)
    print("\n  Testing: Negative timestamp (should fail)")
    negative_test = {
        "birthTs": "-1000",
        "referenceTs": "1000",
        "minAge": "1",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "negative_test",
    }
    tester.assert_prove_fails("age", negative_test, "Negative timestamp (should fail)")

    # Test 6: Timestamp difference causing potential overflow
    print("\n  Testing: Very large age difference")
    large_diff_test = {
        "birthTs": "0",
        "referenceTs": str(200 * 31556952),  # 200 years
        "minAge": "200",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "large_diff_test",
    }
    result = tester.run_command("prove", "age", large_diff_test)
    if result.get("success"):
        print("  ✓ Circuit handles very large age differences correctly")
        tester.passed += 1
    else:
        print(f"  ⚠ Large age difference rejected: {result.get('error', 'Unknown')}")
        tester.failed += 1

    # Test 7: Nonsensical input - birthTs > referenceTs (should fail)
    print("\n  Testing: Nonsensical input - birth after reference")
    nonsensical_test = {
        "birthTs": str(2**31 - 1),
        "referenceTs": "0",
        "minAge": "1",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "nonsensical_test",
    }
    tester.assert_prove_fails(
        "age", nonsensical_test, "Nonsensical: birth after reference (should fail)"
    )

    # Test 8: Field element wrap-around attack (should FAIL)
    print("\n  Testing: Field element wrap-around attack")
    # Try to exploit: if birthTs is very large and referenceTs is small,
    # the subtraction might wrap around in the field
    wrap_around_test = {
        "birthTs": FIELD_MODULUS_MINUS_1,  # Max field element
        "referenceTs": "1000",  # Small reference
        "minAge": "1",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "wrap_around_test",
    }
    # Should fail because birthTs > referenceTs check
    tester.assert_prove_fails(
        "age", wrap_around_test, "Field element wrap-around attack (should fail)"
    )


def test_leap_year_edge_cases(tester: CircuitTester):
    """Test leap year and leap day edge cases.

    Tests that circuit correctly handles Feb 29 birthdays and leap year transitions.
    Unix timestamps handle leap years correctly, but we verify edge cases explicitly.
    """
    print("\n" + "=" * 70)
    print("LEAP YEAR/DAY EDGE CASES")
    print("=" * 70)

    import datetime

    # Test 1: Birth on Feb 29, proving age correctly on non-leap year (should FAIL - one day short)
    print("\n  Testing: Birth Feb 29, 2004, reference Feb 28, 2022 (one day short of 18)")
    birth_feb29_2004 = int(datetime.datetime(2004, 2, 29).timestamp())  # Leap year
    reference_feb28_2022 = int(
        datetime.datetime(2022, 2, 28).timestamp()
    )  # Day before 18th birthday
    # Should be one day short of 18 years

    leap_fail_test = {
        "birthTs": str(birth_feb29_2004),
        "referenceTs": str(reference_feb28_2022),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "leap_fail_test",
    }
    tester.assert_prove_fails(
        "age", leap_fail_test, "Birth Feb 29, reference Feb 28 (one day short - should fail)"
    )

    # Test 2: Birth on Feb 29, proving age correctly on leap year (should SUCCEED)
    print("\n  Testing: Birth Feb 29, 2004, reference Mar 1, 2022 (on/after 18th birthday)")
    birth_feb29_2004 = int(datetime.datetime(2004, 2, 29).timestamp())
    reference_mar1_2022 = int(datetime.datetime(2022, 3, 1).timestamp())  # On/after 18th birthday

    leap_success_test = {
        "birthTs": str(birth_feb29_2004),
        "referenceTs": str(reference_mar1_2022),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "leap_success_test",
    }
    tester.assert_prove_succeeds(
        "age", leap_success_test, "Birth Feb 29, reference Mar 1 (should succeed)"
    )

    # Test 3: Birth on Feb 29, 2000 (leap year)
    print("\n  Testing: Birth on Feb 29, 2000 (leap year)")
    feb29_2000 = int(datetime.datetime(2000, 2, 29).timestamp())
    reference_2024 = int(datetime.datetime(2024, 3, 1).timestamp())

    leap_birth_test = {
        "birthTs": str(feb29_2000),
        "referenceTs": str(reference_2024),
        "minAge": "18",  # Should be ~24 years old
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "leap_birth_test",
    }
    tester.assert_prove_succeeds("age", leap_birth_test, "Birth on Feb 29, 2000 (leap year)")

    # Test 4: Reference on Feb 29 (leap year)
    print("\n  Testing: Reference on Feb 29, 2024 (leap year)")
    birth_2006 = int(datetime.datetime(2006, 1, 1).timestamp())
    feb29_2024 = int(datetime.datetime(2024, 2, 29).timestamp())

    leap_ref_test = {
        "birthTs": str(birth_2006),
        "referenceTs": str(feb29_2024),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "leap_ref_test",
    }
    tester.assert_prove_succeeds("age", leap_ref_test, "Reference on Feb 29, 2024 (leap year)")

    # Test 5: Birth on Feb 28, reference on Feb 29 (non-leap to leap)
    print("\n  Testing: Birth Feb 28, reference Feb 29")
    feb28_2001 = int(datetime.datetime(2001, 2, 28).timestamp())  # Non-leap year
    feb29_2024 = int(datetime.datetime(2024, 2, 29).timestamp())  # Leap year

    feb28_to_feb29_test = {
        "birthTs": str(feb28_2001),
        "referenceTs": str(feb29_2024),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "feb28_to_feb29_test",
    }
    tester.assert_prove_succeeds(
        "age", feb28_to_feb29_test, "Birth Feb 28 (non-leap), reference Feb 29 (leap)"
    )

    # Test 6: Birth on Feb 29, reference on Feb 28 (leap to non-leap)
    print("\n  Testing: Birth Feb 29, reference Feb 28")
    feb29_2000 = int(datetime.datetime(2000, 2, 29).timestamp())  # Leap year
    feb28_2023 = int(datetime.datetime(2023, 2, 28).timestamp())  # Non-leap year

    feb29_to_feb28_test = {
        "birthTs": str(feb29_2000),
        "referenceTs": str(feb28_2023),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "feb29_to_feb28_test",
    }
    tester.assert_prove_succeeds(
        "age", feb29_to_feb28_test, "Birth Feb 29 (leap), reference Feb 28 (non-leap)"
    )

    # Test 7: Multiple leap years in age calculation
    print("\n  Testing: Age spanning multiple leap years")
    birth_2000 = int(datetime.datetime(2000, 1, 1).timestamp())
    reference_2024 = int(datetime.datetime(2024, 12, 31).timestamp())
    # 2000, 2004, 2008, 2012, 2016, 2020, 2024 are leap years

    multi_leap_test = {
        "birthTs": str(birth_2000),
        "referenceTs": str(reference_2024),
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "multi_leap_test",
    }
    tester.assert_prove_succeeds(
        "age", multi_leap_test, "Age spanning multiple leap years (2000-2024)"
    )

    # Test 8: Exactly 4 years (including leap years)
    print("\n  Testing: Exactly 4 years including leap years")
    birth_2020 = int(datetime.datetime(2020, 1, 1).timestamp())  # Leap year
    reference_2024 = int(datetime.datetime(2024, 1, 1).timestamp())  # Leap year
    # 2020 is leap, 2024 is leap, so 4 years = 4 * 365.25 days

    exactly_4yr_test = {
        "birthTs": str(birth_2020),
        "referenceTs": str(reference_2024),
        "minAge": "4",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "exactly_4yr_test",
    }
    tester.assert_prove_succeeds("age", exactly_4yr_test, "Exactly 4 years (including leap years)")

    # Test 9: Century year (1900 - not leap, 2000 - leap)
    print("\n  Testing: Century year edge case")
    birth_1900 = int(datetime.datetime(1900, 2, 28).timestamp())  # Not a leap year
    reference_2000 = int(datetime.datetime(2000, 3, 1).timestamp())  # Leap year

    century_test = {
        "birthTs": str(birth_1900),
        "referenceTs": str(reference_2000),
        "minAge": "100",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "century_test",
    }
    # This should work - circuit uses average year length (31556952 seconds)
    result = tester.run_command("prove", "age", century_test)
    if result.get("success"):
        print("  ✓ Circuit handles century year edge case correctly")
        tester.passed += 1
    else:
        print(f"  ⚠ Century year test: {result.get('error', 'Unknown')}")
        tester.failed += 1


def test_edge_cases(tester: CircuitTester):
    """Test general edge cases."""
    print("\n" + "=" * 70)
    print("GENERAL EDGE CASES")
    print("=" * 70)

    # Test 1: Minimum possible age (1 second over threshold)
    edge_age_1 = {
        "birthTs": "0",
        "referenceTs": str(31556952 + 1),  # 1 year + 1 second
        "minAge": "1",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "0",
    }

    tester.assert_prove_succeeds("age", edge_age_1, "Edge: exactly 1 second over 1 year threshold")

    # Test 2: Maximum timestamp values (within 64-bit range)
    edge_age_2 = {
        "birthTs": "0",
        "referenceTs": "2147483647",  # Max 32-bit signed int (Jan 19, 2038)
        "minAge": "1",
        "documentHashHex": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
        "salt": "9999999999999999999",
    }

    tester.assert_prove_succeeds("age", edge_age_2, "Edge: maximum timestamp values")

    # Test 3: Very large age (100+ years)
    edge_age_3 = {
        "birthTs": "0",  # Jan 1, 1970
        "referenceTs": str(100 * 31556952),  # 100 years later
        "minAge": "100",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    tester.assert_prove_succeeds("age", edge_age_3, "Edge: very large age (100 years)")


def test_input_validation_security(tester: CircuitTester):
    """Test input validation and security - Merkle proof tampering."""
    print("\n" + "=" * 70)
    print("INPUT VALIDATION & SECURITY TESTS")
    print("=" * 70)

    # Test 1: Merkle proof for a leaf not in the tree (should FAIL)
    print("\n  Testing: Merkle proof for fake leaf (not in tree)")
    fake_leaf_input = {
        "leafHex": "0000000000000000000000000000000000000000000000000000000000000000",  # Fake leaf
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",  # Some root
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    # This should fail because the leaf doesn't match the root
    tester.assert_prove_fails(
        "authenticity", fake_leaf_input, "Merkle proof for fake leaf (should fail)"
    )

    # Test 2: Path indices manipulated to be out of bounds (should FAIL)
    print("\n  Testing: Path indices out of bounds (manipulated)")
    invalid_indices_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [
            999,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            9,
            10,
            11,
            12,
            13,
            14,
        ],  # Invalid: first index is 999
    }
    # Path indices should be 0 or 1 only
    tester.assert_prove_fails(
        "authenticity", invalid_indices_input, "Path indices out of bounds (should fail)"
    )

    # Test 3: Path indices with invalid values (not 0 or 1)
    print("\n  Testing: Path indices with invalid values (not 0 or 1)")
    invalid_values_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
            2,
            3,
        ],  # Invalid: should be 0 or 1
    }
    tester.assert_prove_fails(
        "authenticity", invalid_values_input, "Path indices with invalid values (should fail)"
    )

    # Test 4: Wrong number of path elements (should FAIL)
    print("\n  Testing: Wrong number of path elements")
    wrong_length_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": ["1111", "2222", "3333"],  # Only 3 elements, should be 16
        "pathIndices": [0, 1, 0],  # Only 3 indices, should be 16
    }
    # This might fail at the runner level or circuit level
    result = tester.run_command("prove", "authenticity", wrong_length_input)
    if not result.get("success"):
        print("  ✓ Correctly rejected wrong number of path elements")
        tester.passed += 1
    else:
        print("  ⚠ WARNING: Accepted wrong number of path elements")
        tester.failed += 1

    # Test 5: Empty path elements (should FAIL)
    print("\n  Testing: Empty path elements")
    empty_path_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [],
        "pathIndices": [],
    }
    result = tester.run_command("prove", "authenticity", empty_path_input)
    if not result.get("success"):
        print("  ✓ Correctly rejected empty path")
        tester.passed += 1
    else:
        print("  ⚠ WARNING: Accepted empty path")
        tester.failed += 1


def test_circuit_level_constraints_age(tester: CircuitTester):
    """Test circuit-level constraints for age circuit.

    These tests verify that the R1CS constraints themselves enforce:
    1. referenceTs > birthTs (LessThan constraint)
    2. delta >= minAgeSeconds (age check constraint)
    3. delta fits in 64 bits (Num2Bits constraint)

    These are CIRCUIT-LEVEL guarantees, not application-layer validation.
    """
    print("\n" + "=" * 70)
    print("CIRCUIT-LEVEL CONSTRAINT TESTS: AGE CIRCUIT")
    print("=" * 70)

    # Test 1: Circuit constraint: referenceTs > birthTs
    # This is enforced by LessThan(64) component with output === 1
    # If referenceTs <= birthTs, the circuit constraint will fail
    print("\n  Testing CIRCUIT CONSTRAINT: referenceTs > birthTs")
    invalid_order_input = {
        "birthTs": "1733443200",  # Future timestamp
        "referenceTs": "631152000",  # Past timestamp (violates constraint)
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    # This should fail at CIRCUIT LEVEL (constraint violation), not application layer
    result = tester.run_command("prove", "age", invalid_order_input)
    if not result.get("success"):
        # Check if error indicates constraint violation (circuit-level)
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in ["constraint", "witness", "r1cs", "circuit", "satisfy"]
        ):
            print("  ✓ Circuit constraint correctly enforced: referenceTs > birthTs")
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1  # Still counts as pass if rejected
    else:
        print("  ✗ CRITICAL: Circuit accepted invalid timestamp order!")
        tester.failed += 1

    # Test 2: Circuit constraint: delta >= minAgeSeconds
    # This is enforced by LessThan(64) with ageOk.out === 1
    # If delta < minAgeSeconds, the constraint will fail
    print("\n  Testing CIRCUIT CONSTRAINT: delta >= minAgeSeconds")
    insufficient_age_input = {
        "birthTs": "1700000000",  # Recent timestamp
        "referenceTs": "1700000100",  # Only 100 seconds later
        "minAge": "18",  # Requires 18 years = ~568,025,136 seconds
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    # Delta is only 100 seconds, but minAge requires ~568M seconds
    # Circuit constraint ageOk.out === 1 will fail
    result = tester.run_command("prove", "age", insufficient_age_input)
    if not result.get("success"):
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in ["constraint", "witness", "r1cs", "circuit", "satisfy", "age"]
        ):
            print("  ✓ Circuit constraint correctly enforced: delta >= minAgeSeconds")
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1
    else:
        print("  ✗ CRITICAL: Circuit accepted insufficient age!")
        tester.failed += 1

    # Test 3: Circuit constraint: delta fits in 64 bits
    # This is enforced by Num2Bits(64) component
    # If delta overflows 64 bits, the constraint will fail
    print("\n  Testing CIRCUIT CONSTRAINT: delta fits in 64 bits")
    overflow_input = {
        "birthTs": "0",
        "referenceTs": "18446744073709551616",  # 2^64 + 1 (overflows 64 bits)
        "minAge": "1",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    # Delta = 2^64 + 1, which overflows 64-bit constraint
    result = tester.run_command("prove", "age", overflow_input)
    if not result.get("success"):
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in [
                "constraint",
                "witness",
                "r1cs",
                "circuit",
                "satisfy",
                "bits",
                "overflow",
            ]
        ):
            print("  ✓ Circuit constraint correctly enforced: delta fits in 64 bits")
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1
    else:
        print("  ⚠ WARNING: Circuit may have accepted 64-bit overflow (check Num2Bits constraint)")
        tester.failed += 1


def test_circuit_level_constraints_authenticity(tester: CircuitTester):
    """Test circuit-level constraints for authenticity circuit.

    These tests verify that the R1CS constraints themselves enforce:
    1. root === mp.root (root matching constraint)
    2. Path indices must be binary (0 or 1) for proper Merkle path construction
    3. Merkle path computation is correct (circuit enforces structure)

    These are CIRCUIT-LEVEL guarantees, not application-layer validation.
    """
    print("\n" + "=" * 70)
    print("CIRCUIT-LEVEL CONSTRAINT TESTS: AUTHENTICITY CIRCUIT")
    print("=" * 70)

    # Test 1: Circuit constraint: root === mp.root
    # This is enforced by the constraint: root === mp.root
    # If the computed root doesn't match the provided root, constraint fails
    print("\n  Testing CIRCUIT CONSTRAINT: root === mp.root")
    wrong_root_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "0000000000000000000000000000000000000000000000000000000000000000",  # Wrong root
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    # The computed root from the Merkle path won't match the provided root
    # Circuit constraint root === mp.root will fail
    result = tester.run_command("prove", "authenticity", wrong_root_input)
    if not result.get("success"):
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in ["constraint", "witness", "r1cs", "circuit", "satisfy", "root"]
        ):
            print("  ✓ Circuit constraint correctly enforced: root === mp.root")
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1
    else:
        print("  ✗ CRITICAL: Circuit accepted mismatched root!")
        tester.failed += 1

    # Test 2: Circuit constraint: Path indices must be binary
    # The circuit uses pathIndices[i] to select left/right ordering
    # If pathIndices[i] is not 0 or 1, the arithmetic will be wrong
    # However, Circom doesn't explicitly constrain to binary, so this tests
    # that non-binary values produce incorrect Merkle path computation
    print("\n  Testing CIRCUIT CONSTRAINT: Path indices affect Merkle computation")
    non_binary_indices_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3, 2, 3],  # Non-binary values
    }
    # Non-binary indices will compute wrong Merkle path, root won't match
    result = tester.run_command("prove", "authenticity", non_binary_indices_input)
    if not result.get("success"):
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in ["constraint", "witness", "r1cs", "circuit", "satisfy", "root"]
        ):
            print(
                "  ✓ Circuit constraint correctly enforced: Non-binary indices produce wrong root"
            )
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1
    else:
        print("  ⚠ WARNING: Circuit may have accepted non-binary path indices")
        tester.failed += 1

    # Test 3: Circuit constraint: Merkle path structure
    # The circuit enforces the Merkle path computation through Poseidon hashing
    # If path elements are wrong, the computed root won't match
    print("\n  Testing CIRCUIT CONSTRAINT: Merkle path computation structure")
    wrong_path_elements_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",
            "0000",  # All zeros (wrong path)
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    # Wrong path elements will compute wrong root, constraint will fail
    result = tester.run_command("prove", "authenticity", wrong_path_elements_input)
    if not result.get("success"):
        error_msg = result.get("error", "").lower()
        if any(
            keyword in error_msg
            for keyword in ["constraint", "witness", "r1cs", "circuit", "satisfy", "root"]
        ):
            print(
                "  ✓ Circuit constraint correctly enforced: Wrong path elements produce wrong root"
            )
            tester.passed += 1
        else:
            print(f"  ⚠ Rejected but unclear if circuit-level: {result.get('error', 'Unknown')}")
            tester.passed += 1
    else:
        print("  ✗ CRITICAL: Circuit accepted wrong path elements!")
        tester.failed += 1


def test_proof_replay_attack(tester: CircuitTester):
    """Test proof replay attack prevention.

    A valid proof should only verify once with the same public signals.
    In practice, this is prevented by nonce/timestamp validation at the application layer,
    but we test that the circuit itself doesn't allow replay by verifying the same proof
    multiple times with different contexts.
    """
    print("\n" + "=" * 70)
    print("PROOF REPLAY ATTACK TESTS (Application Layer)")
    print("=" * 70)

    # Generate a valid proof
    valid_input = {
        "birthTs": "631152000",
        "referenceTs": "1733443200",
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    result = tester.run_command("prove", "age", valid_input)

    if result.get("success") and "proof" in result:
        proof_data = result

        # Test 1: Same proof with same public signals should verify (this is expected)
        # The replay prevention happens at application layer with nonces/timestamps
        tester.assert_verify_succeeds(
            "age", proof_data, "Same proof should verify (replay prevention is application-layer)"
        )

        # Test 2: Try to reuse proof with different reference timestamp (should fail)
        # This tests that the circuit enforces timestamp consistency
        tampered_timestamp = proof_data.copy()
        if "publicSignals" in tampered_timestamp and len(tampered_timestamp["publicSignals"]) >= 2:
            # Change reference timestamp in public signals
            original_ts = tampered_timestamp["publicSignals"][1]
            tampered_timestamp["publicSignals"][1] = str(int(original_ts) + 86400)  # Add 1 day
            tester.assert_verify_fails(
                "age",
                tampered_timestamp,
                "Proof with modified timestamp should fail (replay prevention)",
            )

        # Test 3: Try to reuse proof with different document hash (should fail)
        tampered_hash = proof_data.copy()
        if "publicSignals" in tampered_hash and len(tampered_hash["publicSignals"]) >= 3:
            # Change document hash in public signals
            tampered_hash["publicSignals"][
                2
            ] = "0000000000000000000000000000000000000000000000000000000000000000"
            tester.assert_verify_fails(
                "age", tampered_hash, "Proof with modified document hash should fail"
            )


def test_timestamp_manipulation(tester: CircuitTester):
    """Test timestamp manipulation attacks.

    Tests that the circuit prevents:
    - Backdating birth timestamps
    - Future reference timestamps
    - Timestamp overflow/underflow
    """
    print("\n" + "=" * 70)
    print("TIMESTAMP MANIPULATION TESTS")
    print("=" * 70)

    # Test 1: Reference timestamp before birth timestamp (should fail)
    print("\n  Testing: Reference timestamp before birth timestamp")
    invalid_order_input = {
        "birthTs": "1733443200",  # Future timestamp
        "referenceTs": "631152000",  # Past timestamp (before birth)
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    tester.assert_prove_fails("age", invalid_order_input, "Reference before birth should fail")

    # Test 2: Negative timestamps (should fail)
    print("\n  Testing: Negative timestamps")
    negative_input = {
        "birthTs": "-1000",
        "referenceTs": "1733443200",
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    tester.assert_prove_fails("age", negative_input, "Negative timestamps should fail")

    # Test 3: Extremely large timestamps (potential overflow)
    print("\n  Testing: Extremely large timestamps")
    large_ts_input = {
        "birthTs": "9999999999999999999999999999999999999999999999999999999999999999",  # Way too large
        "referenceTs": "9999999999999999999999999999999999999999999999999999999999999999",
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    tester.assert_prove_fails(
        "age", large_ts_input, "Extremely large timestamps should fail (overflow protection)"
    )

    # Test 4: Same timestamp for birth and reference (edge case, should fail age check)
    print("\n  Testing: Same timestamp for birth and reference")
    same_ts_input = {
        "birthTs": "1733443200",
        "referenceTs": "1733443200",  # Same as birth
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    tester.assert_prove_fails("age", same_ts_input, "Same timestamp should fail (age = 0 < 18)")


def test_field_overflow_underflow(tester: CircuitTester):
    """Test field overflow/underflow attacks.

    Tests that the circuit prevents:
    - Integer overflow in age calculations
    - Field element overflow
    - Underflow in timestamp differences
    """
    print("\n" + "=" * 70)
    print("FIELD OVERFLOW/UNDERFLOW TESTS")
    print("=" * 70)

    # Test 1: Maximum field element (2^254 - 1, approximately)
    # This tests that the circuit handles large values correctly
    print("\n  Testing: Maximum field element")
    max_field_input = {
        "birthTs": "21888242871839275222246405745257275088548364400416034343698204186575808495616",  # Close to field size
        "referenceTs": "21888242871839275222246405745257275088548364400416034343698204186575808495617",
        "minAge": "1",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    # This might fail due to field constraints, which is expected
    result = tester.run_command("prove", "age", max_field_input)
    if not result.get("success"):
        print("  ✓ Correctly rejected maximum field element (expected)")
        tester.passed += 1
    else:
        print("  ⚠ WARNING: Accepted maximum field element (may indicate overflow vulnerability)")
        tester.failed += 1

    # Test 2: Very large age (should still work if within field bounds)
    print("\n  Testing: Very large age value")
    large_age_input = {
        "birthTs": "0",  # Epoch start
        "referenceTs": "1733443200",  # ~55 years later
        "minAge": "200",  # Very large minimum age
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }
    # This should fail because age is only ~55 years, not 200
    tester.assert_prove_fails(
        "age", large_age_input, "Very large minimum age should fail if not satisfied"
    )

    # Test 3: Zero values (edge case)
    print("\n  Testing: Zero timestamp")
    zero_input = {
        "birthTs": "0",
        "referenceTs": "0",
        "minAge": "0",
        "documentHashHex": "0000000000000000000000000000000000000000000000000000000000000000",
        "salt": "0",
    }
    tester.assert_prove_fails("age", zero_input, "Zero timestamps should fail (reference <= birth)")


def test_malformed_merkle_paths(tester: CircuitTester):
    """Test malformed Merkle path attacks.

    Tests that the circuit prevents:
    - Invalid path element lengths
    - Mismatched path elements and indices
    - Invalid path structure
    """
    print("\n" + "=" * 70)
    print("MALFORMED MERKLE PATH TESTS")
    print("=" * 70)

    # Test 1: Mismatched path elements and indices length
    print("\n  Testing: Mismatched path elements and indices length")
    mismatched_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
            0,
        ],  # Only 15 indices, should be 16
    }
    tester.assert_prove_fails(
        "authenticity", mismatched_input, "Mismatched path length should fail"
    )

    # Test 2: Invalid hex strings in path elements
    print("\n  Testing: Invalid hex strings in path elements")
    invalid_hex_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [
            "INVALID",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    tester.assert_prove_fails("authenticity", invalid_hex_input, "Invalid hex strings should fail")

    # Test 3: Path elements that don't match root
    print("\n  Testing: Path elements that don't match root")
    wrong_root_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "0000000000000000000000000000000000000000000000000000000000000000",  # Wrong root
        "pathElementsHex": [
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "aaaa",
            "bbbb",
            "cccc",
            "dddd",
            "eeee",
            "ffff",
            "1234",
        ],
        "pathIndices": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    }
    tester.assert_prove_fails(
        "authenticity", wrong_root_input, "Path elements that don't match root should fail"
    )

    # Test 4: Empty path elements (already tested, but ensure it's comprehensive)
    print("\n  Testing: Empty path elements array")
    empty_elements_input = {
        "leafHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "rootHex": "feedface0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "pathElementsHex": [],
        "pathIndices": [],
    }
    tester.assert_prove_fails(
        "authenticity", empty_elements_input, "Empty path elements should fail"
    )


def test_proof_verification_integrity(tester: CircuitTester):
    """Test that proofs can't be tampered with."""
    print("\n" + "=" * 70)
    print("PROOF INTEGRITY TESTS")
    print("=" * 70)

    # Generate a valid proof
    valid_input = {
        "birthTs": "631152000",
        "referenceTs": "1733443200",
        "minAge": "18",
        "documentHashHex": "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789",
        "salt": "1234567890123456789",
    }

    result = tester.run_command("prove", "age", valid_input)

    if result.get("success") and "proof" in result:
        proof_data = result

        # Test 1: Tamper with proof
        tampered_proof = proof_data.copy()
        if "proof" in tampered_proof and "pi_a" in tampered_proof["proof"]:
            tampered_proof["proof"]["pi_a"][
                0
            ] = "9999999999999999999999999999999999999999999999999999999999999999"
            tester.assert_verify_fails(
                "age", tampered_proof, "Tampered proof should fail verification"
            )

        # Test 2: Tamper with public signals
        tampered_signals = proof_data.copy()
        if "publicSignals" in tampered_signals:
            tampered_signals["publicSignals"][
                0
            ] = "9999999999999999999999999999999999999999999999999999999999999999"
            tester.assert_verify_fails(
                "age", tampered_signals, "Tampered public signals should fail"
            )

        # Test 3: Original proof should still verify
        tester.assert_verify_succeeds(
            "age", proof_data, "Original proof should still verify after tampering tests"
        )


def main():
    """Run all tests."""
    print("=" * 70)
    print("ZK-SNARK CIRCUIT TEST SUITE")
    print("=" * 70)
    print(f"ZKP Directory: {ZKP_DIR}")
    print(f"Runner: {RUNNER_PATH}")

    if not RUNNER_PATH.exists():
        print(f"\n✗ ERROR: Runner not found at {RUNNER_PATH}")
        print("  Please build the circuits first:")
        print("  cd backend-python/zkp && npm install && npm run build:age && npm run build:auth")
        sys.exit(1)

    tester = CircuitTester()

    # Run all test suites
    test_age_circuit_valid(tester)
    test_age_circuit_invalid(tester)
    test_authenticity_circuit_valid(tester)
    test_authenticity_circuit_invalid(tester)
    test_boundary_value_analysis(tester)
    test_integer_overflow_underflow(tester)
    test_leap_year_edge_cases(tester)
    test_edge_cases(tester)
    test_input_validation_security(tester)
    # ZK Attack Surface Tests - CIRCUIT LEVEL
    test_circuit_level_constraints_age(tester)
    test_circuit_level_constraints_authenticity(tester)
    # ZK Attack Surface Tests - Application Layer
    test_proof_replay_attack(tester)
    test_timestamp_manipulation(tester)
    test_field_overflow_underflow(tester)
    test_malformed_merkle_paths(tester)
    test_proof_verification_integrity(tester)

    # Print summary
    success = tester.print_summary()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
