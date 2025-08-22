import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Loading } from '../components/ui';
import { useUserStore } from '../stores/useUserStore';
import { useGameStore } from '../stores/useGameStore';
import { useMobileOptimization } from '../hooks/useMobileOptimization';
import { showToast } from '../components/Toast';
// import { apiEndpoints } from '../utils/api';
import { useNativeWebSocket } from '../hooks/useNativeWebSocket';
import { useNavigationProtection } from '../hooks/useNavigationProtection';
import GameReport from '../components/GameReport';
import ItemPanel from '../components/ItemPanel';
import ChatPanel from '../components/ChatPanel';
import DuplicateConnectionModal from '../components/DuplicateConnectionModal';
import { getTabCommunicationManager } from '../utils/tabCommunication';

const GameRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { currentRoom, setCurrentRoom, updateRoom, isLoading, setLoading } = useGameStore();
  const { handleInputFocus, isMobile } = useMobileOptimization();
  
  
  // 사운드 시스템
  const playSound = useCallback((type: 'type' | 'success' | 'error' | 'warning') => {
    try {
      // Web Audio API로 간단한 효과음 생성
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      switch (type) {
        case 'type':
          oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
          gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
          oscillator.start();
          oscillator.stop(audioContext.currentTime + 0.1);
          break;
        case 'success':
          oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
          oscillator.frequency.setValueAtTime(659.25, audioContext.currentTime + 0.1); // E5
          oscillator.frequency.setValueAtTime(783.99, audioContext.currentTime + 0.2); // G5
          gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
          oscillator.start();
          oscillator.stop(audioContext.currentTime + 0.3);
          break;
        case 'error':
          oscillator.frequency.setValueAtTime(220, audioContext.currentTime);
          oscillator.frequency.setValueAtTime(196, audioContext.currentTime + 0.15);
          gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
          oscillator.start();
          oscillator.stop(audioContext.currentTime + 0.3);
          break;
        case 'warning':
          oscillator.frequency.setValueAtTime(440, audioContext.currentTime);
          oscillator.frequency.setValueAtTime(880, audioContext.currentTime + 0.1);
          gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
          gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
          oscillator.start();
          oscillator.stop(audioContext.currentTime + 0.2);
          break;
      }
    } catch (error) {
      // 사운드 재생 실패는 무시 (선택적 기능)
    }
  }, []);
  const tabCommManager = getTabCommunicationManager();
  const [roomNotFound, setRoomNotFound] = useState(false);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [duplicateMessage, setDuplicateMessage] = useState('');
  const [gameState, setGameState] = useState<{
    isPlaying: boolean;
    isRoundTransition?: boolean; // 라운드 전환 중 상태 추가
    currentTurnUserId?: string;
    currentChar?: string;
    wordChain: string[];
    scores?: Record<string, number>;
    turnTimeLimit?: number;
    remainingTime?: number;
    currentRound?: number;
    maxRounds?: number;
    showFinalRankings?: boolean;
    finalRankings?: Array<{
      rank: number;
      user_id: number;
      nickname: string;
      score: number;
      words_submitted: number;
      items_used: number;
    }>;
  }>({
    isPlaying: false,
    isRoundTransition: false,
    wordChain: [],
    scores: {},
    turnTimeLimit: 30,
    remainingTime: 30,
    currentRound: 1,
    maxRounds: 3,
    showFinalRankings: false,
    finalRankings: []
  });
  const [currentWord, setCurrentWord] = useState('');
  const [typingEffect, setTypingEffect] = useState<{
    chars: Array<{ char: string; animated: boolean; id: string }>;
    isTyping: boolean;
  }>({ chars: [], isTyping: false });
  const [chatMessages, setChatMessages] = useState<Array<{
    id: string;
    userId: number;
    nickname: string;
    message: string;
    timestamp: string;
    type?: 'user' | 'system' | 'game';
  }>>([]);
  const [wordValidation, setWordValidation] = useState<{
    isValid: boolean;
    message: string;
    isChecking: boolean;
  }>({ isValid: true, message: '', isChecking: false });
  
  // 시각적 효과 상태
  const [visualEffects, setVisualEffects] = useState<{
    wordSubmitEffect: 'none' | 'success' | 'error' | 'shake';
    gameEndCelebration: 'none' | 'victory' | 'game_over';
  }>({ 
    wordSubmitEffect: 'none', 
    gameEndCelebration: 'none'
  });

  // 타이머 카운트다운 (부드러운 연속 애니메이션)
  useEffect(() => {
    if (!gameState.isPlaying || gameState.currentTurnUserId !== user?.id) return;
    
    // 100ms마다 더 부드러운 애니메이션
    const interval = setInterval(() => {
      setGameState(prev => {
        const decrementRate = (prev.remainingTime || 0) > 5 ? 0.1 : (prev.remainingTime || 0) > 3 ? 0.15 : 0.25; // 시간이 적을수록 더 빠르게
        const newTime = Math.max(0.1, (prev.remainingTime || 30) - decrementRate);
        
        // 경고음 재생 (5초 남았을 때 - 한 번만)
        if (Math.floor(newTime) === 5 && Math.floor(prev.remainingTime || 30) === 6) {
          playSound('warning');
        }
        
        return { ...prev, remainingTime: newTime };
      });
    }, 100); // 100ms 간격으로 부드러운 애니메이션
    
    return () => clearInterval(interval);
  }, [gameState.isPlaying, gameState.currentTurnUserId, user?.id, playSound]);

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
  const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
  const { 
    isConnected, 
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

  // 타이핑 애니메이션 효과
  const lastSoundTime = useRef(0);
  const handleWordChange = useCallback((newValue: string) => {
    const oldLength = currentWord.length;
    const newLength = newValue.length;
    
    if (newLength > oldLength) {
      // 연속 타이핑시 사운드 제한 (100ms 간격)
      const now = Date.now();
      if (now - lastSoundTime.current > 100) {
        playSound('type');
        lastSoundTime.current = now;
      }
      
      // 새로운 글자 애니메이션
      const newChars = newValue.split('').map((char, index) => ({
        char,
        animated: index >= oldLength,
        id: `${Date.now()}-${index}`
      }));
      
      setTypingEffect({
        chars: newChars,
        isTyping: true
      });
      
      // 애니메이션 초기화
      setTimeout(() => {
        setTypingEffect(prev => ({
          chars: prev.chars.map(char => ({ ...char, animated: false })),
          isTyping: false
        }));
      }, 300);
    } else {
      // 글자 삭제 시에는 즉시 업데이트
      setTypingEffect({
        chars: newValue.split('').map((char, index) => ({
          char,
          animated: false,
          id: `${Date.now()}-${index}`
        })),
        isTyping: false
      });
    }
    
    setCurrentWord(newValue);
  }, [currentWord, playSound]);

  // 채팅 메시지 추가 함수들
  const addGameMessage = useCallback((message: string) => {
    setChatMessages(prev => [...prev, {
      id: `game-${Date.now()}-${Math.random()}`,
      userId: 0,
      nickname: '게임',
      message,
      timestamp: new Date().toISOString(),
      type: 'game' as const
    }]);
  }, []);

  const addSystemMessage = useCallback((message: string) => {
    setChatMessages(prev => [...prev, {
      id: `system-${Date.now()}-${Math.random()}`,
      userId: 0,
      nickname: '시스템',
      message,
      timestamp: new Date().toISOString(),
      type: 'system' as const
    }]);
  }, []);

  // WebSocket 이벤트 리스너 설정 - useCallback으로 안정화
  const handleRoomJoined = useCallback((data: any) => {
    addGameMessage(`🎮 방에 입장하셨습니다! 게임을 준비하세요.`);
    // game_state_update 이벤트로 플레이어 목록이 업데이트될 예정
  }, [addGameMessage]);

  // 플레이어 입장/퇴장 이벤트
  const handlePlayerJoined = useCallback((data: any) => {
    
    const hostText = data.is_host ? '(방장)' : '';
    addGameMessage(`👋 ${data.nickname}님이 방에 입장하셨습니다! ${hostText}`);
    
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
      } else {
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
  }, [roomId, updateRoom, addGameMessage]);

  const handlePlayerLeft = useCallback((data: any) => {
    
    // 퇴장하는 플레이어 정보 찾기
    const leftPlayer = currentRoomRef.current?.players?.find(p => 
      p.id === String(data.user_id) || p.id === data.user_id
    );
    
    const playerName = leftPlayer?.nickname || data.nickname || 'Unknown';
    addGameMessage(`😢 ${playerName}님이 방을 나갔습니다`);
    
    // Update player list - 해당 플레이어 제거
    if (roomId && currentRoomRef.current && leftPlayer) {
      updateRoom(roomId, {
        currentPlayers: Math.max(1, currentRoomRef.current.currentPlayers - 1),
        players: (currentRoomRef.current.players || []).filter(p => 
          p.id !== String(data.user_id) && p.id !== data.user_id
        )
      });
    }
  }, [roomId, updateRoom, addGameMessage]);

  // 채팅 메시지 이벤트
  const handleChatMessage = useCallback((data: any) => {
    
    setChatMessages(prev => [...prev, {
      id: `chat-${Date.now()}-${data.user_id}-${Math.random()}`,
      userId: data.user_id,
      nickname: data.nickname,
      message: data.message,
      timestamp: new Date().toISOString(),
      type: 'user' as const
    }]);
  }, []);

  // const addSystemMessage = useCallback((message: string) => {
  //   setChatMessages(prev => [...prev, {
  //     id: `system-${Date.now()}`,
  //     userId: 0,
  //     nickname: '시스템',
  //     message,
  //     timestamp: new Date().toISOString(),
  //     type: 'system' as const
  //   }]);
  // }, []);

  // 게임 관련 이벤트들
  const handleGameStarted = useCallback((data: any) => {
    const currentTurnUserIdStr = String(data.current_turn_user_id);
    const isMyTurn = currentTurnUserIdStr === String(user?.id);
    
    // 새 게임 시작 시 상태 완전 초기화
    setGameState({
      isPlaying: true,
      isRoundTransition: false, // 라운드 전환 상태 초기화
      currentTurnUserId: currentTurnUserIdStr,
      currentChar: data.next_char || '',
      remainingTime: data.current_turn_time_limit || 30,
      turnTimeLimit: data.current_turn_time_limit || 30,
      currentRound: data.current_round || 1,
      maxRounds: data.max_rounds || 5,
      scores: data.scores || {},
      wordChain: [], // 새 게임이므로 단어 체인 초기화
      showFinalRankings: false, // 이전 게임 결과창 숨김
      finalRankings: [] // 이전 게임 순위 데이터 초기화
    });
    addGameMessage(`🎮 게임이 시작되었습니다! ${data.current_turn_nickname}님의 차례입니다.`);
  }, [user?.id, addGameMessage]);

  const handleWordSubmitted = useCallback((data: any) => {
    
    if (data.status === 'accepted') {
      // 성공한 단어 제출 - 성공 애니메이션 효과 및 효과음
      playSound('success');
      setVisualEffects(prev => ({ 
        ...prev, 
        wordSubmitEffect: 'success'
      }));
      
      // 성공한 단어 제출
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: String(data.current_turn_user_id),
        currentChar: data.next_char || '',
        remainingTime: data.current_turn_remaining_time || prev.remainingTime,
        wordChain: [...(prev.wordChain || []), data.word],
        scores: { ...(prev.scores || {}), ...data.scores }
      }));
      
      
      // 점수 계산 표시 (글자 수 × 10)
      const wordLength = data.word.length;
      const wordScore = wordLength * 10;
      addGameMessage(`📝 ${data.nickname}님이 "${data.word}" 제출! (+${wordScore}점, ${wordLength}글자)`);
      
      // 다음 플레이어 알림
      const nextPlayer = currentRoomRef.current?.players?.find(p => String(p.id) === String(data.current_turn_user_id));
      if (nextPlayer) {
        const remainingTime = data.current_turn_remaining_time || 30;
        addGameMessage(`⏰ ${nextPlayer.nickname}님의 차례 (${data.next_char}로 시작, ${remainingTime}초)`);
      }
      
      // 효과 초기화
      setTimeout(() => {
        setVisualEffects(prev => ({ 
          ...prev, 
          wordSubmitEffect: 'none'
        }));
      }, 2000);
      
    } else if (data.status === 'pending_validation') {
      addGameMessage(`🔍 ${data.nickname}님이 "${data.word}" 단어를 검증 중...`);
    }
  }, []);
  
  const handleWordSubmissionFailed = useCallback((data: any) => {
    addSystemMessage(`❌ 단어 제출 실패: ${data.reason || '알 수 없는 오류'}`);
    
    // 에러 시각 효과 및 효과음 추가
    playSound('error');
    setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'error' }));
    setTimeout(() => {
      setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'none' }));
    }, 1000);
  }, [addSystemMessage]);
  
  const handlePlayerReady = useCallback((data: any) => {
    
    addGameMessage(`${data.ready ? '✅' : '❌'} ${data.nickname}님이 ${data.ready ? '준비완료' : '준비취소'}했습니다`);
    
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
  }, []);

  // 게임 시작 카운트다운 핸들러
  const handleGameStartingCountdown = useCallback((data: any) => {
    
    showToast.info(data.message || `게임 시작까지 ${data.countdown}초...`);
  }, []);

  // 게임 시작 실패 핸들러
  const handleGameStartFailed = useCallback((data: any) => {
    
    showToast.error(data.reason || '게임 시작에 실패했습니다');
  }, []);

  // 연결 교체 핸들러 (중복 연결 감지)
  const handleConnectionReplaced = useCallback((data: any) => {
    
    addSystemMessage('⚠️ 다른 탭에서 접속하여 현재 연결이 종료됩니다');
    addSystemMessage('🔄 3초 후 로비로 이동합니다...');
    
    // 3초 후 로비로 이동
    setTimeout(() => {
      navigateSafely('/lobby');
    }, 3000);
  }, [navigate, addSystemMessage]);

  // 라운드 시작 카운트다운 핸들러
  const handleRoundStartingCountdown = useCallback((data: any) => {
    
    addGameMessage(`⏰ ${data.message || `라운드 ${data.round} 시작까지 ${data.countdown}초...`}`);
  }, [addGameMessage]);

  // 라운드 전환 핸들러
  const handleRoundTransition = useCallback((data: any) => {
    
    addGameMessage(`⏳ ${data.message || `잠시 후 라운드 ${data.next_round} 시작...`}`);
    
    // 라운드 전환 상태 확실히 설정
    setGameState(prev => ({
      ...prev,
      isRoundTransition: true
    }));
  }, [addGameMessage]);

  // 라운드 완료 핸들러
  const handleRoundCompleted = useCallback((data: any) => {
    
    addGameMessage(`🏁 ${data.message || `라운드 ${data.completed_round} 완료!`}`);
    
    // 라운드 순위 표시
    if (data.rankings && data.rankings.length > 0) {
      const topPlayer = data.rankings[0];
      addGameMessage(`🥇 라운드 우승: ${topPlayer.nickname}님 (${topPlayer.score}점)`);
    }
  }, [addGameMessage]);

  // 다음 라운드 시작 핸들러
  const handleNextRoundStarting = useCallback((data: any) => {
    
    addGameMessage(`🔄 ${data.message || `라운드 ${data.round} 시작!`}`);
    
    // 게임 상태 업데이트 - 턴 정보 포함
    setGameState(prev => ({
      ...prev,
      currentRound: data.round,
      isPlaying: true,
      isRoundTransition: false,  // 라운드 전환 완료
      currentTurnUserId: data.current_turn_user_id ? String(data.current_turn_user_id) : prev.currentTurnUserId,
      currentChar: data.next_char || '',
      remainingTime: data.current_turn_time_limit || 30,
      turnTimeLimit: data.current_turn_time_limit || 30,
      wordChain: [], // 새 라운드이므로 단어 체인 초기화
      scores: { ...(prev.scores || {}), ...(data.scores || {}) }
    }));
    
    // 다음 턴 플레이어 알림
    if (data.current_turn_nickname) {
      addGameMessage(`🎮 ${data.current_turn_nickname}님의 차례입니다!`);
    }
  }, [addGameMessage]);

  // 게임 완료 핸들러
  const handleGameCompleted = useCallback((data: any) => {
    
    // 게임 완료 상태로 설정 (순위 표시)
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: false,
      showFinalRankings: true,
      finalRankings: data.final_rankings || []
    }));
    
    // 승리 축하 효과 트리거
    setVisualEffects(prev => ({ ...prev, gameEndCelebration: 'victory' }));
    
    if (data.winner) {
      addGameMessage(`🏆 ${data.winner.nickname}님이 최종 우승했습니다!`);
    }
    
    // 최종 순위 표시
    if (data.final_rankings && data.final_rankings.length > 0) {
      addGameMessage('🏆 게임이 완료되었습니다! 최종 순위를 확인하세요.');
    }
    
    // 축하 효과 종료
    setTimeout(() => {
      setVisualEffects(prev => ({ ...prev, gameEndCelebration: 'none' }));
    }, 5000);
    
    // 10초 후 순위 창 자동 닫기 및 게임 상태 완전 초기화
    setTimeout(() => {
      setGameState(() => ({ 
        isPlaying: false,
        wordChain: [],
        scores: {},
        turnTimeLimit: 30,
        remainingTime: 30,
        currentRound: 1,
        maxRounds: 3,
        showFinalRankings: false,
        finalRankings: [],
        currentTurnUserId: undefined,
        currentChar: undefined
      }));
    }, 10000);
  }, []);

  // 타이머 관련 핸들러들
  const handleTurnTimerStarted = useCallback((data: any) => {
    
    // 서버에서 전송된 현재 턴의 시간 제한으로 동기화
    const turnTimeLimit = data.time_limit || 30;
    
    setGameState(prev => ({
      ...prev,
      remainingTime: turnTimeLimit,
      turnTimeLimit: turnTimeLimit,
      currentTurnPlayer: data.user_id
    }));
    
  }, []);

  const handleTurnTimeout = useCallback((data: any) => {
    addSystemMessage(`⏰ ${data.message || `${data.timeout_nickname}님의 시간이 초과되었습니다`}`);
    
    // 시간 초과는 라운드 완료를 의미함 (현재 게임 규칙)
    // round_completed 이벤트에서 라운드 완료 처리가 될 예정
    if (data.round_completed) {
      setGameState(prev => ({
        ...prev,
        isRoundTransition: true  // 라운드 전환 중 상태로 변경 (isPlaying은 유지)
      }));
    }
  }, [addSystemMessage]);

  // 게임 종료 핸들러 추가
  const handleGameEnded = useCallback((data: any) => {
    
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: false 
    }));
    
    // 게임 종료 효과 트리거
    setVisualEffects(prev => ({ ...prev, gameEndCelebration: 'game_over' }));
    
    // 게임 종료 메시지
    if (data.winner) {
      addGameMessage(`🏆 ${data.winner}님이 승리했습니다!`);
    } else {
      addGameMessage('🏁 게임이 종료되었습니다.');
    }
    
    addSystemMessage('🔄 5초 후 로비로 이동합니다...');
    
    // 효과 종료
    setTimeout(() => {
      setVisualEffects(prev => ({ ...prev, gameEndCelebration: 'none' }));
    }, 3000);
    
    // 5초 후 로비로 이동
    setTimeout(() => {
      navigateSafely('/lobby');
    }, 5000);
  }, [navigate, addGameMessage, addSystemMessage]);


  // game_state_update 핸들러 추가
  const handleGameStateUpdate = useCallback((data: any) => {
    if (roomId && data.players) {
      
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
    addSystemMessage(`👑❌ ${data.message}`);
    addSystemMessage('🔄 5초 후 로비로 이동합니다...');
    
    // 5초 후 로비로 이동
    setTimeout(() => {
      navigateSafely('/lobby');
    }, 5000);
  }, [navigate, addSystemMessage]);

  const handleHostChanged = useCallback((data: any) => {
    addGameMessage(`👑 ${data.message}`);
    
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
  }, [roomId, updateRoom, addGameMessage]);

  const handleOpponentLeftVictory = useCallback((data: any) => {
    addGameMessage(`🏆 ${data.message}`);
    
    // 승리 처리
    setGameState(prev => ({ 
      ...prev, 
      isPlaying: false,
      gameResult: 'victory',
      resultMessage: data.message
    }));
  }, [addGameMessage]);

  const handlePlayerLeftDuringTurn = useCallback((data: any) => {
    addSystemMessage(`⚠️ ${data.message}`);
    
    // 턴 정보 업데이트
    setGameState(prev => ({
      ...prev,
      currentTurnUserId: String(data.current_turn_user_id),
      remainingTime: data.current_turn_remaining_time || prev.remainingTime
    }));
  }, [addSystemMessage]);

  const handlePlayerLeftGame = useCallback((data: any) => {
    addGameMessage(`🚪 ${data.message}`);
  }, [addGameMessage]);

  const handlePlayerLeftRoom = useCallback((data: any) => {
    addGameMessage(`🚪 ${data.message}`);
  }, [addGameMessage]);

  const handleRoomDisbanded = useCallback((data: any) => {
    addSystemMessage(`💥 ${data.message}`);
    addSystemMessage('🔄 로비로 이동합니다...');
    
    // 로비로 이동
    navigateSafely('/lobby');
  }, [navigate, addSystemMessage]);

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
    on('round_completed', handleRoundCompleted);
    on('next_round_starting', handleNextRoundStarting);
    on('game_completed', handleGameCompleted);
    on('game_starting_countdown', handleGameStartingCountdown);
    on('game_start_failed', handleGameStartFailed);
    on('connection_replaced', handleConnectionReplaced);
    on('round_starting_countdown', handleRoundStartingCountdown);
    on('round_transition', handleRoundTransition);
    on('error', handleError);
    on('success', handleSuccess);
    on('pong', () => {});

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

      // 탭 통신 설정
      if (user?.id) {
        tabCommManager.setCurrentUser(Number(user.id));
        if (roomId) {
          tabCommManager.notifyRoomJoined(roomId);
        }
      }
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
      off('round_completed', handleRoundCompleted);
      off('next_round_starting', handleNextRoundStarting);
      off('game_completed', handleGameCompleted);
      off('game_starting_countdown', handleGameStartingCountdown);
      off('game_start_failed', handleGameStartFailed);
      off('connection_replaced', handleConnectionReplaced);
      off('round_starting_countdown', handleRoundStartingCountdown);
      off('round_transition', handleRoundTransition);
      off('error', handleError);
      off('success', handleSuccess);
      off('pong');
    };
  }, [isConnected, roomId, user?.id, emit, on, off, handleRoomJoined, handlePlayerJoined, handlePlayerLeft, handleChatMessage, handleGameStarted, handleWordSubmitted, handleWordSubmissionFailed, handleTurnTimerStarted, handleTurnTimeout, handlePlayerReady, handleGameStateUpdate, handleHostLeftGame, handleHostChanged, handleOpponentLeftVictory, handlePlayerLeftDuringTurn, handlePlayerLeftGame, handlePlayerLeftRoom, handleRoomDisbanded, handleGameEnded, handleRoundCompleted, handleNextRoundStarting, handleGameCompleted, handleGameStartingCountdown, handleGameStartFailed, handleConnectionReplaced, handleRoundStartingCountdown, handleRoundTransition, handleError, handleSuccess, addGameMessage, addSystemMessage]);

  // 브라우저 내비게이션 보호 (뒤로가기, 새로고침, 탭 닫기 방지)
  const shouldProtectNavigation = () => {
    // 게임이 진행 중이거나 플레이어가 방에 있을 때 보호
    return gameState.isPlaying || 
           (currentRoom && currentRoom.players && currentRoom.players.length > 0 && isConnected);
  };

  const getNavigationMessage = () => {
    const isHost = currentRoom?.players?.find(p => String(p.id) === String(user?.id))?.isHost;
    
    if (gameState.isPlaying && isHost) {
      return '⚠️ 방장이 게임 중에 나가면 모든 플레이어의 게임이 종료됩니다. 정말 나가시겠습니까?';
    } else if (gameState.isPlaying) {
      return '⚠️ 게임이 진행 중입니다. 나가면 패배 처리됩니다. 정말 나가시겠습니까?';
    } else if (isHost) {
      return '정말 나가시겠습니까?';
    } else {
      return '게임 방에서 나가시겠습니까? 다른 플레이어들이 기다리고 있을 수 있습니다.';
    }
  };

  const { navigateSafely } = useNavigationProtection({
    when: Boolean(shouldProtectNavigation()),
    message: getNavigationMessage(),
    onNavigationBlocked: () => {
      // 뒤로가기 시도 시 추가 피드백
      addSystemMessage('⚠️ 게임 중에는 뒤로가기를 할 수 없습니다. 방 나가기 버튼을 이용해주세요.');
    },
    onBeforeUnload: () => {
      // 페이지 언로드 전 서버에 알림 (선택적)
      if (roomId && isConnected) {
        try {
          emit('leave_room', { room_id: roomId });
        } catch (error) {
        }
      }
    }
  });

  // 탭 간 통신 이벤트 처리
  useEffect(() => {
    // 다른 탭에서 같은 사용자가 방에 참가했을 때
    const handleOtherTabRoomJoined = (message: any) => {
      if (message.data.userId === Number(user?.id) && message.data.roomId === roomId) {
        setDuplicateMessage('다른 탭에서 이미 이 방에 참가했습니다.');
        setShowDuplicateModal(true);
      }
    };

    // 다른 탭에서 연결이 설정되었을 때
    const handleOtherTabConnection = (message: any) => {
      if (message.data.userId === Number(user?.id)) {
      }
    };

    tabCommManager.onMessage('ROOM_JOINED', handleOtherTabRoomJoined);
    tabCommManager.onMessage('CONNECTION_ESTABLISHED', handleOtherTabConnection);

    return () => {
      tabCommManager.offMessage('ROOM_JOINED', handleOtherTabRoomJoined);
      tabCommManager.offMessage('CONNECTION_ESTABLISHED', handleOtherTabConnection);
    };
  }, [user?.id, roomId, navigate, tabCommManager]);

  // 중복 연결 모달 핸들러
  const handleDuplicateConnectionContinue = () => {
    setShowDuplicateModal(false);
    // 현재 탭에서 계속 - 기존 연결 강제 종료
    emit('force_takeover_connection', { room_id: roomId });
    addSystemMessage('🔄 기존 연결을 종료하고 현재 탭에서 계속합니다');
  };

  const handleDuplicateConnectionCancel = () => {
    setShowDuplicateModal(false);
    // 로비로 이동
    navigateSafely('/lobby');
  };

  useEffect(() => {
    if (!roomId) {
      navigateSafely('/lobby');
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
      addGameMessage('🏠 방 정보를 불러왔습니다');
    } catch (error) {
      console.error('방 정보 로드 실패:', error);
      setRoomNotFound(true);
      addSystemMessage('❌ 방을 찾을 수 없습니다');
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
        confirmMessage = '정말로 나가시겠습니까?';
      }
      
      // 확인 다이얼로그
      const confirmed = window.confirm(confirmMessage);
      
      if (!confirmed) {
        return;
      }
      
      if (roomId && isConnected) {
        emit('leave_room', { room_id: roomId });
      }
      navigateSafely('/lobby');
      addSystemMessage('🚺 방에서 나갔습니다');
    } catch (error) {
      console.error('방 나가기 실패:', error);
      navigateSafely('/lobby'); // 에러가 있어도 로비로 이동
    }
  };

  const handleReadyToggle = () => {
    if (!isConnected) return;
    
    const currentPlayerReady = currentRoom?.players?.find(p => p.id === user?.id)?.isReady;
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
    
    // 단어 제출 애니메이션 시작
    setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'shake' }));
    
    emit('submit_word', { room_id: roomId, word: currentWord.trim() });
    setCurrentWord('');
    
    // 애니메이션 초기화
    setTimeout(() => {
      setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'none' }));
    }, 500);
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
              <Button onClick={() => navigateSafely('/lobby')}>
                로비로 돌아가기
              </Button>
            </div>
          </Card.Body>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-white/5 to-transparent"></div>
      <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-0 right-0 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      
      {/* Header */}
      <header className="relative z-10 bg-white/10 backdrop-blur-md border-b border-white/20 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-blue-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <span className="text-white font-bold text-lg">🎮</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white font-korean truncate max-w-48 sm:max-w-none">
                    {currentRoom?.name || `게임룸 ${roomId?.slice(-4)}`}
                  </h1>
                  <div className="flex items-center space-x-2 mt-1">
                    {gameState.isPlaying && (
                      <div className="px-3 py-1 bg-gradient-to-r from-purple-500/20 to-blue-500/20 backdrop-blur-sm text-purple-200 rounded-full text-xs font-medium border border-purple-400/30">
                        라운드 {gameState.currentRound}/{gameState.maxRounds}
                      </div>
                    )}
                    <div className={`px-3 py-1 rounded-full text-xs font-medium backdrop-blur-sm border ${
                      isConnected 
                        ? 'bg-green-500/20 text-green-300 border-green-400/30' 
                        : 'bg-red-500/20 text-red-300 border-red-400/30'
                    }`}>
                      {isConnected ? '🟢 연결됨' : '🔴 연결 끊김'}
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <Button 
                variant="glass" 
                size="md" 
                onClick={handleLeaveRoom}
                className="text-white border-white/30 hover:bg-white/20"
              >
                🚪 방 나가기
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {isLoading ? (
          <div className="flex items-center justify-center min-h-[60vh]">
            <Loading size="xl" variant="dots" text="게임룸 로딩 중..." />
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 lg:gap-8">
            {/* 게임 영역 */}
            <div className="xl:col-span-2">
              <div className="bg-white/10 backdrop-blur-md rounded-3xl border border-white/20 shadow-2xl overflow-hidden">
                <div className="bg-gradient-to-r from-purple-500/20 to-blue-500/20 p-6 border-b border-white/20">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center space-x-3">
                      <div className={`w-3 h-3 rounded-full ${gameState.isPlaying ? 'bg-green-400 animate-pulse' : 'bg-yellow-400'}`}></div>
                      <h2 className="text-xl font-bold text-white font-korean">
                        {gameState.isPlaying ? '🎯 끝말잇기 게임' : '⏳ 게임 대기'}
                      </h2>
                    </div>
                    {gameState.isPlaying && gameState.currentTurnUserId === String(user.id) && (
                      <div className="flex items-center space-x-4">
                        <span className={`font-bold text-lg ${
                          (gameState.remainingTime || 0) <= 10 
                            ? 'text-red-300 animate-pulse text-xl drop-shadow-[0_0_10px_rgba(239,68,68,0.8)]' 
                            : 'text-white animate-pulse'
                        }`}>
                          ⏰ {gameState.remainingTime?.toFixed(1)}초
                        </span>
                        <div className="w-24 h-3 bg-white/20 rounded-full overflow-hidden backdrop-blur-sm">
                          <div 
                            className={`h-full rounded-full ${
                              (gameState.remainingTime || 0) > 20 ? 'bg-gradient-to-r from-green-400 to-green-500' :
                              (gameState.remainingTime || 0) > 10 ? 'bg-gradient-to-r from-yellow-400 to-orange-500 animate-pulse' : 
                              (gameState.remainingTime || 0) > 5 ? 'bg-gradient-to-r from-orange-400 to-red-500 animate-pulse drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]' :
                              (gameState.remainingTime || 0) > 3 ? 'bg-gradient-to-r from-red-500 to-red-700 animate-bounce drop-shadow-[0_0_12px_rgba(239,68,68,0.8)]' :
                              'bg-gradient-to-r from-red-600 to-red-800 animate-ping drop-shadow-[0_0_20px_rgba(239,68,68,1)]'
                            }`}
                            style={{ 
                              width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / (gameState.turnTimeLimit || 30)) * 100))}%`,
                              transition: `width ${(gameState.remainingTime || 0) > 10 ? '100ms' : (gameState.remainingTime || 0) > 5 ? '60ms' : (gameState.remainingTime || 0) > 3 ? '40ms' : '20ms'} linear`
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                <div className="p-6">
                  {gameState.isPlaying ? (
                    <div className="space-y-6">
                      {/* 단어 체인 */}
                      <div className="bg-white/5 backdrop-blur-sm rounded-2xl p-6 border border-white/10">
                        <div className="flex items-center space-x-2 mb-4">
                          <span className="text-2xl">🔗</span>
                          <h4 className="font-bold text-white text-lg font-korean">단어 체인</h4>
                        </div>
                        <div className="flex flex-wrap gap-3 max-h-40 overflow-y-auto scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
                          {gameState.wordChain.map((word, index) => (
                            <span 
                              key={`${word}-${index}`}
                              className={`px-4 py-2 rounded-xl text-sm font-medium transition-all duration-500 transform hover:scale-105 ${
                                index === gameState.wordChain.length - 1 
                                  ? 'bg-gradient-to-r from-green-400/20 to-emerald-500/20 text-green-300 border border-green-400/30 animate-pulse scale-110 shadow-lg shadow-green-400/20' 
                                  : 'bg-gradient-to-r from-blue-400/20 to-purple-500/20 text-blue-300 border border-blue-400/30'
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
                          <div className="mt-4 p-4 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl border border-purple-400/20">
                            <p className="text-purple-200 text-sm font-korean">
                            다음 단어는 <strong className="text-purple-300">"{gameState.currentChar}"</strong>로 시작해야 합니다
                          </p>
                          </div>
                        )}
                      </div>

                      {/* 단어 입력 */}
                      {gameState.isRoundTransition ? (
                        <div className="bg-gradient-to-r from-yellow-500/20 to-orange-500/20 backdrop-blur-sm rounded-2xl p-6 text-center border border-yellow-400/30">
                          <div className="flex items-center justify-center space-x-3">
                            <span className="text-3xl animate-spin">🔄</span>
                            <p className="text-yellow-200 font-bold text-lg font-korean">
                              라운드 전환 중입니다...
                            </p>
                          </div>
                        </div>
                      ) : gameState.currentTurnUserId === String(user.id) ? (
                        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 backdrop-blur-sm rounded-2xl p-6 border border-green-400/30 shadow-lg shadow-green-400/10">
                          <div className="flex items-center justify-between mb-4">
                            <div className="flex items-center space-x-3">
                              <span className="text-2xl animate-bounce">🎯</span>
                              <h4 className="font-bold text-green-300 text-lg font-korean">
                                내 차례입니다!
                              </h4>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className={`font-bold text-lg animate-pulse ${
                                (gameState.remainingTime || 0) <= 10 
                                  ? 'text-red-300 text-xl drop-shadow-[0_0_10px_rgba(239,68,68,0.8)]' 
                                  : 'text-green-300'
                              }`}>
                                {gameState.remainingTime?.toFixed(1)}초
                              </span>
                            </div>
                          </div>
                          
                          <div className="w-full h-4 bg-white/10 rounded-full overflow-hidden mb-4 backdrop-blur-sm">
                            <div 
                              className={`h-full rounded-full transition-all ease-out ${
                                (gameState.remainingTime || 0) > 20 ? 'bg-gradient-to-r from-green-400 to-green-500' :
                                (gameState.remainingTime || 0) > 10 ? 'bg-gradient-to-r from-yellow-400 to-orange-500' : 
                                (gameState.remainingTime || 0) > 5 ? 'bg-gradient-to-r from-orange-400 to-red-500 animate-pulse drop-shadow-[0_0_8px_rgba(249,115,22,0.6)]' :
                                (gameState.remainingTime || 0) > 3 ? 'bg-gradient-to-r from-red-500 to-red-700 animate-bounce drop-shadow-[0_0_12px_rgba(239,68,68,0.8)]' :
                                'bg-gradient-to-r from-red-600 to-red-800 animate-ping drop-shadow-[0_0_20px_rgba(239,68,68,1)]'
                              }`}
                              style={{ 
                                width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / (gameState.turnTimeLimit || 30)) * 100))}%`,
                                transition: `width ${(gameState.remainingTime || 0) > 10 ? '100ms' : (gameState.remainingTime || 0) > 5 ? '60ms' : (gameState.remainingTime || 0) > 3 ? '40ms' : '20ms'} linear`
                              }}
                            />
                          </div>
                          
                          
                          {/* 게임 종료 축하/종료 효과 */}
                          {visualEffects.gameEndCelebration !== 'none' && (
                            <div className="fixed inset-0 pointer-events-none z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                              <div className="text-center animate-bounce">
                                {visualEffects.gameEndCelebration === 'victory' ? (
                                  <>
                                    <div className="text-8xl mb-4 animate-pulse">🎉</div>
                                    <div className="text-4xl font-bold text-yellow-300 drop-shadow-[0_0_20px_rgba(255,255,0,0.8)] mb-2">
                                      축하합니다!
                                    </div>
                                    <div className="text-2xl text-green-300">
                                      게임 완료! 🏆
                                    </div>
                                    <div className="flex justify-center space-x-4 mt-4">
                                      <span className="text-5xl animate-bounce" style={{animationDelay: '0.1s'}}>🎊</span>
                                      <span className="text-5xl animate-bounce" style={{animationDelay: '0.2s'}}>🎈</span>
                                      <span className="text-5xl animate-bounce" style={{animationDelay: '0.3s'}}>🎁</span>
                                    </div>
                                  </>
                                ) : (
                                  <>
                                    <div className="text-6xl mb-4">🏁</div>
                                    <div className="text-3xl font-bold text-gray-300 drop-shadow-[0_0_15px_rgba(255,255,255,0.5)]">
                                      게임 종료
                                    </div>
                                    <div className="text-lg text-blue-300 mt-2">
                                      수고하셨습니다!
                                    </div>
                                  </>
                                )}
                              </div>
                            </div>
                          )}
                          
                          <div className="space-y-4">
                            <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-3">
                              <div className="flex-1 relative">
                                <input
                                  type="text"
                                  value={currentWord}
                                  onChange={(e) => handleWordChange(e.target.value)}
                                  onKeyPress={(e) => e.key === 'Enter' && handleSubmitWord()}
                                  onFocus={(e) => isMobile && handleInputFocus(e.target)}
                                  placeholder={!currentWord ? (gameState.currentChar ? `${gameState.currentChar}로 시작하는 단어...` : '단어를 입력하세요...') : ''}
                                  aria-label={gameState.currentChar ? `${gameState.currentChar}로 시작하는 끝말잇기 단어 입력` : '끝말잇기 단어 입력'}
                                  aria-invalid={!wordValidation.isValid && currentWord.trim() ? 'true' : 'false'}
                                  aria-describedby={wordValidation.message ? 'word-validation-message' : undefined}
                                  autoComplete="off"
                                  autoCapitalize="off"
                                  spellCheck="false"
                                  className={`w-full px-4 py-3 bg-white/10 backdrop-blur-sm border-2 rounded-xl focus:outline-none focus:ring-2 transition-all placeholder-white/60 text-lg font-korean ${
                                    currentWord ? 'text-transparent' : 'text-white'
                                  } ${
                                    wordValidation.isChecking ? 'border-gray-400/50 focus:ring-gray-400' :
                                    !wordValidation.isValid && currentWord.trim() ? 'border-red-400/50 focus:ring-red-400 bg-red-500/10' :
                                    wordValidation.isValid && currentWord.trim() && wordValidation.message ? 'border-green-400/50 focus:ring-green-400 bg-green-500/10' :
                                    'border-white/30 focus:ring-green-400'
                                  } ${
                                    visualEffects.wordSubmitEffect === 'success' ? 'animate-pulse border-green-300 bg-green-500/20 ring-4 ring-green-400/30' :
                                    visualEffects.wordSubmitEffect === 'error' ? 'animate-bounce border-red-400 bg-red-500/20 ring-4 ring-red-400/30' :
                                    visualEffects.wordSubmitEffect === 'shake' ? 'animate-bounce border-yellow-400 bg-yellow-500/10' :
                                    ''
                                  }`}
                                  disabled={!isConnected}
                                  style={{ caretColor: 'transparent' }}
                                />
                                
                                {/* 타이핑 애니메이션 오버레이 */}
                                <div className="absolute inset-0 px-4 py-3 pointer-events-none flex items-center text-lg font-korean">
                                  <div className="flex">
                                    {typingEffect.chars.map((charObj) => (
                                      <span
                                        key={charObj.id}
                                        className={`text-white transition-all duration-200 ${
                                          charObj.animated 
                                            ? 'animate-bounce text-yellow-300 text-xl font-bold drop-shadow-lg scale-125 transform' 
                                            : ''
                                        }`}
                                        style={{
                                          textShadow: charObj.animated ? '0 0 10px rgba(255, 255, 0, 0.8)' : 'none'
                                        }}
                                      >
                                        {charObj.char}
                                      </span>
                                    ))}
                                    <span className="animate-pulse text-white/70 ml-1">|</span>
                                  </div>
                                </div>
                                {wordValidation.isChecking && (
                                  <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                                    <div className="animate-spin w-5 h-5 border-2 border-white/30 border-t-white rounded-full"></div>
                                  </div>
                                )}
                              </div>
                              <Button 
                                onClick={handleSubmitWord}
                                disabled={!isConnected || !currentWord.trim() || !wordValidation.isValid}
                                variant={wordValidation.isValid && currentWord.trim() ? 'primary' : 'secondary'}
                                size="lg"
                                aria-label={`단어 "${currentWord}" 제출하기`}
                                aria-describedby={wordValidation.message ? 'word-validation-message' : undefined}
                                className="w-full sm:w-auto px-8 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white font-bold"
                                glow
                              >
                                🚀 제출
                              </Button>
                            </div>
                            {/* 실시간 검증 피드백 */}
                            {currentWord.trim() && (
                              <div 
                                id="word-validation-message"
                                role="status"
                                aria-live="polite"
                                className={`text-sm px-3 py-2 rounded-lg transition-all duration-300 ${
                                  wordValidation.isChecking ? 'text-gray-600 bg-gray-100 animate-pulse' :
                                  !wordValidation.isValid ? 'text-red-600 bg-red-100 border border-red-200' :
                                  wordValidation.message ? 'text-green-600 bg-green-100 border border-green-200 animate-fade-in' : ''
                                }`}>
                                <div className="flex flex-col space-y-1">
                                  <div className="font-medium">
                                    {wordValidation.isChecking ? '🔍 검증 중...' : wordValidation.message}
                                  </div>
                                </div>
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
                        {(currentRoom?.players?.length || 0) < 2 
                          ? `게임 시작을 위해 최소 2명의 플레이어가 필요합니다 (현재: ${currentRoom?.players?.length || 0}명)`
                          : '모든 플레이어가 준비되면 게임을 시작할 수 있습니다'
                        }
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
                            disabled={
                              !isConnected || 
                              !currentRoom?.players?.every(p => p.isReady) ||
                              (currentRoom?.players?.length || 0) < 2
                            }
                          >
                            게임 시작
                          </Button>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* 사이드바 */}
            <div className="space-y-6">
              {/* 플레이어 목록 */}
              <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl overflow-hidden">
                <div className="bg-gradient-to-r from-blue-500/20 to-purple-500/20 p-4 border-b border-white/20">
                  <div className="flex items-center space-x-3">
                    <span className="text-2xl">👥</span>
                    <h3 className="text-lg font-bold text-white font-korean">
                      플레이어 ({currentRoom?.currentPlayers || 0}/{currentRoom?.maxPlayers || 4})
                    </h3>
                  </div>
                </div>
                <div className="p-4">
                  <div className="space-y-3">
                    {currentRoom?.players?.map((player) => (
                      <div 
                        key={player.id} 
                        className={`flex items-center justify-between p-4 rounded-xl transition-all duration-300 ${
                          player.id === user.id 
                            ? 'bg-gradient-to-r from-blue-500/20 to-purple-500/20 border border-blue-400/30 shadow-lg' 
                            : 'bg-white/5 border border-white/10 hover:bg-white/10'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          <div className={`w-4 h-4 rounded-full transition-all duration-300 ${
                            player.isReady 
                              ? 'bg-green-400 shadow-lg shadow-green-400/50 animate-pulse' 
                              : 'bg-gray-400'
                          }`} />
                          <span className={`font-medium font-korean ${
                            player.id === user.id ? 'text-blue-300' : 'text-white'
                          }`}>
                            {player.nickname}
                            {player.id === user.id && ' (나)'}
                          </span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {player.isHost && (
                            <span className="px-3 py-1 bg-gradient-to-r from-yellow-400/20 to-orange-500/20 text-yellow-300 text-xs rounded-full border border-yellow-400/30 font-medium">
                              👑 방장
                            </span>
                          )}
                          {gameState.isPlaying && gameState.currentTurnUserId === player.id && (
                            <span className="px-3 py-1 bg-gradient-to-r from-green-400/20 to-emerald-500/20 text-green-300 text-xs rounded-full border border-green-400/30 font-medium animate-pulse">
                              🎯 턴
                            </span>
                          )}
                        </div>
                      </div>
                    )) || (
                      <div className="text-center py-8">
                        <div className="animate-spin w-8 h-8 border-2 border-white/20 border-t-white rounded-full mx-auto mb-3"></div>
                        <p className="text-white/60 text-sm font-korean">
                          플레이어 정보를 불러오는 중...
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 아이템 패널 */}
              <ItemPanel
                userId={Number(user?.id) || 0}
                roomId={roomId}
                isGameActive={gameState.isPlaying}
                isMyTurn={gameState.currentTurnUserId === String(user?.id)}
                onItemUse={(itemId, targetUserId) => {
                  if (isConnected) {
                    emit('use_item', {
                      room_id: roomId,
                      item_id: itemId,
                      target_user_id: targetUserId
                    });
                  }
                }}
              />

              {/* 채팅 패널 */}
              <ChatPanel
                messages={chatMessages}
                isConnected={isConnected}
                currentUserId={Number(user?.id) || 0}
                onSendMessage={handleSendChat}
              />
            </div>
          </div>
        )}

        {/* 새로고침 안내 */}
        <div className="mt-8 bg-gradient-to-r from-green-500/20 to-emerald-500/20 backdrop-blur-sm rounded-2xl p-6 border border-green-400/30">
          <div className="flex items-center space-x-3 mb-2">
            <span className="text-2xl">✅</span>
            <h4 className="font-bold text-green-300 text-lg font-korean">상태 유지 확인</h4>
          </div>
          <p className="text-green-200 text-sm font-korean">
            이제 새로고침을 해도 현재 방 상태가 유지됩니다! URL에 방 ID가 포함되어 있어 
            브라우저를 닫고 다시 열어도 같은 방으로 돌아올 수 있습니다.
          </p>
        </div>
      </main>
      
      {/* 게임 리포트 */}
      {gameState.showFinalRankings && gameState.finalRankings && gameState.finalRankings.length > 0 && (
        <GameReport
          finalRankings={gameState.finalRankings}
          currentUserId={Number(user?.id) || 0}
          wordChain={gameState.wordChain}
          gameStats={{
            totalRounds: gameState.maxRounds || 5
          }}
          onPlayAgain={() => {
            setGameState(prev => ({ ...prev, showFinalRankings: false }));
            // 게임 상태 초기화
            setGameState({
              isPlaying: false,
              isRoundTransition: false,
              wordChain: [],
              scores: {},
              turnTimeLimit: 30,
              remainingTime: 30,
              currentRound: 1,
              maxRounds: 3,
              showFinalRankings: false,
              finalRankings: []
            });
            // 모든 플레이어를 준비 상태로 리셋하고 새 게임 요청
            emit('reset_game_for_restart', { room_id: roomId });
            addGameMessage('🎮 새 게임을 위해 모든 플레이어가 다시 준비해주세요');
          }}
          onBackToLobby={() => {
            setGameState(prev => ({ ...prev, showFinalRankings: false }));
            navigateSafely('/lobby');
          }}
        />
      )}

      {/* 중복 연결 모달 */}
      <DuplicateConnectionModal
        isOpen={showDuplicateModal}
        message={duplicateMessage}
        onContinue={handleDuplicateConnectionContinue}
        onCancel={handleDuplicateConnectionCancel}
      />
    </div>
  );
};

export default GameRoomPage;