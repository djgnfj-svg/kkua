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
  });
  const [inputWord, setInputWord] = useState('');
  const [isMyTurn, setIsMyTurn] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const { 
    connected, 
    messages, 
    participants, 
    gameStatus, 
    sendMessage: sendSocketMessage
  } = useGameRoomSocket(gameid);

  // Redis 기반 게임 상태 조회
  const fetchGameState = useCallback(async () => {
    try {
      const response = await axiosInstance.get(`/api/game/${gameid}/state`);
      const redisGameState = response.data;
      
      setGameState(prevState => ({
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
      messages.forEach(message => {
        if (message.type === 'word_submitted') {
          // 단어 제출 성공 시
          setGameState(prevState => ({
            ...prevState,
            currentWord: message.word,
            lastCharacter: message.last_character,
            currentPlayerId: message.next_player_id,
            currentRound: message.current_round,
            maxRounds: message.max_rounds,
            timeLeft: message.time_left,
            usedWords: [...prevState.usedWords, message.word]
          }));
          setInputWord('');
          setErrorMessage('');
        } else if (message.type === 'game_time_update') {
          // 시간 업데이트
          setGameState(prevState => ({
            ...prevState,
            timeLeft: message.time_left
          }));
        } else if (message.type === 'game_time_over') {
          // 시간 초과
          setGameState(prevState => ({
            ...prevState,
            currentPlayerId: message.current_player_id,
            timeLeft: 30  // 새 턴 시작 시 시간 리셋
          }));
        } else if (message.type === 'game_over') {
          // 게임 종료
          setGameState(prevState => ({
            ...prevState,
            isGameOver: true,
            status: 'finished'
          }));
        } else if (message.type === 'game_ended_by_host') {
          // 방장이 게임 종료
          setGameState(prevState => ({
            ...prevState,
            isGameOver: true,
            status: 'finished'
          }));
        } else if (message.type === 'game_started_redis') {
          // Redis 게임 시작 알림
          setGameState(prevState => ({
            ...prevState,
            status: 'playing',
            currentWord: message.first_word,
            currentPlayerId: message.first_player_id,
            currentPlayerNickname: message.first_player_nickname,
            lastCharacter: message.first_word?.slice(-1) || '',
            timeLeft: message.time_left || 30,
            usedWords: [message.first_word]
          }));
          
          // 게임 시작 알림 표시
          alert(`🎮 ${message.message}\n턴 순서: ${message.participants_order?.join(' → ')}`);
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
  // Redis API를 통한 단어 제출
  const submitWord = useCallback(async (word) => {
    if (!word || !word.trim()) {
      setErrorMessage('단어를 입력해주세요.');
      return;
    }

    if (!isMyTurn) {
      setErrorMessage('당신의 차례가 아닙니다.');
      return;
    }

    try {
      const response = await axiosInstance.post(`/api/game/${gameid}/submit-word`, {
        word: word.trim()
      });

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
  }, [isMyTurn, gameid]);

  const handleInputChange = useCallback((value) => {
    setInputWord(value);
    if (errorMessage) {
      setErrorMessage('');
    }
  }, [errorMessage]);

  const handleKeyPress = useCallback((e) => {
    if (e.key === 'Enter' && inputWord.trim()) {
      submitWord(inputWord.trim());
    }
  }, [inputWord, submitWord]);

  return {
    gameState,
    inputWord,
    isMyTurn,
    errorMessage,
    connected,
    participants,
    handleInputChange,
    handleKeyPress,
    submitWord,
    setInputWord,
  };
};

export default useWordChain;