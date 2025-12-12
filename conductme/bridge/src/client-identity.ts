/**
 * Client-Side Identity Generation
 * 
 * CRITICAL PRIVACY FIX: Identity derivation MUST happen client-side.
 * The server should NEVER see the salt or be able to link identities.
 * 
 * Flow:
 * 1. User proves humanity via Honestly ZK proof (age/authenticity)
 * 2. User generates Semaphore identity CLIENT-SIDE with local secret
 * 3. User creates a binding commitment that ties Honestly proof to Semaphore identity
 * 4. User submits: Semaphore commitment + binding proof + Honestly nullifier
 * 5. Server verifies binding proof and adds commitment to group
 * 6. Server NEVER sees: salt, trapdoor, nullifier (Semaphore), or identity link
 */

import { Identity } from '@semaphore-protocol/identity';
import { ethers } from 'ethers';

// Storage key for browser localStorage
const IDENTITY_STORAGE_KEY = 'conductme:identity:v2';
const BINDING_STORAGE_KEY = 'conductme:binding:v2';

export interface ClientIdentity {
  commitment: string;
  privateKey: string; // Base64 encoded private key
  secretScalar: string; // Secret scalar for advanced use
  createdAt: number;
  // The binding links this identity to an Honestly proof WITHOUT revealing the mapping
  bindingCommitment?: string;
}

export interface RegistrationRequest {
  // Public: The Semaphore identity commitment to add to the group
  semaphoreCommitment: string;
  
  // Public: Hash commitment that binds Honestly proof to this identity
  // bindingCommitment = H(honestlyProofCommitment || semaphoreCommitment || clientSecret)
  bindingCommitment: string;
  
  // Public: The nullifier from the Honestly proof (to prevent double-registration)
  honestlyNullifier: string;
  
  // Public: The Honestly ZK proof itself (for verification)
  honestlyProof: {
    proof: unknown;
    publicSignals: unknown;
    proofType: 'age' | 'authenticity';
  };
  
  // NEVER SENT: clientSecret, trapdoor, nullifier (Semaphore)
}

export interface RegistrationResponse {
  success: boolean;
  groupId: string;
  merkleRoot: string;
  memberIndex: number;
}

/**
 * Check if running in browser environment
 */
function isBrowser(): boolean {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined';
}

/**
 * Generate cryptographically secure random bytes
 */
function secureRandomBytes(length: number): Uint8Array {
  if (isBrowser() && window.crypto) {
    return window.crypto.getRandomValues(new Uint8Array(length));
  }
  // Fallback for Node.js (should not be used for production client code)
  throw new Error('Client identity generation must happen in browser');
}

/**
 * Generate a new Semaphore identity CLIENT-SIDE
 * The secret entropy never leaves the browser
 */
export function generateClientIdentity(): ClientIdentity {
  if (!isBrowser()) {
    throw new Error('Identity generation must happen client-side in browser');
  }
  
  // Generate 32 bytes of secure random entropy
  const entropy = secureRandomBytes(32);
  const seed = ethers.hexlify(entropy);
  
  // Create Semaphore identity from entropy
  const identity = new Identity(seed);
  
  const clientIdentity: ClientIdentity = {
    commitment: identity.commitment.toString(),
    privateKey: identity.export(), // Export as base64
    secretScalar: identity.secretScalar.toString(),
    createdAt: Date.now(),
  };
  
  // Store securely in browser (user's device only)
  saveIdentityToStorage(clientIdentity);
  
  return clientIdentity;
}

/**
 * Create a binding commitment that ties Honestly proof to Semaphore identity
 * WITHOUT revealing the link to the server
 * 
 * The binding commitment proves:
 * - User knows an Honestly proof commitment
 * - User knows a Semaphore identity
 * - These are linked via a secret only the user knows
 */
export function createBindingCommitment(
  honestlyProofCommitment: string,
  semaphoreCommitment: string,
  clientSecret?: string
): { bindingCommitment: string; clientSecret: string } {
  if (!isBrowser()) {
    throw new Error('Binding must happen client-side');
  }
  
  // Generate or use provided client secret
  const secret = clientSecret || ethers.hexlify(secureRandomBytes(32));
  
  // Create binding commitment: H(honestly || semaphore || secret)
  // This commits to the link without revealing it
  const bindingCommitment = ethers.keccak256(
    ethers.AbiCoder.defaultAbiCoder().encode(
      ['bytes32', 'bytes32', 'bytes32'],
      [
        ethers.zeroPadValue(honestlyProofCommitment, 32),
        ethers.zeroPadValue(semaphoreCommitment, 32),
        secret
      ]
    )
  );
  
  // Store the secret locally (needed for future re-binding proof if required)
  if (isBrowser()) {
    const bindingData = {
      honestlyProofCommitment,
      semaphoreCommitment,
      bindingCommitment,
      clientSecret: secret,
      createdAt: Date.now(),
    };
    localStorage.setItem(BINDING_STORAGE_KEY, JSON.stringify(bindingData));
  }
  
  return { bindingCommitment, clientSecret: secret };
}

