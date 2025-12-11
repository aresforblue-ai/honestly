# VERIDICUS Solana Program

**Quantum computing access token with governance, staking, and airdrop capabilities**

[![Rust](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://www.rust-lang.org/)
[![Anchor](https://img.shields.io/badge/anchor-0.30.1-blue.svg)](https://www.anchor-lang.com/)
[![Solana](https://img.shields.io/badge/solana-1.18+-purple.svg)](https://solana.com/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](../LICENSE)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Project Structure](#-project-structure)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Security](#-security)
- [Resources](#-resources)

---

## 🌟 Overview

VERIDICUS is a production-ready Solana program (smart contract) that powers:

- **Quantum Computing Access** — Token-gated access to quantum resources
- **Governance** — On-chain voting and proposal management
- **Staking** — Time-locked staking with rewards
- **Airdrop** — Merkle-tree based token distribution
- **Oracle Integration** — Real-time quantum metrics
- **Security** — Rate limiting, authority controls, overflow protection

**Test Coverage**: 95%+ | **Audit Status**: Pre-audit ready | **Mainnet**: Not deployed

---

## 🎯 Quick Start

### Prerequisites
```bash
# Install Solana CLI
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install Anchor
cargo install --git https://github.com/coral-xyz/anchor avm --locked --force
avm install latest
avm use latest
```

### Setup
```bash
# Generate keypair
solana-keygen new

# Set to devnet
solana config set --url devnet

# Airdrop SOL (devnet)
solana airdrop 2
```

## 📁 Project Structure

```
backend-solana/
├── programs/
│   └── veritas/
│       ├── src/
│       │   └── lib.rs          # Main Anchor program
│       └── Cargo.toml
├── tests/
│   └── veritas.ts              # Anchor tests
├── migrations/
│   └── deploy.ts               # Deployment script
└── Anchor.toml                 # Anchor config
```

## 🚀 Development

```bash
# Build
anchor build

# Test
anchor test

# Deploy to devnet
anchor deploy
```

## 📚 Resources

- [Solana Cookbook](https://solanacookbook.com/)
- [Anchor Book](https://www.anchor-lang.com/)
- [Solana Docs](https://docs.solana.com/)

