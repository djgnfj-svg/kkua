import React from 'react';

const ParticipantList = ({ participants }) => {
  return (
    <div className="flex flex-row flex-wrap justify-center gap-4 w-full px-4 mb-auto">
      {participants.map((player, index) => (
        <div
          key={player.guest_id || index}
          className="w-[200px] h-[240px] bg-white rounded-xl shadow flex flex-col items-center justify-center gap-2 p-4 border"
        >
          <div className="w-[70px] h-[70px] bg-[#fde2e4] rounded-full flex items-center justify-center text-xl font-bold text-gray-700">
            {player.nickname?.charAt(0)?.toUpperCase() || 'G'}
          </div>
          <div className="font-bold text-sm text-gray-800">
            {player.nickname || `Guest_${player.guest_id}`}
          </div>
          {!player.is_creator && (
            <div
              className={`text-xs px-3 py-1 rounded-full font-semibold ${
                player.status === 'READY' || player.status === 'ready'
                  ? 'bg-yellow-300 text-gray-800'
                  : player.status === 'PLAYING' || player.status === 'playing'
                    ? 'bg-blue-400 text-white'
                    : 'bg-gray-200 text-gray-700'
              }`}
            >
              {player.status === 'READY' || player.status === 'ready'
                ? '대기중'
                : player.status === 'PLAYING' || player.status === 'playing'
                  ? '게임중'
                  : '대기중'}
            </div>
          )}
          {player.is_creator && (
            <div className="text-xs px-3 py-1 bg-red-200 text-red-700 font-semibold rounded-full">
              방장
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ParticipantList;
