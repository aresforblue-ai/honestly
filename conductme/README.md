# ConductMe - Human-Gated AI Orchestration

**World's first privacy-preserving AI orchestration platform with cryptographic proof of humanity.**

[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](../LICENSE)

ConductMe enables you to orchestrate multiple AI agents (Claude, GPT-4, local LLMs) with cryptographic guarantees that every action is authorized by a verified human. This prevents AI agents from operating autonomously without human oversight.

---

## 📋 Table of Contents

- [What Makes This World-Class](#-what-makes-this-world-class)
- [Architecture](#️-architecture)
- [Quick Start](#-quick-start)
- [Features](#-features)
- [Trust Bridge](#-trust-bridge)
- [Deployment](#-deployment)
- [Security](#-security)
- [Development](#-development)

---

## 🎯 What Makes This World-Class

### 1. **Privacy-Preserving Identity**
- Client-side Semaphore identity generation (secrets never leave browser)
- Zero-knowledge proofs for unlinkable actions
- Binding commitments that tie Honestly proofs to identities without revealing links

### 2. **Real AI Orchestration**
- Visual workflow builder (React Flow)
- Multi-agent coordination
- Action logging with cryptographic proofs
- Replay attack prevention via nullifiers

### 3. **Production-Ready Security**
- Privacy-preserving registration (no salt leakage)
- Semaphore group membership proofs
- Audit trails without identity exposure
- Rate limiting and input validation

### 4. **Beautiful, Modern UI**
- Glassmorphism design
- Smooth animations
- Command palette (⌘K)
- Responsive and accessible

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONDUCTME PLATFORM                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                              │
│   │   Frontend   │  Next.js 14 + React + Tailwind               │
│   │  (ConductMe) │  - AI Roster Management                      │
│   │              │  - Workflow Builder                          │
│   │              │  - Command Palette                           │
│   └──────┬───────┘                                              │
│          │                                                      │
│          │  ┌──────────────────────────────────────┐          │
│          └─▶│   Trust Bridge (Privacy-Preserving)   │          │
│             │  - Client-side identity generation    │          │
│             │  - Semaphore proofs                    │          │
│             │  - Binding commitments                 │          │
│             └──────────────┬─────────────────────────┘          │
│                            │                                    │
│                            ▼                                    │
│   ┌──────────────────────────────────────┐                     │
│   │   Honestly Backend                    │                     │
│   │  - ZK Proof Verification              │                     │
│   │  - Identity Registration              │                     │
│   │  - Action Logging                     │                     │
│   └──────────────────────────────────────┘                     │
│                                                                 │
│   ┌──────────────────────────────────────┐                     │
│   │   AI Agents                          │                     │
│   │  - Claude 3 Opus                    │                     │
│   │  - GPT-4 Turbo                      │                     │
│   │  - Local LLMs (Ollama)              │                     │
│   └──────────────────────────────────────┘                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

### Register Your Identity

```typescript
import { register } from '@/lib/trustBridge';

// After generating an Honestly ZK proof
const result = await register(
  honestlyProofCommitment,
  honestlyNullifier,
  honestlyProof
);

// Your identity is now registered (privacy-preserving)
```

### Orchestrate AI Actions

```typescript
import { Conductor, Actions } from '@conductme/trust-bridge';

const conductor = new Conductor({ groupId: 'conductme-main' });
const identity = await getOrCreateIdentity();

// Query Claude with human authorization
const action = Actions.query(
  'claude-3-opus',
  'Analyze this code for security issues'
);

const signedAction = await conductor.executeAction(identity, action);
// Returns: { action, proof, humanVerified: true }
```

## 📁 Project Structure

```
conductme/
├── bridge/              # Trust Bridge (Semaphore + ZK)
│   ├── src/
│   │   ├── client-identity.ts    # Client-side identity (PRIVACY)
│   │   ├── server-registration.ts # Server registration handler
│   │   ├── conductor.ts         # AI orchestration
│   │   └── identity.ts          # Semaphore identity
│   └── SECURITY.md      # Privacy-preserving design
│
├── core/                # Next.js frontend
│   ├── src/
│   │   ├── app/         # Pages and API routes
│   │   ├── components/  # UI components
│   │   └── lib/         # Utilities
│   └── README.md
│
└── src/                 # Main app (Next.js)
    ├── app/             # App router pages
    └── components/      # Shared components
```

## 🔐 Security Features

### Privacy-Preserving Registration

**CRITICAL**: Identity generation happens **exclusively client-side**:

```typescript
// ✅ SECURE - Client-side
const identity = await generateClientIdentity();
// Server never sees: trapdoor, nullifier, or salt

// ❌ INSECURE - Never do this
const identity = deriveFromHonestlyProof(proof, salt); // If salt sent to server
```

### Zero-Knowledge Actions

Every AI action requires a Semaphore proof that:
- Proves membership in verified humans group
- Doesn't reveal which human
- Can't be linked to other actions
- Prevents replay via nullifiers

## 🎨 UI Features

- **AI Roster**: Visual cards for each AI agent
- **Workflow Builder**: Drag-and-drop node editor (React Flow)
- **Command Palette**: Fast navigation (⌘K)
- **Status Indicators**: Real-time connection status
- **Gradient Design**: Modern glassmorphism aesthetic

## 📚 Documentation

- [Trust Bridge README](bridge/README.md) - Semaphore integration
- [Security Guide](bridge/SECURITY.md) - Privacy-preserving design
- [Agent Orchestration Guide](../docs/AGENT-ORCHESTRATION.md) - Complete guide

## 🔗 Integration with Honestly

ConductMe integrates seamlessly with Honestly:

1. **Human Verification**: Use Honestly's age/authenticity proofs
2. **Identity Bridge**: Map Honestly proof → Semaphore identity (privacy-preserving)
3. **Action Logging**: All actions can be anchored to L2 for audit

## 🏆 Production Ready

- ✅ Privacy-preserving identity (client-side generation)
- ✅ Real Semaphore proofs (not mocks)
- ✅ Error handling and loading states
- ✅ Type-safe (full TypeScript)
- ✅ Responsive design
- ✅ Accessible (WCAG compliant)

## 📄 License

MIT

---

**Built for the sovereign AI future.** 🚀
