/**
 * ConductMe Conductor
 * 
 * The core orchestration layer that gates AI actions with human identity proofs.
 * Every AI action must be authorized by a verified human via Semaphore proof.
 */

import { 
  ConductMeIdentity, 
  ConductMeGroup, 
  NullifierRegistry,
  SignalProof,
  createIdentity,
  deriveFromHonestlyProof
} from './identity.js';

export interface AIAction {
  id: string;
  type: 'query' | 'generate' | 'execute' | 'vote' | 'sign';
  aiId: string;
  prompt?: string;
  params?: Record<string, unknown>;
  timestamp: number;
}

export interface SignedAction {
  action: AIAction;
  proof: SignalProof;
  humanVerified: boolean;
}

export interface ConductorConfig {
  groupId: string;
  treeDepth?: number;
  requireProofForActions?: boolean;
  allowedAIs?: string[];
}

/**
 * The Conductor - Human-gated AI orchestration
 */
export class Conductor {
  private group: ConductMeGroup;
  private nullifierRegistry: NullifierRegistry;
  private config: ConductorConfig;
  private actionLog: SignedAction[] = [];
  
  constructor(config: ConductorConfig) {
    this.config = {
      treeDepth: 20,
      requireProofForActions: true,
      ...config,
    };
    
    this.group = new ConductMeGroup(config.groupId, this.config.treeDepth);
    this.nullifierRegistry = new NullifierRegistry();
  }
  
  /**
   * Register a new human operator
   * They must first prove their humanity via Honestly's ZK proof
   */
  async registerHuman(
    honestlyProofCommitment: string,
    salt: string
  ): Promise<ConductMeIdentity> {
    // Derive Semaphore identity from Honestly proof
    const identity = deriveFromHonestlyProof(honestlyProofCommitment, salt);
    
    // Add to the verified humans group
    this.group.addMember(identity.commitment);
    
    // Mark as verified
    identity.verified = true;
    
    console.log(`[Conductor] Human registered: ${identity.commitment.slice(0, 16)}...`);
    
    return identity;
  }
  
  /**
   * Generate a new ephemeral identity (for testing/development)
   */
  generateTestIdentity(): ConductMeIdentity {
    const identity = createIdentity();
    this.group.addMember(identity.commitment);
    identity.verified = true;
    return identity;
  }
  
  /**
   * Execute an AI action with human authorization
   */
  async executeAction(
    identity: ConductMeIdentity,
    action: AIAction
  ): Promise<SignedAction> {
    // Check if AI is allowed
    if (this.config.allowedAIs && !this.config.allowedAIs.includes(action.aiId)) {
      throw new Error(`AI '${action.aiId}' is not in the allowed list`);
    }
    
    // Generate external nullifier from action type + AI
    // This prevents the same human from spamming the same action type
    const externalNullifier = `${this.config.groupId}_${action.type}_${action.aiId}_${Math.floor(action.timestamp / 3600000)}`;
    
    // Generate the proof
    const proof = await this.group.generateMembershipProof(
      identity,
      JSON.stringify(action),
      externalNullifier
    );
    
    // Check nullifier hasn't been used
    if (!this.nullifierRegistry.markUsed(proof.nullifierHash)) {
      throw new Error('This action has already been performed by this identity');
    }
    
    // Verify the proof
    const isValid = await this.group.verifyMembershipProof(proof);
    
    if (!isValid) {
      throw new Error('Invalid membership proof');
    }
    
    const signedAction: SignedAction = {
      action,
      proof,
      humanVerified: true,
    };
    
    // Log the action
    this.actionLog.push(signedAction);
    
    console.log(`[Conductor] Action authorized: ${action.type} -> ${action.aiId}`);
    
    return signedAction;
  }
  
  /**
   * Verify a signed action
   */
  async verifyAction(signedAction: SignedAction): Promise<boolean> {
    // Verify the proof
    const proofValid = await this.group.verifyMembershipProof(signedAction.proof);
    
    // Verify the signal matches the action
    const signalMatches = signedAction.proof.signal === JSON.stringify(signedAction.action);
    
    return proofValid && signalMatches;
  }
  
  /**
   * Get the current group state
   */
  getGroupInfo(): { members: number; root: string } {
    return {
      members: this.group.size(),
      root: this.group.getRoot(),
    };
  }
  
  /**
   * Get action history
   */
  getActionLog(): SignedAction[] {
    return [...this.actionLog];
  }
  
  /**
   * Export state for persistence
   */
  export(): {
    config: ConductorConfig;
    group: ReturnType<ConductMeGroup['export']>;
    nullifiers: string[];
    actionLog: SignedAction[];
  } {
    return {
      config: this.config,
      group: this.group.export(),
      nullifiers: this.nullifierRegistry.export(),
      actionLog: this.actionLog,
    };
  }
  
  /**
   * Import state from persistence
   */
  static import(data: ReturnType<Conductor['export']>): Conductor {
    const conductor = new Conductor(data.config);
    conductor.group = ConductMeGroup.import(data.group);
    conductor.nullifierRegistry = NullifierRegistry.import(data.nullifiers);
    conductor.actionLog = data.actionLog;
    return conductor;
  }
}

/**
 * Action builder helpers
 */
export const Actions = {
  query(aiId: string, prompt: string): AIAction {
    return {
      id: crypto.randomUUID(),
      type: 'query',
      aiId,
      prompt,
      timestamp: Date.now(),
    };
  },
  
  generate(aiId: string, prompt: string, params?: Record<string, unknown>): AIAction {
    return {
      id: crypto.randomUUID(),
      type: 'generate',
      aiId,
      prompt,
      params,
      timestamp: Date.now(),
    };
  },
  
  execute(aiId: string, params: Record<string, unknown>): AIAction {
    return {
      id: crypto.randomUUID(),
      type: 'execute',
      aiId,
      params,
      timestamp: Date.now(),
    };
  },
  
  vote(aiId: string, params: Record<string, unknown>): AIAction {
    return {
      id: crypto.randomUUID(),
      type: 'vote',
      aiId,
      params,
      timestamp: Date.now(),
    };
  },
  
  sign(aiId: string, params: Record<string, unknown>): AIAction {
    return {
      id: crypto.randomUUID(),
      type: 'sign',
      aiId,
      params,
      timestamp: Date.now(),
    };
  },
};

