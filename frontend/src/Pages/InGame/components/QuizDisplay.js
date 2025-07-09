import React from 'react';

const QuizDisplay = ({ quizMsg, timeLeft, message, timeOver }) => {
  return (
    <>
      <div className="text-4xl font-bold mb-8">{quizMsg}</div>
      <div className="text-2xl mb-4">남은 시간: {timeLeft}초</div>
      {timeOver && <div className="text-red-500 text-xl">시간 초과!</div>}
      {message && <div className="text-green-500 text-xl">{message}</div>}
    </>
  );
};

export default QuizDisplay;
