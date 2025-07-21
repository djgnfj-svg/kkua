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
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    const fetchGameResult = async () => {
      if (!roomId) {
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // roomId를 숫자로 변환
        const numericRoomId = parseInt(roomId, 10);

        // 실제 API 호출로 게임 결과 데이터 가져오기
        const response = await axiosInstance.get(`/gamerooms/${numericRoomId}/result`);
        const data = response.data;
        
        // 디버깅을 위한 로그
        console.log('게임 결과 API 응답:', data);
        console.log('플레이어 데이터:', data.players);
        
        // 데이터 검증 및 설정
        const validatedPlayers = Array.isArray(data.players) ? data.players.map(player => ({
          ...player,
          // 백엔드 스키마에 맞는 필드명 확인
          total_score: player.total_score || 0,
          words_submitted: player.words_submitted || 0,
          nickname: player.nickname || 'Unknown Player'
        })) : [];
        
        // 데이터 처리 상태 확인
        const hasProcessingScores = validatedPlayers.length > 0 && validatedPlayers.some(player => player.total_score === -1);
        const allScoresZero = validatedPlayers.length > 0 && validatedPlayers.every(player => player.total_score === 0);
        
        // 백엔드에서 -1로 표시한 경우 또는 모든 점수가 0인 경우 재시도
        const shouldRetryForProcessing = hasProcessingScores || allScoresZero;
        
        if (shouldRetryForProcessing && retryCount < 3) {
          const reason = hasProcessingScores ? '데이터 처리 중' : '모든 플레이어 점수가 0';
          console.log(`${reason} - 재시도 ${retryCount + 1}/3`);
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            fetchGameResult();
          }, 2000 * (retryCount + 1)); // 점진적 지연 (2초, 4초, 6초)
          return;
        }
        
        // -1 점수를 0으로 정규화 (처리 중이었지만 재시도 횟수 초과)
        const normalizedPlayers = validatedPlayers.map(player => ({
          ...player,
          total_score: player.total_score === -1 ? 0 : player.total_score
        }));
        
        setGameData(data);
        setWinner(data.winner_name);
        setPlayers(normalizedPlayers);
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

        // 성공 시 재시도 카운트 리셋
        setRetryCount(0);

      } catch (err) {
        console.error('❌ 게임 결과 로딩 실패:', err);
        console.error('❌ 응답 상태:', err.response?.status);
        console.error('❌ 응답 데이터:', err.response?.data);
        console.error('❌ API URL:', `/gamerooms/${parseInt(roomId, 10)}/result`);
        
        // 특정 에러에 대해서만 재시도
        const shouldRetry = err.response?.status === 500 || err.response?.status === 502 || !err.response;
        
        if (shouldRetry && retryCount < 3) {
          console.log(`네트워크 오류 - 재시도 ${retryCount + 1}/3`);
          setRetryCount(prev => prev + 1);
          setTimeout(() => {
            fetchGameResult();
          }, 1000 * (retryCount + 1)); // 점진적 지연
          return;
        }
        
        // 구체적인 에러 메시지 설정
        let errorMessage = '게임 결과를 불러오는 중 오류가 발생했습니다.';
        
        if (err.response?.status === 404) {
          // 404 에러의 경우 더 구체적인 원인 파악
          const detail = err.response?.data?.detail || '';
          if (detail.includes('게임이 아직 시작되지 않았거나 진행 중')) {
            errorMessage = '게임이 아직 완료되지 않았습니다. 게임을 완료한 후 다시 시도해주세요.';
          } else {
            errorMessage = '게임 결과를 찾을 수 없습니다. 게임 데이터가 아직 처리 중이거나 저장되지 않았을 수 있습니다.';
          }
        } else if (err.response?.status === 403) {
          errorMessage = '게임 결과를 조회할 권한이 없습니다. 게임에 참여했던 플레이어만 결과를 볼 수 있습니다.';
        } else if (err.response?.status === 401) {
          errorMessage = '로그인이 필요합니다. 다시 로그인해주세요.';
        } else if (err.response?.status === 500) {
          errorMessage = '서버에서 오류가 발생했습니다. 잠시 후 다시 시도해주세요.';
        } else if (retryCount >= 3) {
          errorMessage = '게임 결과를 불러오지 못했습니다. 네트워크를 확인하고 다시 시도해주세요.';
        }
        
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    };

    fetchGameResult();
  }, [roomId, retryCount]);

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