// src/lib/ais.ts

export interface AIProfile {
  id: string;
  name: string;
  creator: string;
  type: 'LLM' | 'Image' | 'Code' | 'Audio';
  description: string;
  flair: string; // The "Grok for Flair" part
  tags: string[];
  color: string; // For visual flair
  icon: string; // Lucide React icon name
  url: string;
  isConnected: boolean;
}

export const aiRoster: AIProfile[] = [
  {
    id: 'claude-3-opus',
    name: 'Claude 3 Opus',
    creator: 'Anthropic',
    type: 'LLM',
    description: 'The most powerful Claude model, for complex tasks.',
    flair: 'The meticulous, cautious expert. The "red teamer" who finds the flaws in your plan.',
    tags: ['Analysis', 'Long-form', 'Safety', 'Coding', 'Non-toxic'],
    color: 'bg-orange-500',
    icon: 'UserCheck',
    url: 'https://claude.ai',
    isConnected: true,
  },
  {
    id: 'gpt-4-turbo',
    name: 'GPT-4 Turbo',
    creator: 'OpenAI',
    type: 'LLM',
    description: 'The latest GPT-4 model with improved speed and reasoning.',
    flair: 'The versatile, creative powerhouse. Your go-to for brainstorming and synthesis.',
    tags: ['Creative', 'Coding', 'Reasoning', 'Versatile'],
    color: 'bg-emerald-500',
    icon: 'Sparkles',
    url: 'https://chat.openai.com',
    isConnected: true,
  },
  {
    id: 'github-copilot',
    name: 'GitHub Copilot',
    creator: 'GitHub',
    type: 'Code',
    description: 'Your AI pair programmer.',
    flair: 'The lightning-fast, literal executor. Turns your thoughts into code.',
    tags: ['Code', 'Autocomplete', 'Speed', 'Boilerplate'],
    color: 'bg-gray-800',
    icon: 'Code',
    url: 'https://github.com/features/copilot',
    isConnected: true,
  },
  {
    id: 'midjourney',
    name: 'Midjourney',
    creator: 'Midjourney Inc.',
    type: 'Image',
    description: 'An AI lab that creates images from textual descriptions.',
    flair: 'The visionary, wordless artist. Creates stunning visuals from a whisper.',
    tags: ['Image', 'Artistic', 'Creative', 'Abstract'],
    color: 'bg-violet-500',
    icon: 'Image',
    url: 'https://www.midjourney.com',
    isConnected: true,
  },
  {
    id: 'venice',
    name: 'Venice',
    creator: 'You & AI',
    type: 'LLM',
    description: 'Your strategic synthesizer and sparring partner.',
    flair: 'The whiteboard. Helps you structure ideas and challenge assumptions.',
    tags: ['Strategy', 'Synthesis', 'Framework', 'Sparring'],
    color: 'bg-blue-600',
    icon: 'Waves',
    url: 'https://chat.openai.com', // Placeholder
    isConnected: true,
  },
];




