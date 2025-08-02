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

        // 고급 점수 시스템을 포함한 게임 결과 데이터 가져오기
        let response;
        try {
          // 먼저 새로운 고급 결과 API 시도
          response = await axiosInstance.get(`/api/game/${numericRoomId}/final-results`);
        } catch (enhancedApiError) {
          // 고급 API 실패 시 기존 API로 폴백
          console.log('고급 결과 API 실패, 기존 API 사용:', enhancedApiError.message);
          response = await axiosInstance.get(`/gamerooms/${numericRoomId}/result`);
        }
        const data = response.data;
        
        // 디버깅을 위한 로그
        // 게임 결과 데이터 수신 완료
        
        // 응답 데이터 구조 로깅 (개발 환경에서만)
        if (process.env.NODE_ENV === 'development') {
          console.log('게임 결과 API 응답:', {
            hasData: !!data,
            playersType: typeof data.players,
            playersLength: Array.isArray(data.players) ? data.players.length : 'not array',
            firstPlayer: data.players?.[0] || null,
            allFields: data
          });
        }
        
        // 데이터 검증 및 설정 - 고급 점수 시스템 데이터 처리
        let validatedPlayers = [];
        let isEnhancedData = false;
        
        // 고급 결과 데이터인지 확인
        if (data.player_stats && Array.isArray(data.player_stats)) {
          isEnhancedData = true;
          validatedPlayers = data.player_stats.map((player, index) => ({
            ...player,
            guest_id: player.guest_id || player.guestId || player.id || index,
            nickname: player.nickname || player.name || `플레이어 ${index + 1}`,
            total_score: player.final_score || player.score || 0,
            // 고급 점수 정보 보존
            base_score: player.score || 0,
            final_score: player.final_score || player.score || 0,
            performance_bonus: player.performance_bonus || null,
            rank: player.rank || index + 1,
            score_history: player.score_history || [],
            consecutive_success: player.consecutive_success || 0
          }));
        } else if (Array.isArray(data.players)) {
          // 기존 데이터 형식 처리
          validatedPlayers = data.players.map((player, index) => ({
            ...player,
            guest_id: player.guest_id || player.guestId || player.id || index,
            nickname: player.nickname || player.name || `플레이어 ${index + 1}`,
            total_score: typeof player.total_score === 'number' ? player.total_score : 
                        typeof player.totalScore === 'number' ? player.totalScore :
                        typeof player.score === 'number' ? player.score : 0,
            words_submitted: typeof player.words_submitted === 'number' ? player.words_submitted :
                            typeof player.wordsSubmitted === 'number' ? player.wordsSubmitted :
                            typeof player.words === 'number' ? player.words : 0,
            avg_response_time: typeof player.avg_response_time === 'number' ? player.avg_response_time :
                              typeof player.avgResponseTime === 'number' ? player.avgResponseTime :
                              typeof player.response_time === 'number' ? player.response_time : 0.0,
            longest_word: player.longest_word || player.longestWord || '',
            rank: typeof player.rank === 'number' ? player.rank : index + 1
          })) : [];
        }
        
        // 개발 환경에서 변환된 플레이어 데이터 로깅
        if (process.env.NODE_ENV === 'development') {
          console.log('변환된 플레이어 데이터:', validatedPlayers);
        }
        
        // 데이터 처리 상태 확인
        const hasProcessingScores = validatedPlayers.length > 0 && validatedPlayers.some(player => player.total_score === -1);
        const allScoresZero = validatedPlayers.length > 0 && validatedPlayers.every(player => player.total_score === 0);
        const hasAnyData = validatedPlayers.length > 0 && validatedPlayers.some(player => 
          player.total_score > 0 || player.words_submitted > 0
        );
        
        // 백엔드에서 -1로 표시한 경우, 모든 점수가 0이지만 실제 게임 데이터가 있어야 하는 경우 재시도
        const shouldRetryForProcessing = hasProcessingScores || (allScoresZero && !hasAnyData && (data.used_words?.length > 0 || data.total_words > 0));
        
        if (shouldRetryForProcessing && retryCount < 3) {
          const reason = hasProcessingScores ? '데이터 처리 중' : '모든 플레이어 점수가 0';
          if (process.env.NODE_ENV === 'development') {
            console.log(`게임 결과 재시도 (${retryCount + 1}/3): ${reason}`, {
              hasProcessingScores,
              allScoresZero,
              hasAnyData,
              usedWordsLength: data.used_words?.length,
              totalWords: data.total_words
            });
          }
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
        
        // 고급 데이터인지 기존 데이터인지에 따라 winner 처리
        const winnerName = isEnhancedData 
          ? (normalizedPlayers.length > 0 ? normalizedPlayers[0].nickname : null)
          : data.winner_name;
        setWinner(winnerName);
        
        setPlayers(normalizedPlayers);
        
        // 고급 데이터에서 단어 목록 처리
        const usedWordsList = isEnhancedData 
          ? (data.word_entries ? data.word_entries.map(entry => entry.word) : [])
          : (data.used_words || []);
        setUsedWords(usedWordsList);
        
        // 게임 통계 처리
        const gameStatsData = isEnhancedData ? data.game_stats || {} : data;
        setGameStats({
          totalRounds: gameStatsData.total_rounds || data.total_rounds || 0,
          gameDuration: gameStatsData.game_duration || data.game_duration || '0분 0초',
          totalWords: gameStatsData.total_words || data.total_words || usedWordsList.length,
          averageResponseTime: gameStatsData.average_response_time || data.average_response_time || 0,
          longestWord: gameStatsData.longest_word || data.longest_word || '없음',
          fastestResponse: gameStatsData.fastest_response || data.fastest_response || 0,
          slowestResponse: gameStatsData.slowest_response || data.slowest_response || 0,
          mvp: winnerName || data.mvp_name || '없음',
          isEnhancedData: isEnhancedData,
          wordEntries: isEnhancedData ? data.word_entries || [] : []
        });

        // 성공 시 재시도 카운트 리셋
        setRetryCount(0);

      } catch (err) {
        // 개발 환경에서만 상세 로깅
        if (process.env.NODE_ENV === 'development') {
          console.warn('게임 결과 로딩 실패:', {
            error: err,
            status: err.response?.status,
            data: err.response?.data,
            url: `/gamerooms/${parseInt(roomId, 10)}/result`
          });
        }
        
        // 특정 에러에 대해서만 재시도
        const shouldRetry = err.response?.status === 500 || err.response?.status === 502 || !err.response;
        
        if (shouldRetry && retryCount < 3) {
          // 네트워크 오류로 재시도;
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