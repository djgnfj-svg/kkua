import React from 'react';

const ActionButtons = ({
  isOwner,
  participants,
  handleClickExit,
  handleClickStartBtn,
  handleReady,
  isReady,
  isStartingGame = false,
}) => {
  const allNonOwnerPlayersReady = participants.every(
    (player) =>
      player.is_creator ||
      player.status === 'READY' ||
      player.status === 'ready' ||
      player.is_ready === true
  );

  // 디버깅용 로그
  console.log('🎮 게임시작 버튼 상태 체크:', {
    participants: participants.map(p => ({
      guest_id: p.guest_id,
      nickname: p.nickname,
      is_creator: p.is_creator,
      status: p.status,
      is_ready: p.is_ready,
      ready_check: p.is_creator || p.status === 'READY' || p.status === 'ready' || p.is_ready === true
    })),
    allNonOwnerPlayersReady,
    participantCount: participants.length,
    canStartGame: participants.length >= 2 && allNonOwnerPlayersReady
  });

  return (
    <div className="w-full bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <button
          onClick={handleClickExit}
          className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105"
        >
          {isOwner ? '🗑️ 방 삭제' : '🚪 나가기'}
        </button>
        
        <div className="text-white/80 text-sm">
          {isOwner ? '👑 방장' : '👤 참가자'}
        </div>
      </div>

      {isOwner ? (
        <div className="text-center">
          <div className="relative inline-block group">
            <button
              onClick={() => {
                if (isStartingGame) return;
                
                if (participants.length >= 2 && allNonOwnerPlayersReady) {
                  handleClickStartBtn();
                } else if (participants.length < 2) {
                  alert('게임 시작을 위해 최소 2명의 플레이어가 필요합니다.');
                } else {
                  alert('모든 플레이어가 준비 상태여야 합니다.');
                }
              }}
              className={`px-8 py-4 rounded-xl shadow-lg font-bold text-lg transition-all duration-200 transform ${
                isStartingGame
                  ? 'bg-gradient-to-r from-blue-500 to-blue-600 text-white cursor-wait'
                  : participants.length >= 2 && allNonOwnerPlayersReady
                  ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white hover:scale-105'
                  : 'bg-gradient-to-r from-gray-400 to-gray-500 text-white cursor-not-allowed'
              }`}
              disabled={participants.length < 2 || !allNonOwnerPlayersReady || isStartingGame}
            >
              {isStartingGame ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
                  <span>게임 시작 중...</span>
                </div>
              ) : (
                <>🎮 게임 시작</>
              )}
            </button>
            
            {!isStartingGame && (participants.length < 2 || !allNonOwnerPlayersReady) && (
              <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 bg-black/80 text-white text-sm px-4 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 shadow-md">
                {participants.length < 2 
                  ? '2인 이상일 때 게임을 시작할 수 있습니다' 
                  : '모든 플레이어가 준비 상태여야 합니다'}
              </div>
            )}
            
            {isStartingGame && (
              <div className="absolute -top-16 left-1/2 transform -translate-x-1/2 bg-blue-600/90 text-white text-sm px-4 py-2 rounded-lg whitespace-nowrap z-10 shadow-md">
                모든 플레이어를 게임으로 이동 중...
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center">
          <button
            onClick={handleReady}
            className={`px-8 py-4 rounded-xl shadow-lg font-bold text-lg transition-all duration-200 transform hover:scale-105 ${
              isReady
                ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white'
                : 'bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white'
            }`}
          >
            {isReady ? '✅ 준비완료' : '⏳ 준비하기'}
          </button>
        </div>
      )}
    </div>
  );
};

export default ActionButtons;
