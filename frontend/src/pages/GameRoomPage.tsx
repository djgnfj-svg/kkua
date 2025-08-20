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

  // 타이머 카운트다운
  useEffect(() => {
    if (!gameState.isPlaying || gameState.currentTurnUserId !== user?.id) return;
    
    const interval = setInterval(() => {
      setGameState(prev => {
        const newTime = Math.max(0, (prev.remainingTime || 30) - 1);
        return { ...prev, remainingTime: newTime };
      });
    }, 1000);
    
    return () => clearInterval(interval);
  }, [gameState.isPlaying, gameState.currentTurnUserId, user?.id]);

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
    if (data.room) {
      setCurrentRoom(data.room);
      showToast.success(`${data.room.name}에 입장했습니다! 🎮`);
    } else if (roomId) {
      // Update current room with new info
      updateRoom(roomId, {
        players: data.users || [],
        currentPlayers: data.user_count || currentRoomRef.current?.currentPlayers || 1
      });
      showToast.success(`방에 입장했습니다! 🎮`);
    }
  }, [roomId, setCurrentRoom, updateRoom]);

  // 플레이어 입장/퇴장 이벤트
  const handlePlayerJoined = useCallback((data: any) => {
    console.log('👤 Player joined:', data);
    showToast.info(`새로운 플레이어가 입장했습니다`);
    
    // Update player list
    if (roomId && currentRoomRef.current) {
      updateRoom(roomId, {
        currentPlayers: currentRoomRef.current.currentPlayers + 1,
        players: [...(currentRoomRef.current.players || []), {
          id: data.user_id,
          nickname: data.nickname,
          isHost: false,
          isReady: false
        }]
      });
    }
  }, [roomId, updateRoom]);

  const handlePlayerLeft = useCallback((data: any) => {
    console.log('👋 Player left:', data);
    showToast.info(`플레이어가 퇴장했습니다`);
    
    // Update player list
    if (roomId && currentRoomRef.current) {
      updateRoom(roomId, {
        currentPlayers: Math.max(1, currentRoomRef.current.currentPlayers - 1),
        players: (currentRoomRef.current.players || []).filter(p => p.id !== data.user_id)
      });
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
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: true,
      currentTurnUserId: data.current_turn_user_id,
      currentChar: data.next_char || '',
      scores: data.scores || {}
    }));
    showToast.success(`게임이 시작되었습니다! ${data.current_turn_nickname}님의 차례입니다 🎮`);
  }, []);

  const handleWordSubmitted = useCallback((data: any) => {
    console.log('📝 Word submitted:', data);
    
    if (data.status === 'accepted') {
      // 성공한 단어 제출
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: data.current_turn_user_id,
        currentChar: data.next_char || '',
        wordChain: [...(prev.wordChain || []), data.word],
        scores: { ...(prev.scores || {}), ...data.scores }
      }));
      
      showToast.success(`${data.nickname}님: "${data.word}" ✅`);
      
      // 다음 플레이어 알림
      const nextPlayer = currentRoomRef.current?.players?.find(p => p.id === data.current_turn_user_id);
      if (nextPlayer) {
        showToast.info(`다음 차례: ${nextPlayer.nickname}님 (${data.next_char}로 시작)`);
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
    showToast.info(`${data.nickname}님이 ${data.ready ? '준비완료' : '준비취소'}했습니다`);
    
    // Update player ready status
    if (roomId && currentRoomRef.current) {
      updateRoom(roomId, {
        players: (currentRoomRef.current.players || []).map(p => 
          p.id === data.user_id ? { ...p, isReady: data.ready } : p
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
    if (data.remaining_time) {
      setGameState(prev => ({
        ...prev,
        remainingTime: data.remaining_time
      }));
    }
  }, []);

  const handleTurnTimeout = useCallback((data: any) => {
    console.log('⏰ Turn timeout:', data);
    showToast.warning('시간 초과! 다음 플레이어에게 넘어갑니다');
    // 턴 타임아웃 시 다음 플레이어로 이동
    if (data.current_turn_user_id) {
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: data.current_turn_user_id,
        remainingTime: 30 // 새로운 턴 시작
      }));
    }
  }, []);

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
      off('error', handleError);
      off('success', handleSuccess);
      off('pong');
    };
  }, [isConnected, roomId, user?.id, emit, on, off, handleRoomJoined, handlePlayerJoined, handlePlayerLeft, handleChatMessage, handleGameStarted, handleWordSubmitted, handleWordSubmissionFailed, handleTurnTimerStarted, handleTurnTimeout, handlePlayerReady, handleError, handleSuccess]);

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

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <Loading />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* 게임 영역 */}
            <div className="lg:col-span-2">
              <Card>
                <Card.Header>
                  <div className="flex justify-between items-center">
                    <h2 className="text-lg font-semibold">
                      {gameState.isPlaying ? '끝말잇기 게임' : '게임 대기'}
                    </h2>
                    {gameState.isPlaying && gameState.currentTurnUserId === user.id && (
                      <div className="text-sm font-medium text-blue-600">
                        ⏰ {gameState.remainingTime}초
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
                        <div className="flex flex-wrap gap-2">
                          {gameState.wordChain.map((word, index) => (
                            <span 
                              key={index}
                              className="px-3 py-1 bg-blue-100 text-blue-800 rounded-lg text-sm"
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
                      {gameState.currentTurnUserId === user.id ? (
                        <div className="bg-blue-50 rounded-lg p-4">
                          <h4 className="font-medium text-blue-900 mb-2">
                            내 차례입니다! ({gameState.remainingTime}초 남음)
                          </h4>
                          <div className="flex space-x-2">
                            <input
                              type="text"
                              value={currentWord}
                              onChange={(e) => setCurrentWord(e.target.value)}
                              onKeyPress={(e) => e.key === 'Enter' && handleSubmitWord()}
                              placeholder={gameState.currentChar ? `${gameState.currentChar}로 시작하는 단어...` : '단어를 입력하세요...'}
                              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                              disabled={!isConnected}
                            />
                            <Button 
                              onClick={handleSubmitWord}
                              disabled={!isConnected || !currentWord.trim()}
                            >
                              제출
                            </Button>
                          </div>
                        </div>
                      ) : (
                        <div className="bg-gray-50 rounded-lg p-4 text-center">
                          <p className="text-gray-600">
                            {currentRoom?.players?.find(p => p.id === gameState.currentTurnUserId)?.nickname || '다른 플레이어'}님의 차례입니다...
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