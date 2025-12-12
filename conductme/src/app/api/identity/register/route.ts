import { NextResponse } from 'next/server';
import { getDefaultRegistrar } from '@bridge/server-registration';

/**
 * POST /api/identity/register
 * 
 * Privacy-Preserving Registration Endpoint
 * 
 * CRITICAL: This endpoint NEVER receives:
 * - The user's salt
 * - The user's Semaphore secrets (trapdoor, nullifier)
 * - Any way to link Honestly identity to Semaphore identity
 * 
 * It ONLY receives:
 * - semaphoreCommitment: Public identity commitment
 * - bindingCommitment: Cryptographic proof of link (without revealing it)
 * - honestlyNullifier: To prevent double-registration
 * - honestlyProof: To verify the user is human
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const { 
      semaphoreCommitment, 
      bindingCommitment, 
      honestlyNullifier, 
      honestlyProof 
    } = body;
    
    // Validate required fields
    if (!semaphoreCommitment) {
      return NextResponse.json(
        { error: 'Missing semaphoreCommitment' },
        { status: 400 }
      );
    }
    
    if (!bindingCommitment) {
      return NextResponse.json(
        { error: 'Missing bindingCommitment' },
        { status: 400 }
      );
    }
    
    if (!honestlyNullifier) {
      return NextResponse.json(
        { error: 'Missing honestlyNullifier' },
        { status: 400 }
      );
    }
    
    if (!honestlyProof) {
      return NextResponse.json(
        { error: 'Missing honestlyProof' },
        { status: 400 }
      );
    }
    
    // SECURITY: Reject any request that includes a salt
    // This prevents accidental privacy leaks from old client code
    if ('salt' in body) {
      console.error('[SECURITY] Rejected registration request containing salt');
      return NextResponse.json(
        { error: 'Invalid request: salt should not be sent to server. Update your client.' },
        { status: 400 }
      );
    }
    
    // Use the real PrivacyPreservingRegistrar
    const registrar = getDefaultRegistrar();
    
    // Note: In a serverless environment, the registrar state needs to be persisted.
    // The singleton getDefaultRegistrar() only holds state in memory for the process lifetime.
    
    const result = await registrar.register({
      semaphoreCommitment,
      bindingCommitment,
      honestlyNullifier,
      honestlyProof: honestlyProof as any, // Cast to match interface if needed
    });
    
    if (!result.success) {
      return NextResponse.json(
        { error: result.error },
        { status: 400 }
      );
    }
    
    return NextResponse.json({
      data: {
        commitment: semaphoreCommitment,
        groupId: result.groupId,
        merkleRoot: result.merkleRoot,
        memberIndex: result.memberIndex,
        verified: true,
        createdAt: new Date().toISOString(),
      },
      message: 'Identity registered successfully. Your Semaphore identity has been added to the group.',
    });
  } catch (error) {
    console.error('[API] Registration error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/identity/register
 * Check registration status
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const commitment = searchParams.get('commitment');
  
  if (!commitment) {
    return NextResponse.json(
      { error: 'Missing commitment parameter' },
      { status: 400 }
    );
  }
  
  const registrar = getDefaultRegistrar();
  const isRegistered = registrar.isRegistered(commitment);
  const groupInfo = registrar.getGroupInfo();
  
  return NextResponse.json({
    data: {
      commitment,
      registered: isRegistered,
      groupId: groupInfo.groupId,
    },
  });
}
