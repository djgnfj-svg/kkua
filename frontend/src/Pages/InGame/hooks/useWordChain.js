import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../../contexts/AuthContext';
import useGameRoomSocket from '../../../hooks/useGameRoomSocket';

const useWordChain = () => {
  const { gameid } = useParams();
  const { user } = useAuth();
  const [gameState, setGameState] = useState({
    currentWord: '',
    currentPlayerId: null,
    currentPlayerNickname: '',
    lastCharacter: '',
    usedWords: [],
    turnNumber: 0,
    currentRound: 1,
    maxRounds: 10,
    isGameOver: false,
    timeLeft: 15,
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

  // WebSocket 메시지 처리
  useEffect(() => {
    const handleWordChainMessages = () => {
      messages.forEach(message => {
        if (message.type === 'word_chain_state') {
          setGameState(prevState => ({
            ...prevState,
            currentWord: message.current_word || '',
            currentPlayerId: message.current_player_id,
            currentPlayerNickname: message.current_player_nickname || '',
            lastCharacter: message.last_character || '',
            usedWords: message.used_words || [],
            turnNumber: message.turn_number || 0,
            currentRound: message.current_round || 1,
            maxRounds: message.max_rounds || 10,
            isGameOver: message.is_game_over || false,
          }));
        } else if (message.type === 'word_chain_timer') {
          setGameState(prevState => ({
            ...prevState,
            timeLeft: message.remaining_time || 0,
            currentPlayerId: message.current_player_id,
            currentPlayerNickname: message.current_player_nickname || '',
          }));
        } else if (message.type === 'word_chain_word_submitted') {
          setGameState(prevState => ({
            ...prevState,
            lastCharacter: message.last_character || '',
            currentRound: message.current_round || prevState.currentRound,
            maxRounds: message.max_rounds || prevState.maxRounds,
          }));
          setInputWord('');
          setErrorMessage('');
        } else if (message.type === 'word_chain_error') {
          setErrorMessage(message.message || '오류가 발생했습니다.');
          setTimeout(() => setErrorMessage(''), 3000);
        } else if (message.type === 'word_chain_game_over') {
          setGameState(prevState => ({
            ...prevState,
            isGameOver: true,
          }));
        }
      });
    };

    if (messages.length > 0) {
      handleWordChainMessages();
    }
  }, [messages]);

  // 내 차례인지 확인
  useEffect(() => {
    if (gameState.currentPlayerId && user?.guest_id) {
      setIsMyTurn(gameState.currentPlayerId === user.guest_id);
      console.log('차례 확인:', {
        currentPlayerId: gameState.currentPlayerId,
        myGuestId: user.guest_id,
        isMyTurn: gameState.currentPlayerId === user.guest_id
      });
    }
  }, [gameState.currentPlayerId, user?.guest_id]);

  // 단어 제출
  const submitWord = useCallback((word) => {
    if (!word || !word.trim()) {
      setErrorMessage('단어를 입력해주세요.');
      return;
    }

    if (!isMyTurn) {
      setErrorMessage('당신의 차례가 아닙니다.');
      return;
    }

    // WebSocket으로 단어 제출 메시지 전송
    if (sendSocketMessage) {
      const wordChainMessage = {
        type: 'word_chain',
        action: 'submit_word',
        word: word.trim(),
        timestamp: new Date().toISOString(),
      };

      sendSocketMessage(JSON.stringify(wordChainMessage));
      console.log('단어 제출:', word.trim());
    }
  }, [isMyTurn, sendSocketMessage]);

  // 입력 단어 변경 처리
  const handleInputChange = useCallback((value) => {
    setInputWord(value);
    if (errorMessage) {
      setErrorMessage('');
    }
  }, [errorMessage]);

  // 엔터키 처리
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