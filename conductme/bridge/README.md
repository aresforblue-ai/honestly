# ConductMe Trust Bridge

**Human-gated AI orchestration via Semaphore identity proofs.**

The Trust Bridge connects Honestly's ZK-SNARK proofs to Semaphore's privacy-preserving identity system, enabling human-verified AI actions without revealing identity.

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│                        TRUST FLOW                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   1. PROVE HUMANITY (one-time)                                      │
│      ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│      │   Honestly  │────▶│  Groth16    │────▶│  Semaphore  │       │
│      │   ZK Proof  │     │  Verify     │     │  Identity   │       │
│      └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                      │              │
│                                                      ▼              │
│   2. JOIN GROUP                                                     │
│      ┌─────────────────────────────────────────────────┐           │
│      │            ConductMe Verified Humans            │           │
│      │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐   │           │
│      │  │ C │ │ C │ │ C │ │ C │ │ C │ │ C │ │ C │   │           │
│      │  └───┘ └───┘ └───┘ └───┘ └───┘ └───┘ └───┘   │           │
│      └─────────────────────────────────────────────────┘           │
│                          │                                          │
│                          ▼                                          │
│   3. AUTHORIZE AI ACTIONS (every action)                           │
│      ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│      │    Human    │────▶│  Semaphore  │────▶│  AI Action  │       │
│      │   Request   │     │   Proof     │     │  Executed   │       │
│      └─────────────┘     └─────────────┘     └─────────────┘       │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

C = Identity Commitment (public, unlinkable)
```

## Installation

```bash
cd conductme/bridge
npm install
npm run build
```

## Quick Start

```typescript
import { Conductor, Actions } from '@conductme/trust-bridge';

// 1. Initialize the Conductor
const conductor = new Conductor({
  groupId: 'conductme-mainnet',
  allowedAIs: ['claude-3-opus', 'gpt-4-turbo', 'midjourney'],
});

// 2. Register a human (after they prove via Honestly)
const honestlyProofCommitment = '0x123...'; // From age/authenticity proof
const identity = await conductor.registerHuman(honestlyProofCommitment, 'user-salt');

// 3. Execute AI actions with human authorization
const signedAction = await conductor.executeAction(
  identity,
  Actions.query('claude-3-opus', 'Analyze this code for security issues')
);

// 4. The action is now cryptographically tied to a verified human
console.log(signedAction.humanVerified);     // true
console.log(signedAction.proof.nullifierHash); // Unique, unlinkable identifier
```

## API Reference

### `createIdentity(entropy?: string)`

Create a new Semaphore identity.

```typescript
const identity = createIdentity();
// or with custom entropy
const identity = createIdentity('my-secret-seed');
```

### `deriveFromHonestlyProof(proofCommitment, salt)`

Derive a Semaphore identity from an Honestly ZK proof.

```typescript
const identity = deriveFromHonestlyProof(
  '0x123abc...', // Commitment from Honestly proof
  'random-salt'  // User-provided salt for privacy
);
```

### `Conductor`

The main orchestration class.

```typescript
const conductor = new Conductor({
  groupId: string,           // Unique group identifier
  treeDepth?: number,        // Merkle tree depth (default: 20)
  requireProofForActions?: boolean, // Enforce proofs (default: true)
  allowedAIs?: string[],     // Whitelist of AI IDs
});

// Methods
conductor.registerHuman(proofCommitment, salt) → ConductMeIdentity
conductor.executeAction(identity, action) → SignedAction
conductor.verifyAction(signedAction) → boolean
conductor.getGroupInfo() → { members: number, root: string }
conductor.export() → SerializedState
```

### `Actions`

Helper functions for creating AI actions.

```typescript
Actions.query(aiId, prompt)           // Ask an AI a question
Actions.generate(aiId, prompt, params) // Generate content
Actions.execute(aiId, params)          // Execute a task
Actions.vote(aiId, params)             // Cast a vote
Actions.sign(aiId, params)             // Sign something
```

## Security Properties

### **Sybil Resistance**
Each Honestly proof can only derive one identity. The commitment is deterministic from the proof, preventing multiple registrations.

### **Unlinkability**
Semaphore proofs are zero-knowledge. Actions cannot be linked to each other or to the original identity.

### **Double-Signaling Prevention**
Each action generates a unique nullifier hash. The same identity cannot perform the same action type twice in a time window.

### **Auditability**
All actions are logged with their proofs, enabling post-hoc verification without revealing identities.

## Architecture

```
conductme/bridge/
├── src/
│   ├── identity.ts    # Semaphore identity management
│   ├── conductor.ts   # AI orchestration with proofs
│   └── index.ts       # Public API exports
├── package.json
├── tsconfig.json
└── README.md
```

## Integration with Honestly

The Trust Bridge expects an Honestly proof commitment as input. This commitment comes from:

1. **Age Proof**: Proves age ≥ threshold without revealing birthdate
2. **Authenticity Proof**: Proves document inclusion in verified set

```bash
# Generate an Honestly proof
honestly share --age 18 --dob 1995 --output proof.json

# The proof.json contains a commitment field
# Use this to register with ConductMe
```

## Testing

```bash
npm test
```

## Why Semaphore?

Semaphore provides:
- **Privacy**: Zero-knowledge group membership proofs
- **Efficiency**: On-chain verification in ~200k gas
- **Flexibility**: Works with any group of identities
- **Maturity**: Battle-tested in production (e.g., Worldcoin)

## License

MIT
