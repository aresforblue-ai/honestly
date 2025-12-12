import { aiRoster } from "@/lib/ais";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import Link from "next/link";
import { Plus, Bot, Code, Image as ImageIcon, Sparkles, UserCheck, Waves } from "lucide-react";

const iconMap: Record<string, any> = {
  Bot,
  Code,
  Image: ImageIcon,
  Sparkles,
  UserCheck,
  Waves
};

export default function AgentsPage() {
  return (
    <div className="container mx-auto px-6 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
           <h1 className="text-3xl font-bold tracking-tight">AI Agents</h1>
           <p className="text-muted-foreground">Manage and orchestrate your AI workforce.</p>
        </div>
        <Link href="/agents/register">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Register New Agent
          </Button>
        </Link>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {aiRoster.map((agent) => {
          const Icon = iconMap[agent.icon] || Bot;
          
          return (
            <Link href={`/agents/${agent.id}`} key={agent.id}>
               <Card className="h-full hover:border-primary/50 transition-colors cursor-pointer flex flex-col">
                 <CardHeader>
                   <div className="flex items-center justify-between">
                     <div className={`p-2 rounded-md ${agent.color} text-white`}>
                       <Icon className="h-6 w-6" />
                     </div>
                     <Badge variant={agent.isConnected ? "default" : "secondary"}>
                       {agent.isConnected ? "Connected" : "Offline"}
                     </Badge>
                   </div>
                   <CardTitle className="mt-4">{agent.name}</CardTitle>
                   <CardDescription>{agent.creator}</CardDescription>
                 </CardHeader>
                 <CardContent className="flex-grow">
                   <p className="text-sm text-muted-foreground mb-4">
                     {agent.description}
                   </p>
                   <div className="flex flex-wrap gap-2">
                     {agent.tags.slice(0, 3).map(tag => (
                       <Badge key={tag} variant="outline" className="text-xs">
                         {tag}
                       </Badge>
                     ))}
                     {agent.tags.length > 3 && (
                       <Badge variant="outline" className="text-xs">+{agent.tags.length - 3}</Badge>
                     )}
                   </div>
                 </CardContent>
                 <CardFooter className="pt-0 text-xs text-muted-foreground italic border-t p-4 mt-auto">
                   "{agent.flair}"
                 </CardFooter>
               </Card>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
