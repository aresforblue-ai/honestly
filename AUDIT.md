# Audit Readiness (ZK + API)

This doc packages the essentials for an external cryptographic/security audit (e.g., Trail of Bits, Zellic).

## Scope
- ZK circuits: `age`, `authenticity` (Groth16, bn128/BLS12-381, Poseidon hash, depth 16).
- Prover/Verifier: `backend-python/zkp/snark-runner.js` (snarkjs), verification keys served at `/zkp/artifacts/...`.
- API surface: FastAPI REST `/vault/*`, GraphQL `/graphql`, static `/zkp/artifacts`.
- Data store: Neo4j (minimal mode), optional Kafka/Postgres disabled in `docker-compose.min.yml`.

## Artifact fingerprints (fill before audit)

### Computing SHA256 Checksums

**On Linux/macOS**:
```bash
cd backend-python/zkp
sha256sum artifacts/common/pot16_final.ptau
sha256sum artifacts/age/age.r1cs
sha256sum artifacts/age/age_final.zkey
sha256sum artifacts/age/verification_key.json
sha256sum artifacts/authenticity/authenticity.r1cs
sha256sum artifacts/authenticity/authenticity_final.zkey
sha256sum artifacts/authenticity/verification_key.json
```

**On Windows (PowerShell)**:
```powershell
cd backend-python\zkp
Get-FileHash artifacts\common\pot16_final.ptau -Algorithm SHA256
Get-FileHash artifacts\age\age.r1cs -Algorithm SHA256
Get-FileHash artifacts\age\age_final.zkey -Algorithm SHA256
Get-FileHash artifacts\age\verification_key.json -Algorithm SHA256
Get-FileHash artifacts\authenticity\authenticity.r1cs -Algorithm SHA256
Get-FileHash artifacts\authenticity\authenticity_final.zkey -Algorithm SHA256
Get-FileHash artifacts\authenticity\verification_key.json -Algorithm SHA256
```

**Using Node.js**:
```bash
cd backend-python/zkp
node -e "const fs = require('fs'); const crypto = require('crypto'); const files = ['artifacts/common/pot16_final.ptau', 'artifacts/age/age.r1cs', 'artifacts/age/age_final.zkey', 'artifacts/age/verification_key.json', 'artifacts/authenticity/authenticity.r1cs', 'artifacts/authenticity/authenticity_final.zkey', 'artifacts/authenticity/verification_key.json']; files.forEach(f => { try { const data = fs.readFileSync(f); const hash = crypto.createHash('sha256').update(data).digest('hex'); console.log(`${f}: ${hash}`); } catch(e) { console.log(`${f}: FILE_NOT_FOUND`); } });"
```

### Artifact Checksums

**⚠️ IMPORTANT**: After rebuilding circuits (see `backend-python/zkp/REBUILD_CIRCUITS.md`), compute and fill in these checksums.

**Powers of Tau**:
- `artifacts/common/pot16_final.ptau` — SHA256: `<fill after build>`
  - **Expected**: Should match Hermez Powers of Tau ceremony output
  - **Verify**: `curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau | sha256sum`

**Age Circuit**:
- `artifacts/age/age.r1cs` — SHA256: `<fill after build>`
- `artifacts/age/age_final.zkey` — SHA256: `<fill after build>`
- `artifacts/age/verification_key.json` — SHA256: `<fill after build>`
- **Public Signals Order**: `["minAgeOut", "referenceTsOut", "documentHashOut", "commitment", "nullifier"]`

**Authenticity Circuit**:
- `artifacts/authenticity/authenticity.r1cs` — SHA256: `<fill after build>`
- `artifacts/authenticity/authenticity_final.zkey` — SHA256: `<fill after build>`
- `artifacts/authenticity/verification_key.json` — SHA256: `<fill after build>`
- **Public Signals Order**: `["rootOut", "leafOut", "epochOut", "nullifier"]`

**Hosting**: vkeys served at `/zkp/artifacts/{age,authenticity}/verification_key.json` (enable gzip/cache at proxy).

### Sample Proof Checksums

After generating sample proofs (see below), compute checksums:

```bash
# Age proof
sha256sum artifacts/age/age-proof.sample.json
# Expected: <fill after generation>

# Authenticity proof
sha256sum artifacts/authenticity/authenticity-proof.sample.json
# Expected: <fill after generation>
```

**Note**: Replace `<fill after build>` and `<fill after generation>` with actual checksums before audit submission.

## Reproducible ZK build
From `backend-python/zkp`:
```bash
npm install
curl -L https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_16.ptau -o artifacts/common/pot16_final.ptau

npx circom circuits/age.circom --r1cs --wasm --sym -o artifacts/age
npx circom circuits/authenticity.circom --r1cs --wasm --sym -o artifacts/authenticity

npx snarkjs groth16 setup artifacts/age/age.r1cs artifacts/common/pot16_final.ptau artifacts/age/age_0000.zkey
npx snarkjs zkey contribute artifacts/age/age_0000.zkey artifacts/age/age_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/age/age_final.zkey artifacts/age/verification_key.json

npx snarkjs groth16 setup artifacts/authenticity/authenticity.r1cs artifacts/common/pot16_final.ptau artifacts/authenticity/authenticity_0000.zkey
npx snarkjs zkey contribute artifacts/authenticity/authenticity_0000.zkey artifacts/authenticity/authenticity_final.zkey -n "local"
npx snarkjs zkey export verificationkey artifacts/authenticity/authenticity_final.zkey artifacts/authenticity/verification_key.json
```

