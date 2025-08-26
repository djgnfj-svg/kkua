import React, { useEffect, useState, useRef, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Loading, WordCard, PlayerCard } from '../components/ui';
import { useUserStore } from '../stores/useUserStore';
import { useGameStore } from '../stores/useGameStore';
import { useMobileOptimization } from '../hooks/useMobileOptimization';
import { apiEndpoints } from '../utils/api';
import { useNativeWebSocket } from '../hooks/useNativeWebSocket';
import { useNavigationProtection } from '../hooks/useNavigationProtection';
import GameReport from '../components/GameReport';
import ChatPanel from '../components/ChatPanel';
import DuplicateConnectionModal from '../components/DuplicateConnectionModal';
import ItemPanel from '../components/ItemPanel';
import { DistractionEffects } from '../components/ui/DistractionEffects';
import { getDueumDisplayText, checkDueumWordValidity } from '../utils/dueumRules';
import { getTabCommunicationManager } from '../utils/tabCommunication';

const GameRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { currentRoom, setCurrentRoom, updateRoom, isLoading, setLoading } = useGameStore();
  const { isMobile } = useMobileOptimization();
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  
  
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
    wordChainInfo?: Record<string, { definition: string; difficulty: number; }>; // 단어 뜻 정보 저장
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
    countdownMessage?: string; // 카운트다운 메시지 추가
  }>({
    isPlaying: false,
    isRoundTransition: false,
    wordChain: [],
    wordChainInfo: {},
    scores: {},
    turnTimeLimit: 30,
    remainingTime: 30,
    currentRound: 1,
    maxRounds: 3,
    showFinalRankings: false,
    finalRankings: [],
    countdownMessage: undefined
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

  // 최근 단어 상태 표시
  const [recentWordDisplay, setRecentWordDisplay] = useState<{
    word: string;
    playerName: string;
    status: 'success' | 'failed';
    message: string;
    timestamp: number;
  } | null>(null);

  // 방해 효과 상태
  const [distractionEffects, setDistractionEffects] = useState<Array<{
    id: string;
    type: 'cat_distraction' | 'screen_shake' | 'blur_screen' | 'falling_objects' | 'color_invert';
    duration: number;
    value?: any;
  }>>([]);
  

  // 타이머 카운트다운 (부드러운 연속 애니메이션) - 모든 플레이어에게 표시
  useEffect(() => {
    if (!gameState.isPlaying) return;
    
    // 100ms마다 더 부드러운 애니메이션
    const interval = setInterval(() => {
      setGameState(prev => {
        const decrementRate = (prev.remainingTime || 0) > 5 ? 0.1 : (prev.remainingTime || 0) > 3 ? 0.15 : 0.25; // 시간이 적을수록 더 빠르게
        const newTime = Math.max(0.1, (prev.remainingTime || 30) - decrementRate);
        
        // 경고음 재생 (5초 남았을 때 - 내 차례일 때만)
        if (Math.floor(newTime) === 5 && Math.floor(prev.remainingTime || 30) === 6 && prev.currentTurnUserId === String(user?.id)) {
          playSound('warning');
        }
        
        return { ...prev, remainingTime: newTime };
      });
    }, 100); // 100ms 간격으로 부드러운 애니메이션
    
    return () => clearInterval(interval);
  }, [gameState.isPlaying, playSound]);

  // 실시간 단어 검증
  useEffect(() => {
    if (!currentWord.trim() || !gameState.currentChar) {
      setWordValidation({ isValid: true, message: '', isChecking: false });
      return;
    }

    const timeoutId = setTimeout(async () => {
      setWordValidation(prev => ({ ...prev, isChecking: true }));
      
      try {
        // 첫 글자 검증 (두음법칙 적용)
        if (gameState.currentChar) {
          const dueumResult = checkDueumWordValidity(currentWord, gameState.currentChar);
          if (!dueumResult.isValid) {
            const displayText = getDueumDisplayText(gameState.currentChar);
            setWordValidation({
              isValid: false,
              message: `"${displayText}"로 시작해야 합니다`,
              isChecking: false
            });
            return;
          }
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
  const handleRoomJoined = useCallback((_data: any) => {
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
    // const isMyTurn = currentTurnUserIdStr === String(user?.id);
    
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
      wordChainInfo: {},
      showFinalRankings: false, // 이전 게임 결과창 숨김
      finalRankings: [], // 이전 게임 순위 데이터 초기화
      countdownMessage: undefined
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
      
      // 성공한 단어를 시각적으로 표시 (모든 플레이어가 볼 수 있게)
      const playerName = currentRoom?.players?.find(p => String(p.id) === String(data.user_id))?.nickname || data.nickname || '알 수 없는 플레이어';
      const wordDefinition = data.word_info?.definition || '';
      const difficulty = data.word_info?.difficulty || 1;
      const difficultyText = difficulty === 1 ? '쉬움' : difficulty === 2 ? '보통' : '어려움';
      
      setRecentWordDisplay({
        word: data.word || '',
        playerName: playerName,
        status: 'success',
        message: wordDefinition ? `${wordDefinition} (${difficultyText})` : '성공!',
        timestamp: Date.now()
      });
      
      // 5초 후 자동으로 업데이트
      setTimeout(() => {
        setRecentWordDisplay(null);
      }, 5000);
      
      // 성공한 단어 제출
      setGameState(prev => ({
        ...prev,
        currentTurnUserId: String(data.current_turn_user_id),
        currentChar: data.next_char || '',
        remainingTime: data.current_turn_remaining_time || prev.remainingTime,
        countdownMessage: undefined,
        wordChain: [...(prev.wordChain || []), data.word],
        wordChainInfo: {
          ...(prev.wordChainInfo || {}),
          [data.word]: {
            definition: data.word_info?.definition || '',
            difficulty: data.word_info?.difficulty || 1
          }
        },
        scores: { ...(prev.scores || {}), ...data.scores }
      }));
      
      // 단어 정보 표시 (뜻 포함)
      const wordLength = data.word.length;
      const wordScore = data.score_breakdown?.estimated_total || wordLength * 10;
      
      // 단어 뜻이 있는 경우 포함하여 메시지 생성
      let wordMessage = `📝 ${data.nickname}님이 "${data.word}" 제출! (+${wordScore}점, ${wordLength}글자)`;
      if (wordDefinition && wordDefinition !== `${data.word}의 뜻`) {
        wordMessage += `\n💡 뜻: ${wordDefinition} (${difficultyText})`;
      }
      
      addGameMessage(wordMessage);
      
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
  }, [currentRoom, addGameMessage]);
  
  const handleWordSubmissionFailed = useCallback((data: any) => {
    // 실패한 단어를 시각적으로 표시 (모든 플레이어가 볼 수 있게)
    const playerName = currentRoom?.players?.find(p => String(p.id) === String(data.user_id))?.nickname || '알 수 없는 플레이어';
    setRecentWordDisplay({
      word: data.word || '',
      playerName: playerName,
      status: 'failed',
      message: data.reason || '알 수 없는 오류',
      timestamp: Date.now()
    });
    
    // 5초 후 자동으로 사라지게
    setTimeout(() => {
      setRecentWordDisplay(null);
    }, 5000);
    
    // 채팅에도 메시지 표시
    addSystemMessage(`❌ ${playerName}: "${data.word}" - ${data.reason || '알 수 없는 오류'}`);
    
    // 에러 시각 효과 및 효과음 추가
    playSound('error');
    setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'error' }));
    setTimeout(() => {
      setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'none' }));
    }, 1000);
  }, [currentRoom, addSystemMessage]);
  
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
    addSystemMessage(`❌ ${data.error || '연결 오류가 발생했습니다'}`);
  }, [addSystemMessage]);

  // 성공 응답 처리
  const handleSuccess = useCallback((_data: any) => {
  }, []);

  // 게임 시작 카운트다운 핸들러
  const handleGameStartingCountdown = useCallback((data: any) => {
    setGameState(prev => ({
      ...prev,
      countdownMessage: `🕰️ 게임 시작까지 ${data.countdown}초...`
    }));
    addGameMessage(data.message || `🕰️ 게임 시작까지 ${data.countdown}초...`);
  }, [addGameMessage]);

  // 게임 시작 실패 핸들러
  const handleGameStartFailed = useCallback((data: any) => {
    
    addSystemMessage(`❌ ${data.reason || '게임 시작에 실패했습니다'}`);
  }, [addSystemMessage]);

  // 연결 교체 핸들러 (중복 연결 감지)
  const handleConnectionReplaced = useCallback((_data: any) => {
    
    addSystemMessage('⚠️ 다른 탭에서 접속하여 현재 연결이 종료됩니다');
    addSystemMessage('🔄 3초 후 로비로 이동합니다...');
    
    // 3초 후 로비로 이동
    setTimeout(() => {
      navigateSafely('/lobby');
    }, 3000);
  }, [navigate, addSystemMessage]);

  // 라운드 시작 카운트다운 핸들러
  const handleRoundStartingCountdown = useCallback((data: any) => {
    setGameState(prev => ({
      ...prev,
      countdownMessage: `⏰ 라운드 ${data.round} 시작까지 ${data.countdown}초...`
    }));
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
      countdownMessage: undefined,
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

  // 아이템 사용 이벤트 핸들러
  const handleItemUsed = useCallback((data: any) => {
    const { item, effect_result } = data;
    
    // 방해 아이템인 경우 효과 활성화
    if (['cat_distraction', 'screen_shake', 'blur_screen', 'falling_objects', 'color_invert'].includes(item.effect_type)) {
      const effectId = `${item.effect_type}-${Date.now()}`;
      const newEffect = {
        id: effectId,
        type: item.effect_type as 'cat_distraction' | 'screen_shake' | 'blur_screen' | 'falling_objects' | 'color_invert',
        duration: item.effect_value?.duration || 5,
        value: item.effect_value
      };
      
      setDistractionEffects(prev => [...prev, newEffect]);
      
      // 일정 시간 후 효과 제거
      setTimeout(() => {
        setDistractionEffects(prev => prev.filter(effect => effect.id !== effectId));
      }, newEffect.duration * 1000 + 1000); // 여유시간 추가
    }
    
    // 채팅 메시지 표시
    const userName = currentRoom?.players?.find(p => String(p.id) === String(data.user_id))?.nickname || '플레이어';
    addGameMessage(`🎮 ${userName}님이 "${item.name}" 아이템을 사용했습니다!`);
  }, [currentRoom, addGameMessage]);

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
    on('item_used', handleItemUsed);
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
      off('item_used', handleItemUsed);
      off('error', handleError);
      off('success', handleSuccess);
      off('pong');
    };
  }, [isConnected, roomId, user?.id, emit, on, off, handleRoomJoined, handlePlayerJoined, handlePlayerLeft, handleChatMessage, handleGameStarted, handleWordSubmitted, handleWordSubmissionFailed, handleTurnTimerStarted, handleTurnTimeout, handlePlayerReady, handleGameStateUpdate, handleHostLeftGame, handleHostChanged, handleOpponentLeftVictory, handlePlayerLeftDuringTurn, handlePlayerLeftGame, handlePlayerLeftRoom, handleRoomDisbanded, handleGameEnded, handleRoundCompleted, handleNextRoundStarting, handleGameCompleted, handleGameStartingCountdown, handleGameStartFailed, handleConnectionReplaced, handleRoundStartingCountdown, handleRoundTransition, handleItemUsed, handleError, handleSuccess, addGameMessage, addSystemMessage]);

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
      // 실제 API에서 방 정보 가져오기
      const response = await apiEndpoints.gameRooms.get(roomId);
      const roomData = response.data;
      
      // API 응답 구조에 맞게 데이터 변환
      const room = {
        id: roomData.id,
        name: roomData.name,
        maxPlayers: roomData.max_players,
        currentPlayers: roomData.current_players,
        status: roomData.status,
        createdAt: roomData.created_at,
        players: roomData.players?.map((player: any) => ({
          id: String(player.user_id),
          nickname: player.nickname,
          isHost: player.is_host,
          isReady: player.is_ready
        })) || []
      };
      
      setCurrentRoom(room);
      addGameMessage(`🏠 "${room.name}" 방에 입장했습니다`);
    } catch (error: any) {
      console.error('방 정보 로드 실패:', error);
      
      // 404 에러인 경우 방이 존재하지 않음
      if (error.response?.status === 404) {
        setRoomNotFound(true);
        addSystemMessage('❌ 방을 찾을 수 없습니다');
        // 에러 메시지는 이미 addSystemMessage로 출력됨
      } else {
        // 기타 에러의 경우 임시 방 정보로 대체
        const fallbackRoom = {
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
        
        setCurrentRoom(fallbackRoom);
        addGameMessage('🏠 방 정보를 불러왔습니다 (기본 설정 적용)');
        // 경고 메시지는 이미 addGameMessage로 출력됨
      }
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
      
      // REST API로 방 나가기 호출하여 유저 수 감소
      if (roomId) {
        try {
          console.log('방 나가기 API 호출 시작:', roomId);
          const response = await apiEndpoints.gameRooms.leave(roomId);
          console.log('방 나가기 API 호출 성공:', response.data);
        } catch (error) {
          console.error('방 나가기 API 호출 실패:', error);
        }
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

  const handleSubmitWord = (word?: string) => {
    const wordToSubmit = word || currentWord.trim();
    console.log('🚀 handleSubmitWord 호출됨:', { word, currentWord, wordToSubmit, isConnected, roomId });
    
    if (!isConnected || !wordToSubmit) {
      console.log('❌ 제출 조건 실패:', { isConnected, wordToSubmit });
      return;
    }
    
    // 단어 제출 애니메이션 시작
    setVisualEffects(prev => ({ ...prev, wordSubmitEffect: 'shake' }));
    
    console.log('📤 WebSocket으로 단어 전송:', { room_id: roomId, word: wordToSubmit });
    emit('submit_word', { room_id: roomId, word: wordToSubmit });
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
    <div className="h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 relative flex flex-col">
      {/* Header with user info */}
      <header className="relative z-10 p-3 flex-shrink-0">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <div className="px-3 py-1 bg-white/20 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">{currentRoom?.name || '게임룸'}</span>
              </div>
              <div className="text-white">
                <span className="text-sm font-medium">{user?.nickname || 'Player'}</span>
                <div className={`inline-block ml-2 w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></div>
              </div>
            </div>
          </div>
          <Button 
            size="sm"
            onClick={handleLeaveRoom}
            className="bg-orange-500 hover:bg-orange-600 text-white px-4 py-2 rounded-lg"
          >
            방나가기
          </Button>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 px-3 pb-3 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loading size="xl" variant="dots" text="게임룸 로딩 중..." />
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-2">
            {/* Game Board - Word chains and game state */}
            <div className="bg-purple-800/40 backdrop-blur-lg rounded-lg border border-white/20 min-h-[160px] lg:min-h-[200px]">
              <div className="p-3">
                {/* Round info */}
                {(gameState.isPlaying || (gameState.currentRound && gameState.currentRound > 1)) && (
                  <div className="text-center mb-3">
                    <h2 className="text-white font-bold text-lg">
                      라운드 {gameState.currentRound || 1} / {gameState.maxRounds || 3}
                    </h2>
                  </div>
                )}

                {/* Game state display */}
                {gameState.isPlaying ? (
                  <div className="space-y-3">
                    {/* Current turn indicator */}
                    {gameState.countdownMessage ? (
                      <div className="bg-yellow-500/20 rounded-lg p-3 border border-yellow-400/30">
                        <div className="flex items-center justify-center">
                          <p className="text-yellow-200 font-bold text-lg">{gameState.countdownMessage}</p>
                        </div>
                      </div>
                    ) : gameState.isRoundTransition ? (
                      <div className="text-center py-4">
                        <div className="flex items-center justify-center space-x-3">
                          <span className="text-3xl animate-spin">🔄</span>
                          <p className="text-yellow-200 font-bold text-lg">라운드 전환 중입니다...</p>
                        </div>
                      </div>
                    ) : gameState.currentTurnUserId === String(user.id) ? (
                      <>
                        <div className="bg-green-500/20 rounded-lg p-3 border border-green-400/30">
                          <div className="flex items-center justify-center space-x-3">
                            <span className="text-2xl animate-bounce">🎯</span>
                            <h4 className="font-bold text-green-300 text-lg">내 차례입니다!</h4>
                            {gameState.remainingTime && (
                              <span className={`font-bold text-xl ${
                                (gameState.remainingTime || 0) <= 10 
                                  ? 'text-red-300 animate-pulse' 
                                  : 'text-green-300'
                              }`}>
                                ⏰ {gameState.remainingTime?.toFixed(1)}초
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {/* Progress bar - separate row */}
                        {gameState.remainingTime && (
                          <div className="w-full h-6 bg-white/20 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all ${
                                (gameState.remainingTime || 0) > 20 ? 'bg-green-500' :
                                (gameState.remainingTime || 0) > 10 ? 'bg-yellow-500' : 
                                'bg-red-500 animate-pulse'
                              }`}
                              style={{ 
                                width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / (gameState.turnTimeLimit || 30)) * 100))}%`
                              }}
                            />
                          </div>
                        )}
                      </>
                    ) : (
                      <>
                        <div className="bg-purple-500/20 rounded-lg p-3 border border-purple-400/30">
                          <div className="flex items-center justify-center space-x-3">
                            <span className="text-2xl">⏳</span>
                            <p className="text-white/80">
                              <strong className="text-blue-300">
                                {currentRoom?.players?.find(p => String(p.id) === gameState.currentTurnUserId)?.nickname || '다른 플레이어'}
                              </strong>님의 차례입니다
                            </p>
                            {gameState.remainingTime && (
                              <span className={`font-bold text-xl ${
                                (gameState.remainingTime || 0) <= 10 
                                  ? 'text-red-300 animate-pulse' 
                                  : 'text-purple-300'
                              }`}>
                                ⏰ {gameState.remainingTime?.toFixed(1)}초
                              </span>
                            )}
                          </div>
                        </div>
                        
                        {/* Progress bar - separate row */}
                        {gameState.remainingTime && (
                          <div className="w-full h-6 bg-white/20 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full transition-all ${
                                (gameState.remainingTime || 0) > 20 ? 'bg-green-500' :
                                (gameState.remainingTime || 0) > 10 ? 'bg-yellow-500' : 
                                'bg-red-500 animate-pulse'
                              }`}
                              style={{ 
                                width: `${Math.max(0, Math.min(100, ((gameState.remainingTime || 0) / (gameState.turnTimeLimit || 30)) * 100))}%`
                              }}
                            />
                          </div>
                        )}
                      </>
                    )}
                    
                    {/* Recent word display - 최근 단어 상태 표시 (공간 미리 확보) */}
                    <div className="mb-3">
                      <div className={`p-3 rounded-lg shadow-lg h-16 flex items-center justify-center ${
                        recentWordDisplay ? (
                          recentWordDisplay.status === 'success'
                            ? 'bg-gradient-to-br from-green-500/30 to-emerald-600/30 border border-green-400/50'
                            : 'bg-gradient-to-br from-red-500/30 to-pink-600/30 border border-red-400/50'
                        ) : 'bg-gradient-to-br from-gray-500/20 to-gray-600/20 border border-gray-400/30'
                      }`}>
                        {recentWordDisplay ? (
                          <div className="text-white font-bold text-xl tracking-wide">
                            "{recentWordDisplay.word}"
                          </div>
                        ) : (
                          <div className="text-gray-400 text-sm">
                            최근 단어가 여기에 표시됩니다
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Word chain display with floating cards - Always shown */}
                    <div className="bg-white/5 rounded-lg p-3 border border-white/10">
                      
                      <div className="h-24 flex space-x-3 overflow-hidden">
                        {gameState.wordChain.length > 0 ? (
                          [...gameState.wordChain].reverse().map((word, reverseIndex) => {
                            const originalIndex = gameState.wordChain.length - 1 - reverseIndex;
                            const wordInfo = gameState.wordChainInfo?.[word];
                            const isLatest = reverseIndex === 0; // 첫 번째(맨 왼쪽)가 최신 단어
                            
                            return (
                              <div key={`${word}-${originalIndex}`} className="flex-shrink-0">
                                <WordCard
                                  word={word}
                                  definition={wordInfo?.definition}
                                  difficulty={wordInfo?.difficulty || 1}
                                  score={word.length * 10}
                                  isLatest={isLatest}
                                  index={originalIndex}
                                />
                              </div>
                            );
                          })
                        ) : (
                          <div className="w-full flex items-center justify-center">
                            <div className="text-center">
                              <div className="w-12 h-12 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-2">
                                <span className="text-2xl">🎯</span>
                              </div>
                              <p className="text-white/60 text-xs">
                                {gameState.isPlaying 
                                  ? '첫 단어를 입력하세요'
                                  : '단어들이 여기에 표시됩니다'
                                }
                              </p>
                            </div>
                          </div>
                        )}
                      </div>
                      
                      {gameState.currentChar && (
                        <div className="mt-2 p-3 bg-gradient-to-r from-purple-500/15 to-pink-500/15 rounded-lg border border-purple-400/20 backdrop-blur-sm">
                          <div className="flex items-center justify-center space-x-2">
                            <span className="text-lg">🎯</span>
                            <span className="text-purple-200 text-sm">다음 글자:</span>
                            <span className="text-purple-300 text-lg font-bold">
                              {getDueumDisplayText(gameState.currentChar)}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <div className="mb-4">
                      <div className="w-16 h-16 bg-purple-600/30 rounded-full flex items-center justify-center mx-auto mb-4">
                        <span className="text-3xl">🎮</span>
                      </div>
                      <h3 className="text-white text-xl font-bold mb-2">끝말잇기 게임</h3>
                      <p className="text-purple-200 text-sm">
                        {(currentRoom?.players?.length || 0) < 2 
                          ? `게임 시작을 위해 최소 2명의 플레이어가 필요합니다`
                          : '모든 플레이어가 준비되면 게임을 시작할 수 있습니다'
                        }
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 3-Layer Structure: Players and Chat stacked vertically */}
            <div className="space-y-2">
              {/* Players tab */}
              <div className="bg-purple-800/40 backdrop-blur-lg rounded-lg border border-white/20 overflow-hidden">
                <div className="p-2 relative">
                  <div className="flex space-x-3 overflow-x-auto pb-1 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-transparent hover:scrollbar-thumb-white/20">
                    {currentRoom?.players?.map((player) => {
                      const isCurrentTurn = gameState.isPlaying && gameState.currentTurnUserId === player.id;
                      const playerScore = gameState.scores?.[player.id];
                      
                      return (
                        <div key={player.id} className="flex-shrink-0 w-56">
                          <PlayerCard
                            id={player.id}
                            nickname={player.nickname}
                            isHost={player.isHost}
                            isReady={player.isReady}
                            isCurrentTurn={isCurrentTurn}
                            isMe={player.id === user.id}
                            score={playerScore}
                            isConnected={true}
                          />
                        </div>
                      );
                    }) || (
                      <div className="text-center py-8 w-full">
                        <div className="animate-pulse space-y-3">
                          <div className="h-16 bg-white/10 rounded-xl"></div>
                          <div className="h-16 bg-white/5 rounded-xl"></div>
                        </div>
                        <p className="text-white/60 text-sm mt-3">플레이어 로딩 중...</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Game controls when not playing */}
                  {!gameState.isPlaying && (
                    <div className="p-2 border-t border-white/10">
                      <div className="flex flex-col space-y-2">
                        {(() => {
                          const currentPlayer = currentRoom?.players?.find(p => p.id === user.id);
                          const isHost = currentPlayer?.isHost;
                          const isReady = currentPlayer?.isReady;
                          
                          // 방장이 아닌 경우에만 준비 버튼 표시
                          return !isHost ? (
                            <Button 
                              onClick={handleReadyToggle}
                              disabled={!isConnected}
                              className={`w-full py-3 rounded-lg font-medium transition-all ${
                                isReady 
                                  ? 'bg-gray-600 hover:bg-gray-700 text-gray-300' 
                                  : 'bg-green-600 hover:bg-green-700 text-white shadow-lg'
                              }`}
                            >
                              {isReady ? '준비 취소' : '✅ 준비 완료'}
                            </Button>
                          ) : null;
                        })()}
                        
                        {currentRoom?.players?.find(p => p.id === user.id)?.isHost && (
                          <Button 
                            onClick={handleStartGame}
                            disabled={
                              !isConnected || 
                              !currentRoom?.players?.every(p => p.isReady || p.isHost) ||
                              (currentRoom?.players?.length || 0) < 2
                            }
                            className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
                          >
                            🎮 게임 시작
                          </Button>
                        )}
                        
                        {(currentRoom?.players?.length || 0) < 2 && (
                          <p className="text-center text-purple-200 text-xs">
                            최소 2명이 필요합니다 (현재 {currentRoom?.players?.length || 0}명)
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              </div>
              
              {/* Chat Panel */}
              <ChatPanel
                messages={chatMessages}
                isConnected={isConnected}
                currentUserId={Number(user?.id) || 0}
                onSendMessage={handleSendChat}
                isMyTurn={gameState.currentTurnUserId === String(user?.id)}
                currentChar={gameState.currentChar}
                onSubmitWord={handleSubmitWord}
              />
              
              {/* Item Panel */}
              {user?.id && (
                <ItemPanel
                  userId={Number(user.id)}
                  roomId={roomId}
                  isGameActive={gameState.isPlaying}
                  isMyTurn={gameState.currentTurnUserId === String(user.id)}
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
              )}
            </div>
          </div>
        )}
        
        {/* 게임 리포트 */}
        {gameState.showFinalRankings && gameState.finalRankings && gameState.finalRankings.length > 0 && (
        <GameReport
          finalRankings={gameState.finalRankings}
          currentUserId={Number(user?.id) || 0}
          wordChain={gameState.wordChain}
          gameStats={{
            totalRounds: gameState.maxRounds || 5
          }}
          onBackToLobby={() => {
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
      </main>
      
      {/* 방해 효과 컴포넌트 - 전체 화면에 오버레이 */}
      <DistractionEffects 
        effects={distractionEffects}
        className="fixed inset-0 pointer-events-none z-50"
      />
    </div>
  );
};

export default GameRoomPage;