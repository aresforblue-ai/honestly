import { NextResponse } from 'next/server';
import { aiRoster } from '@/lib/ais';

/**
 * GET /api/ai/[id]
 * Returns a single AI profile by ID
 * 
 * @openapi
 * /api/ai/{id}:
 *   get:
 *     summary: Get AI profile by ID
 *     tags: [AI]
 *     parameters:
 *       - name: id
 *         in: path
 *         required: true
 *         schema:
 *           type: string
 *     responses:
 *       200:
 *         description: AI profile
 *       404:
 *         description: AI not found
 */
export async function GET(
  request: Request,
  { params }: { params: { id: string } }
) {
  const ai = aiRoster.find((a) => a.id === params.id);
  
  if (!ai) {
    return NextResponse.json(
      { error: 'AI profile not found' },
      { status: 404 }
    );
  }

  return NextResponse.json({ data: ai });
}

/**
 * PATCH /api/ai/[id]
 * Update an AI profile's connection status
 */
export async function PATCH(
  request: Request,
  { params }: { params: { id: string } }
) {
  const ai = aiRoster.find((a) => a.id === params.id);
  
  if (!ai) {
    return NextResponse.json(
      { error: 'AI profile not found' },
      { status: 404 }
    );
  }

  try {
    const body = await request.json();
    
    // Only allow updating certain fields
    const updatable = ['isConnected', 'url', 'flair'];
    const updates: Record<string, unknown> = {};
    
    for (const key of updatable) {
      if (key in body) {
        updates[key] = body[key];
      }
    }

    return NextResponse.json({
      data: { ...ai, ...updates },
    });
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 }
    );
  }
}

/**
 * DELETE /api/ai/[id]
 * Remove an AI profile (disconnects it)
 */
export async function DELETE(
  request: Request,
  { params }: { params: { id: string } }
) {
  const ai = aiRoster.find((a) => a.id === params.id);
  
  if (!ai) {
    return NextResponse.json(
      { error: 'AI profile not found' },
      { status: 404 }
    );
  }

  return NextResponse.json({
    message: `AI profile '${ai.name}' disconnected`,
    id: params.id,
  });
}

