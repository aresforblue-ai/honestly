"use client";

/**
 * Real-time Anomaly Detection Dashboard
 * =====================================
 * 
 * Connects to WebSocket for live anomaly streaming.
 * Displays severity-coded alerts with agent details.
 * 
 * Features:
 * - Real-time WebSocket connection
 * - Severity filtering (critical/warning/all)
 * - Alert history with timestamps
 * - Connection status indicator
 * - Auto-reconnection
 */

import React, { useEffect, useState, useCallback, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Button } from "./ui/button";

interface AnomalyEvent {
  type: string;
  agent_id: string;
  anomaly_score: number;
  threshold: number;
  flags: string[];
  severity?: "critical" | "warning" | "info";
  timestamp: string;
  detection_time_ms?: number;
  zkml_proof_hash?: string;
}

interface ConnectionState {
  status: "connected" | "connecting" | "disconnected" | "error";
  room: string;
  lastPing?: string;
}

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/anomalies";

export function AnomalyDashboard() {
  const [anomalies, setAnomalies] = useState<AnomalyEvent[]>([]);
  const [connection, setConnection] = useState<ConnectionState>({
    status: "disconnected",
    room: "all",
  });
  const [filter, setFilter] = useState<"all" | "critical" | "warning">("all");
  const [stats, setStats] = useState({
    total: 0,
    critical: 0,
    warning: 0,
  });
  const [isSimulating, setIsSimulating] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);
  const simulateIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    setConnection(prev => ({ ...prev, status: "connecting" }));
    
    try {
      const ws = new WebSocket(`${WS_URL}?room=${filter}`);
      
      ws.onopen = () => {
        setConnection({ status: "connected", room: filter });
        
        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ action: "ping" }));
          }
        }, 30000);
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === "anomaly") {
            setAnomalies(prev => [data, ...prev].slice(0, 100)); // Keep last 100
            setStats(prev => ({
              total: prev.total + 1,
              critical: prev.critical + (data.severity === "critical" ? 1 : 0),
              warning: prev.warning + (data.severity === "warning" ? 1 : 0),
            }));
          } else if (data.type === "pong") {
            setConnection(prev => ({ ...prev, lastPing: data.timestamp }));
          } else if (data.type === "connected") {
            setConnection(prev => ({ ...prev, room: data.room }));
          }
        } catch (e) {
          console.error("Failed to parse WebSocket message:", e);
        }
      };
      
      ws.onerror = () => {
        setConnection(prev => ({ ...prev, status: "error" }));
      };
      
      ws.onclose = () => {
        setConnection(prev => ({ ...prev, status: "disconnected" }));
        
        // Clear intervals
        if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
        
        // Auto-reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          connect();
        }, 5000);
      };
      
      wsRef.current = ws;
    } catch (e) {
      console.error("WebSocket connection failed:", e);
      setConnection(prev => ({ ...prev, status: "error" }));
    }
  }, [filter]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnection({ status: "disconnected", room: filter });
  }, [filter]);

  // Subscribe to different room
  const subscribe = useCallback((room: "all" | "critical" | "warning") => {
    setFilter(room);
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action: "subscribe", room }));
    }
  }, []);

  // Connect on mount, cleanup on unmount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
      if (simulateIntervalRef.current) clearInterval(simulateIntervalRef.current);
    };
  }, [connect, disconnect]);

  // Simulate zkML anomalies for dev testing
  const simulateAnomaly = useCallback(() => {
    const chains = [
      { chain: "ethereum", prefix: "eth", color: "🔷" },
      { chain: "solana", prefix: "sol", color: "🟣" },
      { chain: "polygon", prefix: "poly", color: "🟪" },
      { chain: "arbitrum", prefix: "arb", color: "🔵" },
    ];
    const agentTypes = ["gpt4", "claude", "llama", "mistral", "gemini"];
    const flags = [
      "rapid_score_change",
      "unusual_pattern", 
      "threshold_breach",
      "cross_chain_drift",
      "wormhole_relay",
      "reputation_spike",
    ];

    const chain = chains[Math.floor(Math.random() * chains.length)];
    const agentType = agentTypes[Math.floor(Math.random() * agentTypes.length)];
    const score = 0.65 + Math.random() * 0.35;
    const severity: "critical" | "warning" | "info" = 
      score > 0.9 ? "critical" : score > 0.75 ? "warning" : "info";

    // Generate fake zkML proof hash (looks like real Groth16)
    const zkmlProofHash = "0x" + Array(64)
      .fill(0)
      .map(() => Math.floor(Math.random() * 16).toString(16))
      .join("");

    const anomaly: AnomalyEvent = {
      type: "anomaly",
      agent_id: `did:honestly:${chain.prefix}:agent:${agentType}-${Math.random().toString(36).slice(2, 8)}`,
      anomaly_score: score,
      threshold: 0.7,
      flags: flags.filter(() => Math.random() > 0.6).slice(0, 3),
      severity,
      timestamp: new Date().toISOString(),
      detection_time_ms: 30 + Math.random() * 200,
      zkml_proof_hash: Math.random() > 0.3 ? zkmlProofHash : undefined,
    };

    // Add cross-chain metadata for Phase 4 preview
    (anomaly as any).source_chain = chain.chain;
    (anomaly as any).relay_protocol = Math.random() > 0.5 ? "wormhole" : "native";

    setAnomalies(prev => [anomaly, ...prev].slice(0, 100));
    setStats(prev => ({
      total: prev.total + 1,
      critical: prev.critical + (severity === "critical" ? 1 : 0),
      warning: prev.warning + (severity === "warning" ? 1 : 0),
    }));
  }, []);

  // Toggle simulation mode
  const toggleSimulation = useCallback(() => {
    if (isSimulating) {
      if (simulateIntervalRef.current) {
        clearInterval(simulateIntervalRef.current);
        simulateIntervalRef.current = null;
      }
      setIsSimulating(false);
    } else {
      // Fire one immediately
      simulateAnomaly();
      // Then every 1.5-3 seconds
      simulateIntervalRef.current = setInterval(() => {
        if (Math.random() > 0.3) simulateAnomaly();
      }, 1500 + Math.random() * 1500);
      setIsSimulating(true);
    }
  }, [isSimulating, simulateAnomaly]);

  // Severity badge color
  const getSeverityColor = (severity?: string, score?: number) => {
    const s = severity || (score && score > 0.9 ? "critical" : score && score > 0.7 ? "warning" : "info");
    switch (s) {
      case "critical": return "bg-red-500 text-white animate-pulse";
      case "warning": return "bg-amber-500 text-black";
      default: return "bg-blue-500 text-white";
    }
  };

  // Connection status color
  const getStatusColor = () => {
    switch (connection.status) {
      case "connected": return "bg-emerald-500";
      case "connecting": return "bg-amber-500 animate-pulse";
      case "error": return "bg-red-500";
      default: return "bg-zinc-500";
    }
  };

  // Format timestamp
  const formatTime = (ts: string) => {
    try {
      return new Date(ts).toLocaleTimeString();
    } catch {
      return ts;
    }
  };

  // Filter anomalies
  const filteredAnomalies = anomalies.filter(a => {
    if (filter === "all") return true;
    return a.severity === filter;
  });

  return (
    <div className="space-y-6 p-6 min-h-screen bg-zinc-950">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            🛡️ Anomaly Detection
          </h1>
          <p className="text-zinc-400 mt-1">
            Real-time ML-powered agent monitoring
          </p>
        </div>
        
        {/* Connection Status */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
            <span className="text-zinc-400 text-sm capitalize">
              {connection.status}
            </span>
          </div>
          
          <Button
            variant={connection.status === "connected" ? "destructive" : "default"}
            size="sm"
            onClick={connection.status === "connected" ? disconnect : connect}
          >
            {connection.status === "connected" ? "Disconnect" : "Connect"}
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardDescription className="text-zinc-500">Total Anomalies</CardDescription>
            <CardTitle className="text-4xl font-mono text-white">{stats.total}</CardTitle>
          </CardHeader>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardDescription className="text-red-400">🚨 Critical</CardDescription>
            <CardTitle className="text-4xl font-mono text-red-500">{stats.critical}</CardTitle>
          </CardHeader>
        </Card>
        
        <Card className="bg-zinc-900 border-zinc-800">
          <CardHeader className="pb-2">
            <CardDescription className="text-amber-400">⚠️ Warning</CardDescription>
            <CardTitle className="text-4xl font-mono text-amber-500">{stats.warning}</CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Filter Buttons + Simulate */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {(["all", "critical", "warning"] as const).map((f) => (
            <Button
              key={f}
              variant={filter === f ? "default" : "outline"}
              size="sm"
              onClick={() => subscribe(f)}
              className={filter === f ? "bg-violet-600 hover:bg-violet-700" : "border-zinc-700 text-zinc-400"}
            >
              {f === "all" ? "All" : f === "critical" ? "🚨 Critical" : "⚠️ Warning"}
            </Button>
          ))}
        </div>
        
        {/* Dev Simulate Controls */}
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={simulateAnomaly}
            className="border-emerald-700 text-emerald-400 hover:bg-emerald-900/30"
          >
            ⚡ Fire Once
          </Button>
          <Button
            variant={isSimulating ? "destructive" : "outline"}
            size="sm"
            onClick={toggleSimulation}
            className={isSimulating 
              ? "bg-orange-600 hover:bg-orange-700 animate-pulse" 
              : "border-orange-700 text-orange-400 hover:bg-orange-900/30"}
          >
            {isSimulating ? "⏹ Stop Sim" : "▶ Auto Simulate"}
          </Button>
        </div>
      </div>

      {/* Anomaly Feed */}
      <Card className="bg-zinc-900 border-zinc-800">
        <CardHeader>
          <CardTitle className="text-white">Live Feed</CardTitle>
          <CardDescription className="text-zinc-500">
            Subscribed to: {connection.room}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredAnomalies.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <div className="text-4xl mb-4">📡</div>
              <p>Waiting for anomalies...</p>
              <p className="text-sm mt-2">
                {connection.status === "connected" 
                  ? "Connected and listening" 
                  : "Reconnecting..."}
              </p>
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {filteredAnomalies.map((anomaly, i) => (
                <div
                  key={`${anomaly.agent_id}-${anomaly.timestamp}-${i}`}
                  className="p-4 rounded-lg bg-zinc-800/50 border border-zinc-700/50 hover:border-zinc-600 transition-colors"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-2">
                        <Badge className={getSeverityColor(anomaly.severity, anomaly.anomaly_score)}>
                          {anomaly.severity?.toUpperCase() || "ANOMALY"}
                        </Badge>
                        <span className="text-zinc-500 text-sm">
                          {formatTime(anomaly.timestamp)}
                        </span>
                      </div>
                      
                      <p className="text-white font-mono text-sm truncate">
                        {anomaly.agent_id}
                      </p>
                      
                      <div className="flex flex-wrap gap-2 mt-2">
                        {anomaly.flags?.map((flag, fi) => (
                          <Badge key={fi} variant="outline" className="text-xs border-zinc-600 text-zinc-400">
                            {flag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    
                    <div className="text-right">
                      <div className="text-2xl font-bold font-mono text-white">
                        {(anomaly.anomaly_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-zinc-500 text-xs">
                        threshold: {(anomaly.threshold * 100).toFixed(0)}%
                      </div>
                      {anomaly.detection_time_ms && (
                        <div className="text-zinc-600 text-xs mt-1">
                          {anomaly.detection_time_ms.toFixed(0)}ms
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {/* Cross-chain & zkML info */}
                  {(anomaly.zkml_proof_hash || (anomaly as any).source_chain) && (
                    <div className="mt-3 pt-3 border-t border-zinc-700 flex flex-wrap gap-4">
                      {(anomaly as any).source_chain && (
                        <div>
                          <span className="text-xs text-zinc-500">Chain: </span>
                          <span className="text-xs text-cyan-400 font-medium capitalize">
                            {(anomaly as any).source_chain}
                          </span>
                          {(anomaly as any).relay_protocol === "wormhole" && (
                            <span className="ml-2 text-xs text-purple-400">
                              🌀 Wormhole
                            </span>
                          )}
                        </div>
                      )}
                      {anomaly.zkml_proof_hash && (
                        <div>
                          <span className="text-xs text-zinc-500">zkML: </span>
                          <code className="text-xs text-violet-400 font-mono">
                            {anomaly.zkml_proof_hash.slice(0, 16)}...
                          </code>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Footer */}
      <div className="text-center text-zinc-600 text-sm">
        Honestly AAIP • ML Anomaly Detection • zkML Verified
      </div>
    </div>
  );
}

export default AnomalyDashboard;

