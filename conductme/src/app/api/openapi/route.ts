import { NextResponse } from 'next/server';

/**
 * GET /api/openapi
 * Returns the OpenAPI 3.0 specification for SDK generation
 */
export async function GET() {
  const spec = {
    openapi: '3.0.3',
    info: {
      title: 'ConductMe AI Orchestration API',
      description: `
API for managing AI profiles in the ConductMe orchestration platform.
Generate SDKs instantly using tools like openapi-generator or swagger-codegen.

## Quick SDK Generation

\`\`\`bash
# TypeScript/JavaScript
npx openapi-generator-cli generate -i https://your-domain/api/openapi -g typescript-fetch -o ./sdk

# Python
openapi-generator generate -i https://your-domain/api/openapi -g python -o ./sdk

# Go
openapi-generator generate -i https://your-domain/api/openapi -g go -o ./sdk

# Rust
openapi-generator generate -i https://your-domain/api/openapi -g rust -o ./sdk
\`\`\`

## Authentication

All endpoints currently use public access. Future versions will require
Semaphore identity proofs for write operations.
      `.trim(),
      version: '1.0.0',
      contact: {
        name: 'ConductMe',
        url: 'https://github.com/your-repo/conductme',
      },
      license: {
        name: 'MIT',
        url: 'https://opensource.org/licenses/MIT',
      },
    },
    servers: [
      {
        url: 'http://localhost:3001',
        description: 'Local development',
      },
      {
        url: 'https://conductme.app',
        description: 'Production',
      },
    ],
    tags: [
      {
        name: 'AI',
        description: 'AI profile management',
      },
      {
        name: 'Workflows',
        description: 'AI workflow orchestration',
      },
      {
        name: 'Identity',
        description: 'ZK identity and proof operations',
      },
    ],
    paths: {
      '/api/ai': {
        get: {
          summary: 'List all AI profiles',
          description: 'Returns all AI profiles in the roster with their connection status.',
          operationId: 'listAIs',
          tags: ['AI'],
          responses: {
            '200': {
              description: 'Successful response',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      data: {
                        type: 'array',
                        items: { $ref: '#/components/schemas/AIProfile' },
                      },
                      count: { type: 'integer', example: 5 },
                    },
                  },
                },
              },
            },
          },
        },
        post: {
          summary: 'Add a new AI profile',
          description: 'Register a new AI in the orchestration roster.',
          operationId: 'createAI',
          tags: ['AI'],
          requestBody: {
            required: true,
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/AIProfileCreate' },
              },
            },
          },
          responses: {
            '201': {
              description: 'AI profile created',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      data: { $ref: '#/components/schemas/AIProfile' },
                    },
                  },
                },
              },
            },
            '400': {
              description: 'Invalid input',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
          },
        },
      },
      '/api/ai/{id}': {
        get: {
          summary: 'Get AI profile by ID',
          operationId: 'getAI',
          tags: ['AI'],
          parameters: [
            {
              name: 'id',
              in: 'path',
              required: true,
              schema: { type: 'string' },
              example: 'claude-3-opus',
            },
          ],
          responses: {
            '200': {
              description: 'Successful response',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      data: { $ref: '#/components/schemas/AIProfile' },
                    },
                  },
                },
              },
            },
            '404': {
              description: 'AI not found',
              content: {
                'application/json': {
                  schema: { $ref: '#/components/schemas/Error' },
                },
              },
            },
          },
        },
        patch: {
          summary: 'Update AI profile',
          operationId: 'updateAI',
          tags: ['AI'],
          parameters: [
            {
              name: 'id',
              in: 'path',
              required: true,
              schema: { type: 'string' },
            },
          ],
          requestBody: {
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/AIProfileUpdate' },
              },
            },
          },
          responses: {
            '200': {
              description: 'Updated successfully',
            },
            '404': {
              description: 'AI not found',
            },
          },
        },
        delete: {
          summary: 'Disconnect AI profile',
          operationId: 'deleteAI',
          tags: ['AI'],
          parameters: [
            {
              name: 'id',
              in: 'path',
              required: true,
              schema: { type: 'string' },
            },
          ],
          responses: {
            '200': {
              description: 'Disconnected successfully',
            },
            '404': {
              description: 'AI not found',
            },
          },
        },
      },
      '/api/workflows': {
        get: {
          summary: 'List all workflows',
          operationId: 'listWorkflows',
          tags: ['Workflows'],
          responses: {
            '200': {
              description: 'Array of workflows',
            },
          },
        },
        post: {
          summary: 'Create a workflow',
          description: 'Create a new AI orchestration workflow.',
          operationId: 'createWorkflow',
          tags: ['Workflows'],
          requestBody: {
            content: {
              'application/json': {
                schema: { $ref: '#/components/schemas/WorkflowCreate' },
              },
            },
          },
          responses: {
            '201': {
              description: 'Workflow created',
            },
          },
        },
      },
      '/api/identity/prove': {
        post: {
          summary: 'Generate ZK identity proof',
          description: 'Generate a Semaphore identity commitment for human verification.',
          operationId: 'generateIdentityProof',
          tags: ['Identity'],
          requestBody: {
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    trapdoor: { type: 'string', description: 'Random trapdoor value' },
                    nullifier: { type: 'string', description: 'Random nullifier value' },
                  },
                },
              },
            },
          },
          responses: {
            '200': {
              description: 'Identity commitment generated',
              content: {
                'application/json': {
                  schema: {
                    type: 'object',
                    properties: {
                      commitment: { type: 'string' },
                      nullifierHash: { type: 'string' },
                    },
                  },
                },
              },
            },
          },
        },
      },
    },
    components: {
      schemas: {
        AIProfile: {
          type: 'object',
          required: ['id', 'name', 'creator', 'type', 'description', 'flair', 'url'],
          properties: {
            id: { type: 'string', example: 'claude-3-opus' },
            name: { type: 'string', example: 'Claude 3 Opus' },
            creator: { type: 'string', example: 'Anthropic' },
            type: {
              type: 'string',
              enum: ['LLM', 'Image', 'Code', 'Audio'],
              example: 'LLM',
            },
            description: { type: 'string' },
            flair: { type: 'string', description: 'Personality description' },
            tags: {
              type: 'array',
              items: { type: 'string' },
              example: ['Analysis', 'Coding', 'Safety'],
            },
            color: { type: 'string', example: 'bg-orange-500' },
            icon: { type: 'string', example: 'UserCheck' },
            url: { type: 'string', format: 'uri' },
            isConnected: { type: 'boolean', default: false },
          },
        },
        AIProfileCreate: {
          type: 'object',
          required: ['id', 'name', 'creator', 'type', 'description', 'flair', 'url'],
          properties: {
            id: { type: 'string' },
            name: { type: 'string' },
            creator: { type: 'string' },
            type: { type: 'string', enum: ['LLM', 'Image', 'Code', 'Audio'] },
            description: { type: 'string' },
            flair: { type: 'string' },
            tags: { type: 'array', items: { type: 'string' } },
            color: { type: 'string' },
            icon: { type: 'string' },
            url: { type: 'string' },
          },
        },
        AIProfileUpdate: {
          type: 'object',
          properties: {
            isConnected: { type: 'boolean' },
            url: { type: 'string' },
            flair: { type: 'string' },
          },
        },
        WorkflowCreate: {
          type: 'object',
          required: ['name', 'steps'],
          properties: {
            name: { type: 'string', example: 'Blog Post Generator' },
            description: { type: 'string' },
            steps: {
              type: 'array',
              items: {
                type: 'object',
                properties: {
                  aiId: { type: 'string' },
                  prompt: { type: 'string' },
                  outputKey: { type: 'string' },
                },
              },
            },
          },
        },
        Error: {
          type: 'object',
          properties: {
            error: { type: 'string' },
          },
        },
      },
    },
  };

  return NextResponse.json(spec, {
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
    },
  });
}

