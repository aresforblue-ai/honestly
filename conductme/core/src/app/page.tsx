// src/app/page.tsx

"use client";

import { useState } from 'react';
import { AICard } from '@/components/ai-card';
import { CommandPalette } from '@/components/command-palette';
import { Button } from '@/components/ui/button';
import { aiRoster } from '@/lib/ais';
import { Search, Plus } from 'lucide-react';

export default function HomePage() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold">Conductme</h1>
          <div className="flex items-center space-x-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCommandPaletteOpen(true)}
            >
              <Search className="mr-2 h-4 w-4" />
              Quick Find
            </Button>
            <Button size="sm">
              <Plus className="mr-2 h-4 w-4" />
              Add AI
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold tracking-tight">Your AI Roster</h2>
          <p className="text-muted-foreground">
            The ensemble at your fingertips. Select, sort, and unleash.
          </p>
        </div>

        {/* AI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {aiRoster.map((ai) => (
            <AICard key={ai.id} ai={ai} />
          ))}
        </div>
      </main>

      {/* Command Palette */}
      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
    </div>
  );
}




