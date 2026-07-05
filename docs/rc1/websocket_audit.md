# Kisan Mitra AI — Release Candidate 1 (RC1) WebSocket Report

This document reports on the live WebSocket stream integration, event schemas, connection bounds, and client recovery loops tested for RC1.

---

## 1. Connection Lifecycle & Metrics

- **Endpoint**: `ws://localhost:8000/ws/live`
- **Session Handshake**: On open, the server responds with a `CONNECTED` welcome envelope containing active connections and limit parameters.
- **Heartbeat Protocol**: A 30-second ping/pong keepalive is initiated from the server. If the client fails to respond, it is pruned from the connection table.
- **Max Connections Guard**: Capped at `MAX_CONNECTIONS = 50`. Connections exceeding the limit receive HTTP 1008 and are rejected safely.

---

## 2. Reconnection & Recovery Control Loop

The frontend hook `useWebSocket.ts` handles client disconnects using an automatic recovery engine:
1. **Network Disruption**: The browser triggers the `onclose` callback.
2. **Backoff Delay**: Clears active timers and schedules a reconnection in `3000ms`.
3. **Attempt Limit**: Retries up to `10 times`. If all attempts fail, it enters a dormant state to prevent browser resource lockups.
4. **Lifecycle Events**:
   - `MISSION_CONTROL_DISCONNECTED`: Dispatched to remaining active dashboard clients.
   - `MISSION_CONTROL_RECONNECTED`: Broadcasted upon successful client recovery.

---

## 3. WebSocket Event Flow Sequencing

```
  [CALL_STARTED] ──► [CALLER_IDENTIFIED] ──► [DIGITAL_TWIN_LOADED]
                                                     │
                                                     ▼
  [SCHEME_MATCHED] (×11) ◄── [SCHEME_SEARCH_STARTED] ┘
         │
         ▼
  [ELIGIBILITY_COMPLETED] ──► [REASONING_COMPLETED] ──► [DOCUMENT_ADVISOR_READY]
                                                                  │
                                                                  ▼
  [CALL_COMPLETED] ◄── [TRANSCRIPT_UPDATED] ◄── [VOICE_RESPONSE_STARTED] ┘
```

Every E2E call execution produces this exact 13-stage order. If a pipeline failure is intercepted, the flow switches to:
```
  [CALL_ERROR] ──► [ERROR_RECOVERY_STARTED]
```
Ensuring the dashboard visual stages remain correct and responsive.
