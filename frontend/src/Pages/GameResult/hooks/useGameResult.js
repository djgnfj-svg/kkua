import { useState, useEffect } from 'react';
import axiosInstance from '../../../Api/axiosInstance';

const useGameResult = (roomId) => {
  const [gameData, setGameData] = useState(null);
  const [winner, setWinner] = useState(null);
  const [players, setPlayers] = useState([]);
  const [usedWords, setUsedWords] = useState([]);
  const [gameStats, setGameStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGameResult = async () => {
      if (!roomId) return;

      try {
        setLoading(true);
        setError(null);

        // roomId를 숫자로 변환
        const numericRoomId = parseInt(roomId, 10);
        console.log('게임 결과 조회 시작:', { roomId, numericRoomId });

        // 실제 API 호출로 게임 결과 데이터 가져오기
        const response = await axiosInstance.get(`/gamerooms/${numericRoomId}/result`);
        const data = response.data;
        
        console.log('API 응답 데이터:', data); // 디버깅용
        
        setGameData(data);
        setWinner(data.winner_name);
        setPlayers(data.players || []);
        setUsedWords(data.used_words || []);
        setGameStats({
          totalRounds: data.total_rounds || 0,
          gameDuration: data.game_duration || '0분 0초',
          totalWords: data.total_words || 0,
          averageResponseTime: data.average_response_time || 0,
          longestWord: data.longest_word || '없음',
          fastestResponse: data.fastest_response || 0,
          slowestResponse: data.slowest_response || 0,
          mvp: data.mvp_name || '없음'
        });

      } catch (err) {
        console.error('게임 결과 로딩 실패:', err);
        console.error('응답 상태:', err.response?.status);
        console.error('응답 데이터:', err.response?.data);
        
        // 구체적인 에러 메시지 설정
        let errorMessage = '게임 결과를 불러오는 중 오류가 발생했습니다.';
        if (err.response?.status === 404) {
          errorMessage = '게임 결과를 찾을 수 없습니다. 게임이 아직 끝나지 않았거나 데이터가 저장되지 않았을 수 있습니다.';
        } else if (err.response?.status === 403) {
          errorMessage = '게임 결과를 조회할 권한이 없습니다.';
        } else if (err.response?.status === 401) {
          errorMessage = '로그인이 필요합니다.';
        }
        
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchGameResult();
  }, [roomId]);

  return {
    gameData,
    winner,
    players,
    usedWords,
    gameStats,
    loading,
    error
  };
};

export default useGameResult;