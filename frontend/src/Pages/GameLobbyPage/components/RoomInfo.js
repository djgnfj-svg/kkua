import React from 'react';

const RoomInfo = ({ roomInfo, participants, connected }) => {
  return (
    <div className="w-full px-6 py-4 bg-white border border-gray-300 rounded-md shadow-sm flex flex-col gap-2 mb-4">
      <div className="w-full flex justify-between items-center">
        <div className="flex items-center space-x-2">
          <div
            className={`w-3 h-3 rounded-full ${
              connected ? 'bg-green-500' : 'bg-red-500'
            }`}
          ></div>
          <span className="text-gray-700 font-semibold text-sm">접속됨</span>
        </div>
      </div>
      <div className="w-full flex justify-center mt-4 mb-4">
        <div className="w-[30%] text-center text-base text-gray-700 font-semibold">
          게임 모드:{' '}
          {roomInfo?.game_mode === 'acade' || roomInfo?.game_mode === 'arcade'
            ? '아케이드'
            : roomInfo?.game_mode || '모드 없음'}
        </div>
        <div className="w-[30%] text-center text-base text-gray-700 font-semibold">
          방 제목: {roomInfo?.title || '제목 없음'}
        </div>
        <div className="w-[30%] text-center text-base text-gray-700 font-semibold">
          인원: {participants.length} / {roomInfo?.max_players || 8}
        </div>
      </div>
    </div>
  );
};

export default RoomInfo;
