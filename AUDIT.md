# Audit Readiness (ZK + API)

This doc packages the essentials for an external cryptographic/security audit (e.g., Trail of Bits, Zellic).

**Commit**: `2e3b5c55113119814da3fd9bac3a5058a89f39dc`

## Scope

- ZK circuits: `age`, `authenticity`, `age_level3`, `Level3Inequality` (Groth16, bn128/BLS12-381, Poseidon hash, depth 16).
- Prover/Verifier: `backend-python/zkp/snark-runner.js` (snarkjs), verification keys served at `/zkp/artifacts/...` with ETag/sha256 integrity gates (`INTEGRITY.json`).
- API surface: FastAPI REST `/vault/*`, GraphQL `/graphql`, static `/zkp/artifacts`.
- Data store: Neo4j (minimal mode), optional Kafka/Postgres disabled in `docker-compose.min.yml`.

## Artifact Checksums

### Powers of Tau

| File | SHA256 |
|------|--------|
| `artifacts/common/pot16_final.ptau` | `1c401abb57c9ce531370f3015c3e75c0892e0f32b8b1e94ace0f6682d9695922` |

Verify against source:

```bash
curl -L https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_16.ptau | sha256sum
```

### Age Circuit

| File | SHA256 |
|------|--------|
| `artifacts/age/age.r1cs` | `e0404cc5146d5b7aee5017ecb7850461763e8ea7142948ac0e13747e28e0fe59` |
| `artifacts/age/age_final.zkey` | `2b231ea59185f9b9d17dde708d8ffbf37529e822d397cd13c923a826e6853f68` |
| `artifacts/age/verification_key.json` | `63ce40cea4c6b53aee89c4c96bab4dd2a27150b0d6f4a20de7e8aa412140fa72` |

**Public Signals Order**: `["minAgeOut", "referenceTsOut", "documentHashOut", "commitment", "nullifier"]`

### Authenticity Circuit

| File | SHA256 |
|------|--------|
| `artifacts/authenticity/authenticity.r1cs` | `f00d54b1a1445d2a541bd292694d3ed78501e3cdc765bb878f0c1c29fb30bd45` |
| `artifacts/authenticity/authenticity_final.zkey` | `7552e2d800781616935961352af83ebc4bc3313b6297b504a348fd4c09094d1d` |
| `artifacts/authenticity/verification_key.json` | `c39181571c3d95f7f9cee32064e1c5284bd55697dc47f2693c303b77a2c4a57d` |

**Public Signals Order**: `["rootOut", "leafOut", "epochOut", "nullifier"]`

### Level3 Age Circuit

| File | SHA256 |
|------|--------|
| `artifacts/age_level3/age_level3.r1cs` | `0f8c1df677ce234a403d31a85e44531153ad4cfc61ceefe0d866a02845f6da60` |
| `artifacts/age_level3/age_level3_final.zkey` | `46f6780e75a11f1ef2acefaf325f9e8912d58b1c0df2cbd34e3e9cdf02522763` |
| `artifacts/age_level3/verification_key.json` | `6069330dc86ebd92a9cffa27baaf5c9ad4a2a89b8da0c16157950ae5484efa1b` |

**Public Signals Order**: `["referenceTs", "minAge", "userID", "documentHash", "nullifier"]`

### Level3 Inequality Circuit

| File | SHA256 |
|------|--------|
| `artifacts/level3_inequality/Level3Inequality.r1cs` | `997ef751a1203383a64ef6bd29ef2c35ccbfa1070f24ddfdacb3ace757ab7811` |
| `artifacts/level3_inequality/Level3Inequality_final.zkey` | `a1f7d6cdc98d7578f043b0682ff7db014792c3cd5c41d251d63bdbc3618e5088` |
| `artifacts/level3_inequality/verification_key.json` | `71405fec2cb20f87505462c2b37ac313d69d3047cffc53dba1cd592b382fe5dd` |

**Public Signals Order**: see `backend-python/zkp/circuits/Level3Inequality.circom`

### Integrity Manifest

| File | SHA256 |
|------|--------|
| `artifacts/INTEGRITY.json` | `56543a1557715f15900c9a0ff9071fd23de304bbaf68e05b8b48247d3972d63f` |

**Hosting**: vkeys served at `/zkp/artifacts/{age,authenticity,age_level3,level3_inequality}/verification_key.json` (enable gzip/cache at proxy).

## Sample Proofs

| File | SHA256 |
|------|--------|
| `samples/age-input.sample.json` | `39ab641a6fe0872ba71cf7da051f483c46cf49b5e0671d5a0f1a0e9f907b50ca` |
| `samples/authenticity-input.sample.json` | `93338dd0c33888c2f746aa7cef9a2909f8e8aac6e6e442946ed3a6d7fa990206` |
| `samples/authenticity-proof.sample.json` | `68b94cf70ca1608e2d2d8d3dce20cc3c6a09a38a9af137c2f556acbf8a5ac4eb` |

