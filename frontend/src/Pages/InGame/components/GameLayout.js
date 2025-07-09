import React from 'react';
import TopMsgAni from '../TopMsg_Ani';

const GameLayout = ({
  typingText,
  handleTypingDone,
  quizMsg,
  message,
  timeLeft,
  timeOver,
  itemList,
  showCount,
  players,
  specialPlayer,
  setSpecialPlayer,
  inputValue,
  setInputValue,
  crashKeyDown,
  crashMessage,
  time_gauge,
  inputTimeLeft,
  setInputTimeLeft,
  catActive,
  frozenTime,
}) => {
  return (
    <div className="w-full h-screen flex flex-col items-center justify-center bg-gray-100">
      <TopMsgAni
        typingText={typingText}
        onTypingDone={handleTypingDone}
        message={message}
      />
      <div className="text-4xl font-bold mb-8">{quizMsg}</div>
      <div className="text-2xl mb-4">남은 시간: {timeLeft}초</div>
      {timeOver && <div className="text-red-500 text-xl">시간 초과!</div>}

      <div className="flex flex-wrap justify-center gap-4 mb-8">
        {itemList.slice(0, showCount).map((item, index) => (
          <div key={index} className="bg-white p-4 rounded shadow">
            {item.word}
          </div>
        ))}
      </div>

      <div className="mb-4">
        현재 플레이어: <span className="font-bold">{specialPlayer}</span>
      </div>

      <input
        type="text"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={crashKeyDown}
        className="border p-2 text-lg"
        placeholder="단어를 입력하세요..."
      />

      <div className="mt-4">
        <button
          onClick={crashMessage}
          className="bg-blue-500 text-white p-2 rounded"
        >
          제출
        </button>
      </div>

      {/* 시간 게이지 및 고양이 애니메이션 (기존 InGame.js에 없었으므로 추가) */}
      <div className="w-full bg-gray-200 h-4 rounded-full mt-4">
        <div
          className="bg-green-500 h-4 rounded-full"
          style={{ width: `${(inputTimeLeft / time_gauge) * 100}%` }}
        ></div>
      </div>
      {catActive ? (
        <img
          src="/imgs/cat_runningA.gif"
          alt="Running Cat"
          className="w-20 h-20"
        />
      ) : (
        <img
          src="/imgs/cat_workingA.gif"
          alt="Working Cat"
          className="w-20 h-20"
        />
      )}
    </div>
  );
};

export default GameLayout;
