import { useEffect, useRef, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { gameResultUrl } from '../Component/urls';

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
      console.log(`웹소켓 연결 시도: /ws/gamerooms/${roomId}`);

      // 웹소켓 연결 생성 (세션 토큰은 쿠키를 통해 자동 전송)
      const socket = new WebSocket(
        `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}`
      );
      socketRef.current = socket;

      socket.onopen = () => {
        console.log('웹소켓 연결 성공!');
        setConnected(true);
        setRoomUpdated(true);
      };

      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('소켓 메시지 수신:', data);

        if (data.type === 'chat') {
          console.log('내 guest_id:', user.guest_id);
          console.log('수신 guest_id:', data.guest_id);
          console.log('수신 message_id:', data.message_id);

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
          // 참가자 목록 직접 업데이트 (API 호출 없음)
          console.log('웹소켓으로 참가자 목록 업데이트:', data.participants);
          if (data.participants && Array.isArray(data.participants)) {
            // 웹소켓으로 받은 참가자 정보를 userInfo 상태로 직접 사용
            setParticipants(data.participants);

            // 시스템 메시지로 추가 (입장/퇴장 알림)
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

            // 방 업데이트 플래그 설정 - GameLobbyPage에서 감지하도록
            setRoomUpdated(true);
          }
        } else if (data.type === 'game_status') {
          setGameStatus(data.status);
        } else if (data.type === 'game_started') {
          // 게임 시작 이벤트 처리 - 모든 참가자를 게임 페이지로 이동
          console.log('🎮 게임 시작 이벤트 수신:', data);
          
          // 게임 페이지로 이동
          const gameUrl = `/keaing/${data.room_id}`;
          window.location.href = gameUrl;
          
          // 시스템 메시지 추가
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
          // 준비 상태 변경 처리
          console.log('🔥 준비 상태 변경 수신:', data);

          // 현재 사용자의 준비 상태인 경우 상태 업데이트
          if (String(data.guest_id) === String(user.guest_id)) {
            console.log('📌 내 준비 상태 업데이트:', data.is_ready);
            setIsReady(data.is_ready);
          }
          // 참가자 목록에서 해당 참가자의 is_ready와 status 상태를 업데이트
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

          // 방 업데이트 플래그 설정 - 참가자 목록 갱신 트리거
          setRoomUpdated(true);

          // 시스템 메시지로 추가
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
          // 자신의 준비 상태 업데이트 응답
          setIsReady(data.is_ready);
        } else if (data.type === 'host_changed') {
          // 방장 변경 처리
          console.log('👑 방장 변경 수신:', data);
          
          // 참가자 목록에서 방장 상태 업데이트
          setParticipants((prev) =>
            prev.map((p) => ({
              ...p,
              is_creator: p.guest_id === data.new_host_id
            }))
          );
          
          // 방 업데이트 플래그 설정
          setRoomUpdated(true);
          
          // 시스템 메시지로 추가
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
          // 참가자 목록 업데이트
          console.log('📅 참가자 목록 업데이트:', data.participants);
          if (data.participants && Array.isArray(data.participants)) {
            setParticipants(data.participants);
            setRoomUpdated(true);
          }
        } else if (data.type === 'game_ended') {
          // 게임 종료 이벤트 처리 - 모든 참가자를 결과 페이지로 이동
          console.log('🏁 게임 종료 이벤트 수신:', data);
          
          // 게임 결과 페이지로 이동
          navigate(gameResultUrl(data.room_id));
          
          // 시스템 메시지 추가
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
        console.log('웹소켓 연결 종료:', event.code, event.reason);
        setConnected(false);
        
        // 비정상 종료인 경우 재연결 시도
        if (event.code !== 1000 && event.code !== 1001) {
          console.log('비정상 종료 감지, 5초 후 재연결 시도...');
          setTimeout(() => {
            if (roomId && isAuthenticated && user) {
              console.log('웹소켓 재연결 시도');
              // 재연결 로직은 useEffect에서 처리됨
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
      // 컴포넌트 언마운트 시 소켓 닫기
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [roomId, isAuthenticated, user]); // 인증 상태와 사용자 정보가 변경되면 재연결

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

  // 준비 상태 토글 함수 추가
  const toggleReady = () => {
    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(
        JSON.stringify({
          type: 'toggle_ready',
        })
      );
      console.log('레디는 하였으나 레디될수없다');
    } else {
      console.error('웹소켓이 연결되지 않았습니다');
    }
  };

  // 상태 업데이트 함수 (준비 또는 시작)
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

  // isReady 상태 디버깅용 useEffect 추가
  useEffect(() => {
    console.log('🟢 현재 isReady 상태:', isReady);
  }, [isReady]);

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
