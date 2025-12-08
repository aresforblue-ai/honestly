import { create } from "zustand";
import { Edge, Node, addEdge, applyEdgeChanges, applyNodeChanges, NodeChange, EdgeChange, Connection } from "reactflow";

type WorkflowState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  saveWorkflow: () => void;
  loadWorkflow: () => void;
  resetWorkflow: () => void;
  lastSavedAt?: string;
};

const STORAGE_KEY = "conductme:workflow";

const initialNodes: Node[] = [
  {
    id: "llm",
    type: "default",
    position: { x: 100, y: 100 },
    data: { label: "LLM (Local)" },
  },
  {
    id: "vision",
    type: "default",
    position: { x: 400, y: 80 },
    data: { label: "Vision" },
  },
  {
    id: "tts",
    type: "default",
    position: { x: 400, y: 220 },
    data: { label: "TTS" },
  },
];

const initialEdges: Edge[] = [
  { id: "e-llm-vision", source: "llm", target: "vision", animated: true },
  { id: "e-llm-tts", source: "llm", target: "tts", animated: true },
];

const isBrowser = () => typeof window !== "undefined";

export const useWorkflowStore = create<WorkflowState>((set, get) => {
  // Lazy-init from storage
  let storedNodes = initialNodes;
  let storedEdges = initialEdges;
  if (isBrowser()) {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        storedNodes = parsed.nodes || initialNodes;
        storedEdges = parsed.edges || initialEdges;
      }
    } catch {
      storedNodes = initialNodes;
      storedEdges = initialEdges;
    }
  }

  const saveWorkflow = () => {
    if (!isBrowser()) return;
    const snapshot = { nodes: get().nodes, edges: get().edges };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
    set({ lastSavedAt: new Date().toISOString() });
  };

  const loadWorkflow = () => {
    if (!isBrowser()) return;
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return;
      const parsed = JSON.parse(raw);
      set({
        nodes: parsed.nodes || initialNodes,
        edges: parsed.edges || initialEdges,
      });
    } catch {
      // ignore
    }
  };

  const resetWorkflow = () => {
    set({ nodes: initialNodes, edges: initialEdges });
  };

  return {
    nodes: storedNodes,
    edges: storedEdges,
    onNodesChange: (changes: NodeChange[]) =>
      set({
        nodes: applyNodeChanges(changes, get().nodes),
      }),
    onEdgesChange: (changes: EdgeChange[]) =>
      set({
        edges: applyEdgeChanges(changes, get().edges),
      }),
    onConnect: (connection: Connection) =>
      set({
        edges: addEdge({ ...connection, animated: true }, get().edges),
      }),
    saveWorkflow,
    loadWorkflow,
    resetWorkflow,
    lastSavedAt: undefined,
  };
});

