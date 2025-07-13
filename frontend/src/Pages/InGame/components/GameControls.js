import React from 'react';

const GameControls = ({ handleClickFinish, handleClickComplete }) => {
  return (
    <div className="fixed bottom-8 right-4 z-[100] space-y-2" style={{ zIndex: 100 }}>
      <button
        onClick={handleClickComplete}
        className="block px-6 py-3 bg-green-500 text-white rounded-lg shadow-lg hover:bg-green-600 transition-all duration-200 font-semibold text-sm"
        title="게임을 완료하고 결과를 확인합니다 (테스트용)"
      >
        🎉 게임 완료
      </button>
      <button
        onClick={handleClickFinish}
        className="block px-6 py-3 bg-red-500 text-white rounded-lg shadow-lg hover:bg-red-600 transition-all duration-200 text-sm"
        title="게임을 강제 종료합니다 (방장만 가능)"
      >
        🛑 게임 종료
      </button>
    </div>
  );
};

export default GameControls;
