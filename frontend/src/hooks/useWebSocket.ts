import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';

interface UseWebSocketOptions {
  url: string;
  roomId?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectInterval?: number;
}

interface WebSocketState {
  socket: Socket | null;
  isConnected: boolean;
  isConnecting: boolean;
  error: string | null;
  reconnectAttempt: number;
}

export const useWebSocket = (options: UseWebSocketOptions) => {
  const {
    url,
    roomId,
    autoConnect = true,
    reconnectAttempts = 5,
    reconnectInterval = 3000
  } = options;

  const [state, setState] = useState<WebSocketState>({
    socket: null,
    isConnected: false,
    isConnecting: false,
    error: null,
    reconnectAttempt: 0
  });

  const socketRef = useRef<Socket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    setState(prev => ({ ...prev, isConnecting: true, error: null }));

    const wsUrl = roomId ? `${url}/gamerooms/${roomId}` : url;
    const socket = io(wsUrl, {
      withCredentials: true,
      transports: ['websocket', 'polling'],
      timeout: 10000,
      forceNew: true,
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      if (!mountedRef.current) return;
      console.log(`🔗 WebSocket connected to ${wsUrl}`);
      setState(prev => ({
        ...prev,
        socket,
        isConnected: true,
        isConnecting: false,
        error: null,
        reconnectAttempt: 0
      }));
    });

    socket.on('disconnect', (reason) => {
      if (!mountedRef.current) return;
      console.log(`🔌 WebSocket disconnected: ${reason}`);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: `Disconnected: ${reason}`
      }));

      // Auto-reconnect logic
      if (reason === 'io server disconnect') {
        // Server initiated disconnect, don't reconnect
        return;
      }

      if (state.reconnectAttempt < reconnectAttempts) {
        reconnectTimeoutRef.current = setTimeout(() => {
          if (mountedRef.current) {
            setState(prev => ({ ...prev, reconnectAttempt: prev.reconnectAttempt + 1 }));
            connect();
          }
        }, reconnectInterval);
      }
    });

    socket.on('connect_error', (error) => {
      if (!mountedRef.current) return;
      console.error('🚫 WebSocket connection error:', error);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: `Connection error: ${error.message}`
      }));
    });

    // Game-specific events
    socket.on('error', (error) => {
      if (!mountedRef.current) return;
      console.error('🎮 Game error:', error);
      setState(prev => ({ ...prev, error: error.message || 'Game error occurred' }));
    });

  }, [url, roomId, reconnectAttempts, reconnectInterval, state.reconnectAttempt]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }

    setState(prev => ({
      ...prev,
      socket: null,
      isConnected: false,
      isConnecting: false,
      error: null,
      reconnectAttempt: 0
    }));
  }, []);

  const emit = useCallback((event: string, data?: any) => {
    if (socketRef.current?.connected) {
      console.log(`📤 Emitting ${event}:`, data);
      socketRef.current.emit(event, data);
    } else {
      console.warn('🚫 Cannot emit - socket not connected');
    }
  }, []);

  const on = useCallback((event: string, callback: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.on(event, callback);
    }
  }, []);

  const off = useCallback((event: string, callback?: (data: any) => void) => {
    if (socketRef.current) {
      socketRef.current.off(event, callback);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;

    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    ...state,
    connect,
    disconnect,
    emit,
    on,
    off
  };
};