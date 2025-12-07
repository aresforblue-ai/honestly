import React from "react";
import ReactFlow, { MiniMap, Controls, Background } from "reactflow";
import "reactflow/dist/style.css";
import { useWorkflowStore } from "@/store/workflowStore";
import { Button } from "@/components/ui/button";

export default function WorkflowsPage() {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, saveWorkflow, loadWorkflow, resetWorkflow, lastSavedAt } =
    useWorkflowStore();

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="border-b">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Workflow / Ensemble Builder</h1>
            <p className="text-muted-foreground">Drag, connect, and orchestrate your local models.</p>
            {lastSavedAt && <p className="text-xs text-muted-foreground">Last saved: {lastSavedAt}</p>}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={loadWorkflow}>
              Load
            </Button>
            <Button variant="outline" size="sm" onClick={saveWorkflow}>
              Save
            </Button>
            <Button variant="secondary" size="sm" onClick={resetWorkflow}>
              Reset
            </Button>
          </div>
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

