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

        // 실제 API 호출로 게임 결과 데이터 가져오기
        try {
          const response = await axiosInstance.get(`/gamerooms/${roomId}/result`);
          const data = response.data;
          
          setGameData(data);
          setWinner(data.winner_name);
          setPlayers(data.players);
          setUsedWords(data.used_words);
          setGameStats({
            totalRounds: data.total_rounds,
            gameDuration: data.game_duration,
            totalWords: data.total_words,
            averageResponseTime: data.average_response_time,
            longestWord: data.longest_word,
            fastestResponse: data.fastest_response,
            slowestResponse: data.slowest_response,
            mvp: data.mvp_name
          });

        } catch (apiError) {
          console.error('API 호출 실패, 목업 데이터 사용:', apiError);
          
          // API 실패 시 목업 데이터 사용
          const mockData = {
          winner: '부러',
          players: [
            { 
              name: '부러', 
              wordsSubmitted: 8, 
              totalScore: 24, 
              avgResponseTime: 3.2,
              longestWord: '컴퓨터과학',
              rank: 1
            },
            { 
              name: '하우두유', 
              wordsSubmitted: 6, 
              totalScore: 18, 
              avgResponseTime: 4.1,
              longestWord: '프로그래밍',
              rank: 2
            },
            { 
              name: '김밥', 
              wordsSubmitted: 5, 
              totalScore: 15, 
              avgResponseTime: 5.2,
              longestWord: '데이터베이스',
              rank: 3
            },
            { 
              name: '후러', 
              wordsSubmitted: 4, 
              totalScore: 12, 
              avgResponseTime: 6.1,
              longestWord: '알고리즘',
              rank: 4
            }
          ],
          usedWords: [
            { word: '사과', player: '부러', timestamp: new Date(Date.now() - 300000), responseTime: 2.1 },
            { word: '과일', player: '하우두유', timestamp: new Date(Date.now() - 280000), responseTime: 3.5 },
            { word: '일기', player: '김밥', timestamp: new Date(Date.now() - 260000), responseTime: 4.2 },
            { word: '기술', player: '후러', timestamp: new Date(Date.now() - 240000), responseTime: 5.8 },
            { word: '컴퓨터', player: '부러', timestamp: new Date(Date.now() - 220000), responseTime: 2.9 },
            { word: '터미널', player: '하우두유', timestamp: new Date(Date.now() - 200000), responseTime: 3.8 },
            { word: '널뛰기', player: '김밥', timestamp: new Date(Date.now() - 180000), responseTime: 6.1 },
            { word: '기계학습', player: '후러', timestamp: new Date(Date.now() - 160000), responseTime: 4.5 },
            { word: '프로그래밍', player: '부러', timestamp: new Date(Date.now() - 140000), responseTime: 2.3 },
            { word: '밍크코트', player: '하우두유', timestamp: new Date(Date.now() - 120000), responseTime: 4.7 },
            { word: '트레이닝', player: '김밥', timestamp: new Date(Date.now() - 100000), responseTime: 5.3 },
            { word: '글쓰기', player: '후러', timestamp: new Date(Date.now() - 80000), responseTime: 6.2 },
            { word: '기능개발', player: '부러', timestamp: new Date(Date.now() - 60000), responseTime: 3.1 },
            { word: '발전소', player: '하우두유', timestamp: new Date(Date.now() - 40000), responseTime: 4.9 },
            { word: '소프트웨어', player: '김밥', timestamp: new Date(Date.now() - 20000), responseTime: 5.8 }
          ],
          gameStats: {
            totalRounds: 15,
            gameDuration: '5분 23초',
            totalWords: 15,
            averageResponseTime: 4.2,
            longestWord: '프로그래밍',
            fastestResponse: 2.1,
            slowestResponse: 6.2,
            mvp: '부러'
          }
        };

        // API 호출 시뮬레이션 (실제로는 아래와 같이 호출)
        // const response = await axiosInstance.get(`/gamerooms/${roomId}/result`);
        // const data = response.data.data;

        await new Promise(resolve => setTimeout(resolve, 1500)); // 로딩 시뮬레이션

        setGameData(mockData);
        setWinner(mockData.winner);
        setPlayers(mockData.players);
        setUsedWords(mockData.usedWords);
        setGameStats(mockData.gameStats);
        }

      } catch (err) {
        console.error('게임 결과 로딩 실패:', err);
        setError('게임 결과를 불러오는 중 오류가 발생했습니다.');
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