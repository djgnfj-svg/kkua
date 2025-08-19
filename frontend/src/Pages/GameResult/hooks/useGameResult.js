import { useState, useEffect } from 'react';
import axiosInstance from '../../../Api/axiosInstance';

/**
 * 게임 결과 처리 훅
 * 게임 결과 데이터를 가져오고 처리하는 로직
 */
const useGameResult = (roomId) => {
  const [players, setPlayers] = useState([]);
  const [gameData, setGameData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!roomId) {
      setError('방 ID가 없습니다.');
      setLoading(false);
      return;
    }

    const fetchGameResult = async () => {
      try {
        setLoading(true);
        setError(null);

        // 백엔드 API 호출
        const response = await axiosInstance.get(`/gamerooms/${roomId}/result`);
        const data = response.data;

        // 플레이어 데이터 정규화
        let validatedPlayers = [];

        if (data && Array.isArray(data.players)) {
          validatedPlayers = data.players.map((player, index) => ({
            ...player,
            guest_id: player.guest_id || player.guestId || player.id || index,
            nickname: player.nickname || player.name || `플레이어 ${index + 1}`,
            total_score:
              typeof player.total_score === 'number'
                ? player.total_score
                : typeof player.totalScore === 'number'
                  ? player.totalScore
                  : typeof player.score === 'number'
                    ? player.score
                    : 0,
            words_submitted:
              typeof player.words_submitted === 'number'
                ? player.words_submitted
                : typeof player.wordsSubmitted === 'number'
                  ? player.wordsSubmitted
                  : typeof player.words === 'number'
                    ? player.words
                    : 0,
            avg_response_time:
              typeof player.avg_response_time === 'number'
                ? player.avg_response_time
                : typeof player.avgResponseTime === 'number'
                  ? player.avgResponseTime
                  : typeof player.response_time === 'number'
                    ? player.response_time
                    : 0.0,
            longest_word: player.longest_word || player.longestWord || '',
            rank: typeof player.rank === 'number' ? player.rank : index + 1,
          }));
        }

        setPlayers(validatedPlayers);
        setGameData(data);
      } catch (err) {
        console.error('게임 결과 로딩 실패:', err);
        setError(
          err.response?.data?.detail || '게임 결과를 불러오지 못했습니다'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchGameResult();
  }, [roomId]);

  const retryFetch = () => {
    if (roomId) {
      setError(null);
      // useEffect가 다시 실행되도록 트리거
      setLoading(true);
    }
  };

  return {
    players,
    gameData,
    loading,
    error,
    retryFetch,
  };
};

export default useGameResult;
