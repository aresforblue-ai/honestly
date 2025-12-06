#!/usr/bin/env node
const fs = require("fs");
const path = require("path");
const crypto = require("crypto");
const snarkjs = require("snarkjs");

function loadArtifacts(circuit) {
  const base = path.join(__dirname, "artifacts", circuit);
  const wasmPath = path.join(base, `${circuit}.wasm`);
  const zkeyPath = path.join(base, `${circuit}_final.zkey`);
  const vkeyPath = path.join(base, "verification_key.json");
  if (!fs.existsSync(wasmPath) || !fs.existsSync(zkeyPath) || !fs.existsSync(vkeyPath)) {
    throw new Error(`Artifacts missing for circuit '${circuit}'. Build wasm/zkey/vkey first.`);
  }
  return {
    wasm: wasmPath,
    zkey: zkeyPath,
    vkey: JSON.parse(fs.readFileSync(vkeyPath, "utf8")),
  };
}

function hexToField(hex) {
  return BigInt("0x" + hex).toString();
}

function normalizeInput(circuit, input) {
  const out = { ...input };
  if (circuit === "age") {
    if (!out.salt) {
      out.salt = crypto.randomBytes(16).toString("hex");
    }
    if (out.documentHashHex) {
      out.documentHash = hexToField(out.documentHashHex);
      delete out.documentHashHex;
    }
  }
  if (circuit === "authenticity") {
    if (out.leafHex) {
      out.leaf = hexToField(out.leafHex);
      delete out.leafHex;
    }
    if (out.rootHex) {
      out.root = hexToField(out.rootHex);
      delete out.rootHex;
    }
    if (out.pathElementsHex) {
      out.pathElements = out.pathElementsHex.map(hexToField);
      delete out.pathElementsHex;
    }
  }
  return out;
}

async function prove(circuit, inputFile) {
  const artifacts = loadArtifacts(circuit);
  const input = JSON.parse(fs.readFileSync(inputFile, "utf8"));
  const normalized = normalizeInput(circuit, input);
  const { proof, publicSignals } = await snarkjs.groth16.fullProve(normalized, artifacts.wasm, artifacts.zkey);
  return { proof, publicSignals };
}

async function verify(circuit, proofFile) {
  const artifacts = loadArtifacts(circuit);
  const proofData = JSON.parse(fs.readFileSync(proofFile, "utf8"));
  return snarkjs.groth16.verify(artifacts.vkey, proofData.publicSignals, proofData.proof);
}

async function main() {
  const [command, circuit, ...rest] = process.argv.slice(2);
  if (!command || !circuit) {
    console.error("Usage: node snark-runner.js <prove|verify> <circuit> --input-file=...|--proof-file=...");
    process.exit(1);
  }
  try {
    if (command === "prove") {
      const inputFile = rest.find((a) => a.startsWith("--input-file="))?.split("=")[1];
      if (!inputFile) throw new Error("Missing --input-file");
      const result = await prove(circuit, inputFile);
      console.log(JSON.stringify(result, null, 2));
    } else if (command === "verify") {
      const proofFile = rest.find((a) => a.startsWith("--proof-file="))?.split("=")[1];
      if (!proofFile) throw new Error("Missing --proof-file");
      const ok = await verify(circuit, proofFile);
      console.log(ok);
      if (!ok) process.exit(1);
    } else {
      throw new Error("Unknown command");
    }
  } catch (err) {
    console.error(err.message || err);
    process.exit(1);
  }
}

main();


