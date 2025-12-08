import { NextResponse } from 'next/server';
import { aiRoster, type AIProfile } from '@/lib/ais';

/**
 * GET /api/ai
 * Returns all AI profiles in the roster
 * 
 * @openapi
 * /api/ai:
 *   get:
 *     summary: List all AI profiles
 *     tags: [AI]
 *     responses:
 *       200:
 *         description: Array of AI profiles
 *         content:
 *           application/json:
 *             schema:
 *               type: object
 *               properties:
 *                 data:
 *                   type: array
 *                   items:
 *                     $ref: '#/components/schemas/AIProfile'
 *                 count:
 *                   type: integer
 */
export async function GET() {
  return NextResponse.json({
    data: aiRoster,
    count: aiRoster.length,
  });
}

/**
 * POST /api/ai
 * Add a new AI profile to the roster
 */
export async function POST(request: Request) {
  try {
    const body = await request.json() as Partial<AIProfile>;
    
    // Validate required fields
    const required = ['id', 'name', 'creator', 'type', 'description', 'flair', 'url'];
    for (const field of required) {
      if (!(field in body)) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        );
      }
    }

    // In a real app, this would persist to a database
    // For now, return the created profile
    const newProfile: AIProfile = {
      id: body.id!,
      name: body.name!,
      creator: body.creator!,
      type: body.type!,
      description: body.description!,
      flair: body.flair!,
      tags: body.tags || [],
      color: body.color || 'bg-gray-500',
      icon: body.icon || 'Bot',
      url: body.url!,
      isConnected: body.isConnected ?? false,
    };

    return NextResponse.json({ data: newProfile }, { status: 201 });
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 }
    );
  }
}

