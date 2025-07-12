import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import WinnerAnnouncement from './components/WinnerAnnouncement';
import GameStatistics from './components/GameStatistics';
import PlayerRanking from './components/PlayerRanking';
import WordTimeline from './components/WordTimeline';
import ActionButtons from './components/ActionButtons';
import useGameResult from './hooks/useGameResult';

const GameResult = () => {
  const { roomId } = useParams();
  const navigate = useNavigate();
  
  const {
    gameData,
    winner,
    players,
    usedWords,
    gameStats,
    loading,
    error
  } = useGameResult(roomId);

  const [showConfetti, setShowConfetti] = useState(false);

  useEffect(() => {
    // 우승자 발표 시 confetti 효과
    if (winner && !loading) {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 5000);
    }
  }, [winner, loading]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <div className="text-xl font-semibold text-gray-700">게임 결과를 불러오는 중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-50 flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-2xl shadow-lg">
          <div className="text-6xl mb-4">😵</div>
          <div className="text-xl font-semibold text-gray-700 mb-2">게임 결과를 불러올 수 없습니다</div>
          <div className="text-gray-600 mb-6">{error}</div>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
          >
            홈으로 돌아가기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-purple-50">
      {/* Confetti 효과 */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-50">
          {Array.from({ length: 50 }).map((_, i) => (
            <div
              key={i}
              className="absolute w-2 h-2 bg-yellow-400 rounded-full animate-confetti"
              style={{
                left: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
                animationDuration: `${3 + Math.random() * 2}s`
              }}
            />
          ))}
        </div>
      )}

      {/* 헤더 */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 p-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src="/imgs/logo/kkeua_logoA.png" alt="끄아 로고" className="h-10" />
            <div>
              <h1 className="text-2xl font-bold text-gray-800">게임 결과</h1>
              <div className="text-sm text-gray-600">방 #{roomId}</div>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-sm text-gray-600">게임 종료</div>
            <div className="text-lg font-semibold text-gray-800">
              {new Date().toLocaleTimeString()}
            </div>
          </div>
        </div>
      </div>

      {/* 메인 컨텐츠 */}
      <div className="max-w-6xl mx-auto p-6 space-y-8">
        {/* 우승자 발표 */}
        <WinnerAnnouncement winner={winner} />

        {/* 게임 통계 및 순위 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <GameStatistics gameStats={gameStats} />
          <PlayerRanking players={players} />
        </div>

        {/* 단어 타임라인 */}
        <WordTimeline usedWords={usedWords} players={players} />

        {/* 액션 버튼들 */}
        <ActionButtons roomId={roomId} />
      </div>

      {/* 푸터 */}
      <div className="bg-white/50 backdrop-blur-sm border-t border-gray-200 p-6 mt-12">
        <div className="max-w-6xl mx-auto text-center text-gray-600">
          <div className="mb-2">끄아 (KKUA) - 실시간 멀티플레이어 끝말잇기</div>
          <div className="text-sm">재미있게 플레이하셨나요? 다시 한 게임 어떠세요? 🎮</div>
        </div>
      </div>

      {/* Confetti 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes confetti {
          0% {
            transform: translateY(-100vh) rotate(0deg);
            opacity: 1;
          }
          100% {
            transform: translateY(100vh) rotate(720deg);
            opacity: 0;
          }
        }
        .animate-confetti {
          animation: confetti linear infinite;
        }
      `}</style>
    </div>
  );
};

export default GameResult;