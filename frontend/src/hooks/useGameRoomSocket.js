import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';

/**
 * 게임룸 WebSocket 연결 관리 훅
 * 실시간 게임 통신을 위한 WebSocket 연결과 메시지 처리를 담당
 */
export default function useGameRoomSocket(roomId) {
  // 연결 상태 관리
  const [connected, setConnected] = useState(false);
  const [isReconnecting, setIsReconnecting] = useState(false);

  // 게임 데이터 상태
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [gameStatus, setGameStatus] = useState('waiting');
  const [roomUpdated, setRoomUpdated] = useState(false);
  const [isReady, setIsReady] = useState(false);

  // Refs
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const connectionAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  // Context hooks
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const toast = useToast();

  // WebSocket 연결 함수
  const connectWebSocket = useCallback(() => {
    if (!roomId || !isAuthenticated) {
      console.log('연결 조건이 충족되지 않음:', { roomId, isAuthenticated });
      return;
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      console.log('이미 연결되어 있음');
      return;
    }

    try {
      const wsUrl = `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}`;
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket 연결됨');
        setConnected(true);
        setIsReconnecting(false);
        connectionAttempts.current = 0;

        if (toast) {
          toast.showSuccess('게임룸에 연결되었습니다.');
        }
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (err) {
          console.error('메시지 파싱 실패:', err, event.data);
        }
      };

      socket.onclose = (event) => {
        console.log('WebSocket 연결 종료:', event.code, event.reason);
        setConnected(false);

        if (
          !event.wasClean &&
          connectionAttempts.current < maxReconnectAttempts
        ) {
          attemptReconnect();
        }
      };

      socket.onerror = (error) => {
        console.error('WebSocket 오류:', error);
        setConnected(false);
      };

      socketRef.current = socket;
    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      if (toast) {
        toast.showError('게임룸 연결에 실패했습니다.');
      }
    }
  }, [roomId, isAuthenticated, toast]);

  // WebSocket 메시지 처리
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket 메시지:', data);

    switch (data.type) {
      case 'user_joined':
        setParticipants((prev) => [...prev, data.user]);
        if (toast) {
          toast.showInfo(`${data.user.nickname}님이 입장했습니다.`);
        }
        break;

      case 'user_left':
        setParticipants((prev) =>
          prev.filter((p) => p.user_id !== data.user_id)
        );
        if (toast) {
          toast.showInfo(`${data.nickname}님이 퇴장했습니다.`);
        }
        break;

      case 'participants_list':
        setParticipants(data.participants || []);
        break;

      case 'game_started':
        setGameStatus('playing');
        if (toast) {
          toast.showSuccess('게임이 시작되었습니다!');
        }
        break;

      case 'game_over':
        setGameStatus('finished');
        if (toast) {
          toast.showInfo('게임이 종료되었습니다.');
        }
        navigate(`/gameroom/${roomId}/result`);
        break;

      case 'message':
        setMessages((prev) => [
          ...prev,
          {
            id: Date.now(),
            user: data.user,
            content: data.content,
            timestamp: new Date().toISOString(),
          },
        ]);
        break;

      case 'room_updated':
        setRoomUpdated(true);
        break;

      default:
        console.log('알 수 없는 메시지 타입:', data.type);
    }
  };

  // 재연결 시도
  const attemptReconnect = () => {
    if (connectionAttempts.current >= maxReconnectAttempts) {
      console.log('최대 재연결 시도 횟수 초과');
      if (toast) {
        toast.showError(
          '게임룸 연결이 끊어졌습니다. 페이지를 새로고침해주세요.'
        );
      }
      return;
    }

    connectionAttempts.current++;
    setIsReconnecting(true);

    const delay = Math.min(
      1000 * Math.pow(2, connectionAttempts.current),
      10000
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(
        `재연결 시도 ${connectionAttempts.current}/${maxReconnectAttempts}`
      );
      connectWebSocket();
    }, delay);
  };

  // 메시지 전송
  const sendMessage = useCallback(
    (message) => {
      if (socketRef.current?.readyState === WebSocket.OPEN) {
        socketRef.current.send(JSON.stringify(message));
        return true;
      } else {
        console.error('WebSocket이 연결되지 않음');
        if (toast) {
          toast.showError('연결이 끊어졌습니다. 재연결을 시도해주세요.');
        }
        return false;
      }
    },
    [toast]
  );

  // 준비 상태 토글
  const toggleReady = useCallback(() => {
    const success = sendMessage({
      type: 'toggle_ready',
      user_id: user?.user_id,
    });

    if (success) {
      setIsReady((prev) => !prev);
    }
  }, [sendMessage, user]);

  // 상태 업데이트
  const updateStatus = useCallback((status) => {
    setGameStatus(status);
  }, []);

  // 수동 재연결
  const manualReconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socketRef.current) {
      socketRef.current.close();
    }

    connectionAttempts.current = 0;
    setIsReconnecting(true);

    setTimeout(() => {
      connectWebSocket();
    }, 500);
  }, [connectWebSocket]);

  // Effect: 컴포넌트 마운트 시 연결
  useEffect(() => {
    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [connectWebSocket]);

  return {
    connected,
    isReconnecting,
    connectionAttempts: connectionAttempts.current,
    maxReconnectAttempts,
    messages,
    participants,
    gameStatus,
    isReady,
    sendMessage,
    toggleReady,
    updateStatus,
    manualReconnect,
    roomUpdated,
    setRoomUpdated,
  };
}
