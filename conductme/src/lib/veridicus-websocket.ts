/**
 * VERIDICUS WebSocket Client
 * 
 * Real-time event streaming for VERIDICUS token metrics, quantum jobs, and network activity.
 */

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/veridicus';

export type VeridicusEventType = 
  | 'job_executed'
  | 'token_burned'
  | 'staking_update'
  | 'governance_vote'
  | 'network_activity';

export interface VeridicusEvent {
  type: VeridicusEventType;
  timestamp: number;
  data: any;
}

export type EventCallback = (event: VeridicusEvent) => void;

export class VeridicusWebSocket {
  private ws: WebSocket | null = null;
  private callbacks: Map<VeridicusEventType | 'all', Set<EventCallback>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 5000;
  private pingInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.connect();
  }

  private connect() {
    try {
      this.ws = new WebSocket(WS_URL);

      this.ws.onopen = () => {
        console.log('VERIDICUS WebSocket connected');
        this.reconnectAttempts = 0;
        this.startPing();
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'pong') {
            return; // Ignore pong messages
          }

          const veridicusEvent: VeridicusEvent = {
            type: data.type,
            timestamp: data.timestamp || Date.now(),
            data: data.data || data,
          };

          this.emit(veridicusEvent);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('VERIDICUS WebSocket error:', error);
      };

      this.ws.onclose = () => {
        console.log('VERIDICUS WebSocket disconnected');
        this.stopPing();
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Failed to connect VERIDICUS WebSocket:', error);
      this.attemptReconnect();
    }
  }

  private startPing() {
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPing() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached');
      return;
    }

    this.reconnectAttempts++;
    setTimeout(() => {
      console.log(`Reconnecting VERIDICUS WebSocket (attempt ${this.reconnectAttempts})...`);
      this.connect();
    }, this.reconnectDelay);
  }

  private emit(event: VeridicusEvent) {
    const callbacks = this.callbacks.get(event.type);
    if (callbacks) {
      callbacks.forEach((callback) => {
        try {
          callback(event);
        } catch (error) {
          console.error('Error in event callback:', error);
        }
      });
    }

    // Also emit to 'all' listeners
    const allCallbacks = this.callbacks.get('all');
    if (allCallbacks) {
      allCallbacks.forEach((callback) => {
        try {
          callback(event);
        } catch (error) {
          console.error('Error in event callback:', error);
        }
      });
    }
  }

  /**
   * Subscribe to events
   */
  on(eventType: VeridicusEventType | 'all', callback: EventCallback) {
    if (!this.callbacks.has(eventType)) {
      this.callbacks.set(eventType, new Set());
    }
    this.callbacks.get(eventType)!.add(callback);

    // Return unsubscribe function
    return () => {
      this.off(eventType, callback);
    };
  }

  /**
   * Unsubscribe from events
   */
  off(eventType: VeridicusEventType | 'all', callback: EventCallback) {
    const callbacks = this.callbacks.get(eventType);
    if (callbacks) {
      callbacks.delete(callback);
    }
  }

  /**
   * Get connection status
   */
  getStatus(): 'connected' | 'connecting' | 'disconnected' | 'error' {
    if (!this.ws) return 'disconnected';
    
    switch (this.ws.readyState) {
      case WebSocket.CONNECTING:
        return 'connecting';
      case WebSocket.OPEN:
        return 'connected';
      case WebSocket.CLOSING:
      case WebSocket.CLOSED:
        return 'disconnected';
      default:
        return 'error';
    }
  }

  /**
   * Disconnect
   */
  disconnect() {
    this.stopPing();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.callbacks.clear();
  }
}

// Singleton instance
let wsInstance: VeridicusWebSocket | null = null;

/**
 * Get or create WebSocket instance
 */
export function getVeridicusWebSocket(): VeridicusWebSocket {
  if (!wsInstance) {
    wsInstance = new VeridicusWebSocket();
  }
  return wsInstance;
}

/**
 * React hook for VERIDICUS WebSocket events
 */
import { useEffect } from 'react';

export function useVERIDICUSWebSocket(
  eventType: VeridicusEventType | 'all',
  callback: EventCallback
) {
  const ws = getVeridicusWebSocket();

  useEffect(() => {
    ws.on(eventType, callback);
    return () => {
      ws.off(eventType, callback);
    };
  }, [eventType, callback, ws]);
}

