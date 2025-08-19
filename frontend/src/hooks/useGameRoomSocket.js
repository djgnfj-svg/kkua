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
    if (!roomId || !isAuthenticated || !user) {
      console.log('연결 조건이 충족되지 않음:', { roomId, isAuthenticated, user: !!user });
      return;
    }

    if (socketRef.current?.readyState === WebSocket.OPEN) {
      console.log('이미 연결되어 있음');
      return;
    }

    // 이전 연결이 있으면 정리
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    try {
      const wsUrl = `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}`;
      console.log('WebSocket 연결 시도:', wsUrl);
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        console.log('WebSocket 연결됨');
        setConnected(true);
        setIsReconnecting(false);
        connectionAttempts.current = 0;

        // 초기 연결시에만 토스트 표시 (재연결시에는 표시하지 않음)
        if (toast && connectionAttempts.current === 0 && !isReconnecting) {
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

        // 1005는 정상 종료, 1001은 사용자가 떠남 - 재연결하지 않음
        if (event.code !== 1005 && event.code !== 1001 && !event.wasClean && 
            connectionAttempts.current < maxReconnectAttempts) {
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
  }, [roomId, isAuthenticated, user]);

  // WebSocket 메시지 처리
  const handleWebSocketMessage = (data) => {
    console.log('WebSocket 메시지:', data);

    switch (data.type) {
      case 'user_joined':
        if (data.user && data.user.nickname) {
          setParticipants((prev) => [...prev, data.user]);
          if (toast) {
            toast.showInfo(`${data.user.nickname}님이 입장했습니다.`);
          }
        } else {
          console.error('메시지 파싱 실패: Cannot read properties of undefined (reading \'nickname\')', data);
        }
        break;

      case 'player_joined':
        if (data.nickname) {
          if (toast) {
            toast.showInfo(`${data.nickname}님이 입장했습니다.`);
          }
          setRoomUpdated(true); // 참가자 목록 업데이트를 위해
        }
        break;

      case 'player_left':
        if (data.nickname) {
          if (toast) {
            toast.showInfo(`${data.nickname}님이 퇴장했습니다.`);
          }
          setRoomUpdated(true); // 참가자 목록 업데이트를 위해
        }
        break;

      case 'user_left':
        setParticipants((prev) =>
          prev.filter((p) => p.user_id !== data.user_id)
        );
        if (toast) {
          toast.showInfo(`${data.user?.nickname || data.nickname || '사용자'}님이 퇴장했습니다.`);
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

      case 'player_kicked':
        if (toast) {
          toast.showWarning(data.message || `${data.kicked_player?.nickname}님이 강퇴되었습니다.`);
        }
        setRoomUpdated(true);
        break;

      case 'kicked_from_room':
        if (toast) {
          toast.showError(data.message || '방장에 의해 강퇴되었습니다.');
        }
        // 강퇴당한 경우 로비로 이동
        setTimeout(() => {
          navigate('/lobby');
        }, 2000);
        break;

      case 'kick_success':
        if (toast) {
          toast.showSuccess(data.message || '플레이어를 강퇴했습니다.');
        }
        setRoomUpdated(true);
        break;

      case 'participant_list_updated':
        console.log('participant_list_updated 메시지 받음:', data);
        if (data.participants) {
          console.log('참가자 목록 업데이트:', data.participants);
          setParticipants(data.participants);
        }
        if (data.message && toast) {
          toast.showInfo(data.message);
        }
        setRoomUpdated(true);
        break;

      case 'participants_update':
        if (data.participants) {
          console.log('participants_update 받음:', data.participants);
          setParticipants(data.participants);
        }
        setRoomUpdated(true);
        break;

      case 'host_changed':
        if (toast) {
          toast.showInfo(data.message || `${data.new_host_nickname}님이 새로운 방장이 되었습니다.`);
        }
        setRoomUpdated(true);
        break;

      case 'status_changed':
        if (toast) {
          toast.showInfo('참가자 상태가 변경되었습니다.');
        }
        setRoomUpdated(true);
        break;

      case 'ready_status_updated':
        if (toast) {
          toast.showInfo('준비 상태가 업데이트되었습니다.');
        }
        setRoomUpdated(true);
        break;

      case 'ready_status_changed':
        if (data.nickname) {
          const status = data.is_ready ? '준비 완료' : '준비 해제';
          if (toast) {
            toast.showInfo(`${data.nickname}님이 ${status}했습니다.`);
          }
        }
        setRoomUpdated(true);
        break;

      case 'game_started_redis':
        setGameStatus('playing');
        if (toast) {
          toast.showSuccess('게임이 시작되었습니다!');
        }
        navigate(`/gameroom/${roomId}/game`);
        break;

      case 'game_ended_by_host':
        setGameStatus('finished');
        if (toast) {
          toast.showInfo(`게임이 종료되었습니다! 승자: ${data.winner_nickname || '무승부'}`);
        }
        navigate(`/gameroom/${roomId}/result`);
        break;

      case 'game_completed':
        setGameStatus('finished');
        if (toast) {
          toast.showSuccess(`게임이 완료되었습니다! 승자: ${data.winner_nickname || '무승부'}`);
        }
        if (data.show_modal) {
          // 게임 완료 모달 표시 로직 추가 가능
        }
        navigate(`/gameroom/${roomId}/result`);
        break;

      case 'game_time_over':
        if (toast) {
          toast.showWarning('시간이 초과되었습니다!');
        }
        setRoomUpdated(true);
        break;

      case 'word_chain_result':
        if (toast) {
          toast.showInfo(data.message || '단어 결과를 확인하세요.');
        }
        break;

      case 'word_chain_error':
        if (toast) {
          toast.showError(data.message || '잘못된 단어입니다.');
        }
        break;

      case 'chat':
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

      case 'error':
        if (toast) {
          toast.showError(data.message || '오류가 발생했습니다.');
        }
        break;

      case 'pong':
        // ping-pong 응답, 특별한 처리 불필요
        break;

      case 'room_created':
        // 방 생성 알림 (로비에서만 사용)
        break;

      case 'connected':
        console.log('서버 연결 확인:', data);
        break;

      case 'word_chain_initialized':
        if (toast) {
          toast.showInfo('게임이 초기화되었습니다.');
        }
        break;

      case 'word_chain_started':
        if (toast) {
          toast.showSuccess('게임이 시작되었습니다!');
        }
        setGameStatus('playing');
        break;

      case 'word_chain_result':
        if (toast) {
          toast.showInfo(data.message || '단어 결과를 확인하세요.');
        }
        break;

      case 'word_chain_word_submitted':
        if (data.submitted_by && data.word) {
          if (toast) {
            toast.showInfo(`${data.submitted_by.nickname}님이 "${data.word}"를 제출했습니다.`);
          }
        }
        break;

      case 'word_chain_game_over':
        if (toast) {
          toast.showWarning(data.message || '게임이 종료되었습니다!');
        }
        setGameStatus('finished');
        break;

      case 'word_chain_game_ended':
        if (toast) {
          toast.showInfo(data.message || '게임이 종료되었습니다.');
        }
        setGameStatus('finished');
        break;

      case 'game_ended':
        setGameStatus('finished');
        if (toast) {
          toast.showInfo(data.message || '게임이 종료되었습니다.');
        }
        navigate(`/gameroom/${roomId}/result`);
        break;

      case 'turn_timeout':
        if (toast) {
          toast.showWarning('시간이 초과되었습니다!');
        }
        break;

      default:
        console.log('알 수 없는 메시지 타입:', data.type);
    }
  };

  // 재연결 시도
  const attemptReconnect = useCallback(() => {
    if (connectionAttempts.current >= maxReconnectAttempts) {
      console.log('최대 재연결 시도 횟수 초과');
      if (toast) {
        toast.showError(
          '게임룸 연결이 끊어졌습니다. 페이지를 새로고침해주세요.'
        );
      }
      return;
    }

    // 인증 상태 재확인
    if (!isAuthenticated || !user) {
      console.log('재연결 시도 중단: 인증 상태 없음');
      return;
    }

    connectionAttempts.current++;
    setIsReconnecting(true);

    const delay = Math.min(
      1000 * Math.pow(2, connectionAttempts.current),
      10000
    );

    console.log(
      `재연결 시도 예약 ${connectionAttempts.current}/${maxReconnectAttempts}, ${delay}ms 후`
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      console.log(
        `재연결 시도 실행 ${connectionAttempts.current}/${maxReconnectAttempts}`
      );
      connectWebSocket();
    }, delay);
  }, [isAuthenticated, user, connectWebSocket]);

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
      guest_id: user?.guest_id,
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
