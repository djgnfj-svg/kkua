import React from 'react';

const ParticipantList = ({ participants }) => {
  const getStatusColor = (status, isCreator) => {
    if (isCreator) {
      return 'bg-gradient-to-r from-purple-500 to-purple-600 text-white';
    }

    switch (status) {
      case 'READY':
      case 'ready':
        return 'bg-gradient-to-r from-green-500 to-green-600 text-white';
      case 'PLAYING':
      case 'playing':
        return 'bg-gradient-to-r from-blue-500 to-blue-600 text-white';
      default:
        return 'bg-gradient-to-r from-yellow-500 to-yellow-600 text-white';
    }
  };

  const getStatusText = (status, isCreator) => {
    if (isCreator) return '👑 방장';

    switch (status) {
      case 'READY':
      case 'ready':
        return '✅ 준비완료';
      case 'PLAYING':
      case 'playing':
        return '🎮 게임중';
      default:
        return '⏳ 대기중';
    }
  };

  const getAvatarColor = (index) => {
    const colors = [
      'bg-gradient-to-br from-pink-400 to-pink-600',
      'bg-gradient-to-br from-blue-400 to-blue-600',
      'bg-gradient-to-br from-green-400 to-green-600',
      'bg-gradient-to-br from-purple-400 to-purple-600',
      'bg-gradient-to-br from-yellow-400 to-yellow-600',
      'bg-gradient-to-br from-indigo-400 to-indigo-600',
      'bg-gradient-to-br from-red-400 to-red-600',
      'bg-gradient-to-br from-teal-400 to-teal-600',
    ];
    return colors[index % colors.length];
  };

  return (
    <div className="w-full">
      <div className="text-center mb-4">
        <h3 className="text-white text-lg font-semibold">👥 참가자 목록</h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        {participants.map((player, index) => (
          <div
            key={player.guest_id || index}
            className="bg-white/10 backdrop-blur-md rounded-xl p-4 border border-white/20 shadow-lg hover:bg-white/20 transition-all duration-200 transform hover:scale-105"
          >
            <div className="flex flex-col items-center space-y-3">
              {/* 아바타 */}
              <div
                className={`w-16 h-16 ${getAvatarColor(index)} rounded-full flex items-center justify-center text-white text-xl font-bold shadow-lg`}
              >
                {player.nickname?.charAt(0)?.toUpperCase() || 'G'}
              </div>

              {/* 닉네임 */}
              <div className="text-white font-semibold text-center truncate w-full">
                {player.nickname || `Guest_${player.guest_id}`}
              </div>

              {/* 상태 배지 */}
              <div
                className={`text-xs px-3 py-1 rounded-full font-semibold shadow-md ${getStatusColor(player.status, player.is_creator)}`}
              >
                {getStatusText(player.status, player.is_creator)}
              </div>

              {/* 추가 정보 */}
              <div className="text-white/70 text-xs text-center">
                {player.is_creator ? '방장님' : `ID: ${player.guest_id}`}
              </div>
            </div>
          </div>
        ))}

        {/* 빈 슬롯 표시 */}
        {Array.from({ length: Math.max(0, 8 - participants.length) }).map(
          (_, index) => (
            <div
              key={`empty-${index}`}
              className="bg-white/5 backdrop-blur-md rounded-xl p-4 border border-white/10 shadow-lg"
            >
              <div className="flex flex-col items-center space-y-3">
                <div className="w-16 h-16 bg-white/10 rounded-full flex items-center justify-center text-white/50 text-xl">
                  👤
                </div>
                <div className="text-white/50 text-sm">빈 슬롯</div>
                <div className="text-xs px-3 py-1 rounded-full bg-white/10 text-white/50">
                  대기중
                </div>
              </div>
            </div>
          )
        )}
      </div>
    </div>
  );
};

export default ParticipantList;
