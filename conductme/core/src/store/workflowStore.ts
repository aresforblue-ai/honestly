import { create } from "zustand";
import { Edge, Node, addEdge, applyEdgeChanges, applyNodeChanges, NodeChange, EdgeChange, Connection, getOutgoers } from "reactflow";

type ExecutionStatus = 'idle' | 'running' | 'completed' | 'error';

type NodeData = {
  label: string;
  status?: 'pending' | 'running' | 'completed' | 'error';
  output?: any;
};

type WorkflowState = {
  nodes: Node<NodeData>[];
  edges: Edge[];
  executionStatus: ExecutionStatus;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  onConnect: (connection: Connection) => void;
  saveWorkflow: () => void;
  loadWorkflow: () => void;
  resetWorkflow: () => void;
  executeWorkflow: () => Promise<void>;
  lastSavedAt?: string;
};

const STORAGE_KEY = "conductme:workflow";

const initialNodes: Node<NodeData>[] = [
  {
    id: "llm",
    type: "default",
    position: { x: 100, y: 100 },
    data: { label: "LLM (Local)", status: 'pending' },
    style: { background: '#fff', border: '1px solid #777', width: 150 },
  },
  {
    id: "vision",
    type: "default",
    position: { x: 400, y: 80 },
    data: { label: "Vision", status: 'pending' },
    style: { background: '#fff', border: '1px solid #777', width: 150 },
  },
  {
    id: "tts",
    type: "default",
    position: { x: 400, y: 220 },
    data: { label: "TTS", status: 'pending' },
    style: { background: '#fff', border: '1px solid #777', width: 150 },
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
    set({ nodes: initialNodes, edges: initialEdges, executionStatus: 'idle' });
  };

  const updateNodeStatus = (nodeId: string, status: 'pending' | 'running' | 'completed' | 'error') => {
    set({
      nodes: get().nodes.map((n) => {
        if (n.id === nodeId) {
          let style = { ...n.style };
          switch (status) {
            case 'running':
              style = { ...style, border: '2px solid #eab308', background: '#fefce8' }; // yellow
              break;
            case 'completed':
              style = { ...style, border: '2px solid #22c55e', background: '#f0fdf4' }; // green
              break;
            case 'error':
              style = { ...style, border: '2px solid #ef4444', background: '#fef2f2' }; // red
              break;
            default:
              style = { ...style, border: '1px solid #777', background: '#fff' };
          }
          
          return { 
            ...n, 
            style,
            data: { ...n.data, status } 
          };
        }
        return n;
      }),
    });
  };

  const executeNode = async (node: Node<NodeData>) => {
    updateNodeStatus(node.id, 'running');
    
    // Simulate execution time
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // TODO: In the future, call actual API based on node type
    console.log(`Executed node ${node.id} (${node.data.label})`);
    
    updateNodeStatus(node.id, 'completed');
  };

  const executeWorkflow = async () => {
    const { nodes, edges } = get();
    if (nodes.length === 0) return;

    set({ executionStatus: 'running' });

    // Reset all statuses
    set({
      nodes: nodes.map(n => ({ 
        ...n, 
        style: { ...n.style, border: '1px solid #777', background: '#fff' },
        data: { ...n.data, status: 'pending' } 
      }))
    });

    try {
      // Find starting nodes (nodes with no incoming edges)
      const incomingEdges = new Set(edges.map(e => e.target));
      const startNodes = nodes.filter(n => !incomingEdges.has(n.id));

      const queue = startNodes.length > 0 ? [...startNodes] : [nodes[0]];
      const visited = new Set<string>();

      while (queue.length > 0) {
        const currentNode = queue.shift();
        if (!currentNode || visited.has(currentNode.id)) continue;

        await executeNode(currentNode);
        visited.add(currentNode.id);

        // Find next nodes
        const outgoers = getOutgoers(currentNode, get().nodes, get().edges);
        outgoers.forEach(outgoer => {
            if (!visited.has(outgoer.id)) {
                queue.push(outgoer);
            }
        });
      }

      set({ executionStatus: 'completed' });
    } catch (error) {
      console.error("Workflow execution failed", error);
      set({ executionStatus: 'error' });
    }
  };

  return {
    nodes: storedNodes,
    edges: storedEdges,
    executionStatus: 'idle',
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
    executeWorkflow,
    lastSavedAt: undefined,
  };
});
