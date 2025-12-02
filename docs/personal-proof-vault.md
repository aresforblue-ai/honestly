## Personal Proof Vault MVP

This document outlines the MVP that turns the starter Truth Engine into a user‑facing “Personal Proof Vault.” The goal is to let a user register sensitive life events, mint zero‑knowledge friendly proofs, and publish tamper‑proof attestations without exposing the underlying payloads.

### Pillars
1. **Vault API & Storage** – Encrypted payloads stay in the user’s custody; the backend stores only hashes, metadata, and relationships so verifiers can audit lineage.
2. **Selective Disclosure Proofs** – Deterministic proof templates (“Document Authenticity”, “Accredited Investor”, etc.) are generated from stored entries. They return human‑readable statements plus a zk‑friendly hash commitment.
3. **Blockchain Attestation Layer** – Every proof can be anchored to a ledger. The MVP ships with a local append‑only ledger file and an abstraction to swap in Polygon/Base/Fabric anchors later.

### Data Flow
```
Client -> GraphQL Mutation (createVaultEntry)
      -> Neo4j stores VaultEntry node (hash + metadata)
      -> Ledger append keeps audit trail

Client -> GraphQL Mutation (generateProof)
      -> VaultService builds proof artifact + Merkle-friendly hash
      -> Proof node links back to VaultEntry

Client -> GraphQL Mutation (recordAttestation)
      -> Chain/network metadata stored as Attestation node
      -> Ledger append simulates on-chain receipt (tx hash, chain, etc.)
```

### GraphQL Surface (new)
- `createVaultEntry(input: VaultEntryInput!): VaultEntry`
- `generateProof(input: ProofRequestInput!): ProofArtifact`
- `recordAttestation(input: AttestationInput!): AttestationReceipt`
- `vaultEntries(ownerId: ID!): [VaultEntry!]!`
- `vaultProofs(ownerId: ID!): [ProofArtifact!]!`
- `vaultTimeline(ownerId: ID!, limit: Int = 25): [TimelineEvent!]!`

See `api/schema.graphql` for exact field definitions.

### Files Introduced
- `api/services/vault.py` – Stateless helper that encapsulates hashing, ledger appends, and Neo4j persistence for entries/proofs/attestations.
- `docs/attestation_ledger.jsonl` (auto-created) – Append-only JSON lines log mirroring what would be published on-chain.

### Demo Script
1. Start stack (`docker-compose up -d`, then `uvicorn api.app:app --reload`).
2. Run GraphQL mutation `createVaultEntry` with:
   ```graphql
   mutation {
     createVaultEntry(input: {
       ownerId: "user-123",
       entryType: "GOV_ID",
       payloadSummary: "Passport ending 9921 verified by Notary",
       tags: ["identity", "travel"]
     }) {
       entryId
       payloadHash
       secureReference
     }
   }
   ```
3. Generate a proof (e.g., “I am travel-ready with a valid passport”) using `generateProof`.
4. Anchor it via `recordAttestation` with `chain: "demo-ledger"` and share the returned receipt.
5. Query `vaultTimeline(ownerId: "user-123")` to show a live feed of signed events.

### Extending to Production
- Swap ledger implementation with Polygon/Base or Hyperledger Fabric using the same `record_attestation` hook.
- Replace placeholder zk proof payloads with real circuits (Circom/Groth16) and store proof artifacts alongside hashes.
- Connect secure storage (e.g., HSM, AWS KMS, Lit Protocol) for encrypting `secureReference` pointers.
- Add streaming webhooks so downstream apps receive proof/attestation events in real time.

