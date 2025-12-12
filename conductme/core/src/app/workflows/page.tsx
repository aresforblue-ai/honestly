import React from "react";
import ReactFlow, { MiniMap, Controls, Background } from "reactflow";
import "reactflow/dist/style.css";
import { useWorkflowStore } from "@/store/workflowStore";
import { Button } from "@/components/ui/button";
import { Play, RotateCcw, Save, Upload } from "lucide-react";

export default function WorkflowsPage() {
  const { 
    nodes, 
    edges, 
    onNodesChange, 
    onEdgesChange, 
    onConnect, 
    saveWorkflow, 
    loadWorkflow, 
    resetWorkflow, 
    executeWorkflow,
    executionStatus,
    lastSavedAt 
  } = useWorkflowStore();

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
            <Button 
              className="bg-green-600 hover:bg-green-700 text-white"
              size="sm" 
              onClick={executeWorkflow}
              disabled={executionStatus === 'running'}
            >
              <Play className="mr-2 h-4 w-4" />
              {executionStatus === 'running' ? 'Running...' : 'Run Workflow'}
            </Button>
            <div className="w-px h-8 bg-border mx-2" />
            <Button variant="outline" size="sm" onClick={loadWorkflow}>
              <Upload className="mr-2 h-4 w-4" />
              Load
            </Button>
            <Button variant="outline" size="sm" onClick={saveWorkflow}>
              <Save className="mr-2 h-4 w-4" />
              Save
            </Button>
            <Button variant="ghost" size="sm" onClick={resetWorkflow}>
              <RotateCcw className="mr-2 h-4 w-4" />
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
