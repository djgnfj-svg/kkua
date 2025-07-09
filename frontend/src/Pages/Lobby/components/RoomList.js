import React from 'react';

const RoomList = ({ rooms, onEnter }) => {
  if (rooms.length === 0 || !rooms[0] || rooms[0].title === '') {
    return (
      <div className="flex items-center justify-center bg-white min-h-[20vh] border rounded-md mx-4 mt-6 mb-2 shadow-md">
        <p className="text-gray-500 text-center text-lg">방을 생성해주세요.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto text-left space-y-4 px-2 md:px-10 md:pt-16 pb-24">
      {rooms.map((room, index) => (
        <div
          key={room.room_id || index}
          className="bg-white p-4 md:p-8 min-h-[12vh] md:min-h-[16vh] border-b shadow-md md:shadow-lg flex items-center justify-between"
        >
          <div>
            <h3 className="font-bold mb-0.5 tracking-widest text-lg md:text-xl">
              {room?.title || '제목 없음'}
            </h3>
            <p className="text-sm md:text-lg font-bold">
              {room?.game_mode || '알 수 없음'} [ {room?.participant_count || 0}{' '}
              /{room?.max_players || 0} ]
            </p>
          </div>
          {room.status === 'waiting' ? (
            room.participant_count >= room.max_players ? (
              <button
                className="text-white px-3 py-1 rounded bg-gray-500 cursor-not-allowed"
                disabled
              >
                인원 초과
              </button>
            ) : (
              <button
                className="text-white px-3 py-1 rounded bg-red-500 hover:bg-red-600"
                onClick={() => onEnter(room.room_id)}
              >
                입장하기
              </button>
            )
          ) : (
            <button
              className="text-white px-3 py-1 rounded bg-gray-500"
              disabled
            >
              끄아 중
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default RoomList;
