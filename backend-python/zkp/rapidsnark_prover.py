#!/usr/bin/env python3
"""
Rapidsnark Prover Integration
=============================

High-performance Groth16 prover using iden3's rapidsnark C++ implementation.
5-10x faster than SnarkJS with sub-8GB RAM usage for 1M+ constraint circuits.

Usage:
    from rapidsnark_prover import RapidsnarkProver
    
    prover = RapidsnarkProver()
    proof, public_signals = prover.prove("age_level3", witness_data)

Requirements:
    - rapidsnark binary in PATH or RAPIDSNARK_BIN env var
    - Compiled .zkey files in artifacts directory
    - C++ witness generator (for Level 3 circuits)
"""

import json
import os
import shutil
import subprocess
import tempfile
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)

# Circuit configurations
CIRCUIT_CONFIG = {
    # Simple circuits - use SnarkJS (fast enough)
    "age": {"use_rapidsnark": False, "witness_type": "wasm"},
    "authenticity": {"use_rapidsnark": False, "witness_type": "wasm"},
    
    # Level 3 circuits - use Rapidsnark (5-10x faster)
    "age_level3": {"use_rapidsnark": True, "witness_type": "cpp"},
    "level3_inequality": {"use_rapidsnark": True, "witness_type": "cpp"},
    
    # AAIP circuits - use Rapidsnark (production performance)
    "agent_capability": {"use_rapidsnark": True, "witness_type": "cpp"},
    "agent_reputation": {"use_rapidsnark": True, "witness_type": "cpp"},
}


class RapidsnarkError(Exception):
    """Raised when rapidsnark prover fails"""
    pass


class WitnessGenerationError(Exception):
    """Raised when witness generation fails"""
    pass


