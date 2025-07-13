import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { gameResultUrl } from '../utils/urls';
import { invalidateCache } from '../utils/cacheManager';

export default function useGameRoomSocket(roomId) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [gameStatus, setGameStatus] = useState('waiting');
  const socketRef = useRef(null);
  const [roomUpdated, setRoomUpdated] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const reconnectTimeoutRef = useRef(null);
  const connectionAttempts = useRef(0);

  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!roomId || !isAuthenticated || !user) {
      return;
    }

    const connectWebSocket = () => {
      // 이미 연결되어 있으면 무시
      if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
        return;
      }

      try {
        const wsUrl = `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}`;
        const socket = new WebSocket(wsUrl);
        socketRef.current = socket;

        socket.onopen = () => {
          setConnected(true);
          setRoomUpdated(true);
          connectionAttempts.current = 0;
        };

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            handleMessage(data);
          } catch (parseError) {
            console.error('WebSocket 메시지 파싱 에러:', parseError);
          }
        };

        socket.onclose = (event) => {
          setConnected(false);
          
          // 정상적인 종료가 아닌 경우에만 재연결 시도
          if (event.code !== 1000 && event.code !== 1001 && connectionAttempts.current < 3) {
            connectionAttempts.current += 1;
            
            // 간단한 재연결 로직 (5초 후)
            reconnectTimeoutRef.current = setTimeout(() => {
              connectWebSocket();
            }, 5000);
          }
        };

        socket.onerror = () => {
          setConnected(false);
        };

      } catch (error) {
        console.error('WebSocket 생성 오류:', error);
      }
    };

    const handleMessage = (data) => {
      if (data.type === 'chat') {
        const isOwnMessage =
          data.guest_id === user.guest_id ||
          data.message_id?.startsWith(`${user.guest_id}-`);

        if (!isOwnMessage) {
          setMessages((prev) => [
            ...prev,
            {
              nickname: data.nickname,
              message: typeof data.message === 'string' ? data.message : JSON.stringify(data.message),
              guest_id: data.guest_id,
              timestamp: data.timestamp,
              type: data.type,
              message_id: data.message_id,
            },
          ]);
        }
      } else if (data.type === 'participants_update') {
        if (data.participants && Array.isArray(data.participants)) {
          setParticipants(data.participants);
          
          // 참가자 변경 시 관련 캐시 무효화
          invalidateCache.room(roomId);

          if (data.message) {
            setMessages((prev) => [
              ...prev,
              {
                nickname: '시스템',
                message: data.message,
                type: 'system',
                timestamp: data.timestamp || new Date().toISOString(),
              },
            ]);
          }

          setRoomUpdated(true);
        }
      } else if (data.type === 'game_status') {
        setGameStatus(data.status);
      } else if (data.type === 'game_started' || data.type === 'game_started_redis') {
        setMessages((prev) => [
          ...prev,
          {
            nickname: '시스템',
            message: data.message || '게임이 시작되었습니다! 게임 페이지로 이동합니다.',
            type: 'system',
            timestamp: new Date().toISOString(),
          },
        ]);
        
        setGameStatus('playing');
        
        // 게임 페이지로 이동
        setTimeout(() => {
          navigate(`/keaing/${roomId}`);
        }, 1000); // 1초 후 이동
      } else if (data.type === 'ready_status_changed') {
        if (String(data.guest_id) === String(user.guest_id)) {
          setIsReady(data.is_ready);
        }
        
        setParticipants((prev) =>
          prev.map((p) =>
            p.guest_id === data.guest_id
              ? { 
                  ...p, 
                  is_ready: data.is_ready,
                  status: data.is_ready ? 'ready' : 'waiting'
                }
              : p
          )
        );

        // 준비 상태 변경 시 캐시 무효화
        invalidateCache.room(roomId);
        setRoomUpdated(true);

        setMessages((prev) => [
          ...prev,
          {
            nickname: '시스템',
            message: `${data.nickname || '플레이어'}님이 ${data.is_ready ? '준비완료' : '대기중'} 상태가 되었습니다.`,
            type: 'system',
            timestamp: data.timestamp || new Date().toISOString(),
          },
        ]);
      } else if (data.type === 'ready_status_updated') {
        setIsReady(data.is_ready);
      } else if (data.type === 'host_changed') {
        setParticipants((prev) =>
          prev.map((p) => ({
            ...p,
            is_creator: p.guest_id === data.new_host_id
          }))
        );
        
        setRoomUpdated(true);
        
        setMessages((prev) => [
          ...prev,
          {
            nickname: '시스템',
            message: data.message || `${data.new_host_nickname}님이 새로운 방장이 되었습니다.`,
            type: 'system',
            timestamp: new Date().toISOString(),
          },
        ]);
      } else if (data.type === 'participant_list_updated') {
        if (data.participants && Array.isArray(data.participants)) {
          setParticipants(data.participants);
          setRoomUpdated(true);
        }
      } else if (data.type === 'game_ended' || data.type === 'game_ended_by_host') {
        setGameStatus('finished');
        
        setMessages((prev) => [
          ...prev,
          {
            nickname: '시스템',
            message: data.message || '게임이 종료되었습니다! 결과 페이지로 이동합니다.',
            type: 'system',
            timestamp: new Date().toISOString(),
          },
        ]);
        
        // 결과 페이지로 이동 (result_available이 true일 때만)
        if (data.result_available) {
          setTimeout(() => {
            navigate(gameResultUrl(data.room_id || roomId));
          }, 2000); // 2초 후 이동
        }
      } else if (data.type === 'game_completed') {
        setGameStatus('finished');
        
        setMessages((prev) => [
          ...prev,
          {
            nickname: '시스템',
            message: data.message || '🎉 게임이 완료되었습니다! 결과를 확인하세요.',
            type: 'system',
            timestamp: new Date().toISOString(),
          },
        ]);
        
        // 게임 완료 이벤트 발생 (InGame에서 처리하도록)
        if (data.show_modal && window.gameCompletedCallback) {
          window.gameCompletedCallback({
            winner_id: data.winner_id,
            winner_nickname: data.winner_nickname,
            room_id: data.room_id,
            completed_by_nickname: data.completed_by_nickname
          });
        }
      }
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [roomId, isAuthenticated, user, navigate]);

  // 메시지 전송 함수
  const sendMessage = (message) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN && user) {
      const messageData = {
        type: 'chat',
        message: message,
        guest_id: user.guest_id,
        nickname: user.nickname,
        timestamp: new Date().toISOString(),
        message_id: `${user.guest_id}-${Date.now()}`,
      };
      socketRef.current.send(JSON.stringify(messageData));
      return true;
    }
    return false;
  };

  const toggleReady = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'toggle_ready',
        })
      );
      return true;
    }
    return false;
  };

  const updateStatus = (status) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'status',
          status,
        })
      );
      return true;
    }
    return false;
  };

  return {
    connected,
    messages,
    participants,
    gameStatus,
    isReady,
    sendMessage,
    toggleReady,
    updateStatus,
    roomUpdated,
    setRoomUpdated,
  };
}