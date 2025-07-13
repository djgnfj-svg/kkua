import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WinnerAnnouncement from '../../GameResult/components/WinnerAnnouncement';
import GameStatistics from '../../GameResult/components/GameStatistics';
import PlayerRanking from '../../GameResult/components/PlayerRanking';
import WordTimeline from '../../GameResult/components/WordTimeline';
import useGameResult from '../../GameResult/hooks/useGameResult';

const GameResultModal = ({ isOpen, onClose, roomId, winnerData }) => {
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(false);

  const {
    gameData,
    winner,
    players,
    usedWords,
    gameStats,
    loading,
    error
  } = useGameResult(roomId);

  useEffect(() => {
    // 모달이 열리고 우승자가 있으면 confetti 효과
    if (isOpen && (winner || winnerData) && !loading) {
      setShowConfetti(true);
      setTimeout(() => setShowConfetti(false), 5000);
    }
  }, [isOpen, winner, winnerData, loading]);

  useEffect(() => {
    // ESC 키로 모달 닫기
    const handleEscapeKey = (event) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'hidden'; // 배경 스크롤 방지
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const handleBackdropClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleNewGame = () => {
    onClose();
    navigate('/lobby');
  };

  const handleGoToLobby = () => {
    onClose();
    navigate('/lobby');
  };

  // 로딩 상태
  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm"></div>
        <div className="relative bg-white rounded-2xl p-8 max-w-md mx-4">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <div className="text-xl font-semibold text-gray-700">게임 결과를 불러오는 중...</div>
          </div>
        </div>
      </div>
    );
  }

  // 에러 상태
  if (error) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        <div className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm" onClick={handleBackdropClick}></div>
        <div className="relative bg-white rounded-2xl p-8 max-w-md mx-4">
          <div className="text-center">
            <div className="text-6xl mb-4">😵</div>
            <div className="text-xl font-semibold text-gray-700 mb-2">게임 결과를 불러올 수 없습니다</div>
            <div className="text-gray-600 mb-6">{error}</div>
            <button
              onClick={onClose}
              className="px-6 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
            >
              닫기
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* 배경 오버레이 */}
      <div 
        className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm transition-opacity duration-300"
        onClick={handleBackdropClick}
      ></div>

      {/* Confetti 효과 */}
      {showConfetti && (
        <div className="fixed inset-0 pointer-events-none z-60">
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

      {/* 모달 컨텐츠 */}
      <div className="relative bg-gradient-to-br from-blue-50 to-purple-50 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto transform transition-all duration-300 scale-100">
        {/* 헤더 */}
        <div className="bg-white/80 backdrop-blur-sm border-b border-gray-200 p-4 rounded-t-2xl sticky top-0 z-10">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <img src="/imgs/logo/kkeua_logoA.png" alt="끄아 로고" className="h-10" />
              <div>
                <h1 className="text-2xl font-bold text-gray-800">게임 결과</h1>
                <div className="text-sm text-gray-600">방 #{roomId}</div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="text-sm text-gray-600">게임 완료</div>
                <div className="text-lg font-semibold text-gray-800">
                  {new Date().toLocaleTimeString()}
                </div>
              </div>
              
              {/* 닫기 버튼 */}
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* 메인 컨텐츠 */}
        <div className="p-6 space-y-8">
          {/* 우승자 발표 */}
          <WinnerAnnouncement winner={winner || winnerData} />

          {/* 게임 통계 및 순위 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <GameStatistics gameStats={gameStats} />
            
            {/* 간단한 플레이어 순위 */}
            <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
              <h3 className="text-2xl font-bold text-gray-800 mb-6">🏆 플레이어 순위</h3>
              {Array.isArray(players) && players.length > 0 ? (
                <div className="space-y-3">
                  {players.slice(0, 5).map((player, index) => {
                    // 디버깅: 플레이어 데이터 확인
                    console.log('Player data:', player);
                    return (
                    <div key={player.guest_id || index} className="flex items-center justify-between p-3 bg-white rounded-lg shadow">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                          {((player.nickname || player.name || '?') + '').charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="font-semibold">{player.nickname || player.name || '플레이어'}</div>
                          <div className="text-sm text-gray-600">
                            점수: {player.total_score || player.totalScore || 0}
                          </div>
                        </div>
                      </div>
                      <div className="text-2xl">
                        {index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '🏅'}
                      </div>
                    </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center text-gray-500 py-8">
                  플레이어 데이터를 불러오는 중...
                </div>
              )}
            </div>
          </div>

          {/* 단어 타임라인 */}
          <WordTimeline usedWords={usedWords} players={players} />

          {/* 액션 버튼들 */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <button
              onClick={handleNewGame}
              className="px-8 py-3 bg-green-500 text-white font-semibold rounded-lg hover:bg-green-600 transition-colors shadow-lg"
            >
              🎮 새 게임
            </button>
            <button
              onClick={handleGoToLobby}
              className="px-8 py-3 bg-blue-500 text-white font-semibold rounded-lg hover:bg-blue-600 transition-colors shadow-lg"
            >
              🏠 로비로
            </button>
            <button
              onClick={onClose}
              className="px-8 py-3 bg-gray-500 text-white font-semibold rounded-lg hover:bg-gray-600 transition-colors shadow-lg"
            >
              ✖️ 닫기
            </button>
          </div>
        </div>

        {/* 푸터 */}
        <div className="bg-white/50 backdrop-blur-sm border-t border-gray-200 p-6 rounded-b-2xl">
          <div className="text-center text-gray-600">
            <div className="mb-2">끄아 (KKUA) - 실시간 멀티플레이어 끝말잇기</div>
            <div className="text-sm">재미있게 플레이하셨나요? 다시 한 게임 어떠세요? 🎮</div>
          </div>
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

export default GameResultModal;