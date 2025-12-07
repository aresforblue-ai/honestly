import { create } from "zustand";
import { Edge, Node, addEdge, applyEdgeChanges, applyNodeChanges, NodeChange, EdgeChange, Connection } from "reactflow";

type WorkflowState = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
};

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

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: initialNodes,
  edges: initialEdges,
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
}));

