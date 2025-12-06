import { AIProfile } from "@/lib/ais";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Power } from "lucide-react";
import * as LucideIcons from "lucide-react";

const Icon = ({ name }: { name: string }) => {
  const LucideIcon = (LucideIcons as Record<string, any>)[name];
  if (!LucideIcon) return null;
  return <LucideIcon className="h-5 w-5" />;
};

interface AICardProps {
  ai: AIProfile;
}

export function AICard({ ai }: AICardProps) {
  return (
    <Card className="flex flex-col justify-between h-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-3">
          <Avatar className={`${ai.color} text-white`}>
            <AvatarFallback>
              <Icon name={ai.icon} />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <CardTitle className="text-lg">{ai.name}</CardTitle>
            <CardDescription className="text-sm">{ai.creator}</CardDescription>
          </div>
          <div
            className={`w-3 h-3 rounded-full ${
              ai.isConnected ? "bg-green-500" : "bg-red-500"
            }`}
            title={ai.isConnected ? "Connected" : "Disconnected"}
          />
        </div>
      </CardHeader>
      <div className="px-6 pb-3 space-y-3">
        <p className="text-sm text-muted-foreground">{ai.flair}</p>
        <div className="flex flex-wrap gap-1">
          {ai.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
        <div className="flex justify-between items-center pt-2">
          <Button variant="outline" size="sm" asChild>
            <a href={ai.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="mr-2 h-4 w-4" />
              Launch
            </a>
          </Button>
          <Button variant="ghost" size="sm">
            <Power className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}
import { AIProfile } from "@/lib/ais";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ExternalLink, Power } from "lucide-react";
import * as LucideIcons from "lucide-react";

const Icon = ({ name }: { name: string }) => {
  const LucideIcon = (LucideIcons as any)[name];
  return LucideIcon ? <LucideIcon className="h-5 w-5" /> : null;
};

interface AICardProps {
  ai: AIProfile;
}

export function AICard({ ai }: AICardProps) {
  return (
    <Card className="flex flex-col justify-between h-full hover:shadow-lg transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center space-x-3">
          <Avatar className={`${ai.color} text-white`}>
            <AvatarFallback>
              <Icon name={ai.icon} />
            </AvatarFallback>
          </Avatar>
          <div className="flex-1">
            <CardTitle className="text-lg">{ai.name}</CardTitle>
            <CardDescription className="text-sm">{ai.creator}</CardDescription>
          </div>
          <div
            className={`w-3 h-3 rounded-full ${ai.isConnected ? "bg-green-500" : "bg-red-500"}`}
            title={ai.isConnected ? "Connected" : "Disconnected"}
          />
        </div>
      </CardHeader>
      <div className="px-6 pb-3 space-y-3">
        <p className="text-sm text-muted-foreground">{ai.flair}</p>
        <div className="flex flex-wrap gap-1">
          {ai.tags.map((tag) => (
            <Badge key={tag} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
        </div>
        <div className="flex justify-between items-center pt-2">
          <Button variant="outline" size="sm" asChild>
            <a href={ai.url} target="_blank" rel="noopener noreferrer">
              <ExternalLink className="mr-2 h-4 w-4" />
              Launch
            </a>
          </Button>
          <Button variant="ghost" size="sm" aria-label="Toggle power">
            <Power className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </Card>
  );
}


