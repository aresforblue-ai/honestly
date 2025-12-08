"use client";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { aiRoster } from '@/lib/ais';
import { Badge } from '@/components/ui/badge';

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Type a command or search for an AI..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Suggestions">
          <CommandItem>
            <span className="mr-2">🎯</span>
            <span>Find an AI for &quot;writing secure code&quot;</span>
          </CommandItem>
          <CommandItem>
            <span className="mr-2">🔗</span>
            <span>Create a new workflow</span>
          </CommandItem>
          <CommandItem>
            <span className="mr-2">⚡</span>
            <span>Run &quot;Blog Post&quot; ensemble</span>
          </CommandItem>
        </CommandGroup>
        <CommandGroup heading="All AIs">
          {aiRoster.map((ai) => (
            <CommandItem key={ai.id} onSelect={() => window.open(ai.url, '_blank')}>
              <div className="flex items-center justify-between w-full">
                <span>{ai.name}</span>
                <Badge variant="outline">{ai.type}</Badge>
              </div>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
