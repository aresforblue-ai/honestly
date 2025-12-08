"use client";

import { AIProfile } from '@/lib/ais';
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ExternalLink, Power, UserCheck, Sparkles, Code, Image, Waves, Zap, Shield, Lock } from 'lucide-react';

// Icon mapping for dynamic rendering
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  UserCheck,
  Sparkles,
  Code,
  Image,
  Waves,
  Zap,
  Shield,
};

interface AICardProps {
  ai: AIProfile;
}

export function AICard({ ai }: AICardProps) {
  const IconComponent = iconMap[ai.icon] || UserCheck;
  
  // Dynamic gradient based on AI color
  const gradientMap: Record<string, string> = {
    'bg-blue-500': 'from-blue-500 to-blue-600',
    'bg-purple-500': 'from-purple-500 to-violet-600',
    'bg-green-500': 'from-emerald-500 to-green-600',
    'bg-orange-500': 'from-orange-500 to-amber-600',
    'bg-pink-500': 'from-pink-500 to-rose-600',
    'bg-indigo-500': 'from-indigo-500 to-purple-600',
  };
  
  const gradient = gradientMap[ai.color] || 'from-blue-500 to-indigo-600';
  
  return (
    <Card className="group relative flex flex-col justify-between h-full overflow-hidden border-border/30 bg-card/40 backdrop-blur-xl transition-all duration-300 hover:border-primary/40 hover:shadow-xl hover:shadow-primary/5 hover:-translate-y-1">
      {/* Animated background glow */}
      <div className={`absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 bg-gradient-to-br ${gradient} blur-3xl -z-10`} style={{ transform: 'scale(0.8)', opacity: 0.1 }} />
      
      {/* Status indicator line */}
      <div className={`absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r ${gradient} ${ai.isConnected ? 'opacity-100' : 'opacity-30'}`} />
      
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-4">
          {/* Avatar with glow effect */}
          <div className="relative">
            <Avatar className={`h-12 w-12 bg-gradient-to-br ${gradient} text-white ring-2 ring-background shadow-lg`}>
              <AvatarFallback className="bg-transparent">
                <IconComponent className="h-6 w-6" />
              </AvatarFallback>
            </Avatar>
            {/* Pulse ring for connected status */}
            {ai.isConnected && (
              <span className="absolute -bottom-0.5 -right-0.5 flex h-4 w-4">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-4 w-4 bg-green-500 border-2 border-background"></span>
              </span>
            )}
          </div>
          
          <div className="flex-1 min-w-0">
            <CardTitle className="text-lg font-semibold truncate group-hover:text-primary transition-colors">
              {ai.name}
            </CardTitle>
            <CardDescription className="text-sm text-muted-foreground/80 truncate">
              {ai.creator}
            </CardDescription>
          </div>
          
          {/* ZK Verified badge */}
          <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-primary/10 border border-primary/20">
            <Lock className="h-3 w-3 text-primary" />
            <span className="text-[10px] font-medium text-primary">ZK</span>
          </div>
        </div>
      </CardHeader>
      
      <div className="px-6 pb-5 space-y-4">
        {/* Flair text with subtle styling */}
        <p className="text-sm text-muted-foreground/90 italic leading-relaxed line-clamp-2">
          "{ai.flair}"
        </p>
        
        {/* Tags with improved styling */}
        <div className="flex flex-wrap gap-1.5">
          {ai.tags.slice(0, 4).map((tag) => (
            <Badge 
              key={tag} 
              variant="secondary" 
              className="text-[10px] px-2 py-0.5 bg-secondary/50 hover:bg-secondary/80 transition-colors cursor-default"
            >
              {tag}
            </Badge>
          ))}
          {ai.tags.length > 4 && (
            <Badge variant="outline" className="text-[10px] px-2 py-0.5">
              +{ai.tags.length - 4}
            </Badge>
          )}
        </div>
        
        {/* Actions */}
        <div className="flex justify-between items-center pt-2 border-t border-border/30">
          <Button 
            variant="default" 
            size="sm" 
            className={`bg-gradient-to-r ${gradient} hover:opacity-90 transition-opacity shadow-md`}
            asChild
          >
            <a href={ai.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="mr-2 h-3.5 w-3.5" />
              Launch
            </a>
          </Button>
          
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="icon" 
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <Zap className="h-4 w-4" />
            </Button>
            <Button 
              variant="ghost" 
              size="icon" 
              className={`h-8 w-8 transition-colors ${ai.isConnected ? 'text-green-500 hover:text-red-500' : 'text-muted-foreground hover:text-green-500'}`}
            >
              <Power className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
