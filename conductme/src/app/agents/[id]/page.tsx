"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { aiRoster } from "@/lib/ais";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area"; // Check if this exists, else use div
import { Bot, User, Send, ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;
  const agent = aiRoster.find((a) => a.id === id);

  const [prompt, setPrompt] = useState("");
  const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string }>>([]);
  const [loading, setLoading] = useState(false);

  if (!agent) {
    return (
      <div className="container mx-auto px-6 py-8 text-center">
        <h1 className="text-2xl font-bold">Agent Not Found</h1>
        <Link href="/agents">
          <Button variant="link">Back to Agents</Button>
        </Link>
      </div>
    );
  }

  const handleSend = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (!prompt.trim() || loading) return;

    const newMessages = [...messages, { role: 'user' as const, content: prompt }];
    setMessages(newMessages);
    setPrompt("");
    setLoading(true);

    try {
      const res = await fetch(`/api/ai/${agent.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: newMessages,
        }),
      });

      if (!res.ok) throw new Error("Failed to send message");

      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.data.response }]);
    } catch (error) {
      console.error(error);
      setMessages(prev => [...prev, { role: 'assistant', content: "Error: Failed to get response from agent." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-8 h-[calc(100vh-4rem)] flex flex-col">
      <div className="flex items-center gap-4 mb-6">
        <Link href="/agents">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-4 w-4" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            {agent.name}
            <Badge variant={agent.isConnected ? "default" : "secondary"}>
              {agent.isConnected ? "Online" : "Offline"}
            </Badge>
          </h1>
          <p className="text-muted-foreground">{agent.description}</p>
        </div>
      </div>

      <div className="flex-grow border rounded-md bg-card shadow-sm flex flex-col overflow-hidden">
        <div className="p-4 border-b bg-muted/30">
          <p className="text-sm italic text-muted-foreground">"{agent.flair}"</p>
        </div>
        
        <div className="flex-grow overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-muted-foreground mt-20">
              <Bot className="h-12 w-12 mx-auto mb-2 opacity-20" />
              <p>Start a conversation with {agent.name}</p>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div
                key={idx}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    msg.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <div className="flex items-center gap-2 mb-1 opacity-70 text-xs">
                    {msg.role === 'user' ? <User className="h-3 w-3" /> : <Bot className="h-3 w-3" />}
                    <span>{msg.role === 'user' ? 'You' : agent.name}</span>
                  </div>
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="flex justify-start">
              <div className="bg-muted rounded-lg p-3">
                 <Loader2 className="h-4 w-4 animate-spin" />
              </div>
            </div>
          )}
        </div>

        <div className="p-4 border-t bg-background">
          <form onSubmit={handleSend} className="flex gap-2">
            <Input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder={`Message ${agent.name}...`}
              disabled={loading}
              className="flex-grow"
            />
            <Button type="submit" disabled={loading || !prompt.trim()}>
              <Send className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
