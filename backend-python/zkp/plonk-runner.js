#!/usr/bin/env node

/**
 * PLONK Proof Runner
 * 
 * Generates and verifies PLONK proofs using snarkjs.
 * PLONK uses a universal trusted setup (no circuit-specific setup needed).
 * 
 * Usage:
 *   node plonk-runner.js prove <circuit> <input.json> <output.json>
 *   node plonk-runner.js verify <circuit> <proof.json>
 *   node plonk-runner.js setup <circuit>
 */

import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

// Dynamic import for snarkjs (ES modules)
const snarkjs = await import('snarkjs');

const __dirname = dirname(fileURLToPath(import.meta.url));

// Circuit configurations
const CIRCUITS = {
  age: {
    wasm: 'artifacts/plonk/age/age_plonk_js/age_plonk.wasm',
    zkey: 'artifacts/plonk/age/age_plonk.zkey',
    vkey: 'artifacts/plonk/age/verification_key.json',
    r1cs: 'artifacts/plonk/age/age_plonk.r1cs',
  },
  authenticity: {
    wasm: 'artifacts/plonk/authenticity/authenticity_plonk_js/authenticity_plonk.wasm',
    zkey: 'artifacts/plonk/authenticity/authenticity_plonk.zkey',
    vkey: 'artifacts/plonk/authenticity/verification_key.json',
    r1cs: 'artifacts/plonk/authenticity/authenticity_plonk.r1cs',
  },
};

// Universal SRS (Powers of Tau for PLONK on BLS12-381)
const UNIVERSAL_SRS = 'artifacts/common/pot20_bls12381.ptau';

async function prove(circuitName, inputFile, outputFile) {
  const circuit = CIRCUITS[circuitName];
  if (!circuit) {
    console.error(`Unknown circuit: ${circuitName}`);
    console.error(`Available: ${Object.keys(CIRCUITS).join(', ')}`);
    process.exit(1);
  }

  const wasmPath = join(__dirname, circuit.wasm);
  const zkeyPath = join(__dirname, circuit.zkey);

  if (!existsSync(wasmPath) || !existsSync(zkeyPath)) {
    console.error(`Circuit artifacts not found. Run 'node plonk-runner.js setup ${circuitName}' first.`);
    process.exit(1);
  }

  console.log(`[PLONK] Generating proof for ${circuitName}...`);
  const startTime = Date.now();

  const input = JSON.parse(readFileSync(inputFile, 'utf-8'));

  // Generate PLONK proof
  const { proof, publicSignals } = await snarkjs.plonk.fullProve(
    input,
    wasmPath,
    zkeyPath
  );

  const duration = Date.now() - startTime;
  console.log(`[PLONK] Proof generated in ${duration}ms`);

  const output = {
    protocol: 'plonk',
    curve: 'bls12381',
    proof,
    publicSignals,
    circuit: circuitName,
    timestamp: new Date().toISOString(),
    proving_time_ms: duration,
  };

  writeFileSync(outputFile, JSON.stringify(output, null, 2));
  console.log(`[PLONK] Proof written to ${outputFile}`);

  return output;
}

async function verify(circuitName, proofFile) {
  const circuit = CIRCUITS[circuitName];
  if (!circuit) {
    console.error(`Unknown circuit: ${circuitName}`);
    process.exit(1);
  }

  const vkeyPath = join(__dirname, circuit.vkey);

  if (!existsSync(vkeyPath)) {
    console.error(`Verification key not found: ${vkeyPath}`);
    process.exit(1);
  }

  console.log(`[PLONK] Verifying ${circuitName} proof...`);
  const startTime = Date.now();

  const proofData = JSON.parse(readFileSync(proofFile, 'utf-8'));
  const vkey = JSON.parse(readFileSync(vkeyPath, 'utf-8'));

  const isValid = await snarkjs.plonk.verify(
    vkey,
    proofData.publicSignals,
    proofData.proof
  );

  const duration = Date.now() - startTime;

  if (isValid) {
    console.log(`[PLONK] ✓ Proof is VALID (verified in ${duration}ms)`);
  } else {
    console.log(`[PLONK] ✗ Proof is INVALID`);
    process.exit(1);
  }

  return isValid;
}

