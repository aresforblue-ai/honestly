import React from "react";
import ReactFlow, { MiniMap, Controls, Background } from "reactflow";
import "reactflow/dist/style.css";
import { useWorkflowStore } from "@/store/workflowStore";

export default function WorkflowsPage() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect } = useWorkflowStore();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b">
        <div className="container mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold">Workflow / Ensemble Builder</h1>
          <p className="text-muted-foreground">Drag, connect, and orchestrate your local models.</p>
        </div>
      </div>
      <div className="container mx-auto px-6 py-6 h-[80vh]">
        <div className="h-full rounded-lg border bg-card">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView
          >
            <MiniMap />
            <Controls />
            <Background variant="dots" gap={12} size={1} />
          </ReactFlow>
        </div>
      </div>
    </div>
  );
}

