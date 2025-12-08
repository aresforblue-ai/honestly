"""
WebSocket Router for Real-time Anomaly Streaming
=================================================

Streams anomaly detection events to connected dashboards via WebSocket.

Features:
- Real-time anomaly alerts from Kafka
- Connection management with heartbeat
- Room-based subscriptions (all, critical, agent-specific)
- Automatic reconnection support

Usage:
    # Connect to WebSocket
    ws://localhost:8000/ws/anomalies
    
    # Subscribe to specific room
    {"action": "subscribe", "room": "critical"}
    
    # Events pushed automatically from Kafka consumer
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

router = APIRouter(tags=["websocket"])

# Connection manager
class ConnectionManager:
    """Manages WebSocket connections and rooms."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "all": set(),
            "critical": set(),  # anomaly_score > 0.9
            "warning": set(),   # anomaly_score > 0.7
        }
        self.connection_info: Dict[WebSocket, Dict] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, room: str = "all"):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        
        async with self._lock:
            if room not in self.active_connections:
                self.active_connections[room] = set()
            
            self.active_connections[room].add(websocket)
            self.active_connections["all"].add(websocket)
            
            self.connection_info[websocket] = {
                "connected_at": datetime.now(timezone.utc).isoformat(),
                "room": room,
                "messages_sent": 0,
            }
        
        logger.info(f"WebSocket connected to room '{room}'. Total: {len(self.active_connections['all'])}")
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "room": room,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            for room in self.active_connections.values():
                room.discard(websocket)
            
            if websocket in self.connection_info:
                del self.connection_info[websocket]
        
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections['all'])}")
    
    async def subscribe(self, websocket: WebSocket, room: str):
        """Subscribe a connection to a room."""
        async with self._lock:
            if room not in self.active_connections:
                self.active_connections[room] = set()
            self.active_connections[room].add(websocket)
            
            if websocket in self.connection_info:
                self.connection_info[websocket]["room"] = room
        
        await websocket.send_json({
            "type": "subscribed",
            "room": room,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    
    async def broadcast(self, message: Dict[str, Any], room: str = "all"):
        """Broadcast message to all connections in a room."""
        if room not in self.active_connections:
            return
        
        dead_connections = set()
        
        for connection in self.active_connections[room].copy():
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_json(message)
                    if connection in self.connection_info:
                        self.connection_info[connection]["messages_sent"] += 1
                else:
                    dead_connections.add(connection)
            except Exception as e:
                logger.warning(f"Failed to send to WebSocket: {e}")
                dead_connections.add(connection)
        
        # Clean up dead connections
        for dead in dead_connections:
            await self.disconnect(dead)
    
    async def broadcast_anomaly(self, anomaly: Dict[str, Any]):
        """Broadcast anomaly to appropriate rooms based on severity."""
        score = anomaly.get("anomaly_score", 0)
        
        # Add metadata
        anomaly["type"] = "anomaly"
        anomaly["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Broadcast to all
        await self.broadcast(anomaly, "all")
        
        # Broadcast to severity-specific rooms
        if score > 0.9:
            anomaly["severity"] = "critical"
            await self.broadcast(anomaly, "critical")
        elif score > 0.7:
            anomaly["severity"] = "warning"
            await self.broadcast(anomaly, "warning")
        
        # Broadcast to agent-specific room if exists
        agent_id = anomaly.get("agent_id")
        if agent_id and f"agent:{agent_id}" in self.active_connections:
            await self.broadcast(anomaly, f"agent:{agent_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.active_connections.get("all", set())),
            "rooms": {
                room: len(conns) 
                for room, conns in self.active_connections.items()
            },
            "connections": [
                {
                    "room": info.get("room"),
                    "connected_at": info.get("connected_at"),
                    "messages_sent": info.get("messages_sent"),
                }
                for info in self.connection_info.values()
            ],
        }


# Global connection manager
manager = ConnectionManager()


@router.websocket("/ws/anomalies")
async def websocket_anomalies(
    websocket: WebSocket,
    room: str = Query(default="all"),
):
    """
    WebSocket endpoint for real-time anomaly streaming.
    
    Query params:
        room: Subscription room (all, critical, warning, agent:<id>)
    
    Client messages:
        {"action": "subscribe", "room": "critical"}
        {"action": "ping"}
    
    Server messages:
        {"type": "anomaly", "agent_id": "...", "anomaly_score": 0.85, ...}
        {"type": "connected", "room": "all"}
        {"type": "pong"}
    """
    await manager.connect(websocket, room)
    
    try:
        while True:
            # Wait for client messages
            data = await websocket.receive_json()
            
            action = data.get("action")
            
            if action == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            
            elif action == "subscribe":
                new_room = data.get("room", "all")
                await manager.subscribe(websocket, new_room)
            
            elif action == "stats":
                await websocket.send_json({
                    "type": "stats",
                    "data": manager.get_stats(),
                })
            
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)


@router.get("/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return manager.get_stats()


# Kafka consumer integration
async def start_kafka_consumer():
    """
    Start Kafka consumer that pushes anomalies to WebSocket.
    
    Run this in a background task on startup.
    """
    try:
        from kafka import KafkaConsumer
    except ImportError:
        logger.warning("kafka-python not installed, WebSocket won't receive Kafka events")
        return
    
    KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC = os.getenv("KAFKA_TOPIC_ANOMALY", "anomaly.detected")
    
    try:
        consumer = KafkaConsumer(
            KAFKA_TOPIC,
            bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset="latest",
            enable_auto_commit=True,
            group_id="websocket-consumer",
        )
        
        logger.info(f"Kafka consumer started for {KAFKA_TOPIC}")
        
        for message in consumer:
            try:
                anomaly = message.value
                await manager.broadcast_anomaly(anomaly)
            except Exception as e:
                logger.error(f"Error processing Kafka message: {e}")
                
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")


# Export for use in main app
def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager."""
    return manager