class RapidsnarkProver:
    """
    High-performance Groth16 prover using rapidsnark.
    
    Automatically falls back to SnarkJS for simple circuits or if
    rapidsnark binary is not available.
    """
    
    def __init__(
        self,
        artifacts_dir: Optional[Path] = None,
        rapidsnark_bin: Optional[str] = None,
        snarkjs_path: Optional[str] = None,
        thread_count: Optional[int] = None,
    ):
        """
        Initialize the prover.
        
        Args:
            artifacts_dir: Path to ZKP artifacts (default: ./artifacts)
            rapidsnark_bin: Path to rapidsnark binary (default: from PATH or env)
            snarkjs_path: Path to snarkjs (default: npx snarkjs)
            thread_count: Number of threads for rapidsnark (default: auto)
        """
        self.artifacts_dir = artifacts_dir or Path(__file__).parent / "artifacts"
        self.rapidsnark_bin = rapidsnark_bin or os.environ.get("RAPIDSNARK_BIN", "rapidsnark")
        self.snarkjs_path = snarkjs_path or "npx snarkjs"
        self.thread_count = thread_count or os.cpu_count() or 4
        
        # Check rapidsnark availability
        self._rapidsnark_available = self._check_rapidsnark()
        if self._rapidsnark_available:
            logger.info(f"Rapidsnark available: {self.rapidsnark_bin}")
        else:
            logger.warning("Rapidsnark not found, falling back to SnarkJS for all circuits")
    
    def _check_rapidsnark(self) -> bool:
        """Check if rapidsnark binary is available."""
        try:
            result = subprocess.run(
                [self.rapidsnark_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _get_circuit_paths(self, circuit: str) -> Dict[str, Path]:
        """Get paths to circuit artifacts."""
        base = self.artifacts_dir / circuit
        
        # Handle different naming conventions
        circuit_name = circuit
        if circuit == "level3_inequality":
            circuit_name = "Level3Inequality"
        
        return {
            "zkey": base / f"{circuit_name}_final.zkey",
            "wasm": base / f"{circuit_name}_js" / f"{circuit_name}.wasm",
            "cpp_witness": base / circuit_name,  # C++ binary
            "vkey": base / "verification_key.json",
        }
    
    def _generate_witness_wasm(
        self,
        circuit: str,
        input_data: Dict[str, Any],
        output_path: Path
    ) -> None:
        """Generate witness using WASM (SnarkJS)."""
        paths = self._get_circuit_paths(circuit)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name
        
        try:
            cmd = f"{self.snarkjs_path} wtns calculate {paths['wasm']} {input_file} {output_path}"
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                raise WitnessGenerationError(f"WASM witness generation failed: {result.stderr}")
        finally:
            os.unlink(input_file)
    
    def _generate_witness_cpp(
        self,
        circuit: str,
        input_data: Dict[str, Any],
        output_path: Path
    ) -> None:
        """Generate witness using C++ binary (faster, lower memory)."""
        paths = self._get_circuit_paths(circuit)
        cpp_binary = paths["cpp_witness"]
        
        if not cpp_binary.exists():
            logger.warning(f"C++ witness generator not found for {circuit}, falling back to WASM")
            return self._generate_witness_wasm(circuit, input_data, output_path)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(input_data, f)
            input_file = f.name
        
        try:
            result = subprocess.run(
                [str(cpp_binary), input_file, str(output_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                raise WitnessGenerationError(f"C++ witness generation failed: {result.stderr}")
        finally:
            os.unlink(input_file)
    
    def _prove_rapidsnark(
        self,
        circuit: str,
        witness_path: Path,
        proof_path: Path,
        public_path: Path
    ) -> None:
        """Generate proof using rapidsnark (fast C++ prover)."""
        paths = self._get_circuit_paths(circuit)
        
        # rapidsnark <circuit.zkey> <witness.wtns> <proof.json> <public.json>
        cmd = [
            self.rapidsnark_bin,
            str(paths["zkey"]),
            str(witness_path),
            str(proof_path),
            str(public_path)
        ]
        
        # Set thread count via environment
        env = os.environ.copy()
        env["OMP_NUM_THREADS"] = str(self.thread_count)
        
        logger.debug(f"Running rapidsnark: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env
        )
        
        if result.returncode != 0:
            raise RapidsnarkError(f"Rapidsnark proving failed: {result.stderr}")
    
    def _prove_snarkjs(
        self,
        circuit: str,
        witness_path: Path,
        proof_path: Path,
        public_path: Path
    ) -> None:
        """Generate proof using SnarkJS (slower but always available)."""
        paths = self._get_circuit_paths(circuit)
        
        cmd = f"{self.snarkjs_path} groth16 prove {paths['zkey']} {witness_path} {proof_path} {public_path}"
        
        logger.debug(f"Running snarkjs: {cmd}")
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ, "NODE_OPTIONS": "--max-old-space-size=8192"}
        )
        
        if result.returncode != 0:
            raise RapidsnarkError(f"SnarkJS proving failed: {result.stderr}")
    
    def prove(
        self,
        circuit: str,
        input_data: Dict[str, Any],
        force_rapidsnark: bool = False,
        force_snarkjs: bool = False
    ) -> Tuple[Dict[str, Any], list]:
        """
        Generate a Groth16 proof for the given circuit and inputs.
        
        Args:
            circuit: Circuit name (e.g., "age_level3", "agent_reputation")
            input_data: Circuit input signals as a dictionary
            force_rapidsnark: Force use of rapidsnark (fails if not available)
            force_snarkjs: Force use of SnarkJS (slower but guaranteed)
        
        Returns:
            Tuple of (proof_dict, public_signals_list)
        
        Raises:
            RapidsnarkError: If proving fails
            WitnessGenerationError: If witness generation fails
        """
        config = CIRCUIT_CONFIG.get(circuit, {"use_rapidsnark": False, "witness_type": "wasm"})
        
        # Determine which prover to use
        use_rapidsnark = (
            not force_snarkjs and
            (force_rapidsnark or config["use_rapidsnark"]) and
            self._rapidsnark_available
        )
        
        # Determine witness generation method
        witness_type = config.get("witness_type", "wasm")
        
        logger.info(f"Proving {circuit} with {'rapidsnark' if use_rapidsnark else 'snarkjs'}, witness={witness_type}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            witness_path = tmpdir / "witness.wtns"
            proof_path = tmpdir / "proof.json"
            public_path = tmpdir / "public.json"
            
            # Generate witness
            if witness_type == "cpp":
                self._generate_witness_cpp(circuit, input_data, witness_path)
            else:
                self._generate_witness_wasm(circuit, input_data, witness_path)
            
            # Generate proof
            if use_rapidsnark:
                self._prove_rapidsnark(circuit, witness_path, proof_path, public_path)
            else:
                self._prove_snarkjs(circuit, witness_path, proof_path, public_path)
            
            # Read results
            with open(proof_path) as f:
                proof = json.load(f)
            with open(public_path) as f:
                public_signals = json.load(f)
            
            return proof, public_signals
    
    def verify(
        self,
        circuit: str,
        proof: Dict[str, Any],
        public_signals: list
    ) -> bool:
        """
        Verify a Groth16 proof.
        
        Note: Verification is always done with SnarkJS as it's fast enough
        and rapidsnark doesn't include a verifier.
        
        Args:
            circuit: Circuit name
            proof: Proof dictionary
            public_signals: Public signals list
        
        Returns:
            True if proof is valid, False otherwise
        """
        paths = self._get_circuit_paths(circuit)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            proof_path = tmpdir / "proof.json"
            public_path = tmpdir / "public.json"
            
            with open(proof_path, 'w') as f:
                json.dump(proof, f)
            with open(public_path, 'w') as f:
                json.dump(public_signals, f)
            
            cmd = f"{self.snarkjs_path} groth16 verify {paths['vkey']} {public_path} {proof_path}"
            
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            return result.returncode == 0 and "OK" in result.stdout


# Singleton instance for convenience
_default_prover: Optional[RapidsnarkProver] = None


def get_prover() -> RapidsnarkProver:
    """Get the default prover instance."""
    global _default_prover
    if _default_prover is None:
        _default_prover = RapidsnarkProver()
    return _default_prover


def prove(circuit: str, input_data: Dict[str, Any]) -> Tuple[Dict[str, Any], list]:
    """Convenience function to generate a proof."""
    return get_prover().prove(circuit, input_data)


def verify(circuit: str, proof: Dict[str, Any], public_signals: list) -> bool:
    """Convenience function to verify a proof."""
    return get_prover().verify(circuit, proof, public_signals)


# CLI interface
if __name__ == "__main__":
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Rapidsnark Groth16 Prover")
    parser.add_argument("command", choices=["prove", "verify", "benchmark"])
    parser.add_argument("--circuit", "-c", required=True, help="Circuit name")
    parser.add_argument("--input", "-i", help="Input JSON file")
    parser.add_argument("--proof", "-p", help="Proof JSON file")
    parser.add_argument("--public", help="Public signals JSON file")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--force-snarkjs", action="store_true", help="Force SnarkJS")
    parser.add_argument("--force-rapidsnark", action="store_true", help="Force rapidsnark")
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    prover = RapidsnarkProver()
    
    if args.command == "prove":
        if not args.input:
            print("Error: --input required for prove", file=sys.stderr)
            sys.exit(1)
        
        with open(args.input) as f:
            input_data = json.load(f)
        
        import time
        start = time.time()
        proof, public_signals = prover.prove(
            args.circuit,
            input_data,
            force_snarkjs=args.force_snarkjs,
            force_rapidsnark=args.force_rapidsnark
        )
        elapsed = time.time() - start
        
        result = {"proof": proof, "publicSignals": public_signals}
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"✅ Proof generated in {elapsed:.2f}s -> {args.output}")
        else:
            print(json.dumps(result, indent=2))
            print(f"\n✅ Proof generated in {elapsed:.2f}s", file=sys.stderr)
    
    elif args.command == "verify":
        if not args.proof:
            print("Error: --proof required for verify", file=sys.stderr)
            sys.exit(1)
        
        with open(args.proof) as f:
            data = json.load(f)
        
        proof = data.get("proof", data)
        public_signals = data.get("publicSignals", [])
        
        if args.public:
            with open(args.public) as f:
                public_signals = json.load(f)
        
        valid = prover.verify(args.circuit, proof, public_signals)
        print(f"{'✅ Valid' if valid else '❌ Invalid'}")
        sys.exit(0 if valid else 1)
    
    elif args.command == "benchmark":
        # Run benchmark comparing SnarkJS vs Rapidsnark
        if not args.input:
            print("Error: --input required for benchmark", file=sys.stderr)
            sys.exit(1)
        
        with open(args.input) as f:
            input_data = json.load(f)
        
        import time
        
        print(f"\n📊 Benchmarking {args.circuit}...\n")
        
        # SnarkJS
        print("Running SnarkJS...")
        start = time.time()
        proof_js, public_js = prover.prove(args.circuit, input_data, force_snarkjs=True)
        time_js = time.time() - start
        print(f"  SnarkJS: {time_js:.2f}s")
        
        # Rapidsnark (if available)
        if prover._rapidsnark_available:
            print("Running Rapidsnark...")
            start = time.time()
            proof_rs, public_rs = prover.prove(args.circuit, input_data, force_rapidsnark=True)
            time_rs = time.time() - start
            print(f"  Rapidsnark: {time_rs:.2f}s")
            
            speedup = time_js / time_rs
            print(f"\n⚡ Speedup: {speedup:.1f}x faster with Rapidsnark")
        else:
            print("\n⚠️ Rapidsnark not available for comparison")

