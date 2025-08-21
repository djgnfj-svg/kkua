import { useEffect, useRef, useState, useCallback } from 'react';
import { useNetworkRecovery } from './useNetworkRecovery';

export interface WebSocketMessage {
  type: string;
  data?: any;
  timestamp?: string;
  request_id?: string;
}

interface UseNativeWebSocketOptions {
  url: string;
  roomId?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface WebSocketState {
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempt: number;
}

export const useNativeWebSocket = (options: UseNativeWebSocketOptions) => {
  const {
    url,
    roomId,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options;

  const { isOnline, withErrorRecovery } = useNetworkRecovery({
    onReconnected: () => {
      if (!state.isConnected && !state.isConnecting) {
        connect();
      }
    }
  });

  const [state, setState] = useState<WebSocketState>({
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempt: 0
  });

  const wsRef = useRef<WebSocket | null>(null);
  const eventHandlersRef = useRef<Map<string, ((data: any) => void)[]>>(new Map());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);
  const requestIdRef = useRef(0);

  const generateRequestId = useCallback(() => {
    return `req_${Date.now()}_${++requestIdRef.current}`;
  }, []);

  // 재연결 카운터를 별도 ref로 관리하여 무한 루프 방지
  const reconnectCountRef = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    try {
      // Build WebSocket URL based on room
      const wsProtocol = url.startsWith('https') ? 'wss' : 'ws';
      const baseUrl = url.replace(/^https?/, wsProtocol);
      
      // Get token from Zustand storage
      let sessionToken = null;
      try {
        const zustandStorage = localStorage.getItem('kkua-user-storage');
        if (zustandStorage) {
          const parsed = JSON.parse(zustandStorage);
          sessionToken = parsed?.state?.user?.sessionToken;
        }
      } catch (error) {
        console.error('Failed to get session token:', error);
      }
      
      // Add token to URL as query parameter (WebSocket doesn't support custom headers)
      const wsUrl = roomId 
        ? `${baseUrl}/ws/rooms/${roomId}${sessionToken ? `?token=${sessionToken}` : ''}` 
        : `${baseUrl}/ws${sessionToken ? `?token=${sessionToken}` : ''}`;

      console.log(`🔗 Connecting to WebSocket: ${wsUrl.replace(/token=[^&]*/, 'token=***')}`);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!mountedRef.current) return;
        console.log(`✅ WebSocket connected to ${wsUrl.replace(/token=[^&]*/, 'token=***')}`);
        reconnectCountRef.current = 0; // 연결 성공 시 카운터 리셋
        setState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          error: null,
          reconnectAttempt: 0
        }));
      };

      ws.onclose = (event) => {
        if (!mountedRef.current) return;
        console.log(`🔌 WebSocket disconnected: ${event.code} ${event.reason}`);
        
        // 1006 에러이고 reason이 비어있으면 토큰 만료로 추정
        let errorMessage = event.reason || `Connection closed (${event.code})`;
        if (event.code === 1006 && !event.reason) {
          errorMessage = '인증이 만료되었습니다. 페이지를 새로고침 해주세요.';
          // 토큰 만료 시 localStorage에서 토큰 제거
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
        
        setState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          error: errorMessage,
          reconnectAttempt: reconnectCountRef.current
        }));

        // Auto-reconnect logic - 정상 종료(1000)가 아니고 재연결 횟수 제한 내에서만
        // 1006 에러(인증 실패)는 재연결 시도하지 않음
        if (event.code !== 1000 && event.code !== 1006 && reconnectCountRef.current < reconnectAttempts) {
          reconnectCountRef.current += 1;
          console.log(`🔄 Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect();
            }
          }, reconnectInterval);
        }
      };

      ws.onerror = (error) => {
        if (!mountedRef.current) return;
        console.error('🚫 WebSocket error:', error);
        setState(prev => ({
          ...prev,
          error: 'WebSocket connection error'
        }));
      };

      ws.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log(`📥 Received: ${message.type}`, message.data);

          // Call registered handlers
          const handlers = eventHandlersRef.current.get(message.type) || [];
          handlers.forEach(handler => {
            try {
              handler(message.data || message);
            } catch (err) {
              console.error(`Handler error for ${message.type}:`, err);
            }
          });
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      setState(prev => ({
        ...prev,
        isConnecting: false,
        error: 'Failed to create WebSocket connection'
      }));
    }
  }, [url, roomId, reconnectAttempts, reconnectInterval]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Client disconnect');
      wsRef.current = null;
    }

    setState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempt: 0
    }));
  }, []);

  const emit = useCallback((type: string, data?: any, withRequestId = false) => {
    if (wsRef.current?.readyState !== WebSocket.OPEN) {
      console.warn('🚫 Cannot send message - WebSocket not connected');
      return null;
    }

    const message: WebSocketMessage = {
      type,
      data: data || {},
      timestamp: new Date().toISOString()
    };

    if (withRequestId) {
      message.request_id = generateRequestId();
    }

    console.log(`📤 Sending: ${type}`, message);
    wsRef.current.send(JSON.stringify(message));
    
    return message.request_id || null;
  }, [generateRequestId]);

  const on = useCallback((event: string, callback: (data: any) => void) => {
    if (!eventHandlersRef.current.has(event)) {
      eventHandlersRef.current.set(event, []);
    }
    eventHandlersRef.current.get(event)!.push(callback);
  }, []);

  const off = useCallback((event: string, callback?: (data: any) => void) => {
    if (!callback) {
      // Remove all handlers for this event
      eventHandlersRef.current.delete(event);
    } else {
      // Remove specific handler
      const handlers = eventHandlersRef.current.get(event);
      if (handlers) {
        const index = handlers.indexOf(callback);
        if (index > -1) {
          handlers.splice(index, 1);
        }
        if (handlers.length === 0) {
          eventHandlersRef.current.delete(event);
        }
      }
    }
  }, []);

  // Ping functionality
  const ping = useCallback(() => {
    emit('ping', { timestamp: new Date().toISOString() });
  }, [emit]);

  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      connect();
    }

    // Set up ping interval
    const pingInterval = setInterval(ping, 30000); // Ping every 30 seconds

    return () => {
      mountedRef.current = false;
      clearInterval(pingInterval);
      disconnect();
    };
  }, [autoConnect, connect, disconnect, ping]);

  return {
    ...state,
    connect,
    disconnect,
    emit,
    on,
    off,
    ping
  };
};