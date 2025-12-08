import { NextResponse } from 'next/server';

/**
 * Workflow: A sequence of AI actions to accomplish a goal
 */
export interface WorkflowStep {
  id: string;
  aiId: string;
  prompt: string;
  inputFrom?: string;  // ID of previous step to use as input
  outputKey: string;   // Key to store output for next steps
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  steps: WorkflowStep[];
  createdAt: string;
  updatedAt: string;
}

// In-memory storage for demo (would be DB in production)
const workflows: Map<string, Workflow> = new Map([
  ['blog-generator', {
    id: 'blog-generator',
    name: 'Blog Post Generator',
    description: 'Research → Outline → Write → Edit → Image',
    steps: [
      { id: 's1', aiId: 'gpt-4-turbo', prompt: 'Research the topic: {{topic}}', outputKey: 'research' },
      { id: 's2', aiId: 'claude-3-opus', prompt: 'Create an outline based on: {{research}}', inputFrom: 's1', outputKey: 'outline' },
      { id: 's3', aiId: 'gpt-4-turbo', prompt: 'Write the blog post following: {{outline}}', inputFrom: 's2', outputKey: 'draft' },
      { id: 's4', aiId: 'claude-3-opus', prompt: 'Edit and improve: {{draft}}', inputFrom: 's3', outputKey: 'final' },
      { id: 's5', aiId: 'midjourney', prompt: 'Create a header image for: {{topic}}', outputKey: 'image' },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }],
  ['code-review', {
    id: 'code-review',
    name: 'Secure Code Review',
    description: 'Static analysis → Security scan → Optimization suggestions',
    steps: [
      { id: 's1', aiId: 'github-copilot', prompt: 'Analyze code structure: {{code}}', outputKey: 'structure' },
      { id: 's2', aiId: 'claude-3-opus', prompt: 'Security audit this code: {{code}}\n\nStructure: {{structure}}', inputFrom: 's1', outputKey: 'security' },
      { id: 's3', aiId: 'gpt-4-turbo', prompt: 'Suggest optimizations: {{code}}\n\nSecurity notes: {{security}}', inputFrom: 's2', outputKey: 'optimizations' },
    ],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  }],
]);

/**
 * GET /api/workflows
 * List all workflows
 */
export async function GET() {
  return NextResponse.json({
    data: Array.from(workflows.values()),
    count: workflows.size,
  });
}

/**
 * POST /api/workflows
 * Create a new workflow
 */
export async function POST(request: Request) {
  try {
    const body = await request.json();
    
    if (!body.name || !body.steps || !Array.isArray(body.steps)) {
      return NextResponse.json(
        { error: 'Missing required fields: name, steps (array)' },
        { status: 400 }
      );
    }
    
    const id = body.id || `wf-${Date.now()}`;
    const now = new Date().toISOString();
    
    const workflow: Workflow = {
      id,
      name: body.name,
      description: body.description,
      steps: body.steps.map((s: Partial<WorkflowStep>, i: number) => ({
        id: s.id || `step-${i}`,
        aiId: s.aiId,
        prompt: s.prompt,
        inputFrom: s.inputFrom,
        outputKey: s.outputKey || `output-${i}`,
      })),
      createdAt: now,
      updatedAt: now,
    };
    
    workflows.set(id, workflow);
    
    return NextResponse.json({ data: workflow }, { status: 201 });
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body' },
      { status: 400 }
    );
  }
}

