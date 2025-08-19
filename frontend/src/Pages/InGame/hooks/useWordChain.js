import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import useGameRoomSocket from '../../../hooks/useGameRoomSocket';
import axiosInstance from '../../../Api/axiosInstance';

const useWordChain = () => {
  const { gameid } = useParams();
  const { user } = useAuth();
  const [gameState, setGameState] = useState({
    status: 'waiting',
    currentWord: '',
    currentPlayerId: null,
    currentPlayerNickname: '',
    lastCharacter: '',
    usedWords: [],
    turnNumber: 0,
    currentRound: 1,
    maxRounds: 10,
    isGameOver: false,
    timeLeft: 30,
    turnTimeLimit: 30,
  });
  const [inputWord, setInputWord] = useState('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [lastScoreInfo, setLastScoreInfo] = useState(null);

  const {
    connected,
    isReconnecting,
    connectionAttempts,
    maxReconnectAttempts,
    messages,
    participants,
    gameStatus,
    sendMessage: sendSocketMessage,
    manualReconnect,
  } = useGameRoomSocket(gameid);

  // Redis 기반 게임 상태 조회
  const fetchGameState = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/game/${gameid}/state`);
      const redisGameState = response.data;

      setGameState((prevState) => ({
        ...prevState,
        status: redisGameState.status,
        currentWord: redisGameState.last_word,
        currentPlayerId: redisGameState.current_player_id,
        currentPlayerNickname: redisGameState.current_player_nickname || '',
        lastCharacter: redisGameState.last_character,
        usedWords: redisGameState.used_words || [],
        currentRound: redisGameState.round_number,
        maxRounds: redisGameState.max_rounds,
        timeLeft: redisGameState.time_left,
        turnTimeLimit: 30, // Redis에서 기본값 가져오기, 추후 설정에서 가져올 수 있음
        isGameOver: redisGameState.status === 'finished',
      }));
    } catch (error) {
      console.error('게임 상태 조회 실패:', error);
    }
  }, [gameid]);

  // 초기 게임 상태 로드 및 주기적 업데이트
  useEffect(() => {
    if (gameid) {
      fetchGameState();

      // 3초마다 게임 상태 업데이트 (WebSocket 보완용)
      const interval = setInterval(fetchGameState, 3000);
      return () => clearInterval(interval);
    }
  }, [gameid, fetchGameState]);

  // WebSocket 메시지 처리
  useEffect(() => {
    const handleWebSocketMessages = () => {
      messages.forEach((message) => {
        if (message.type === 'word_submitted') {
          // 단어 제출 성공 시 - 새 턴 시작으로 타이머 리셋
          setGameState((prevState) => ({
            ...prevState,
            currentWord: message.word,
            lastCharacter: message.last_character,
            currentPlayerId: message.next_player_id,
            currentRound: message.current_round,
            maxRounds: message.max_rounds,
            timeLeft: message.time_left || prevState.turnTimeLimit, // 서버에서 시간을 주지 않으면 기본값 사용
            usedWords: [...prevState.usedWords, message.word],
          }));

          // 고급 점수 정보 처리
          if (message.score_info && message.submitted_by_nickname) {
            setLastScoreInfo({
              scoreInfo: message.score_info,
              playerTotalScore: message.player_total_score,
              scoreBreakdownMessage: message.score_breakdown_message,
              playerNickname: message.submitted_by_nickname,
              timestamp: Date.now(),
            });
          }

          setInputWord('');
          setErrorMessage('');
        } else if (message.type === 'game_time_update') {
          // 서버와의 시간 동기화 - 정확한 시간으로 강제 업데이트
          setGameState((prevState) => ({
            ...prevState,
            timeLeft: Math.max(0, message.time_left),
          }));
        } else if (message.type === 'game_time_over') {
          // 시간 초과
          setGameState((prevState) => ({
            ...prevState,
            currentPlayerId: message.current_player_id,
            timeLeft: prevState.turnTimeLimit, // 새 턴 시작 시 시간 리셋
          }));
        } else if (message.type === 'game_over') {
          // 게임 종료
          setGameState((prevState) => ({
            ...prevState,
            isGameOver: true,
            status: 'finished',
          }));

          // 게임 종료 알림 표시
          alert(`🏁 게임이 종료되었습니다!`);
        } else if (message.type === 'game_ended_by_host') {
          // 방장이 게임 종료
          setGameState((prevState) => ({
            ...prevState,
            isGameOver: true,
            status: 'finished',
          }));

          // 게임 종료 알림 표시
          if (message.message) {
            alert(message.message);
          }
        } else if (message.type === 'game_started_redis') {
          // Redis 게임 시작 알림
          setGameState((prevState) => ({
            ...prevState,
            status: 'playing',
            currentWord: message.first_word,
            currentPlayerId: message.first_player_id,
            currentPlayerNickname: message.first_player_nickname,
            lastCharacter: message.first_word?.slice(-1) || '',
            timeLeft: message.time_left || 30,
            turnTimeLimit: 30,
            usedWords: [message.first_word],
          }));

          // 게임 시작 알림 표시
          alert(
            `🎮 ${message.message}\n턴 순서: ${message.participants_order?.join(' → ')}`
          );
        }

        // 기존 WebSocket 메시지 처리 (호환성)
        if (message.type === 'word_chain_error') {
          setErrorMessage(message.message || '오류가 발생했습니다.');
          setTimeout(() => setErrorMessage(''), 3000);
        }
      });
    };

    if (messages.length > 0) {
      handleWebSocketMessages();
    }
  }, [messages]);

  useEffect(() => {
    if (gameState.currentPlayerId && user?.guest_id) {
      setIsMyTurn(gameState.currentPlayerId === user.guest_id);
    }
  }, [gameState.currentPlayerId, user?.guest_id]);

  // 실시간 클라이언트 사이드 타이머
  useEffect(() => {
    let timer;

    if (gameState.status === 'playing' && gameState.timeLeft > 0) {
      timer = setInterval(() => {
        setGameState((prevState) => {
          // 시간이 0에 도달하면 타이머 정지
          if (prevState.timeLeft <= 0) {
            return prevState;
          }

          const newTimeLeft = Math.max(0, prevState.timeLeft - 1);
          return {
            ...prevState,
            timeLeft: newTimeLeft,
          };
        });
      }, 1000);
    }

    return () => {
      if (timer) {
        clearInterval(timer);
      }
    };
  }, [gameState.status, gameState.currentPlayerId]); // currentPlayerId 변경 시 타이머 재시작
  // Redis API를 통한 단어 제출
  const submitWord = useCallback(
    async (word) => {
      if (!word || !word.trim()) {
        setErrorMessage('단어를 입력해주세요.');
        return;
      }

      if (!isMyTurn) {
        setErrorMessage('당신의 차례가 아닙니다.');
        return;
      }

      try {
        const response = await axiosInstance.post(
          `/api/game/${gameid}/submit-word`,
          {
            word: word.trim(),
          }
        );

        if (response.data.success) {
          // 성공 시 WebSocket에서 자동으로 상태 업데이트됨
          setInputWord('');
          setErrorMessage('');
        } else {
          setErrorMessage(response.data.message || '단어 제출에 실패했습니다.');
        }
      } catch (error) {
        if (error.response?.data?.detail) {
          setErrorMessage(error.response.data.detail);
        } else {
          setErrorMessage('단어 제출 중 오류가 발생했습니다.');
        }

        // 에러 메시지 3초 후 자동 제거
        setTimeout(() => setErrorMessage(''), 3000);
      }
    },
    [isMyTurn, gameid]
  );

  const handleInputChange = useCallback(
    (value) => {
      setInputWord(value);
      if (errorMessage) {
        setErrorMessage('');
      }
    },
    [errorMessage]
  );

  const handleKeyPress = useCallback(
    (e) => {
      if (e.key === 'Enter' && inputWord.trim()) {
        submitWord(inputWord.trim());
      }
    },
    [inputWord, submitWord]
  );

  return {
    gameState,
    inputWord,
    isMyTurn,
    errorMessage,
    lastScoreInfo,
    setLastScoreInfo,
    connected,
    isReconnecting,
    connectionAttempts,
    maxReconnectAttempts,
    participants,
    manualReconnect,
    handleInputChange,
    handleKeyPress,
    submitWord,
    setInputWord,
  };
};

export default useWordChain;
