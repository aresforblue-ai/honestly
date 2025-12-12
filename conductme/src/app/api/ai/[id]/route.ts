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
 * POST /api/ai/[id]
 * Execute a prompt against the specific AI agent
 */
export async function POST(
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
    const { prompt, messages } = await request.json();
    
    if (!prompt && (!messages || messages.length === 0)) {
       return NextResponse.json(
        { error: 'Missing prompt or messages' },
        { status: 400 }
      );
    }

    // Determine which API to call based on AI ID or type
    let result = '';
    
    if (ai.id.includes('gpt')) {
      // Call OpenAI
      result = await callOpenAI(ai.id, messages || [{ role: 'user', content: prompt }]);
    } else if (ai.id.includes('claude')) {
      // Call Anthropic
      result = await callAnthropic(ai.id, messages || [{ role: 'user', content: prompt }]);
    } else if (ai.id === 'github-copilot') {
      // Mock Copilot for now (no public API usually accessible this easily without auth flow)
      result = "I can help you write code. Please provide the context.";
    } else {
      // Default / Local fallback
      result = `[${ai.name}] I received your message: "${prompt || messages[messages.length-1].content}". (Real API integration pending for this model)`;
    }

    return NextResponse.json({ 
      data: {
        response: result,
        model: ai.id,
        timestamp: new Date().toISOString()
      }
    });

  } catch (error) {
    console.error(`[AI Execution] Error calling ${params.id}:`, error);
    return NextResponse.json(
      { error: 'Failed to execute AI request', details: (error as Error).message },
      { status: 500 }
    );
  }
}

/**
 * Helper to call OpenAI API
 */
async function callOpenAI(model: string, messages: any[]) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return "[Mock] OpenAI API key not found. Please set OPENAI_API_KEY.";
  }

  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${apiKey}`
    },
    body: JSON.stringify({
      model: model, // e.g., 'gpt-4-turbo'
      messages: messages,
    })
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`OpenAI API Error: ${err}`);
  }

  const data = await response.json();
  return data.choices[0].message.content;
}

/**
 * Helper to call Anthropic API
 */
async function callAnthropic(model: string, messages: any[]) {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return "[Mock] Anthropic API key not found. Please set ANTHROPIC_API_KEY.";
  }

  // Anthropic messages format is slightly different (no system in messages usually, passed separate)
  // For simplicity here, we assume messages are user/assistant
  
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: model === 'claude-3-opus' ? 'claude-3-opus-20240229' : 'claude-3-sonnet-20240229',
      max_tokens: 1024,
      messages: messages.map(m => ({ role: m.role, content: m.content })),
    })
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Anthropic API Error: ${err}`);
  }

  const data = await response.json();
  return data.content[0].text;
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
