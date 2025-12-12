/**
 * Semaphore Identity Manager
 * 
 * Creates and manages cryptographic identities for human verification.
 * Each identity consists of:
 *   - trapdoor: Random secret value
 *   - nullifier: Used to prevent double-signaling
 *   - commitment: Public identifier (hash of trapdoor + nullifier)
 */

import { Identity } from '@semaphore-protocol/identity';
import { Group } from '@semaphore-protocol/group';
import { generateProof, verifyProof } from '@semaphore-protocol/proof';
import { ethers } from 'ethers';

export interface ConductMeIdentity {
  commitment: string;
  privateKey: string; // Base64 encoded private key (replaces trapdoor + nullifier)
  secretScalar: string; // Secret scalar derived from private key
  createdAt: number;
  verified: boolean;
}

export interface SignalProof {
  proof: unknown; // PackedGroth16Proof or full proof
  nullifierHash: string;
  signal: string;
  externalNullifier: string;
  merkleTreeRoot: string;
  merkleTreeDepth?: number;
}

/**
 * Create a new Semaphore identity from entropy
 */
export function createIdentity(entropy?: string): ConductMeIdentity {
  // If no entropy provided, generate random
  const seed = entropy || ethers.hexlify(ethers.randomBytes(32));
  
  const identity = new Identity(seed);
  
  return {
    commitment: identity.commitment.toString(),
    privateKey: identity.export(), // Export as base64
    secretScalar: identity.secretScalar.toString(),
    createdAt: Date.now(),
    verified: false,
  };
}

/**
 * Recover an identity from stored private key
 */
export function recoverIdentity(privateKey: string): ConductMeIdentity {
  // Reconstruct identity from exported private key
  const identity = Identity.import(privateKey);
  
  return {
    commitment: identity.commitment.toString(),
    privateKey,
    secretScalar: identity.secretScalar.toString(),
    createdAt: Date.now(),
    verified: true,
  };
}

/**
 * @deprecated PRIVACY VULNERABILITY - DO NOT USE
 * 
 * This function is deprecated because it allows the server to link
 * Honestly proofs to Semaphore identities if the salt is sent to the server.
 * 
 * Use client-side identity generation instead:
 * 
 * ```typescript
 * // Client-side (browser)
 * import { generateClientIdentity, prepareRegistrationRequest } from './client-identity';
 * 
 * const identity = generateClientIdentity();
 * const request = prepareRegistrationRequest(identity, honestlyProof, nullifier, proof);
 * 
 * // Send only the request to server (no salt!)
 * await fetch('/api/register', { body: JSON.stringify(request) });
 * ```
 * 
 * @see ./client-identity.ts for the secure implementation
 */
export function deriveFromHonestlyProof(
  proofCommitment: string,
  salt: string
): ConductMeIdentity {
  console.warn(
    '[SECURITY WARNING] deriveFromHonestlyProof is deprecated due to privacy concerns. ' +
    'Use client-side identity generation instead. See client-identity.ts'
  );
  
  // Derive identity deterministically from the Honestly proof
  const seed = ethers.keccak256(
    ethers.AbiCoder.defaultAbiCoder().encode(
      ['bytes32', 'bytes32'],
      [proofCommitment, salt]
    )
  );
  
  return createIdentity(seed);
}

/**
 * ConductMe Group Manager
 * Manages the set of verified human identities
 */
export class ConductMeGroup {
  private group: Group;
  private groupId: string;
  
  constructor(groupId: string) {
    this.groupId = groupId;
    this.group = new Group(); // New Group API doesn't require tree depth
  }
  
  /**
   * Add a verified human to the group
   */
  addMember(commitment: string): void {
    this.group.addMember(BigInt(commitment));
  }
  
  /**
   * Remove a member (e.g., if identity compromised)
   */
  removeMember(commitment: string): void {
    const index = this.group.indexOf(BigInt(commitment));
    if (index !== -1) {
      this.group.removeMember(index);
    }
  }
  
  /**
   * Check if a commitment is in the group
   */
  hasMember(commitment: string): boolean {
    return this.group.indexOf(BigInt(commitment)) !== -1;
  }
  
  /**
   * Get the current Merkle root
   */
  getRoot(): string {
    return this.group.root.toString();
  }
  
  /**
   * Get group size
   */
  size(): number {
    return this.group.size;
  }
  
  /**
   * Generate a proof that a member is in the group
   */
  async generateMembershipProof(
    identity: ConductMeIdentity,
    signal: string,
    externalNullifier: string
  ): Promise<SignalProof> {
    const semaphoreIdentity = Identity.import(identity.privateKey);
    
    const proof = await generateProof(
      semaphoreIdentity,
      this.group,
      signal,
      externalNullifier
    );
    
    return {
      proof: proof.points, // New API uses 'points' for packed proof
      nullifierHash: proof.nullifier.toString(),
      signal: proof.message.toString(),
      externalNullifier: proof.scope.toString(),
      merkleTreeRoot: proof.merkleTreeRoot.toString(),
      merkleTreeDepth: proof.merkleTreeDepth,
    };
  }
  
  /**
   * Verify a membership proof
   */
  async verifyMembershipProof(signalProof: SignalProof): Promise<boolean> {
    return verifyProof({
      merkleTreeDepth: signalProof.merkleTreeDepth || 20,
      merkleTreeRoot: signalProof.merkleTreeRoot,
      nullifier: signalProof.nullifierHash,
      message: signalProof.signal,
      scope: signalProof.externalNullifier,
      points: signalProof.proof,
    } as any);
  }
  
  /**
   * Export group state for persistence
   */
  export(): string {
    return JSON.stringify({
      groupId: this.groupId,
      groupData: this.group.export(),
    });
  }
  
  /**
   * Import group state
   */
  static import(data: string): ConductMeGroup {
    const parsed = JSON.parse(data);
    const conductMeGroup = new ConductMeGroup(parsed.groupId);
    conductMeGroup.group = Group.import(parsed.groupData);
    return conductMeGroup;
  }
}

/**
 * Nullifier Registry
 * Prevents double-signaling (same identity can't perform same action twice)
 */
export class NullifierRegistry {
  private usedNullifiers: Set<string> = new Set();
  
  /**
   * Check and mark a nullifier as used
   * Returns true if the nullifier was fresh, false if already used
   */
  markUsed(nullifierHash: string): boolean {
    if (this.usedNullifiers.has(nullifierHash)) {
      return false;
    }
    this.usedNullifiers.add(nullifierHash);
    return true;
  }
  
  /**
   * Check if a nullifier has been used
   */
  isUsed(nullifierHash: string): boolean {
    return this.usedNullifiers.has(nullifierHash);
  }
  
  /**
   * Export for persistence
   */
  export(): string[] {
    return Array.from(this.usedNullifiers);
  }
  
  /**
   * Import from persistence
   */
  static import(nullifiers: string[]): NullifierRegistry {
    const registry = new NullifierRegistry();
    for (const n of nullifiers) {
      registry.usedNullifiers.add(n);
    }
    return registry;
  }
}