Generate proofs:

```bash
cd backend-python/zkp
export NODE_OPTIONS="--max-old-space-size=8192"
node snark-runner.js prove age --input-file samples/age-input.sample.json > samples/age-proof.sample.json
node snark-runner.js verify age --proof-file samples/age-proof.sample.json
node snark-runner.js prove authenticity --input-file samples/authenticity-input.sample.json > samples/authenticity-proof.sample.json
node snark-runner.js verify authenticity --proof-file samples/authenticity-proof.sample.json
```

## Reproducible ZK Build

From `backend-python/zkp`:

```bash
npm install
make zkp-rebuild
# or on Windows: ./rebuild-circuits.ps1 -All

# Generate integrity manifest
python scripts/verify_key_integrity.py

# For level3 circuits (memory-intensive):
export NODE_OPTIONS="--max-old-space-size=8192"
```

CI: `.github/workflows/zkp.yml` rebuilds circuits, regenerates integrity hashes, and runs ZK property tests on circuit changes.

## Computing Checksums

**Linux/macOS**:

```bash
cd backend-python/zkp
sha256sum artifacts/common/pot16_final.ptau
sha256sum artifacts/age/age.r1cs
sha256sum artifacts/age/age_final.zkey
sha256sum artifacts/age/verification_key.json
```

**Windows (PowerShell)**:

```powershell
cd backend-python\zkp
Get-FileHash artifacts\common\pot16_final.ptau -Algorithm SHA256
Get-FileHash artifacts\age\age.r1cs -Algorithm SHA256
Get-FileHash artifacts\age\age_final.zkey -Algorithm SHA256
Get-FileHash artifacts\age\verification_key.json -Algorithm SHA256
```

## Environment and Security Posture

- **Minimal stack**: `docker-compose.min.yml` (API + Neo4j + frontend + ConductMe Core). Kafka/Postgres disabled.
- **CORS**: `ALLOWED_ORIGINS` must be set; `STRICT_CORS=true` to fail fast if unset; `ENABLE_CORS=true`.
- **Auth**: JWT/OIDC (JWKS RS/ES) with HS256 fallback; API key for `/ai/*`; bundle endpoint is public but rate-limited.
- **Rate limiting**: configure Redis-backed limiter in prod; defaults cover `/vault/share` and `/zkp/artifacts`. Tune via `RATE_LIMIT_WINDOW`, `RATE_LIMIT_MAX`, `RATE_LIMIT_PATHS`.
- **Security headers**: `ENABLE_SECURITY_HEADERS=true` adds nosniff, frame deny, referrer policy, HSTS (HTTPS only).
- **Static vkeys**: served at `/zkp/artifacts/...` (cacheable; gzip at proxy) with integrity checks (`INTEGRITY.json`).
- **Vault key**: loaded via KMS/env/file; `ALLOW_GENERATED_VAULT_KEY=true` only for dev.

## Verification Flow

- **Backend**: proofs can be verified via snark-runner (Node) callable from Python; API currently serves bundles and vkeys, with verification typically client-side.
- **Frontend**: snarkjs verify using fetched vkey and bundle `{proof, publicSignals, circuit}`; expects public signal order above.

## DAST / Negative Tests

ZAP baseline:

```bash
docker run --rm -t owasp/zap2docker-stable zap-baseline.py -t https://staging.yourdomain -r zap-baseline.html
```

ZAP full:

```bash
docker run --rm -t -v $(pwd):/zap/wrk owasp/zap2docker-stable zap-full-scan.py -t https://staging.yourdomain -r zap-full.html
```

Abuse cases:

- Malformed JSON → expect 400, no stack trace.
- Rate-limit bypass on `/vault/share/{token}/bundle` → expect 429 and recovery, no resource exhaustion.
- Headers: `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security` (HTTPS).

## Performance (target p99 < 200ms)

k6 script at `tests/perf/k6-load.js`:

```bash
BASE_URL=https://staging.yourdomain AUTH="Bearer ..." k6 run tests/perf/k6-load.js
```

Scenarios: ramp to 100 VUs (5m hold), spike 10→500 VUs. Thresholds: `p(99)<200ms`, error rate <1%.

Capture and attach k6 summary (p95/p99, errors). Optimize vkey caching/bundle size if over budget.

## Chaos Drills

- Kill Redis (rate limiter) during load; expect graceful 429/503 and automatic recovery on return.
- Kill Neo4j; expect health/readiness to fail, dependent routes 503, and auto-reconnect when back.

## Deliverables to Auditors

- This `AUDIT.md`
- Checksums of ptau/r1cs/zkey/vkey (above)
- Sample valid proofs + public signals per circuit
- Environment config (CORS, auth, rate limits)
- API surface list and versions (circom/snarkjs/npm lockfile)
- k6 report, ZAP report
- Commit hash: `2e3b5c55113119814da3fd9bac3a5058a89f39dc`
