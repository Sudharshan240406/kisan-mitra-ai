"use client";

import { useState, useEffect, useRef, useCallback } from "react";

export interface WSEvent {
  type: string;
  timestamp: number;
  payload: Record<string, any>;
}

interface UseWebSocketOptions {
  url: string;
  autoReconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  events: WSEvent[];
  lastEvent: WSEvent | null;
  isConnected: boolean;
  clientCount: number;
  reconnectCount: number;
  clearEvents: () => void;
  sendMessage: (msg: string) => void;
}

export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const {
    url,
    autoReconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 100, // Safe window for Render cold boots
  } = options;

  const [events, setEvents] = useState<WSEvent[]>([]);
  const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [clientCount, setClientCount] = useState(0);
  const [reconnectCount, setReconnectCount] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectCountRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectCountRef.current = 0;
        setReconnectCount(0);
      };

      ws.onmessage = (event) => {
        try {
          const data: WSEvent = JSON.parse(event.data);

          // Handle heartbeat and lifecycle client counts
          if (data.type === "HEARTBEAT") {
            setClientCount(data.payload?.clients ?? 0);
            return;
          }
          if (data.type === "CONNECTED" || data.type === "MISSION_CONTROL_RECONNECTED" || data.type === "MISSION_CONTROL_DISCONNECTED") {
            setClientCount(data.payload?.connected_clients ?? 1);
          }
          if (data.type === "PONG") return;

          setLastEvent(data);
          setEvents((prev) => [data, ...prev].slice(0, 200));
        } catch {
          // Ignore parse errors
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        wsRef.current = null;

        if (autoReconnect && reconnectCountRef.current < maxReconnectAttempts) {
          reconnectTimerRef.current = setTimeout(() => {
            reconnectCountRef.current += 1;
            setReconnectCount(reconnectCountRef.current);
            connect();
          }, reconnectInterval);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // Connection failed
    }
  }, [url, autoReconnect, reconnectInterval, maxReconnectAttempts]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [connect]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setLastEvent(null);
  }, []);

  const sendMessage = useCallback((msg: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(msg);
    }
  }, []);

  return { events, lastEvent, isConnected, clientCount, reconnectCount, clearEvents, sendMessage };
}
