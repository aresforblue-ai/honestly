import { NextResponse } from 'next/server';

/**
 * POST /api/identity/action
 * 
 * Execute an AI action with human identity proof.
 * Requires a valid Semaphore proof to authorize the action.
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    const { 
      commitment, 
      action, 
      proof,
      nullifierHash 
    } = body;
    
    if (!commitment || !action) {
      return NextResponse.json(
        { error: 'Missing required fields: commitment, action' },
        { status: 400 }
      );
    }
    
    // Validate action structure
    if (!action.type || !action.aiId) {
      return NextResponse.json(
        { error: 'Action must have type and aiId' },
        { status: 400 }
      );
    }
    
    // In production:
    // 1. Verify the Semaphore proof
    // 2. Check nullifier hasn't been used (prevent replay)
    // 3. Execute the action
    // 4. Log for audit
    
    const actionId = `act-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    
    // Simulate verification
    const isVerified = proof && nullifierHash;
    
    if (!isVerified && process.env.NODE_ENV === 'production') {
      return NextResponse.json(
        { error: 'Valid proof required for production' },
        { status: 401 }
      );
    }
    
    // Log the action
    const signedAction = {
      id: actionId,
      action: {
        ...action,
        id: action.id || actionId,
        timestamp: action.timestamp || Date.now(),
      },
      commitment,
      nullifierHash: nullifierHash || `null-${actionId}`,
      verified: true,
      executedAt: new Date().toISOString(),
    };
    
    console.log(`[ConductMe] Action authorized: ${action.type} -> ${action.aiId}`);
    
    return NextResponse.json({
      data: signedAction,
      message: 'Action authorized and logged',
    });
  } catch (error) {
    console.error('[ConductMe] Action error:', error);
    return NextResponse.json(
      { error: 'Failed to process action' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/identity/action
 * List recent actions (audit log)
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const commitment = searchParams.get('commitment');
  const limit = parseInt(searchParams.get('limit') || '50');
  
  // In production, fetch from database filtered by commitment
  const mockActions = [
    {
      id: 'act-demo-1',
      action: { type: 'query', aiId: 'claude-3-opus', prompt: 'Analyze...' },
      verified: true,
      executedAt: new Date(Date.now() - 3600000).toISOString(),
    },
    {
      id: 'act-demo-2',
      action: { type: 'generate', aiId: 'midjourney' },
      verified: true,
      executedAt: new Date(Date.now() - 7200000).toISOString(),
    },
  ];
  
  return NextResponse.json({
    data: mockActions.slice(0, limit),
    count: mockActions.length,
    commitment,
  });
}

