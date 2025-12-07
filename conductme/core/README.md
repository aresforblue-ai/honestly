# ConductMe Core

The conductor for your local AI swarm. Orchestrate multiple AI models with cryptographic proof of humanity.

## Quick Start

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Open http://localhost:3000
```

## Features

- **AI Roster**: Manage your collection of AI models with status/version
- **Visual Cards**: At-a-glance health and state for each model
- **Command Palette**: Fast navigation and actions for power users
- **Trust Bridge Ready**: Semaphore/ZK integration path for proof-of-humanity
- **Type Safety**: Full TypeScript
- **Modern Stack**: Next.js 14, Tailwind CSS, Radix UI

## Architecture

This is the frontend core of ConductMe. It connects to:

- **Trust Bridge**: Semaphore identity + ZK proof validation
- **Local AI Swarm**: Your GPU-bound models (e.g., Ollama/llama.cpp)
- **Honestly Backend**: Proof generation/verification (Groth16), integrity services

## Next Steps

1) Connect to the Trust Bridge (Semaphore identity/proofs)
2) Add workflow/ensemble builder (chain models, node-based UI)
3) Integrate local AI endpoints (user-configured LLM/TTS/vision)
4) Add cryptographic signing for all actions (identity-bound logs)

See stubs/placeholders:

- Trust Bridge: `src/lib/trustBridge.ts`
- Workflows: `src/app/workflows/page.tsx`
- Signing: `src/lib/signing.ts`

---

**Built for the sovereign AI future.**
