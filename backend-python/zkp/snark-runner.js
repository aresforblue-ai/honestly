#!/usr/bin/env node
/**
 * Thin CLI for Groth16 proving and verifying with snarkjs.
 * Reads JSON from stdin by default (or --input-file/--proof-file).
 */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { Command } from "commander";
import { groth16 } from "snarkjs";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const circuits = {
  age: {
    name: "age",
    wasm: path.join(__dirname, "artifacts", "age", "age_js", "age.wasm"),
    zkey: path.join(__dirname, "artifacts", "age", "age_final.zkey"),
    vkey: path.join(__dirname, "artifacts", "age", "verification_key.json"),
    publicSignals: ["minAgeOut", "referenceTsOut", "documentHashOut", "commitment", "nullifier"],
  },
  authenticity: {
    name: "authenticity",
    wasm: path.join(__dirname, "artifacts", "authenticity", "authenticity_js", "authenticity.wasm"),
    zkey: path.join(__dirname, "artifacts", "authenticity", "authenticity_final.zkey"),
    vkey: path.join(__dirname, "artifacts", "authenticity", "verification_key.json"),
    publicSignals: ["rootOut", "leafOut", "epochOut", "nullifier"],
  },
};

async function readJsonMaybe(filePath) {
  if (filePath) {
    return JSON.parse(fs.readFileSync(filePath, "utf8"));
  }
  const stdin = fs.readFileSync(0, "utf8");
  return JSON.parse(stdin);
}

function assertExists(label, p) {
  if (!fs.existsSync(p)) {
    throw new Error(`${label} not found at ${p}. Build/setup the circuit first.`);
  }
}

function mapNamed(publicSignals, names) {
  const out = {};
  names.forEach((n, i) => {
    out[n] = publicSignals[i];
  });
  return out;
}

const program = new Command();

program
  .command("prove")
  .argument("<circuit>", "circuit name (age|authenticity)")
  .option("--input-file <path>", "JSON input file (defaults to stdin)")
  .action(async (circuitName, options) => {
    const circuit = circuits[circuitName];
    if (!circuit) {
      console.error(`Unknown circuit: ${circuitName}`);
      process.exit(1);
    }

    assertExists("wasm", circuit.wasm);
    assertExists("zkey", circuit.zkey);

    try {
      const input = await readJsonMaybe(options.inputFile);
      const res = await groth16.fullProve(input, circuit.wasm, circuit.zkey);
      const namedSignals = mapNamed(res.publicSignals, circuit.publicSignals);

      const payload = {
        circuit: circuit.name,
        proof: res.proof,
        publicSignals: res.publicSignals,
        namedSignals,
      };

      console.log(JSON.stringify(payload, null, 2));
    } catch (err) {
      console.error(`Proving failed: ${err.message || err}`);
      process.exit(1);
    }
  });

program
  .command("verify")
  .argument("<circuit>", "circuit name (age|authenticity)")
  .option("--proof-file <path>", "proof bundle file (defaults to stdin)")
  .action(async (circuitName, options) => {
    const circuit = circuits[circuitName];
    if (!circuit) {
      console.error(`Unknown circuit: ${circuitName}`);
      process.exit(1);
    }

    assertExists("verification key", circuit.vkey);

    try {
      const bundle = await readJsonMaybe(options.proofFile);
      const vkey = JSON.parse(fs.readFileSync(circuit.vkey, "utf8"));
      const ok = await groth16.verify(vkey, bundle.publicSignals, bundle.proof);

      console.log(JSON.stringify({ circuit: circuit.name, verified: ok }, null, 2));
      if (!ok) {
        process.exit(1);
      }
    } catch (err) {
      console.error(`Verification failed: ${err.message || err}`);
      process.exit(1);
    }
  });

program.parseAsync().catch((err) => {
  console.error(err);
  process.exit(1);
});

