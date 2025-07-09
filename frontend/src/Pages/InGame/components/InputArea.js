import React from 'react';

const InputArea = ({
  inputValue,
  setInputValue,
  crashKeyDown,
  crashMessage,
  inputTimeLeft,
  time_gauge,
  catActive,
}) => {
  return (
    <>
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
    </>
  );
};

export default InputArea;