async function setup(circuitName) {
  const circuit = CIRCUITS[circuitName];
  if (!circuit) {
    console.error(`Unknown circuit: ${circuitName}`);
    process.exit(1);
  }

  const r1csPath = join(__dirname, circuit.r1cs);
  const srsPath = join(__dirname, UNIVERSAL_SRS);
  const zkeyPath = join(__dirname, circuit.zkey);
  const vkeyPath = join(__dirname, circuit.vkey);

  // Ensure output directory exists
  const outDir = dirname(zkeyPath);
  if (!existsSync(outDir)) {
    mkdirSync(outDir, { recursive: true });
  }

  console.log(`[PLONK] Setting up ${circuitName} circuit...`);

  if (!existsSync(r1csPath)) {
    console.error(`R1CS file not found: ${r1csPath}`);
    console.error(`Compile the circuit first:`);
    console.error(`  circom circuits/plonk/${circuitName}_plonk.circom --r1cs --wasm -o artifacts/plonk/${circuitName}/`);
    process.exit(1);
  }

  if (!existsSync(srsPath)) {
    console.error(`Universal SRS not found: ${srsPath}`);
    console.error(`Download it:`);
    console.error(`  curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_20.ptau -o ${srsPath}`);
    process.exit(1);
  }

  // PLONK setup (universal - no toxic waste!)
  console.log(`[PLONK] Running PLONK setup (this may take a moment)...`);
  await snarkjs.plonk.setup(r1csPath, srsPath, zkeyPath);

  // Export verification key
  console.log(`[PLONK] Exporting verification key...`);
  const vkey = await snarkjs.zKey.exportVerificationKey(zkeyPath);
  writeFileSync(vkeyPath, JSON.stringify(vkey, null, 2));

  console.log(`[PLONK] Setup complete!`);
  console.log(`  zkey: ${zkeyPath}`);
  console.log(`  vkey: ${vkeyPath}`);
}

async function exportSolidityVerifier(circuitName, outputPath) {
  const circuit = CIRCUITS[circuitName];
  if (!circuit) {
    console.error(`Unknown circuit: ${circuitName}`);
    process.exit(1);
  }

  const zkeyPath = join(__dirname, circuit.zkey);

  if (!existsSync(zkeyPath)) {
    console.error(`zkey not found. Run setup first.`);
    process.exit(1);
  }

  console.log(`[PLONK] Exporting Solidity verifier...`);

  const templates = {
    plonk: await snarkjs.zKey.exportSolidityVerifier(zkeyPath),
  };

  writeFileSync(outputPath, templates.plonk);
  console.log(`[PLONK] Solidity verifier written to ${outputPath}`);
}

// CLI
const [, , command, ...args] = process.argv;

switch (command) {
  case 'prove':
    if (args.length < 3) {
      console.error('Usage: plonk-runner.js prove <circuit> <input.json> <output.json>');
      process.exit(1);
    }
    await prove(args[0], args[1], args[2]);
    break;

  case 'verify':
    if (args.length < 2) {
      console.error('Usage: plonk-runner.js verify <circuit> <proof.json>');
      process.exit(1);
    }
    await verify(args[0], args[1]);
    break;

  case 'setup':
    if (args.length < 1) {
      console.error('Usage: plonk-runner.js setup <circuit>');
      process.exit(1);
    }
    await setup(args[0]);
    break;

  case 'export-verifier':
    if (args.length < 2) {
      console.error('Usage: plonk-runner.js export-verifier <circuit> <output.sol>');
      process.exit(1);
    }
    await exportSolidityVerifier(args[0], args[1]);
    break;

  default:
    console.log(`
PLONK Proof Runner

Commands:
  prove <circuit> <input.json> <output.json>  Generate a PLONK proof
  verify <circuit> <proof.json>               Verify a PLONK proof
  setup <circuit>                             Setup circuit (one-time)
  export-verifier <circuit> <output.sol>      Export Solidity verifier

Circuits:
  age           Age verification (≥ min_age)
  authenticity  Document authenticity (Merkle inclusion)

Examples:
  node plonk-runner.js setup age
  node plonk-runner.js prove age samples/age-input.json proof.json
  node plonk-runner.js verify age proof.json

PLONK vs Groth16:
  - PLONK: Universal SRS, no toxic waste, larger proofs (~1KB)
  - Groth16: Circuit-specific setup, smaller proofs (~128 bytes)
`);
}

