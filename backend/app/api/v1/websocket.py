"""
Kisan Mitra AI — WebSocket Live Event Stream
===============================================
Streams real-time IVR call events to the dashboard via WebSocket.

Events:
  CALL_STARTED, TRANSCRIPT_UPDATED, FARMER_IDENTIFIED,
  SCHEME_MATCHING, ELIGIBILITY_COMPLETE, REASONING_COMPLETE,
  VOICE_RESPONSE_STARTED, CALL_COMPLETED
"""
from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("kisan_mitra_ai.api.websocket")

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections for live dashboard streaming."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._event_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=1000)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self._connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self._connections:
            self._connections.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(self._connections)}")

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Send an event to all connected clients."""
        dead: list[WebSocket] = []
        message = json.dumps(event)
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    async def push_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Queue an event for broadcasting."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload,
        }
        await self.broadcast(event)

    @property
    def client_count(self) -> int:
        return len(self._connections)


# Global connection manager instance
ws_manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for live dashboard event streaming.
    Clients connect here to receive real-time IVR call events.
    """
    await ws_manager.connect(websocket)
    try:
        # Send welcome event
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "timestamp": time.time(),
            "payload": {"message": "Connected to Kisan Mitra Live Event Stream"},
        }))

        # Keep connection alive, listen for pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Handle client messages (ping/pong)
                if data == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "PONG",
                        "timestamp": time.time(),
                        "payload": {},
                    }))
            except asyncio.TimeoutError:
                # Send heartbeat
                try:
                    await websocket.send_text(json.dumps({
                        "type": "HEARTBEAT",
                        "timestamp": time.time(),
                        "payload": {"clients": ws_manager.client_count},
                    }))
                except Exception:
                    break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)
