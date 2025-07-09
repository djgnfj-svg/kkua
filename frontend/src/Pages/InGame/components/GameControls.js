import React from 'react';

const GameControls = ({ handleClickFinish }) => {
  return (
    <div className="fixed bottom-4 left-4 z-50">
      <button
        onClick={handleClickFinish}
        className="bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:bg-red-600 transition"
      >
        게임 종료
      </button>
    </div>
  );
};

export default GameControls;
