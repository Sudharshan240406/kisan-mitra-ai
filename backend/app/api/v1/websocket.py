"""
Kisan Mitra AI — WebSocket Live Event Stream (Phase 16)
=========================================================
Streams real-time IVR call events to the Mission Control dashboard.

Full event catalogue:
  CALL_STARTED, CALLER_IDENTIFIED, DIGITAL_TWIN_LOADED,
  SCHEME_SEARCH_STARTED, SCHEME_MATCHED, ELIGIBILITY_COMPLETED,
  REASONING_COMPLETED, DOCUMENT_ADVISOR_READY, VOICE_RESPONSE_STARTED,
  TRANSCRIPT_UPDATED, CALL_COMPLETED,
  CALL_ERROR, ERROR_RECOVERY_STARTED,
  DEMO_STARTED, DEMO_PROGRESS, DEMO_FARMER_COMPLETE, DEMO_COMPLETED,
  MISSION_CONTROL_DISCONNECTED, MISSION_CONTROL_RECONNECTED,
  CONNECTED, PONG, HEARTBEAT
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

# Security: cap concurrent WebSocket connections to prevent resource exhaustion
MAX_CONNECTIONS: int = 50


class ConnectionManager:
    """
    Manages active WebSocket connections for live dashboard streaming.
    Features:
    - Graceful dead-connection pruning on broadcast
    - MISSION_CONTROL_DISCONNECTED / RECONNECTED lifecycle events
    - Connection limit enforcement (MAX_CONNECTIONS)
    - Reconnect counter per session
    """

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []
        self._reconnect_count: int = 0

    async def connect(self, websocket: WebSocket) -> bool:
        """
        Accept and register a WebSocket connection.
        Returns False if MAX_CONNECTIONS is reached (connection rejected).
        """
        if len(self._connections) >= MAX_CONNECTIONS:
            logger.warning(
                f"WebSocket connection rejected: limit of {MAX_CONNECTIONS} reached."
            )
            await websocket.close(code=1008, reason="Too many connections")
            return False

        await websocket.accept()
        is_reconnect = self._reconnect_count > 0
        self._connections.append(websocket)
        logger.info(f"WebSocket client connected. Total: {len(self._connections)}")

        # Notify all existing clients about the reconnection
        if is_reconnect:
            await self.broadcast({
                "type": "MISSION_CONTROL_RECONNECTED",
                "timestamp": time.time(),
                "payload": {
                    "connected_clients": len(self._connections),
                    "reconnect_count": self._reconnect_count,
                },
            })
        return True

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister a WebSocket and notify remaining clients."""
        if websocket in self._connections:
            self._connections.remove(websocket)
            self._reconnect_count += 1
        remaining = len(self._connections)
        logger.info(f"WebSocket client disconnected. Remaining: {remaining}")

        # Fire-and-forget disconnect notification (sync context)
        # Remaining clients receive the event on next broadcast cycle
        if remaining > 0:
            asyncio.ensure_future(self.broadcast({
                "type": "MISSION_CONTROL_DISCONNECTED",
                "timestamp": time.time(),
                "payload": {
                    "connected_clients": remaining,
                    "reconnect_count": self._reconnect_count,
                },
            }))

    async def broadcast(self, event: dict[str, Any]) -> None:
        """Send an event to all connected clients, pruning dead connections."""
        dead: list[WebSocket] = []
        message = json.dumps(event)
        for ws in list(self._connections):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._connections:
                self._connections.remove(ws)

    async def push_event(self, event_type: str, payload: dict[str, Any]) -> None:
        """Build and broadcast a typed event envelope."""
        event = {
            "type": event_type,
            "timestamp": time.time(),
            "payload": payload,
        }
        await self.broadcast(event)

    @property
    def client_count(self) -> int:
        return len(self._connections)

    @property
    def reconnect_count(self) -> int:
        return self._reconnect_count


# Module-level singleton — shared across all API routes
ws_manager = ConnectionManager()


@router.websocket("/ws/live")
async def websocket_live(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for Mission Control live event streaming.

    Protocol:
    - Client connects → receives CONNECTED welcome event
    - Client sends "ping" → server responds with PONG
    - Server sends HEARTBEAT every 30s with connected client count
    - On disconnect → MISSION_CONTROL_DISCONNECTED fired to remaining clients
    - On reconnect → MISSION_CONTROL_RECONNECTED fired to all clients
    """
    accepted = await ws_manager.connect(websocket)
    if not accepted:
        return

    try:
        # Welcome event with session info
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "timestamp": time.time(),
            "payload": {
                "message": "Connected to Kisan Mitra Mission Control",
                "connected_clients": ws_manager.client_count,
                "max_connections": MAX_CONNECTIONS,
                "version": "16.0",
            },
        }))

        # Main event loop
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "PONG",
                        "timestamp": time.time(),
                        "payload": {"clients": ws_manager.client_count},
                    }))
                # Silently ignore unknown client messages
            except asyncio.TimeoutError:
                # Heartbeat to keep connection alive
                try:
                    await websocket.send_text(json.dumps({
                        "type": "HEARTBEAT",
                        "timestamp": time.time(),
                        "payload": {
                            "clients": ws_manager.client_count,
                            "reconnects": ws_manager.reconnect_count,
                        },
                    }))
                except Exception:
                    break  # Connection is dead

    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
    finally:
        ws_manager.disconnect(websocket)
