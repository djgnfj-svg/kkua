import React from 'react';

const ActionButtons = ({
  isOwner,
  participants,
  currentUser,
  onToggleReady,
  onLeaveRoom,
  onStartGame,
}) => {
  // 현재 사용자의 준비 상태 확인
  const currentUserInfo = participants.find(p => p.guest_id === currentUser?.guest_id);
  const isReady = currentUserInfo?.is_ready || false;

  // 모든 참가자가 준비되었는지 확인 (방장 제외)
  const allPlayersReady = participants
    .filter(p => !p.is_creator && p.guest_id !== currentUser?.guest_id)
    .every(p => p.is_ready === true);
  
  const canStartGame = participants.length >= 2 && allPlayersReady;

  return (
    <div className="w-full bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 shadow-lg">
      <div className="flex justify-center items-center gap-4">
        {isOwner ? (
          <button
            onClick={onStartGame || (() => alert('게임 시작 기능은 준비 중입니다!'))}
            className={`px-8 py-4 font-bold text-lg rounded-xl shadow-lg transition-all duration-200 transform hover:scale-105 ${
              canStartGame
                ? 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white'
                : 'bg-gradient-to-r from-gray-400 to-gray-500 text-gray-300 cursor-not-allowed'
            }`}
            disabled={!canStartGame}
          >
            {canStartGame ? '🎮 게임 시작' : '⏳ 플레이어 대기중'}
          </button>
        ) : (
          <button
            onClick={onToggleReady}
            className={`px-6 py-3 font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 ${
              isReady
                ? 'bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white'
                : 'bg-gradient-to-r from-yellow-500 to-yellow-600 hover:from-yellow-600 hover:to-yellow-700 text-white'
            }`}
          >
            {isReady ? '✅ 준비완료' : '⏳ 준비하기'}
          </button>
        )}

        <button
          onClick={onLeaveRoom}
          className="px-6 py-3 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white font-semibold rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105"
        >
          {isOwner ? '🗑️ 방 삭제' : '🚪 나가기'}
        </button>
      </div>
      
      {/* 디버그 정보 */}
      {isOwner && (
        <div className="mt-4 p-3 bg-black/30 rounded-lg text-xs text-white/70">
          <div>참가자: {participants.length}명</div>
          <div>모든 플레이어 준비됨: {allPlayersReady ? '✅' : '❌'}</div>
          <div>게임 시작 가능: {canStartGame ? '✅' : '❌'}</div>
        </div>
      )}
    </div>
  );
};

export default ActionButtons;
