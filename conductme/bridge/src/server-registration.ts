/**
 * Server-Side Registration Handler
 * 
 * PRIVACY-PRESERVING: The server never sees the salt or identity derivation.
 * It only receives:
 * - Semaphore commitment (public)
 * - Binding commitment (proves link without revealing it)
 * - Honestly proof + nullifier (for verification)
 * 
 * The server's job:
 * 1. Verify the Honestly proof is valid
 * 2. Check the Honestly nullifier hasn't been used (prevent double-registration)
 * 3. Add the Semaphore commitment to the group
 * 4. Store the binding commitment (for audit, not for linking)
 */

import { ConductMeGroup, NullifierRegistry } from './identity';

export interface RegistrationRequest {
  semaphoreCommitment: string;
  bindingCommitment: string;
  honestlyNullifier: string;
  honestlyProof: {
    proof: unknown;
    publicSignals: unknown;
    proofType: 'age' | 'authenticity';
  };
}

export interface RegistrationResult {
  success: boolean;
  error?: string;
  groupId?: string;
  merkleRoot?: string;
  memberIndex?: number;
}

/**
 * Registry for used Honestly proof nullifiers
 * Prevents the same Honestly proof from registering multiple Semaphore identities
 */
export class HonestlyNullifierRegistry {
  private usedNullifiers: Map<string, { 
    bindingCommitment: string;
    registeredAt: number;
  }> = new Map();
  
  /**
   * Check if an Honestly nullifier has been used
   */
  isUsed(nullifier: string): boolean {
    return this.usedNullifiers.has(nullifier);
  }
  
  /**
   * Mark an Honestly nullifier as used
   */
  markUsed(nullifier: string, bindingCommitment: string): void {
    this.usedNullifiers.set(nullifier, {
      bindingCommitment,
      registeredAt: Date.now(),
    });
  }
  
  /**
   * Export for persistence
   */
  export(): Array<{ nullifier: string; bindingCommitment: string; registeredAt: number }> {
    return Array.from(this.usedNullifiers.entries()).map(([nullifier, data]) => ({
      nullifier,
      ...data,
    }));
  }
  
  /**
   * Import from persistence
   */
  static import(data: Array<{ nullifier: string; bindingCommitment: string; registeredAt: number }>): HonestlyNullifierRegistry {
    const registry = new HonestlyNullifierRegistry();
    for (const entry of data) {
      registry.usedNullifiers.set(entry.nullifier, {
        bindingCommitment: entry.bindingCommitment,
        registeredAt: entry.registeredAt,
      });
    }
    return registry;
  }
}

/**
 * Verify an Honestly ZK proof
 * In production, this calls the Honestly verification endpoint
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const process: { env: Record<string, string | undefined> };

async function verifyHonestlyProof(
  proof: RegistrationRequest['honestlyProof'],
  nullifier: string
): Promise<{ valid: boolean; error?: string }> {
  // TODO: Integrate with actual Honestly proof verification
  // This would call the /ai/verify-proof endpoint
  
  const HONESTLY_API = process.env.HONESTLY_API_URL || 'http://localhost:8000';
  
  try {
    const response = await fetch(`${HONESTLY_API}/ai/verify-proof`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        proof_type: proof.proofType,
        proof: proof.proof,
        public_signals: proof.publicSignals,
      }),
    });
    
    if (!response.ok) {
      return { valid: false, error: 'Honestly API error' };
    }
    
    const result = await response.json();
    return { valid: result.verified === true };
  } catch (error) {
    // For development, allow mock verification
    if (process.env.NODE_ENV === 'development') {
      console.warn('[DEV] Skipping Honestly proof verification');
      return { valid: true };
    }
    return { valid: false, error: 'Failed to verify Honestly proof' };
  }
}

/**
 * Server-side registration handler
 * 
 * CRITICAL: This function NEVER receives or processes:
 * - The user's salt
 * - The user's trapdoor/nullifier (Semaphore secrets)
 * - Any way to link Honestly identity to Semaphore identity
 */
export class PrivacyPreservingRegistrar {
  private group: ConductMeGroup;
  private honestlyNullifiers: HonestlyNullifierRegistry;
  private bindingCommitments: Map<string, string> = new Map(); // commitment -> binding
  
