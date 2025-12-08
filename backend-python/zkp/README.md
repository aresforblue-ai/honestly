# Honestly ZK-SNARK kit

Groth16 + Circom/snarkjs pipeline for fast (<1s) verification and QR-friendly payloads. Circuits cover:

- `age`: prove birth timestamp is at least `minAge` years before a reference timestamp, and bind to the document hash via a Poseidon commitment.
- `authenticity`: Poseidon Merkle inclusion proof for a document hash.
- `age_level3` / `Level3Inequality`: extended/nullifier-aware variants (rebuild artifacts if you change these circuits).

## Layout

- `circuits/age.circom`, `circuits/authenticity.circom`
- `snark-runner.js`: thin CLI for proving/verifying (Node + snarkjs + circomlibjs)
- `artifacts/`: place compiled wasm/zkey/vkey outputs here
- `package.json`: dependencies + helper scripts

## Quick start (age + authenticity)

```bash
cd backend-python/zkp
npm install
# Get a ptau (example: powers of tau 16); adjust size to your tree depth/constraints
curl -L https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau

# Build circuits
npx circom circuits/age.circom --r1cs --wasm --sym -o artifacts/age
npx circom circuits/authenticity.circom --r1cs --wasm --sym -o artifacts/authenticity

# Groth16 setup
npx snarkjs groth16 setup artifacts/age/age.r1cs artifacts/common/pot16_final.ptau artifacts/age/age_0000.zkey
npx snarkjs zkey contribute artifacts/age/age_0000.zkey artifacts/age/age_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/age/age_final.zkey artifacts/age/verification_key.json

# Repeat for authenticity
npx snarkjs groth16 setup artifacts/authenticity/authenticity.r1cs artifacts/common/pot16_final.ptau artifacts/authenticity/authenticity_0000.zkey
npx snarkjs zkey contribute artifacts/authenticity/authenticity_0000.zkey artifacts/authenticity/authenticity_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/authenticity/authenticity_final.zkey artifacts/authenticity/verification_key.json
```

## Rebuild (all circuits, including nullifier/level3)

You can use npm scripts already defined in `package.json`:

```bash
cd backend-python/zkp
npm install
# Download ptau once (mirror that works in CI)
curl -L https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau

# Compile
npm run build:age
npm run build:auth
npm run build:age-level3
npm run build:inequality-level3

# Groth16 setup
npm run setup:age
npm run setup:auth
npm run setup:age-level3
npm run setup:inequality-level3

# Contribute + export vkeys
npm run contribute:age && npm run vk:age
npm run contribute:auth && npm run vk:auth
npm run contribute:age-level3 && npm run vk:age-level3
npm run contribute:inequality-level3 && npm run vk:inequality-level3
npm run hash:vkeys
python scripts/verify_key_integrity.py   # refresh INTEGRITY.json + *.sha256
```

Artifacts land under `artifacts/<circuit>/` (wasm/zkey/vkey). Regenerate proofs after rebuilding.

Alternatively, from repo root:

```bash
make zkp-rebuild
```

## Prove/verify via runner

```bash
# Prove (reads JSON from file/stdin)
node snark-runner.js prove age --input-file ./samples/age-input.sample.json > ./samples/age-proof.sample.json

# Verify
node snark-runner.js verify age --proof-file ./samples/age-proof.sample.json
```

Input format for age (all numbers as decimal strings):

```json
{
  "birthTs": "631152000",          // private
  "referenceTs": "1733443200",     // public (usually issuance time)
  "minAge": "18",                  // public
  "documentHashHex": "ab12...ff",  // public Poseidon input (hex SHA-256)
  "salt": "1234567890123456789"    // private; optional (auto-generated if missing)
}
```

Authenticity input (Poseidon Merkle, depth 16 by default):

```json
{
  "leafHex": "ab12...ff",
  "rootHex": "cd34...ee",
  "pathElementsHex": ["..."],   // length = DEPTH
  "pathIndices": [0,1,...]      // 0 = leaf on left, 1 = leaf on right
}
```

## Poseidon hashing helper

To match circuit commitments/nullifiers off-chain:

```bash
# CSV inputs (decimal or 0x)
node poseidon-hash.js --inputs 1,2,3

# Or from stdin JSON array
echo '["0x01","0x02","0x03"]' | node poseidon-hash.js
```

## Notes

- Circuits use Poseidon for constraint efficiency.
- Public signals order matters; the runner returns both the raw `publicSignals` array and a named map.
- If artifacts are missing, the runner returns a clear error directing you to build them.
- Sample inputs/proofs are in `samples/` for quick smoke tests. Replace placeholder vk/proofs with real generated ones for production.
- Heavy circuits (level3) may need a larger Node heap during build/proving: set `NODE_OPTIONS="--max-old-space-size=8192"`; Windows is more likely to need this.
- Property tests: from `backend-python`, run `ZK_TESTS=1 pytest tests/test_zk_properties.py -v` after rebuilding artifacts.
