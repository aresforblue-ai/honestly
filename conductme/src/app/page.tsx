"use client";

import { useState, useEffect } from 'react';
import { AICard } from '@/components/ai-card';
import { CommandPalette } from '@/components/command-palette';
import { Button } from '@/components/ui/button';
import { aiRoster } from '@/lib/ais';
import { Search, Plus, Zap, Shield, Waves } from 'lucide-react';

export default function HomePage() {
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  // Keyboard shortcut for command palette
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setCommandPaletteOpen((open) => !open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground gradient-bg">
      {/* Header */}
      <header className="border-b border-border/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
              <Waves className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">
                ConductMe
              </h1>
              <p className="text-xs text-muted-foreground">AI Orchestration</p>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCommandPaletteOpen(true)}
              className="hidden sm:flex"
            >
              <Search className="mr-2 h-4 w-4" />
              Quick Find
              <kbd className="ml-2 pointer-events-none hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium opacity-100 sm:flex">
                ⌘K
              </kbd>
            </Button>
            <Button size="sm" className="bg-gradient-to-r from-blue-500 to-violet-600 hover:from-blue-600 hover:to-violet-700">
              <Plus className="mr-2 h-4 w-4" />
              Add AI
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        {/* Hero Section */}
        <div className="mb-12 text-center">
          <h2 className="text-4xl font-bold tracking-tight mb-3">
            Your AI Ensemble
          </h2>
          <p className="text-muted-foreground max-w-2xl mx-auto">
            Orchestrate, coordinate, and unleash your AI agents. Each one proven human-gated with zero-knowledge cryptography.
          </p>
        </div>

        {/* Stats Bar */}
        <div className="flex justify-center gap-8 mb-10">
          <div className="flex items-center gap-2 text-sm">
            <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
            <span className="text-muted-foreground">{aiRoster.filter(ai => ai.isConnected).length} Connected</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Zap className="h-4 w-4 text-yellow-500" />
            <span className="text-muted-foreground">Ready to Conduct</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Shield className="h-4 w-4 text-blue-500" />
            <span className="text-muted-foreground">ZK-Verified</span>
          </div>
        </div>

        {/* AI Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {aiRoster.map((ai) => (
            <AICard key={ai.id} ai={ai} />
          ))}
        </div>

        {/* Footer CTA */}
        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-muted/50 text-sm text-muted-foreground">
            <Shield className="h-4 w-4" />
            Powered by Groth16 + Semaphore identity proofs
          </div>
        </div>
      </main>

      {/* Command Palette */}
      <CommandPalette open={commandPaletteOpen} onOpenChange={setCommandPaletteOpen} />
    </div>
  );
}
