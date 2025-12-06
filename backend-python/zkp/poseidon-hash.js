#!/usr/bin/env node
/**
 * Poseidon hash helper for aligning off-chain hashes with circuits.
 * Usage:
 *   node poseidon-hash.js --inputs 1,2,3
 *   echo '[ "0x01", "0x02", "0x03" ]' | node poseidon-hash.js
 */
import { poseidon } from "circomlibjs";
import { Command } from "commander";
import fs from "fs";

const program = new Command();

function parseInputs(str) {
  return str
    .split(",")
    .map((v) => v.trim())
    .filter(Boolean)
    .map(toBigInt);
}

function toBigInt(v) {
  if (typeof v === "bigint") return v;
  if (typeof v === "number") return BigInt(v);
  if (typeof v === "string") {
    const s = v.trim();
    if (s.startsWith("0x") || s.startsWith("0X")) return BigInt(s);
    return BigInt(s);
  }
  throw new Error(`Unsupported input value: ${v}`);
}

function toHex(bi) {
  return "0x" + bi.toString(16);
}

program
  .option("--inputs <csv>", "Comma-separated inputs (decimal or 0x hex)")
  .option("--stdin", "Read JSON array from stdin (alternative to --inputs)")
  .action(async (opts) => {
    let values;
    if (opts.stdin) {
      const data = fs.readFileSync(0, "utf8");
      values = JSON.parse(data).map(toBigInt);
    } else if (opts.inputs) {
      values = parseInputs(opts.inputs);
    } else {
      console.error("Provide --inputs \"a,b,c\" or --stdin with JSON array");
      process.exit(1);
    }

    const res = poseidon(values);
    const hex = toHex(res);

    const output = {
      inputs: values.map((v) => v.toString()),
      poseidon: hex,
    };

    console.log(JSON.stringify(output, null, 2));
  });

program.parseAsync().catch((err) => {
  console.error(err);
  process.exit(1);
});


