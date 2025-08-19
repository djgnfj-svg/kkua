import React from 'react';

const GameTimer = ({
  timeLeft,
  totalTime = 120,
  inputTimeLeft,
  inputTimeTotal = 12,
}) => {
  // 전체 게임 시간 진행률 계산
  const gameProgress = (timeLeft / totalTime) * 100;

  // 입력 시간 진행률 계산
  const inputProgress = (inputTimeLeft / inputTimeTotal) * 100;

  // 시간에 따른 색상 결정
  const getTimeColor = (time, total) => {
    const percentage = (time / total) * 100;
    if (percentage > 50) return 'text-green-600';
    if (percentage > 25) return 'text-yellow-600';
    return 'text-red-600 animate-pulse';
  };

  // 원형 프로그레스바를 위한 SVG 경로 계산
  const radius = 45;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (gameProgress / 100) * circumference;

  return (
    <div className="flex flex-col items-center space-y-4">
      {/* 메인 게임 타이머 - 원형 프로그레스바 */}
      <div className="relative">
        <svg className="w-32 h-32 transform -rotate-90">
          {/* 배경 원 */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke="rgb(229 231 235)"
            strokeWidth="8"
            fill="none"
          />
          {/* 진행 원 */}
          <circle
            cx="64"
            cy="64"
            r={radius}
            stroke={
              gameProgress > 50
                ? 'rgb(34 197 94)'
                : gameProgress > 25
                  ? 'rgb(250 204 21)'
                  : 'rgb(239 68 68)'
            }
            strokeWidth="8"
            fill="none"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-linear"
          />
        </svg>

        {/* 중앙 시간 표시 */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div
            className={`text-3xl font-bold ${getTimeColor(timeLeft, totalTime)}`}
          >
            {timeLeft}
          </div>
          <div className="text-xs text-gray-500">초</div>
        </div>
      </div>

      {/* 입력 시간 타이머 - 가로 바 형태 */}
      <div className="w-full max-w-xs">
        <div className="flex justify-between items-center mb-1">
          <span className="text-xs text-gray-600">입력 시간</span>
          <span
            className={`text-sm font-bold ${getTimeColor(inputTimeLeft, inputTimeTotal)}`}
          >
            {inputTimeLeft}초
          </span>
        </div>

        <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
          {/* 배경 애니메이션 효과 */}
          {inputTimeLeft <= 3 && (
            <div className="absolute inset-0 bg-red-300 opacity-50 animate-pulse" />
          )}

          {/* 진행 바 */}
          <div
            className={`h-full transition-all duration-1000 ease-linear rounded-full ${
              inputProgress > 50
                ? 'bg-green-500'
                : inputProgress > 25
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
            }`}
            style={{ width: `${inputProgress}%` }}
          >
            {/* 그라데이션 효과 */}
            <div className="h-full bg-gradient-to-r from-transparent to-white/30" />
          </div>

          {/* 경고 애니메이션 */}
          {inputTimeLeft <= 3 && inputTimeLeft > 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-xs font-bold text-red-700 animate-bounce">
                서둘러!
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 시간 경고 메시지 */}
      {timeLeft <= 10 && timeLeft > 0 && (
        <div className="text-red-600 text-sm font-bold animate-pulse">
          게임이 곧 종료됩니다!
        </div>
      )}
    </div>
  );
};

export default GameTimer;