## Sample proofs
Run:
```bash
node snark-runner.js prove age --input-file ./samples/age-input.sample.json > ./samples/age-proof.sample.json
node snark-runner.js verify age --proof-file ./samples/age-proof.sample.json
node snark-runner.js prove authenticity --input-file ./samples/authenticity-input.sample.json > ./samples/authenticity-proof.sample.json
node snark-runner.js verify authenticity --proof-file ./samples/authenticity-proof.sample.json
```

Replace placeholder vkeys/proofs with generated ones before audit. Include checksums of `ptau`, `r1cs`, `zkey`, `verification_key.json`, and sample proofs.

### Sample Proof Checksums (fill after generation)

After running the proof generation commands above:

**Age Proof**:
- `samples/age-proof.sample.json` — SHA256: `<fill after generation>`
- `samples/age-input.sample.json` — SHA256: `<fill after generation>`

**Authenticity Proof**:
- `samples/authenticity-proof.sample.json` — SHA256: `<fill after generation>`
- `samples/authenticity-input.sample.json` — SHA256: `<fill after generation>`

Public signal order:
- age: `[minAgeOut, referenceTsOut, documentHashOut, commitment]`
- authenticity: `[rootOut, leafOut]`

## Environment and security posture (audit deployment)
- Minimal stack: `docker-compose.min.yml` (API + Neo4j + frontend). Kafka/Postgres disabled.
- CORS: `ALLOWED_ORIGINS` must be set; `STRICT_CORS=true` to fail fast if unset; `ENABLE_CORS=true`.
- Auth: replace mock user with JWT/OIDC for protected routes; bundle endpoint is public but rate-limited.
- Rate limiting: configure Redis-backed limiter in prod; defaults cover `/vault/share` and `/zkp/artifacts`. Tune via `RATE_LIMIT_WINDOW`, `RATE_LIMIT_MAX`, `RATE_LIMIT_PATHS`.
- Security headers: `ENABLE_SECURITY_HEADERS=true` adds nosniff, frame deny, referrer policy, HSTS (HTTPS only).
- Static vkeys: served at `/zkp/artifacts/...` (cacheable; gzip at proxy).

## Verification flow
- Backend: proofs can be verified via snark-runner (Node) callable from Python; API currently serves bundles and vkeys, with verification typically client-side.
- Frontend: snarkjs verify using fetched vkey and bundle `{proof, publicSignals, circuit}`; expects public signal order above.

## DAST / negative tests
- ZAP baseline:
  ```bash
  docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t https://staging.yourdomain -r zap-baseline.html
  ```
- ZAP full:
  ```bash
  docker run --rm -t -v $(pwd):/zap/wrk owasp/zap2docker-stable zap-full-scan.py -t https://staging.yourdomain -r zap-full.html
  ```
- Abuse cases:
  - Malformed JSON → expect 400, no stack trace.
  - Rate-limit bypass on `/vault/share/{token}/bundle` → expect 429 and recovery, no resource exhaustion.
  - Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security` (HTTPS).

## Performance (target p99 < 200ms)
- k6 script at `tests/perf/k6-load.js`:
  ```bash
  BASE_URL=https://staging.yourdomain AUTH="Bearer ..." k6 run tests/perf/k6-load.js
  ```
  Scenarios: ramp to 100 VUs (5m hold), spike 10→500 VUs. Thresholds: `p(99)<200ms`, error rate <1%.
- Capture and attach k6 summary (p95/p99, errors). Optimize vkey caching/bundle size if over budget.

## Chaos drills
- Kill Redis (rate limiter) during load; expect graceful 429/503 and automatic recovery on return.
- Kill Neo4j; expect health/readiness to fail, dependent routes 503, and auto-reconnect when back.

## Audit handoff bundle
- This `AUDIT.md`.
- Checksums file for ptau/r1cs/zkey/vkey and sample proofs.
- Sample proofs + public signals (valid).
- k6 report, ZAP report.
- Lockfiles (package-lock/package.json versions), commit hash.

## Environment and security
- CORS: `ALLOWED_ORIGINS` required; `STRICT_CORS=true` to fail fast if unset.
- Rate limiting: public bundle endpoint guarded; configure Redis-backed limiter for production.
- Headers: `ENABLE_SECURITY_HEADERS=true` adds no-sniff, frame deny, referrer policy, HSTS (https only).
- Auth: replace mock user with JWT/OIDC in production.
- Static vkeys: served at `/zkp/artifacts/...` (cacheable, gzip recommended at proxy).

## Load test (target p99 < 200ms)
k6 script at `tests/perf/k6-load.js`:
```bash
BASE_URL=https://staging.yourdomain AUTH="Bearer ..." k6 run tests/perf/k6-load.js
```
Scenarios:
- Ramp: to 100 VUs, hold 5m.
- Spike: 10 -> 500 VUs instantly at t=9m.
Thresholds: `p(99)<200ms`, error rate <1%.

## ZAP / DAST
Baseline:
```bash
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t https://staging.yourdomain -r zap-baseline.html
```
Full:
```bash
docker run --rm -t -v $(pwd):/zap/wrk owasp/zap2docker-stable zap-full-scan.py -t https://staging.yourdomain -r zap-full.html
```

## Chaos drills
- Kill Redis (rate limiter) during load; expect graceful 429/503, auto-recovery when back.
- Kill Neo4j; expect health/readiness to show down, 503 on dependent routes, auto-reconnect on return.

## Deliverables to auditors
- This AUDIT.md
- Checksums of ptau/r1cs/zkey/vkey
- Sample valid proofs + public signals per circuit
- Environment config (CORS, auth, rate limits)
- API surface list and versions (circom/snarkjs/npm lockfile)

