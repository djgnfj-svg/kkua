import React from 'react';

const GameStatistics = ({ gameStats }) => {
  const {
    totalRounds = 0,
    gameDuration = '0분 0초',
    totalWords = 0,
    averageResponseTime = 0,
    longestWord = '',
    fastestResponse = 0,
    slowestResponse = 0,
    mvp = '',
  } = gameStats || {};

  // 데이터 유효성 검사 및 기본값 처리
  const hasValidData = totalWords > 0;
  const hasResponseTimeData = averageResponseTime > 0 || fastestResponse > 0;

  const stats = [
    {
      icon: '🎯',
      label: '총 라운드',
      value: totalRounds,
      unit: '라운드',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
    },
    {
      icon: '⏱️',
      label: '게임 시간',
      value: gameDuration,
      unit: '',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
    },
    {
      icon: '📝',
      label: '총 단어',
      value: totalWords,
      unit: '개',
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      borderColor: 'border-purple-200',
    },
    {
      icon: '⚡',
      label: '평균 응답시간',
      value: hasResponseTimeData ? averageResponseTime.toFixed(1) : '측정 중',
      unit: hasResponseTimeData ? '초' : '',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
    },
    {
      icon: '📏',
      label: '가장 긴 단어',
      value: longestWord || (hasValidData ? '단어 없음' : '준비 중'),
      unit: '',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
    },
    {
      icon: '🏃',
      label: '최고 기록',
      value:
        hasResponseTimeData && fastestResponse > 0
          ? fastestResponse.toFixed(1)
          : '측정 중',
      unit: hasResponseTimeData && fastestResponse > 0 ? '초' : '',
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      borderColor: 'border-indigo-200',
    },
  ];

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center">
          📊 게임 통계
        </h3>
        {mvp && (
          <div className="flex items-center bg-gradient-to-r from-yellow-100 to-orange-100 px-4 py-2 rounded-full border border-yellow-300">
            <span className="text-lg mr-2">🏆</span>
            <div>
              <div className="text-xs text-gray-600">MVP</div>
              <div className="font-bold text-orange-700">{mvp}</div>
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, index) => (
          <div
            key={index}
            className={`p-4 rounded-xl border-2 ${stat.bgColor} ${stat.borderColor} hover:shadow-md transition-all duration-300 animate-fadeIn`}
            style={{
              animationDelay: `${index * 0.1}s`,
            }}
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-2xl">{stat.icon}</span>
              <div
                className={`text-xs px-2 py-1 rounded-full ${stat.bgColor} ${stat.color} font-medium`}
              >
                {stat.label}
              </div>
            </div>

            <div className="text-center">
              <div className={`text-2xl font-bold ${stat.color} mb-1`}>
                {stat.value}{' '}
                {stat.unit && (
                  <span className="text-sm text-gray-600">{stat.unit}</span>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 상세 통계 */}
      <div className="mt-8 pt-6 border-t border-gray-200">
        <h4 className="text-lg font-semibold text-gray-800 mb-4">상세 분석</h4>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* 응답 시간 분석 */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">최고 기록</span>
              <span className="font-semibold text-green-600">
                {hasResponseTimeData && fastestResponse > 0
                  ? `${fastestResponse.toFixed(1)}초`
                  : '측정 중'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">평균 기록</span>
              <span className="font-semibold text-blue-600">
                {hasResponseTimeData
                  ? `${averageResponseTime.toFixed(1)}초`
                  : '측정 중'}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">최저 기록</span>
              <span className="font-semibold text-red-600">
                {hasResponseTimeData && slowestResponse > 0
                  ? `${slowestResponse.toFixed(1)}초`
                  : '측정 중'}
              </span>
            </div>

            {/* 응답시간 시각화 바 */}
            {hasResponseTimeData && slowestResponse > fastestResponse && (
              <div className="mt-4">
                <div className="text-xs text-gray-500 mb-2">응답시간 분포</div>
                <div className="relative h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="absolute h-full bg-gradient-to-r from-green-400 to-red-400 rounded-full"
                    style={{ width: '100%' }}
                  />
                  <div
                    className="absolute h-full w-1 bg-white border border-gray-400"
                    style={{
                      left: `${Math.min(Math.max(((averageResponseTime - fastestResponse) / (slowestResponse - fastestResponse)) * 100, 0), 100)}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-500 mt-1">
                  <span>빠름</span>
                  <span>보통</span>
                  <span>느림</span>
                </div>
              </div>
            )}
          </div>

          {/* 게임 효율성 */}
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">라운드당 평균 시간</span>
              <span className="font-semibold text-purple-600">
                {totalRounds > 0 ? averageResponseTime.toFixed(1) : 0}초
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">평균 단어 길이</span>
              <span className="font-semibold text-indigo-600">
                {totalWords > 0 ? longestWord.length || 0 : 0}글자
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">게임 효율성</span>
              <span className="font-semibold text-teal-600">
                {totalRounds > 0
                  ? Math.round((totalWords / totalRounds) * 100)
                  : 0}
                %
              </span>
            </div>

            {/* 게임 효율성 시각화 */}
            <div className="mt-4">
              <div className="text-xs text-gray-500 mb-2">전체 게임 평가</div>
              <div className="flex space-x-1">
                {Array.from({ length: 5 }).map((_, i) => (
                  <div
                    key={i}
                    className={`flex-1 h-2 rounded ${
                      i <
                      Math.floor((totalWords / Math.max(totalRounds, 1)) * 2)
                        ? 'bg-gradient-to-r from-green-400 to-blue-400'
                        : 'bg-gray-200'
                    }`}
                  />
                ))}
              </div>
              <div className="text-xs text-center text-gray-500 mt-1">
                {totalWords > totalRounds * 0.8
                  ? '우수'
                  : totalWords > totalRounds * 0.5
                    ? '보통'
                    : '개선 필요'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default GameStatistics;