  constructor(groupId: string) {
    this.group = new ConductMeGroup(groupId); // New API doesn't need tree depth
    this.honestlyNullifiers = new HonestlyNullifierRegistry();
  }
  
  /**
   * Register a new human operator
   * 
   * The server receives ONLY:
   * - semaphoreCommitment: The public identity to add to group
   * - bindingCommitment: Cryptographic proof of link (without revealing it)
   * - honestlyNullifier: To prevent double-registration
   * - honestlyProof: To verify the user is human
   */
  async register(request: RegistrationRequest): Promise<RegistrationResult> {
    const { 
      semaphoreCommitment, 
      bindingCommitment, 
      honestlyNullifier, 
      honestlyProof 
    } = request;
    
    // 1. Validate inputs
    if (!semaphoreCommitment || !bindingCommitment || !honestlyNullifier || !honestlyProof) {
      return { success: false, error: 'Missing required fields' };
    }
    
    // 2. Check if Honestly nullifier already used
    if (this.honestlyNullifiers.isUsed(honestlyNullifier)) {
      return { 
        success: false, 
        error: 'This Honestly proof has already been used to register an identity' 
      };
    }
    
    // 3. Check if Semaphore commitment already in group
    if (this.group.hasMember(semaphoreCommitment)) {
      return { 
        success: false, 
        error: 'This identity is already registered' 
      };
    }
    
    // 4. Verify the Honestly proof
    const verification = await verifyHonestlyProof(honestlyProof, honestlyNullifier);
    if (!verification.valid) {
      return { 
        success: false, 
        error: verification.error || 'Invalid Honestly proof' 
      };
    }
    
    // 5. Add to group (server never knows WHO this identity belongs to)
    this.group.addMember(semaphoreCommitment);
    
    // 6. Mark Honestly nullifier as used
    this.honestlyNullifiers.markUsed(honestlyNullifier, bindingCommitment);
    
    // 7. Store binding commitment (for audit, NOT for linking)
    this.bindingCommitments.set(semaphoreCommitment, bindingCommitment);
    
    console.log(`[Registrar] New member added: ${semaphoreCommitment.slice(0, 16)}...`);
    console.log(`[Registrar] Group size: ${this.group.size()}`);
    
    return {
      success: true,
      groupId: this.getGroupId(),
      merkleRoot: this.group.getRoot(),
      memberIndex: this.group.size() - 1,
    };
  }
  
  /**
   * Check if a commitment is registered
   */
  isRegistered(commitment: string): boolean {
    return this.group.hasMember(commitment);
  }
  
  /**
   * Get the group for proof generation/verification
   */
  getGroup(): ConductMeGroup {
    return this.group;
  }
  
  /**
   * Get group info (public)
   */
  getGroupInfo(): { groupId: string; size: number; root: string } {
    return {
      groupId: this.getGroupId(),
      size: this.group.size(),
      root: this.group.getRoot(),
    };
  }
  
  private getGroupId(): string {
    return (this.group as any).groupId || 'conductme';
  }
  
  /**
   * Export state for persistence
   */
  export(): string {
    return JSON.stringify({
      groupData: this.group.export(),
      honestlyNullifiers: this.honestlyNullifiers.export(),
      bindingCommitments: Array.from(this.bindingCommitments.entries()),
    });
  }
  
  /**
   * Import state from persistence
   */
  static import(data: string): PrivacyPreservingRegistrar {
    const parsed = JSON.parse(data);
    const groupData = JSON.parse(parsed.groupData);
    const registrar = new PrivacyPreservingRegistrar(groupData.groupId);
    registrar.group = ConductMeGroup.import(parsed.groupData);
    registrar.honestlyNullifiers = HonestlyNullifierRegistry.import(parsed.honestlyNullifiers);
    registrar.bindingCommitments = new Map(parsed.bindingCommitments);
    return registrar;
  }
}

/**
 * Singleton instance for the default registrar
 */
let defaultRegistrar: PrivacyPreservingRegistrar | null = null;

export function getDefaultRegistrar(): PrivacyPreservingRegistrar {
  if (!defaultRegistrar) {
    defaultRegistrar = new PrivacyPreservingRegistrar('conductme-main');
  }
  return defaultRegistrar;
}

