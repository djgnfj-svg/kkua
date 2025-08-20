import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Loading } from '../components/ui';
import { useUserStore } from '../stores/useUserStore';
import { useGameStore } from '../stores/useGameStore';
import { showToast } from '../components/Toast';
import { apiEndpoints } from '../utils/api';
import { useNativeWebSocket } from '../hooks/useNativeWebSocket';

const GameRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { currentRoom, setCurrentRoom, updateRoom, isLoading, setLoading } = useGameStore();
  const [roomNotFound, setRoomNotFound] = useState(false);
  const [gameState, setGameState] = useState<{
    isPlaying: boolean;
    currentTurnUserId?: string;
    currentChar?: string;
    wordChain: string[];
    scores?: Record<string, number>;
    turnTimeLimit?: number;
    remainingTime?: number;
  }>({
    isPlaying: false,
    wordChain: [],
    scores: {},
    turnTimeLimit: 30,
    remainingTime: 30
  });
  const [currentWord, setCurrentWord] = useState('');
  const [wordValidation, setWordValidation] = useState<{
    isValid: boolean;
    message: string;
    isChecking: boolean;
  }>({ isValid: true, message: '', isChecking: false });

  // 타이머 카운트다운 (서버 동기화)
  useEffect(() => {
    if (!gameState.isPlaying || gameState.currentTurnUserId !== user?.id) return;
    
    const interval = setInterval(() => {
      setGameState(prev => {
        const newTime = Math.max(0.1, (prev.remainingTime || 30) - 1);
        return { ...prev, remainingTime: newTime };
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [gameState.isPlaying, gameState.currentTurnUserId, user?.id]);

  // 실시간 단어 검증
  useEffect(() => {
    if (!currentWord.trim() || !gameState.currentChar) {
      setWordValidation({ isValid: true, message: '', isChecking: false });
      return;
    }

    const timeoutId = setTimeout(async () => {
      setWordValidation(prev => ({ ...prev, isChecking: true }));
      
      try {
        // 첫 글자 검증
        const firstChar = currentWord.charAt(0);
        if (firstChar !== gameState.currentChar) {
          setWordValidation({
            isValid: false,
            message: `"${gameState.currentChar}"로 시작해야 합니다`,
            isChecking: false
          });
          return;
        }

        // 길이 검증
        if (currentWord.length < 2) {
          setWordValidation({
            isValid: false,
            message: '2글자 이상 입력해주세요',
            isChecking: false
          });
          return;
        }

        // 한글 검증
        const koreanRegex = /^[가-힣]+$/;
        if (!koreanRegex.test(currentWord)) {
          setWordValidation({
            isValid: false,
            message: '한글만 입력 가능합니다',
            isChecking: false
          });
          return;
        }

        // 중복 검증
        if (gameState.wordChain.includes(currentWord)) {
          setWordValidation({
            isValid: false,
            message: '이미 사용된 단어입니다',
            isChecking: false
          });
          return;
        }

        // 모든 검증 통과
        setWordValidation({
          isValid: true,
          message: '✅ 유효한 단어입니다',
          isChecking: false
        });
        
      } catch (error) {
        setWordValidation({
          isValid: true,
          message: '',
          isChecking: false
        });
      }
    }, 500); // 500ms 후 검증 시작

    return () => clearTimeout(timeoutId);
  }, [currentWord, gameState.currentChar, gameState.wordChain]);

  // WebSocket 연결
  const wsUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const { 
    isConnected, 
    error: wsError, 
    emit, 
    on, 
    off 
  } = useNativeWebSocket({
    url: wsUrl,
    roomId,
    autoConnect: !!roomId,
  });

  // currentRoom을 ref로 관리하여 무한 루프 방지
  const currentRoomRef = useRef(currentRoom);
  const hasJoinedRef = useRef(false);
  
  useEffect(() => {
    currentRoomRef.current = currentRoom;
  }, [currentRoom]);

  // WebSocket 이벤트 리스너 설정 - useCallback으로 안정화
  const handleRoomJoined = useCallback((data: any) => {
    console.log('🎮 Room joined:', data);
    showToast.success(data.message || '방에 입장했습니다! 🎮');
    // game_state_update 이벤트로 플레이어 목록이 업데이트될 예정
  }, []);

  // 플레이어 입장/퇴장 이벤트
  const handlePlayerJoined = useCallback((data: any) => {
    console.log('👤 Player joined:', data);
    console.log('현재 플레이어 목록:', currentRoomRef.current?.players);
    
    showToast.info(`${data.nickname}님이 입장했습니다 ${data.is_host ? '(방장)' : ''}`);
    
    // 중복 체크 - 이미 있는 플레이어인지 확인
    if (roomId && currentRoomRef.current) {
      const existingPlayer = currentRoomRef.current.players?.find(p => 
        p.id === String(data.user_id) || p.id === data.user_id
      );
      
      if (!existingPlayer) {
        // 새로운 플레이어만 추가
        updateRoom(roomId, {
          currentPlayers: currentRoomRef.current.currentPlayers + 1,
          players: [...(currentRoomRef.current.players || []), {
            id: String(data.user_id),
            nickname: data.nickname,
            isHost: data.is_host || false,
            isReady: false
          }]
        });
        console.log(`새 플레이어 추가됨: ${data.nickname} (ID: ${data.user_id})`);
      } else {
        console.log(`플레이어 이미 존재: ${data.nickname} (ID: ${data.user_id})`);
        // 이미 존재하는 플레이어는 정보만 업데이트
        updateRoom(roomId, {
          players: (currentRoomRef.current.players || []).map(p => 
            p.id === String(data.user_id) || p.id === data.user_id
              ? { ...p, isHost: data.is_host || false, nickname: data.nickname }
              : p
          )
        });
      }
    }
  }, [roomId, updateRoom]);

  const handlePlayerLeft = useCallback((data: any) => {
    console.log('👋 Player left:', data);
    
    // 퇴장하는 플레이어 정보 찾기
    const leftPlayer = currentRoomRef.current?.players?.find(p => 
      p.id === String(data.user_id) || p.id === data.user_id
    );
    
    showToast.info(`${leftPlayer?.nickname || 'Unknown'}님이 퇴장했습니다`);
    
    // Update player list - 해당 플레이어 제거
    if (roomId && currentRoomRef.current && leftPlayer) {
      updateRoom(roomId, {
        currentPlayers: Math.max(1, currentRoomRef.current.currentPlayers - 1),
        players: (currentRoomRef.current.players || []).filter(p => 
          p.id !== String(data.user_id) && p.id !== data.user_id
        )
      });
      console.log(`플레이어 제거됨: ${leftPlayer.nickname} (ID: ${data.user_id})`);
    }
  }, [roomId, updateRoom]);

  // 채팅 메시지 이벤트
  const handleChatMessage = useCallback((data: any) => {
    console.log('💬 Chat message:', data);
    showToast.info(`${data.nickname}: ${data.message}`);
  }, []);

  // 게임 관련 이벤트들
  const handleGameStarted = useCallback((data: any) => {
    console.log('🎮 Game started:', data);
    console.log('🎮 Current turn user ID:', data.current_turn_user_id, 'Type:', typeof data.current_turn_user_id);
    console.log('🎮 My user ID:', user?.id, 'Type:', typeof user?.id);
    
    const currentTurnUserIdStr = String(data.current_turn_user_id);
    const isMyTurn = currentTurnUserIdStr === String(user?.id);
    
    console.log('🎮 Is my turn?', isMyTurn, 'Comparison:', currentTurnUserIdStr, '===', String(user?.id));
    
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: true,
      currentTurnUserId: currentTurnUserIdStr, // 문자열로 변환
      currentChar: data.next_char || '',
      remainingTime: data.current_turn_remaining_time || 30,
      scores: data.scores || {}
    }));
    showToast.success(`게임이 시작되었습니다! ${data.current_turn_nickname}님의 차례입니다 🎮`);
  }, [user?.id]);

  const handleWordSubmitted = useCallback((data: any) => {
    console.log('📝 Word submitted:', data);
    
    if (data.status === 'accepted') {
      // 성공한 단어 제출
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: String(data.current_turn_user_id),
        currentChar: data.next_char || '',
        remainingTime: data.current_turn_remaining_time || prev.remainingTime,
        wordChain: [...(prev.wordChain || []), data.word],
        scores: { ...(prev.scores || {}), ...data.scores }
      }));
      
      showToast.success(`${data.nickname}님: "${data.word}" ✅`);
      
      // 다음 플레이어 알림
      const nextPlayer = currentRoomRef.current?.players?.find(p => String(p.id) === String(data.current_turn_user_id));
      if (nextPlayer) {
        const remainingTime = data.current_turn_remaining_time || 30;
        showToast.info(`다음 차례: ${nextPlayer.nickname}님 (${data.next_char}로 시작, ${remainingTime}초)`);
      }
    } else if (data.status === 'pending_validation') {
      showToast.info(`${data.nickname}님이 "${data.word}" 단어를 제출했습니다...`);
    }
  }, []);
  
  const handleWordSubmissionFailed = useCallback((data: any) => {
    console.log('❌ Word submission failed:', data);
    showToast.error(data.reason || '단어 제출에 실패했습니다');
  }, []);
  
  const handlePlayerReady = useCallback((data: any) => {
    console.log('✅ Player ready:', data);
    console.log('현재 플레이어 목록:', currentRoomRef.current?.players);
    
    showToast.info(`${data.nickname}님이 ${data.ready ? '준비완료' : '준비취소'}했습니다`);
    
    // Update player ready status - 양쪽 타입 모두 확인
    if (roomId && currentRoomRef.current) {
      updateRoom(roomId, {
        players: (currentRoomRef.current.players || []).map(p => 
          p.id === String(data.user_id) || p.id === data.user_id 
            ? { ...p, isReady: data.ready } : p
        )
      });
    }
  }, [roomId, updateRoom]);

  // 에러 처리
  const handleError = useCallback((data: any) => {
    console.error('🚫 WebSocket error:', data);
    showToast.error(data.error || '연결 오류가 발생했습니다');
  }, []);

  // 성공 응답 처리
  const handleSuccess = useCallback((data: any) => {
    console.log('✅ Success:', data);
  }, []);

  // 타이머 관련 핸들러들
  const handleTurnTimerStarted = useCallback((data: any) => {
    console.log('⏰ Turn timer started:', data);
    
    // 서버에서 전송된 정확한 시간으로 동기화
    const serverTime = data.remaining_time || data.time_limit || 30;
    
    setGameState(prev => ({
      ...prev,
      remainingTime: serverTime,
      turnTimeLimit: serverTime
    }));
    
    console.log(`타이머 동기화: ${serverTime}초`);
  }, []);

  const handleTurnTimeout = useCallback((data: any) => {
    console.log('⏰ Turn timeout:', data);
    showToast.warning(`${data.timeout_nickname}님의 시간이 초과되었습니다`);
    
    // 타임아웃된 플레이어의 남은 시간 정보도 표시
    if (data.timeout_player_remaining_time !== undefined) {
      showToast.info(`${data.timeout_nickname}님의 남은 시간: ${data.timeout_player_remaining_time}초`);
    }
    
    // 턴 타임아웃 시 다음 플레이어로 이동
    if (data.current_turn_user_id) {
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: String(data.current_turn_user_id),
        remainingTime: data.current_turn_remaining_time || 30 // 다음 플레이어의 개별 시간
      }));
    }
  }, []);

  // 게임 종료 핸들러 추가
  const handleGameEnded = useCallback((data: any) => {
    console.log('🏁 Game ended:', data);
    
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: false 
    }));
    
    if (data.reason === 'time_elimination') {
      showToast.error(`${data.eliminated_player}님이 시간 소진으로 탈락했습니다!`);
      if (data.winner) {
        showToast.success(`🏆 ${data.winner}님이 승리했습니다!`);
      }
    }
    
    // 5초 후 로비로 이동
    setTimeout(() => {
      navigate('/lobby');
    }, 5000);
  }, [navigate]);

  // 플레이어 탈락 핸들러 추가
  const handlePlayerEliminated = useCallback((data: any) => {
    console.log('💀 Player eliminated:', data);
    
    showToast.error(`${data.eliminated_player}님이 시간 소진으로 탈락했습니다!`);
    
    // 다음 플레이어로 턴 이동
    if (data.current_turn_user_id) {
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: String(data.current_turn_user_id),
        remainingTime: data.current_turn_remaining_time || 30
      }));
    }
  }, []);

  // game_state_update 핸들러 추가
  const handleGameStateUpdate = useCallback((data: any) => {
    console.log('🔄 Game state update:', data);
    if (roomId && data.players) {
      console.log('게임 상태 업데이트 - 플레이어 목록:', data.players);
      
      // 플레이어 목록 전체 업데이트
      updateRoom(roomId, {
        players: data.players,
        currentPlayers: data.players.length,
        status: data.status
      });
      
      // 게임 상태도 업데이트 (게임이 시작된 경우)
      if (data.status === 'playing') {
        setGameState(prev => ({
          ...prev,
          isPlaying: true,
          currentTurnUserId: data.current_turn ? String(data.players[data.current_turn]?.user_id) : prev.currentTurnUserId
        }));
      }
    }
  }, [roomId, updateRoom]);

  // 고도화된 방 나가기 이벤트 핸들러들
  const handleHostLeftGame = useCallback((data: any) => {
    console.log('👑❌ Host left game:', data);
    showToast.error(data.message);
    
    // 5초 후 로비로 이동
    setTimeout(() => {
      navigate('/lobby');
    }, 5000);
    
    showToast.info('5초 후 로비로 이동합니다...');
  }, [navigate]);

  const handleHostChanged = useCallback((data: any) => {
    console.log('👑🔄 Host changed:', data);
    showToast.info(data.message);
    
    // 새로운 방장 정보로 플레이어 목록 업데이트
    if (roomId && currentRoomRef.current?.players) {
      const updatedPlayers = currentRoomRef.current.players.map(player => ({
        ...player,
        isHost: String(player.id) === String(data.new_host_user_id)
      }));
      
      updateRoom(roomId, {
        players: updatedPlayers
      });
    }
  }, [roomId, updateRoom]);

  const handleOpponentLeftVictory = useCallback((data: any) => {
    console.log('🏆 Opponent left victory:', data);
    showToast.success(data.message);
    
    // 승리 처리
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: false,
      gameResult: 'victory',
      resultMessage: data.message
    }));
  }, []);

  const handlePlayerLeftDuringTurn = useCallback((data: any) => {
    console.log('🚪 Player left during turn:', data);
    showToast.warning(data.message);
    
    // 턴 정보 업데이트
    setGameState(prev => ({
      ...prev,
      currentTurnUserId: String(data.current_turn_user_id),
      remainingTime: data.current_turn_remaining_time || prev.remainingTime
    }));
  }, []);

  const handlePlayerLeftGame = useCallback((data: any) => {
    console.log('🚪 Player left game:', data);
    showToast.info(data.message);
  }, []);

  const handlePlayerLeftRoom = useCallback((data: any) => {
    console.log('🚪 Player left room:', data);
    showToast.info(data.message);
  }, []);

  const handleRoomDisbanded = useCallback((data: any) => {
    console.log('💥 Room disbanded:', data);
    showToast.error(data.message);
    
    // 로비로 이동
    navigate('/lobby');
  }, [navigate]);

  useEffect(() => {
    if (!isConnected || !roomId) return;

    // 이벤트 리스너 등록
    on('room_joined', handleRoomJoined);
    on('player_joined', handlePlayerJoined);
    on('player_left', handlePlayerLeft);
    on('chat_message', handleChatMessage);
    on('game_started', handleGameStarted);
    on('word_submitted', handleWordSubmitted);
    on('word_submission_failed', handleWordSubmissionFailed);
    on('turn_timer_started', handleTurnTimerStarted);
    on('turn_timeout', handleTurnTimeout);
    on('player_ready_status', handlePlayerReady);
    on('game_state_update', handleGameStateUpdate);
    on('host_left_game', handleHostLeftGame);
    on('host_changed', handleHostChanged);
    on('opponent_left_victory', handleOpponentLeftVictory);
    on('player_left_during_turn', handlePlayerLeftDuringTurn);
    on('player_left_game', handlePlayerLeftGame);
    on('player_left_room', handlePlayerLeftRoom);
    on('room_disbanded', handleRoomDisbanded);
    on('game_ended', handleGameEnded);
    on('player_eliminated', handlePlayerEliminated);
    on('error', handleError);
    on('success', handleSuccess);
    on('pong', (data: any) => console.log('🏓 Pong received:', data));

    // 방 입장 요청 - 최초 연결 시에만
    if (!hasJoinedRef.current) {
      hasJoinedRef.current = true;
      emit('join_room', { 
        room_id: roomId,
        user: {
          id: user?.id,
          nickname: user?.nickname
        }
      }, true);
    }

    return () => {
      // 이벤트 리스너 정리
      off('room_joined', handleRoomJoined);
      off('player_joined', handlePlayerJoined);
      off('player_left', handlePlayerLeft);
      off('chat_message', handleChatMessage);
      off('game_started', handleGameStarted);
      off('word_submitted', handleWordSubmitted);
      off('word_submission_failed', handleWordSubmissionFailed);
      off('turn_timer_started', handleTurnTimerStarted);
      off('turn_timeout', handleTurnTimeout);
      off('player_ready_status', handlePlayerReady);
      off('game_state_update', handleGameStateUpdate);
      off('host_left_game', handleHostLeftGame);
      off('host_changed', handleHostChanged);
      off('opponent_left_victory', handleOpponentLeftVictory);
      off('player_left_during_turn', handlePlayerLeftDuringTurn);
      off('player_left_game', handlePlayerLeftGame);
      off('player_left_room', handlePlayerLeftRoom);
      off('room_disbanded', handleRoomDisbanded);
      off('game_ended', handleGameEnded);
      off('player_eliminated', handlePlayerEliminated);
      off('error', handleError);
      off('success', handleSuccess);
      off('pong');
    };
  }, [isConnected, roomId, user?.id, emit, on, off, handleRoomJoined, handlePlayerJoined, handlePlayerLeft, handleChatMessage, handleGameStarted, handleWordSubmitted, handleWordSubmissionFailed, handleTurnTimerStarted, handleTurnTimeout, handlePlayerReady, handleGameStateUpdate, handleHostLeftGame, handleHostChanged, handleOpponentLeftVictory, handlePlayerLeftDuringTurn, handlePlayerLeftGame, handlePlayerLeftRoom, handleRoomDisbanded, handleGameEnded, handlePlayerEliminated, handleError, handleSuccess]);

  useEffect(() => {
    if (!roomId) {
      navigate('/lobby');
      return;
    }

    // 방 정보 로드 (실제로는 방 참가 API 호출)
    loadRoomInfo();
  }, [roomId]);

  const loadRoomInfo = async () => {
    if (!roomId) return;
    
    setLoading(true);
    try {
      // 임시: 방 정보를 시뮬레이션
      // 실제로는 API에서 방 정보를 가져와야 함
      const mockRoom = {
        id: roomId,
        name: `게임룸 ${roomId.slice(-4)}`,
        maxPlayers: 4,
        currentPlayers: 1,
        status: 'waiting' as const,
        createdAt: new Date().toISOString(),
        players: [
          {
            id: user?.id || '1',
            nickname: user?.nickname || 'Unknown',
            isHost: true,
            isReady: false
          }
        ]
      };
      
      setCurrentRoom(mockRoom);
      showToast.success('방 정보를 불러왔습니다');
    } catch (error) {
      console.error('방 정보 로드 실패:', error);
      setRoomNotFound(true);
      showToast.error('방을 찾을 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveRoom = async () => {
    try {
      // 게임 중인지 확인
      const isGameInProgress = gameState.isPlaying;
      const isHost = currentRoom?.players?.find(p => String(p.id) === String(user?.id))?.isHost;
      
      // 확인 메시지 생성
      let confirmMessage = '정말로 방을 나가시겠습니까?';
      
      if (isGameInProgress && isHost) {
        confirmMessage = '⚠️ 방장이 게임 중에 나가면 모든 플레이어의 게임이 종료됩니다.\n정말로 나가시겠습니까?';
      } else if (isGameInProgress) {
        confirmMessage = '⚠️ 게임이 진행 중입니다. 나가면 패배 처리됩니다.\n정말로 나가시겠습니까?';
      } else if (isHost) {
        confirmMessage = '⚠️ 방장이 나가면 다른 플레이어에게 방장이 넘어갑니다.\n정말로 나가시겠습니까?';
      }
      
      // 확인 다이얼로그
      const confirmed = window.confirm(confirmMessage);
      
      if (!confirmed) {
        return;
      }
      
      if (roomId && isConnected) {
        emit('leave_room', { room_id: roomId });
      }
      navigate('/lobby');
      showToast.info('방에서 나갔습니다');
    } catch (error) {
      console.error('방 나가기 실패:', error);
      navigate('/lobby'); // 에러가 있어도 로비로 이동
    }
  };

  const handleReadyToggle = () => {
    if (!isConnected) return;
    
    const currentPlayerReady = currentRoom?.players?.find(p => p.id === user.id)?.isReady;
    emit('ready_game', { 
      room_id: roomId,
      ready: !currentPlayerReady
    });
  };

  const handleStartGame = () => {
    if (!isConnected) return;
    
    emit('start_game', { room_id: roomId });
  };

  const handleSubmitWord = () => {
    if (!isConnected || !currentWord.trim()) return;
    
    emit('submit_word', { room_id: roomId, word: currentWord.trim() });
    setCurrentWord('');
  };

  const handleSendChat = (message: string) => {
    if (!isConnected || !message.trim()) return;
    
    emit('chat_message', { room_id: roomId, message: message.trim() });
  };

  if (!user) {
    return null;
  }

  if (roomNotFound) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="w-full max-w-md">
          <Card.Body>
            <div className="text-center">
              <h2 className="text-xl font-bold text-gray-900 mb-4">방을 찾을 수 없습니다</h2>
              <p className="text-gray-600 mb-4">
                요청하신 방이 존재하지 않거나 이미 종료되었습니다.
              </p>
              <Button onClick={() => navigate('/lobby')}>
                로비로 돌아가기
              </Button>
            </div>
          </Card.Body>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                {currentRoom?.name || `게임룸 ${roomId?.slice(-4)}`}
              </h1>
              <div className={`ml-4 px-2 py-1 rounded-full text-xs font-medium ${
                isConnected 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-red-100 text-red-800'
              }`}>
                {isConnected ? '연결됨' : '연결 끊김'}
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                variant="secondary" 
                size="sm" 
                onClick={handleLeaveRoom}
              >
                방 나가기
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        {isLoading ? (
          <Loading />
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
            {/* 게임 영역 */}
            <div className="xl:col-span-2">
              <Card>
                <Card.Header>
                  <div className="flex justify-between items-center">
                    <h2 className="text-lg font-semibold">
                      {gameState.isPlaying ? '끝말잇기 게임' : '게임 대기'}
                    </h2>
                    {gameState.isPlaying && gameState.currentTurnUserId === String(user.id) && (
                      <div className="text-sm font-medium text-blue-600 flex items-center space-x-2">
                        <span>⏰ {gameState.remainingTime?.toFixed(1)}초</span>
                        <div className="w-12 sm:w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div 
                            className={`h-full transition-all duration-1000 ${
                              (gameState.remainingTime || 0) > 15 ? 'bg-green-500' :
                              (gameState.remainingTime || 0) > 5 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ 
                              width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / 30) * 100))}%` 
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </Card.Header>
                <Card.Body>
                  {gameState.isPlaying ? (
                    <div className="space-y-4">
                      {/* 단어 체인 */}
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-2">단어 체인</h4>
                        <div className="flex flex-wrap gap-2 max-h-32 sm:max-h-40 overflow-y-auto">
                          {gameState.wordChain.map((word, index) => (
                            <span 
                              key={`${word}-${index}`}
                              className={`px-2 sm:px-3 py-1 rounded-lg text-sm transition-all duration-500 transform ${
                                index === gameState.wordChain.length - 1 
                                  ? 'bg-green-100 text-green-800 animate-pulse scale-105' 
                                  : 'bg-blue-100 text-blue-800'
                              }`}
                              style={{
                                animationDelay: `${index * 100}ms`
                              }}
                            >
                              {word}
                            </span>
                          ))}
                        </div>
                        {gameState.currentChar && (
                          <p className="mt-2 text-sm text-gray-600">
                            다음 단어는 <strong>"{gameState.currentChar}"</strong>로 시작해야 합니다
                          </p>
                        )}
                      </div>

                      {/* 단어 입력 */}
                      {gameState.currentTurnUserId === String(user.id) ? (
                        <div className="bg-blue-50 rounded-lg p-4">
                          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 space-y-1 sm:space-y-0">
                            <h4 className="font-medium text-blue-900">
                              내 차례입니다!
                            </h4>
                            <div className="flex items-center space-x-2 text-sm">
                              <span className="font-medium text-blue-900">{gameState.remainingTime?.toFixed(1)}초</span>
                            </div>
                          </div>
                          <div className="w-full h-3 bg-blue-200 rounded-full overflow-hidden mb-3">
                            <div 
                              className={`h-full transition-all duration-1000 ${
                                (gameState.remainingTime || 0) > 15 ? 'bg-green-500' :
                                (gameState.remainingTime || 0) > 5 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ 
                                width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / 30) * 100))}%` 
                              }}
                            />
                          </div>
                          <div className="space-y-2">
                            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                              <input
                                type="text"
                                value={currentWord}
                                onChange={(e) => setCurrentWord(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleSubmitWord()}
                                placeholder={gameState.currentChar ? `${gameState.currentChar}로 시작하는 단어...` : '단어를 입력하세요...'}
                                className={`flex-1 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 transition-colors text-base ${
                                  wordValidation.isChecking ? 'border-gray-300 focus:ring-gray-400' :
                                  !wordValidation.isValid && currentWord.trim() ? 'border-red-300 focus:ring-red-500 bg-red-50' :
                                  wordValidation.isValid && currentWord.trim() && wordValidation.message ? 'border-green-300 focus:ring-green-500 bg-green-50' :
                                  'border-gray-300 focus:ring-blue-500'
                                }`}
                                disabled={!isConnected}
                              />
                              <Button 
                                onClick={handleSubmitWord}
                                disabled={!isConnected || !currentWord.trim() || !wordValidation.isValid}
                                variant={wordValidation.isValid && currentWord.trim() ? 'primary' : 'secondary'}
                                className="w-full sm:w-auto"
                              >
                                제출
                              </Button>
                            </div>
                            {/* 실시간 검증 피드백 */}
                            {currentWord.trim() && (
                              <div className={`text-sm px-2 py-1 rounded transition-colors ${
                                wordValidation.isChecking ? 'text-gray-600 bg-gray-100' :
                                !wordValidation.isValid ? 'text-red-600 bg-red-100' :
                                wordValidation.message ? 'text-green-600 bg-green-100' : ''
                              }`}>
                                {wordValidation.isChecking ? '🔍 검증 중...' : wordValidation.message}
                              </div>
                            )}
                          </div>
                        </div>
                      ) : (
                        <div className="bg-gray-50 rounded-lg p-4 text-center">
                          <p className="text-gray-600">
                            {currentRoom?.players?.find(p => String(p.id) === gameState.currentTurnUserId)?.nickname || '다른 플레이어'}님의 차례입니다...
                          </p>
                        </div>
                      )}

                      {/* 점수 */}
                      {gameState.scores && Object.keys(gameState.scores).length > 0 && (
                        <div className="bg-green-50 rounded-lg p-4">
                          <h4 className="font-medium text-green-900 mb-2">점수</h4>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(gameState.scores).map(([userId, score]) => {
                              const player = currentRoom?.players?.find(p => p.id === userId);
                              return (
                                <div key={userId} className="flex justify-between">
                                  <span>{player?.nickname || `Player ${userId}`}</span>
                                  <span className="font-bold">{score}점</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <p className="text-gray-600 mb-4">
                        모든 플레이어가 준비되면 게임을 시작할 수 있습니다
                      </p>
                      <div className="space-x-2">
                        <Button 
                          variant="secondary"
                          onClick={handleReadyToggle}
                          disabled={!isConnected}
                        >
                          {currentRoom?.players?.find(p => p.id === user.id)?.isReady ? '준비 취소' : '준비 완료'}
                        </Button>
                        {currentRoom?.players?.find(p => p.id === user.id)?.isHost && (
                          <Button 
                            onClick={handleStartGame}
                            disabled={!isConnected || !currentRoom?.players?.every(p => p.isReady)}
                          >
                            게임 시작
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </Card.Body>
              </Card>
            </div>

            {/* 사이드바 */}
            <div className="space-y-6">
              {/* 플레이어 목록 */}
              <Card>
                <Card.Header>
                  <h3 className="text-lg font-semibold">
                    플레이어 ({currentRoom?.currentPlayers || 0}/{currentRoom?.maxPlayers || 4})
                  </h3>
                </Card.Header>
                <Card.Body>
                  <div className="space-y-3">
                    {currentRoom?.players?.map((player) => (
                      <div 
                        key={player.id} 
                        className={`flex items-center justify-between p-3 rounded-lg ${
                          player.id === user.id ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center">
                          <div className={`w-3 h-3 rounded-full mr-2 ${
                            player.isReady ? 'bg-green-500' : 'bg-gray-300'
                          }`} />
                          <span className={`font-medium ${
                            player.id === user.id ? 'text-blue-900' : 'text-gray-900'
                          }`}>
                            {player.nickname}
                            {player.id === user.id && ' (나)'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-1">
                          {player.isHost && (
                            <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
                              방장
                            </span>
                          )}
                          {gameState.isPlaying && gameState.currentTurnUserId === player.id && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                              턴
                            </span>
                          )}
                        </div>
                      </div>
                    )) || (
                      <p className="text-gray-500 text-center py-4">
                        플레이어 정보를 불러오는 중...
                      </p>
                    )}
                  </div>
                </Card.Body>
              </Card>

              {/* 간단한 채팅 */}
              <Card>
                <Card.Header>
                  <h3 className="text-lg font-semibold">채팅</h3>
                </Card.Header>
                <Card.Body>
                  <div className="space-y-3">
                    <input
                      type="text"
                      placeholder="채팅 메시지..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          handleSendChat((e.target as HTMLInputElement).value);
                          (e.target as HTMLInputElement).value = '';
                        }
                      }}
                      disabled={!isConnected}
                    />
                    <Button
                      variant="secondary"
                      size="sm"
                      disabled={!isConnected}
                      onClick={() => {
                        const input = document.querySelector('input[placeholder="채팅 메시지..."]') as HTMLInputElement;
                        if (input?.value) {
                          handleSendChat(input.value);
                          input.value = '';
                        }
                      }}
                    >
                      💬
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </div>
          </div>
        )}

        {/* 새로고침 안내 */}
        <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-900 mb-2">✅ 상태 유지 확인</h4>
          <p className="text-green-700 text-sm">
            이제 새로고침을 해도 현재 방 상태가 유지됩니다! URL에 방 ID가 포함되어 있어 
            브라우저를 닫고 다시 열어도 같은 방으로 돌아올 수 있습니다.
          </p>
        </div>
      </main>
    </div>
  );
};

export default GameRoomPage;