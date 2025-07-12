import React from 'react';

const RoomInfo = ({ roomInfo, participants, connected }) => {
  return (
    <div className="w-full bg-white/10 backdrop-blur-md rounded-xl p-6 border border-white/20 shadow-lg">
      <div className="w-full flex justify-between items-center mb-4">
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              connected ? 'bg-green-400' : 'bg-red-400'
            } animate-pulse`}
          ></div>
          <span className="text-white font-medium text-sm">
            {connected ? '연결됨' : '연결 끊김'}
          </span>
        </div>
        <div className="text-white/80 text-sm">
          🎮 끄아 게임 로비
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 text-center">
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="text-white/70 text-sm mb-1">게임 모드</div>
          <div className="text-white font-bold text-lg">
            {roomInfo?.game_mode === 'acade' || roomInfo?.game_mode === 'arcade'
              ? '🎯 아케이드'
              : roomInfo?.game_mode || '🎮 기본'}
          </div>
        </div>
        
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="text-white/70 text-sm mb-1">방 제목</div>
          <div className="text-white font-bold text-lg truncate">
            {roomInfo?.title || '제목 없음'}
          </div>
        </div>
        
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="text-white/70 text-sm mb-1">참가자</div>
          <div className="text-white font-bold text-lg">
            👥 {participants.length} / {roomInfo?.max_players || 8}
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="text-white/70 text-sm mb-1">라운드 수</div>
          <div className="text-white font-bold text-lg">
            🎯 {roomInfo?.max_rounds || 10}
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="text-white/70 text-sm mb-1">제한 시간</div>
          <div className="text-white font-bold text-lg">
            ⏱️ {roomInfo?.time_limit ? Math.floor(roomInfo.time_limit / 60) : 2}분
          </div>
        </div>
      </div>
    </div>
  );
};

export default RoomInfo;
