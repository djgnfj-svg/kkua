import React from 'react';

const RoomList = ({ rooms, onEnter, isEntering, enteringRoomId }) => {
  if (rooms.length === 0 || !rooms[0] || rooms[0].title === '') {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-white/70">
          <div className="w-24 h-24 mx-auto mb-4 bg-white/10 rounded-full flex items-center justify-center">
            <span className="text-4xl">🎮</span>
          </div>
          <p className="text-lg mb-2">아직 게임방이 없습니다</p>
          <p className="text-sm text-white/50">새 게임방을 만들어 보세요!</p>
        </div>
      </div>
    );
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'waiting': return '⏳';
      case 'playing': return '🎯';
      case 'finished': return '🏁';
      default: return '❓';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'waiting': return '대기중';
      case 'playing': return '게임중';
      case 'finished': return '종료됨';
      default: return '알 수 없음';
    }
  };

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
        {rooms.map((room, index) => (
          <div
            key={room.room_id || index}
            className="bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all duration-200 hover:scale-[1.02] shadow-lg"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-2 mb-2">
                  <span className="text-xl">{getStatusIcon(room.status)}</span>
                  <h3 className="text-white font-bold text-lg truncate">
                    {room?.title || '제목 없음'}
                  </h3>
                </div>
                <div className="flex items-center space-x-4 text-sm text-white/70">
                  <span className="flex items-center space-x-1">
                    <span>🎮</span>
                    <span>{room?.game_mode || '아케이드'}</span>
                  </span>
                  <span className="flex items-center space-x-1">
                    <span>👥</span>
                    <span>{room?.participant_count || 0}/{room?.max_players || 0}</span>
                  </span>
                </div>
                {room?.creator_nickname && (
                  <div className="flex items-center space-x-1 text-xs text-purple-300 mt-1">
                    <span>👑</span>
                    <span>{room.creator_nickname}</span>
                  </div>
                )}
              </div>
              
              <div className="flex flex-col items-end space-y-2">
                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  room.status === 'waiting' 
                    ? 'bg-green-500/20 text-green-300 border border-green-500/30' 
                    : room.status === 'playing'
                    ? 'bg-yellow-500/20 text-yellow-300 border border-yellow-500/30'
                    : 'bg-gray-500/20 text-gray-300 border border-gray-500/30'
                }`}>
                  {getStatusText(room.status)}
                </span>
              </div>
            </div>

            <div className="flex justify-end">
              {room.status === 'waiting' ? (
                room.participant_count >= room.max_players ? (
                  <button
                    className="px-4 py-2 bg-gray-500/50 text-white/50 rounded-lg cursor-not-allowed"
                    disabled
                  >
                    인원 초과
                  </button>
                ) : (
                  <button
                    className={`px-6 py-2 font-semibold rounded-lg transition-all duration-200 shadow-lg flex items-center space-x-2 ${
                      isEntering && enteringRoomId === room.room_id
                        ? 'bg-gray-500/50 text-white/70 cursor-not-allowed'
                        : 'bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white transform hover:scale-105'
                    }`}
                    onClick={() => onEnter(room.room_id)}
                    disabled={isEntering}
                  >
                    {isEntering && enteringRoomId === room.room_id ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/50 border-t-white rounded-full animate-spin"></div>
                        <span>입장 중...</span>
                      </>
                    ) : (
                      <span>입장하기</span>
                    )}
                  </button>
                )
              ) : (
                <button
                  className="px-4 py-2 bg-gray-500/50 text-white/50 rounded-lg cursor-not-allowed"
                  disabled
                >
                  입장 불가
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RoomList;
