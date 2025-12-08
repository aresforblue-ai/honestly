# honestly-cli

Command-line interface for generating and sharing ZK-SNARK proofs.

## Installation

```bash
cd cli
npm install
npm link  # Makes 'honestly' available globally
```

## Quick Start

```bash
# Generate an age proof (prove you're 18+)
honestly share --age 18 --dob 1995

# Generate with QR code for mobile sharing
honestly share --age 21 --dob 1990 --qr

# Save proof to file
honestly share --age 18 --dob 1995 --output my-proof.json

# Generate document authenticity proof
honestly share --document abc123def456 --qr

# Verify a proof from file
honestly verify --file my-proof.json

# Verify from share URL
honestly verify --url http://localhost:8000/vault/share/hns_abc123

# View system info
honestly info

# Run trusted setup (for circuit compilation)
honestly setup --circuit all
```

## Commands

### `share`

Generate and share a ZK proof.

| Option | Description |
|--------|-------------|
| `--age <min>` | Minimum age to prove (e.g., 18, 21) |
| `--dob <year>` | Year of birth (required for age proofs) |
| `--document <hash>` | Document hash for authenticity proofs |
| `--circuit <type>` | `groth16` (default) or `plonk` |
| `--output <file>` | Save proof to JSON file |
| `--qr` | Display QR code for sharing |
| `--api <url>` | API endpoint (default: http://localhost:8000) |

### `verify`

Verify a ZK proof.

| Option | Description |
|--------|-------------|
| `--url <url>` | Share URL to verify |
| `--file <path>` | Local proof file to verify |
| `--vk <path>` | Custom verification key file |

### `setup`

Run trusted setup for ZK circuits.

| Option | Description |
|--------|-------------|
| `--circuit <name>` | `age`, `authenticity`, or `all` |
| `--ptau <file>` | Custom Powers of Tau file |
| `--contribute` | Add entropy contribution to phase 2 |

### `info`

Display system information and available circuits.

## Examples

### Age Verification for a Bar/Club

```bash
# Prove you're 21+ without revealing exact age
honestly share --age 21 --dob 1998 --qr --output bar-proof.json

# Bouncer scans QR or visits URL to verify
honestly verify --url https://honestly.app/v/hns_abc123
```

### Document Authenticity for Legal Proceedings

```bash
# Hash your document first
HASH=$(sha256sum contract.pdf | cut -d' ' -f1)

# Generate proof that document exists in verified set
honestly share --document $HASH --circuit plonk --output legal-proof.json
```

### Batch Processing

```bash
# Generate proofs for multiple users
for dob in 1985 1990 1995 2000; do
  honestly share --age 18 --dob $dob --output "proof-${dob}.json"
done
```

## Proof Formats

### Groth16 (Default)

- **Curve:** BN128 (alt_bn128)
- **Proof size:** ~128 bytes
- **Verification:** ~2ms
- **Best for:** On-chain verification, small proofs

### PLONK (Experimental)

- **Curve:** BLS12-381
- **Proof size:** ~1KB
- **Verification:** ~10ms
- **Best for:** Universal trusted setup, future-proofing

## Integration

### With API

```bash
# Upload proof directly
honestly share --age 18 --dob 1995 --api https://api.honestly.app

# Verify via API
honestly verify --url https://api.honestly.app/vault/share/hns_xxx
```

### With Frontend

The generated share URLs work directly with the frontend verification page:

```
https://honestly.app/verify/hns_abc123
```

## Security Notes

1. **Never share your date of birth** - only the proof is transmitted
2. **Proofs are one-time use** - each generation creates a unique nullifier
3. **Share links expire** - default 24 hours, configurable
4. **Rate limited** - API prevents brute-force attacks

## Development

```bash
# Run without installing
node bin/honestly.js share --age 18 --dob 1995

# Debug mode
DEBUG=honestly* honestly share --age 18 --dob 1995
```

## License

MIT

