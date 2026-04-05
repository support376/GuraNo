import { useRef, useCallback, useEffect, useState } from 'react';
import type { WSMessage } from '@/types/websocket';

type MessageHandler = (msg: WSMessage) => void;

const BACKEND_URL = 'wss://gurano-backend.onrender.com';

export function useWebSocket(sessionId: string | null, onMessage: MessageHandler) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const retryRef = useRef(0);

  const connect = useCallback(() => {
    if (!sessionId) return;

    // Use env var, or hardcoded Render URL, or same-origin fallback
    const wsBase = import.meta.env.VITE_WS_URL || BACKEND_URL;
    const url = `${wsBase}/ws/${sessionId}`;

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retryRef.current = 0;
      };
      ws.onclose = () => {
        setConnected(false);
        retryRef.current += 1;
        // Reconnect with backoff, max 5 retries
        if (retryRef.current < 5) {
          setTimeout(() => connect(), 2000 * retryRef.current);
        }
      };
      ws.onerror = () => ws.close();
      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data) as WSMessage;
        onMessage(msg);
      };
    } catch (e) {
      console.warn('WebSocket connection failed:', e);
    }
  }, [sessionId, onMessage]);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((msg: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { connected, send };
}
