"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ArrowLeft, Loader2 } from "lucide-react";
import Link from "next/link";
import { useToast } from "@/components/ui/use-toast"; // Assuming this exists, if not I'll skip toast

export default function RegisterAgentPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  // const { toast } = useToast(); 

  const [formData, setFormData] = useState({
    id: "",
    name: "",
    creator: "",
    type: "LLM",
    description: "",
    flair: "",
    tags: "",
    url: "",
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.id]: e.target.value });
  };

  const handleSelectChange = (value: string) => {
    setFormData({ ...formData, type: value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const payload = {
        ...formData,
        tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
        isConnected: true, // Auto-connect
        color: 'bg-gray-500', // Default
        icon: 'Bot'
      };

      const res = await fetch('/api/ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || 'Failed to register agent');
      }

      // toast({ title: "Agent Registered", description: `${formData.name} has been added to the roster.` });
      router.push('/agents');
      router.refresh();
    } catch (error) {
      console.error(error);
      alert('Error registering agent: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-6 py-8 max-w-2xl">
      <div className="mb-6">
        <Link href="/agents">
          <Button variant="ghost" size="sm" className="mb-2">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Agents
          </Button>
        </Link>
        <h1 className="text-3xl font-bold">Register New Agent</h1>
        <p className="text-muted-foreground">Add a new AI model or agent to your orchestration layer.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit}>
          <CardHeader>
            <CardTitle>Agent Details</CardTitle>
            <CardDescription>All fields are required for the registry.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="id">ID (Slug)</Label>
                <Input id="id" placeholder="e.g. my-agent-v1" value={formData.id} onChange={handleChange} required pattern="[a-z0-9-]+" />
                <p className="text-[10px] text-muted-foreground">Lowercase, numbers, hyphens only.</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="type">Type</Label>
                <Select onValueChange={handleSelectChange} defaultValue={formData.type}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LLM">LLM</SelectItem>
                    <SelectItem value="Image">Image Generation</SelectItem>
                    <SelectItem value="Code">Code Assistant</SelectItem>
                    <SelectItem value="Audio">Audio/Speech</SelectItem>
                    <SelectItem value="Agent">Autonomous Agent</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="name">Display Name</Label>
              <Input id="name" placeholder="e.g. My Custom Agent" value={formData.name} onChange={handleChange} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="creator">Creator / Provider</Label>
              <Input id="creator" placeholder="e.g. OpenAI, Anthropic, or Self-Hosted" value={formData.creator} onChange={handleChange} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="url">API Endpoint / URL</Label>
              <Input id="url" placeholder="https://api..." value={formData.url} onChange={handleChange} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description</Label>
              <Textarea id="description" placeholder="What does this agent do?" value={formData.description} onChange={handleChange} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="flair">Flavor Text (Personality)</Label>
              <Input id="flair" placeholder="e.g. The helpful coding wizard." value={formData.flair} onChange={handleChange} required />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tags">Tags (comma separated)</Label>
              <Input id="tags" placeholder="coding, analysis, creative" value={formData.tags} onChange={handleChange} />
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button type="submit" disabled={loading}>
              {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Register Agent
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
