import React from 'react';

const ActionButtons = ({
  isOwner,
  participants,
  handleClickExit,
  handleClickStartBtn,
  handleReady,
  isReady,
}) => {
  return (
    <div className="w-full px-6 py-4 bg-white border border-gray-300 rounded-md shadow-sm flex flex-col gap-2 mb-4">
      <div className="w-full flex justify-between items-center">
        <button
          onClick={handleClickExit}
          className={`px-4 py-2 ${isOwner ? 'bg-red-600' : 'bg-red-500'} text-white rounded-lg shadow hover:bg-red-700 transition-all`}
        >
          {isOwner ? '방 삭제' : '나가기'}
        </button>
      </div>

      {isOwner ? (
        <div className="w-full text-center mt-8 mb-4">
          <div className="relative inline-block group">
            <button
              onClick={() => {
                const allNonOwnerPlayersReady = participants.every(
                  (player) =>
                    player.is_creator ||
                    player.status === 'READY' ||
                    player.status === 'ready'
                );

                if (participants.length >= 2 && allNonOwnerPlayersReady) {
                  handleClickStartBtn();
                } else if (participants.length < 2) {
                  alert('게임 시작을 위해 최소 2명의 플레이어가 필요합니다.');
                } else {
                  alert('모든 플레이어가 준비 상태여야 합니다.');
                }
              }}
              className={`px-6 py-2 rounded-lg shadow transition-all font-bold ${
                participants.length >= 2
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-400 text-white cursor-not-allowed'
              }`}
            >
              게임 시작
            </button>
            {participants.length < 2 && (
              <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-black text-white text-sm px-4 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 shadow-md">
                2인 이상일 때 게임을 시작할 수 있습니다
              </div>
            )}
          </div>
        </div>
      ) : (
        !isOwner && (
          <button
            onClick={handleReady}
            className={`mt-8 mb-4 px-6 py-2 ${
              isReady
                ? 'bg-green-500 hover:bg-green-600'
                : 'bg-yellow-500 hover:bg-yellow-600'
            } text-white rounded-lg shadow transition-all`}
          >
            {isReady ? '준비완료' : '준비하기'}
          </button>
        )
      )}
    </div>
  );
};

export default ActionButtons;
