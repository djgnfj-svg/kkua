import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import WinnerAnnouncement from '../../GameResult/components/WinnerAnnouncement';
import useGameResult from '../../GameResult/hooks/useGameResult';

const GameResultModal = ({ isOpen, onClose, roomId, winnerData }) => {
  const navigate = useNavigate();
  const [showConfetti, setShowConfetti] = useState(false);

  const {
    gameData,
    winner,
    players,
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

          {/* 플레이어 순위 (단순화된 버전) */}
          <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-8 text-center">🏆 최종 순위</h2>
            {Array.isArray(players) && players.length > 0 ? (
              <div className="space-y-4">
                {players.map((player, index) => {
                  // 더 안전한 데이터 접근 및 디버깅
                  console.log(`플레이어 ${index} 데이터:`, player);
                  
                  const nickname = player?.nickname || '알 수 없는 플레이어';
                  const totalScore = Number(player?.total_score) || 0;
                  const wordsSubmitted = Number(player?.words_submitted) || 0;
                  const guestId = player?.guest_id || index;
                  
                  console.log(`플레이어 ${nickname}: 점수=${totalScore}, 단어수=${wordsSubmitted}`);
                  
                  // 점수가 0인 경우에 대한 특별 처리
                  const displayScore = totalScore === 0 ? '점수 집계 중...' : totalScore.toLocaleString();
                  
                  // 순위별 스타일링
                  const getRankStyle = (rank) => {
                    switch(rank) {
                      case 0: return 'bg-gradient-to-r from-yellow-100 to-yellow-200 border-yellow-300 text-yellow-800';
                      case 1: return 'bg-gradient-to-r from-gray-100 to-gray-200 border-gray-300 text-gray-800';
                      case 2: return 'bg-gradient-to-r from-orange-100 to-orange-200 border-orange-300 text-orange-800';
                      default: return 'bg-white border-gray-200 text-gray-700';
                    }
                  };

                  const getRankIcon = (rank) => {
                    switch(rank) {
                      case 0: return { icon: '🥇', size: 'text-4xl' };
                      case 1: return { icon: '🥈', size: 'text-4xl' };
                      case 2: return { icon: '🥉', size: 'text-4xl' };
                      default: return { icon: '🏅', size: 'text-3xl' };
                    }
                  };

                  const rankStyle = getRankStyle(index);
                  const rankIcon = getRankIcon(index);
                  
                  return (
                    <div key={guestId} className={`flex items-center justify-between p-6 rounded-xl border-2 ${rankStyle} shadow-lg transform transition-all duration-300 hover:scale-105`}>
                      <div className="flex items-center space-x-6">
                        {/* 순위 아이콘 */}
                        <div className={`${rankIcon.size} flex-shrink-0`}>
                          {rankIcon.icon}
                        </div>
                        
                        {/* 플레이어 정보 */}
                        <div className="flex items-center space-x-4">
                          <div className="w-12 h-12 bg-purple-500 text-white rounded-full flex items-center justify-center text-lg font-bold">
                            {nickname.toString().charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <div className="text-xl font-bold">{nickname}</div>
                            <div className="text-sm opacity-75">
                              {wordsSubmitted}개 단어 제출
                            </div>
                          </div>
                        </div>
                      </div>
                      
                      {/* 점수 */}
                      <div className="text-right">
                        <div className="text-3xl font-bold">
                          {totalScore === 0 ? (
                            <span className="text-gray-500 text-lg">점수 집계 중...</span>
                          ) : (
                            <span>{totalScore.toLocaleString()}</span>
                          )}
                        </div>
                        {totalScore > 0 && <div className="text-sm opacity-75">점</div>}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center text-gray-500 py-12">
                <div className="text-4xl mb-4">🎮</div>
                <div className="text-lg">순위 데이터를 불러오는 중...</div>
              </div>
            )}
          </div>

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