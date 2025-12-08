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
  trapdoor: string;
  nullifier: string;
  createdAt: number;
  verified: boolean;
}

export interface SignalProof {
  proof: unknown;
  nullifierHash: string;
  signal: string;
  externalNullifier: string;
  merkleTreeRoot: string;
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
    trapdoor: identity.trapdoor.toString(),
    nullifier: identity.nullifier.toString(),
    createdAt: Date.now(),
    verified: false,
  };
}

/**
 * Recover an identity from stored secrets
 */
export function recoverIdentity(trapdoor: string, nullifier: string): ConductMeIdentity {
  // Reconstruct identity from secrets
  const identity = new Identity(`${trapdoor}_${nullifier}`);
  
  return {
    commitment: identity.commitment.toString(),
    trapdoor,
    nullifier,
    createdAt: Date.now(),
    verified: true,
  };
}

/**
 * Derive identity from an age/authenticity proof
 * This links the ZK-verified human to a Semaphore identity
 */
export function deriveFromHonestlyProof(
  proofCommitment: string,
  salt: string
): ConductMeIdentity {
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
  
  constructor(groupId: string, treeDepth: number = 20) {
    this.groupId = groupId;
    this.group = new Group(treeDepth);
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
    return this.group.members.length;
  }
  
  /**
   * Generate a proof that a member is in the group
   */
  async generateMembershipProof(
    identity: ConductMeIdentity,
    signal: string,
    externalNullifier: string
  ): Promise<SignalProof> {
    const semaphoreIdentity = new Identity(
      `${identity.trapdoor}_${identity.nullifier}`
    );
    
    const proof = await generateProof(
      semaphoreIdentity,
      this.group,
      externalNullifier,
      signal
    );
    
    return {
      proof: proof.proof,
      nullifierHash: proof.nullifierHash.toString(),
      signal,
      externalNullifier,
      merkleTreeRoot: proof.merkleTreeRoot.toString(),
    };
  }
  
  /**
   * Verify a membership proof
   */
  async verifyMembershipProof(signalProof: SignalProof): Promise<boolean> {
    return verifyProof({
      proof: signalProof.proof as any,
      merkleTreeRoot: BigInt(signalProof.merkleTreeRoot),
      nullifierHash: BigInt(signalProof.nullifierHash),
      externalNullifier: signalProof.externalNullifier,
      signal: signalProof.signal,
    });
  }
  
  /**
   * Export group state for persistence
   */
  export(): { groupId: string; members: string[]; root: string } {
    return {
      groupId: this.groupId,
      members: this.group.members.map(m => m.toString()),
      root: this.getRoot(),
    };
  }
  
  /**
   * Import group state
   */
  static import(data: { groupId: string; members: string[]; root: string }): ConductMeGroup {
    const group = new ConductMeGroup(data.groupId);
    for (const member of data.members) {
      group.addMember(member);
    }
    return group;
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