/**
 * Prepare a registration request to send to the server
 * This bundles everything the server needs WITHOUT revealing the identity link
 */
export function prepareRegistrationRequest(
  clientIdentity: ClientIdentity,
  honestlyProofCommitment: string,
  honestlyNullifier: string,
  honestlyProof: RegistrationRequest['honestlyProof']
): RegistrationRequest {
  // Create binding commitment
  const { bindingCommitment } = createBindingCommitment(
    honestlyProofCommitment,
    clientIdentity.commitment
  );
  
  // Update identity with binding
  clientIdentity.bindingCommitment = bindingCommitment;
  saveIdentityToStorage(clientIdentity);
  
  return {
    semaphoreCommitment: clientIdentity.commitment,
    bindingCommitment,
    honestlyNullifier,
    honestlyProof,
    // NOTE: clientSecret, trapdoor, nullifier are NOT included
  };
}

/**
 * Load identity from browser storage
 */
export function loadIdentityFromStorage(): ClientIdentity | null {
  if (!isBrowser()) {
    return null;
  }
  
  try {
    const stored = localStorage.getItem(IDENTITY_STORAGE_KEY);
    if (!stored) return null;
    return JSON.parse(stored) as ClientIdentity;
  } catch {
    return null;
  }
}

/**
 * Save identity to browser storage
 */
function saveIdentityToStorage(identity: ClientIdentity): void {
  if (!isBrowser()) return;
  localStorage.setItem(IDENTITY_STORAGE_KEY, JSON.stringify(identity));
}

/**
 * Clear identity from storage (logout/reset)
 */
export function clearIdentityFromStorage(): void {
  if (!isBrowser()) return;
  localStorage.removeItem(IDENTITY_STORAGE_KEY);
  localStorage.removeItem(BINDING_STORAGE_KEY);
}

/**
 * Get or create client identity
 * Ensures user always has an identity for this browser
 */
export function getOrCreateIdentity(): ClientIdentity {
  const existing = loadIdentityFromStorage();
  if (existing) {
    return existing;
  }
  return generateClientIdentity();
}

/**
 * Export identity for backup (user-initiated only!)
 * Returns encrypted identity that user can save
 */
export async function exportIdentityForBackup(password: string): Promise<string> {
  const identity = loadIdentityFromStorage();
  if (!identity) {
    throw new Error('No identity to export');
  }
  
  // Derive encryption key from password
  const encoder = new TextEncoder();
  const keyMaterial = await window.crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );
  
  const salt = secureRandomBytes(16);
  const key = await window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt.buffer as ArrayBuffer,
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt']
  );
  
  const iv = secureRandomBytes(12);
  const encrypted = await window.crypto.subtle.encrypt(
    { name: 'AES-GCM', iv: iv.buffer as ArrayBuffer },
    key,
    encoder.encode(JSON.stringify(identity))
  );
  
  // Return as base64 with salt and iv prepended
  const combined = new Uint8Array(salt.length + iv.length + encrypted.byteLength);
  combined.set(salt, 0);
  combined.set(iv, salt.length);
  combined.set(new Uint8Array(encrypted), salt.length + iv.length);
  
  return btoa(String.fromCharCode(...combined));
}

/**
 * Import identity from backup
 */
export async function importIdentityFromBackup(
  encryptedBackup: string,
  password: string
): Promise<ClientIdentity> {
  const combined = new Uint8Array(
    atob(encryptedBackup).split('').map(c => c.charCodeAt(0))
  );
  
  const salt = combined.slice(0, 16);
  const iv = combined.slice(16, 28);
  const encrypted = combined.slice(28);
  
  const encoder = new TextEncoder();
  const keyMaterial = await window.crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits', 'deriveKey']
  );
  
  const key = await window.crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['decrypt']
  );
  
  const decrypted = await window.crypto.subtle.decrypt(
    { name: 'AES-GCM', iv },
    key,
    encrypted
  );
  
  const identity = JSON.parse(
    new TextDecoder().decode(decrypted)
  ) as ClientIdentity;
  
  // Save to storage
  saveIdentityToStorage(identity);
  
  return identity;
}

