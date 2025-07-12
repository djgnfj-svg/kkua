import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { gameResultUrl } from '../utils/urls';

export default function useGameRoomSocket(roomId) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [participants, setParticipants] = useState([]);
  const [gameStatus, setGameStatus] = useState('waiting');
  const socketRef = useRef(null);
  const [roomUpdated, setRoomUpdated] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (roomId && isAuthenticated && user) {
      const socket = new WebSocket(
        `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}`
      );
      socketRef.current = socket;

      socket.onopen = () => {
        setConnected(true);
        setRoomUpdated(true);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'chat') {
          const isOwnMessage =
            data.guest_id === user.guest_id ||
            data.message_id?.startsWith(`${user.guest_id}-`);

          const alreadyExists = messages.some(
            (msg) => msg.message_id === data.message_id
          );

          if (!isOwnMessage && !alreadyExists) {
            setMessages((prev) => [
              ...prev,
              {
                nickname: data.nickname,
                message:
                  typeof data.message === 'string'
                    ? data.message
                    : JSON.stringify(data.message),
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
        } else if (data.type === 'game_started') {
          const gameUrl = `/keaing/${data.room_id}`;
          window.location.href = gameUrl;
          
          setMessages((prev) => [
            ...prev,
            {
              nickname: '시스템',
              message: '게임이 시작되었습니다! 게임 페이지로 이동합니다.',
              type: 'system',
              timestamp: new Date().toISOString(),
            },
          ]);
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
        } else if (data.type === 'game_ended') {
          navigate(gameResultUrl(data.room_id));
          
          setMessages((prev) => [
            ...prev,
            {
              nickname: '시스템',
              message: '게임이 종료되었습니다! 결과 페이지로 이동합니다.',
              type: 'system',
              timestamp: new Date().toISOString(),
            },
          ]);
        }
      };

      socket.onclose = (event) => {
        setConnected(false);
        
        if (event.code !== 1000 && event.code !== 1001) {
          setTimeout(() => {
            if (roomId && isAuthenticated && user) {
              // Reconnection logic handled by useEffect
            }
          }, 5000);
        }
      };

      socket.onerror = (error) => {
        console.error('웹소켓 오류:', error);
        setConnected(false);
      };
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [roomId, isAuthenticated, user]);

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
    } else {
      console.error('웹소켓이 연결되지 않았습니다');
    }
  };

  const toggleReady = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'toggle_ready',
        })
      );
    } else {
      console.error('웹소켓이 연결되지 않았습니다');
    }
  };

  const updateStatus = (status) => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'status',
          status,
        })
      );
    } else {
      console.error('웹소켓이 연결되지 않았습니다');
    }
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
