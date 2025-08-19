import React from 'react';

const PlayerRanking = ({ players = [] }) => {
  // 순위별 색상 및 아이콘 설정
  const getRankStyle = (rank) => {
    switch (rank) {
      case 1:
        return {
          bgGradient: 'bg-gradient-to-br from-yellow-100 to-yellow-200',
          border: 'border-yellow-400',
          text: 'text-yellow-800',
          medal: '🥇',
          ringColor: 'ring-yellow-400',
          badgeGradient: 'bg-gradient-to-r from-yellow-400 to-yellow-600',
        };
      case 2:
        return {
          bgGradient: 'bg-gradient-to-br from-gray-100 to-gray-200',
          border: 'border-gray-400',
          text: 'text-gray-800',
          medal: '🥈',
          ringColor: 'ring-gray-400',
          badgeGradient: 'bg-gradient-to-r from-gray-400 to-gray-600',
        };
      case 3:
        return {
          bgGradient: 'bg-gradient-to-br from-orange-100 to-orange-200',
          border: 'border-orange-400',
          text: 'text-orange-800',
          medal: '🥉',
          ringColor: 'ring-orange-400',
          badgeGradient: 'bg-gradient-to-r from-orange-400 to-orange-600',
        };
      default:
        return {
          bgGradient: 'bg-gradient-to-br from-blue-50 to-blue-100',
          border: 'border-blue-200',
          text: 'text-blue-800',
          medal: '🏅',
          ringColor: 'ring-blue-200',
          badgeGradient: 'bg-gradient-to-r from-blue-400 to-blue-600',
        };
    }
  };

  // 플레이어를 순위순으로 정렬
  const sortedPlayers = [...players].sort((a, b) => a.rank - b.rank);

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center">
          🏆 플레이어 순위
        </h3>
        <div className="text-sm text-gray-600">총 {players.length}명 참가</div>
      </div>

      <div className="space-y-4">
        {sortedPlayers.map((player, index) => {
          const rankStyle = getRankStyle(player.rank);
          const isTopThree = player.rank <= 3;

          return (
            <div
              key={player.guest_id || player.name || index}
              className={`relative p-4 rounded-xl border-2 ${rankStyle.bgGradient} ${rankStyle.border} transition-all duration-300 hover:shadow-lg animate-slideIn ${
                isTopThree ? 'ring-2 ' + rankStyle.ringColor : ''
              }`}
              style={{
                animationDelay: `${index * 0.15}s`,
              }}
            >
              {/* 순위 배지 */}
              <div className="absolute -top-2 -left-2 w-8 h-8 rounded-full bg-white border-2 border-gray-300 flex items-center justify-center font-bold text-sm shadow-md">
                {player.rank}
              </div>

              {/* 메달 (상위 3위) */}
              {isTopThree && (
                <div
                  className="absolute -top-2 -right-2 text-2xl animate-bounce"
                  style={{ animationDelay: `${index * 0.2 + 1}s` }}
                >
                  {rankStyle.medal}
                </div>
              )}

              <div className="flex items-center justify-between">
                {/* 플레이어 정보 */}
                <div className="flex items-center space-x-4">
                  {/* 아바타 */}
                  <div
                    className={`w-14 h-14 ${rankStyle.badgeGradient} rounded-full flex items-center justify-center text-white font-bold text-xl shadow-md`}
                  >
                    {(player.nickname || player.name || '?')
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  {/* 이름 및 기본 정보 */}
                  <div>
                    <div
                      className={`text-xl font-bold ${rankStyle.text} flex items-center space-x-2`}
                    >
                      <span>
                        {player.nickname || player.name || '플레이어'}
                      </span>
                      {player.rank === 1 && (
                        <span className="text-sm bg-yellow-400 text-yellow-900 px-2 py-1 rounded-full font-medium animate-pulse">
                          WINNER
                        </span>
                      )}
                    </div>
                    <div className="text-sm text-gray-600 space-x-4">
                      <span>
                        점수:{' '}
                        <span className="font-semibold text-blue-600">
                          {typeof player.total_score === 'number'
                            ? player.total_score
                            : typeof player.totalScore === 'number'
                              ? player.totalScore
                              : typeof player.score === 'number'
                                ? player.score
                                : 0}
                          점
                        </span>
                      </span>
                      <span>
                        단어:{' '}
                        <span className="font-semibold text-green-600">
                          {typeof player.words_submitted === 'number'
                            ? player.words_submitted
                            : typeof player.wordsSubmitted === 'number'
                              ? player.wordsSubmitted
                              : typeof player.words === 'number'
                                ? player.words
                                : 0}
                          개
                        </span>
                      </span>
                    </div>
                  </div>
                </div>

                {/* 상세 통계 */}
                <div className="text-right space-y-1">
                  <div className="text-sm text-gray-600">
                    평균 응답:{' '}
                    <span className="font-semibold">
                      {(
                        player.avg_response_time ||
                        player.avgResponseTime ||
                        0
                      ).toFixed(1)}
                      초
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    최고 단어:{' '}
                    <span className="font-semibold">
                      {player.longest_word || player.longestWord || '없음'}
                    </span>
                  </div>
                </div>
              </div>

              {/* 성과 지표 바 */}
              <div className="mt-4 space-y-2">
                {/* 점수 바 */}
                <div>
                  {(() => {
                    const score =
                      typeof player.total_score === 'number'
                        ? player.total_score
                        : typeof player.totalScore === 'number'
                          ? player.totalScore
                          : typeof player.score === 'number'
                            ? player.score
                            : 0;
                    const maxScore = Math.max(30, score + 10); // 동적 최대값 설정
                    return (
                      <>
                        <div className="flex justify-between text-xs text-gray-600 mb-1">
                          <span>점수</span>
                          <span>
                            {score}/{maxScore}
                          </span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div
                            className={`h-full ${rankStyle.badgeGradient} rounded-full transition-all duration-1000`}
                            style={{
                              width: `${Math.min((score / maxScore) * 100, 100)}%`,
                              animationDelay: `${index * 0.2 + 0.5}s`,
                            }}
                          />
                        </div>
                      </>
                    );
                  })()}
                </div>

                {/* 응답 속도 바 (낮을수록 좋음) */}
                <div>
                  <div className="flex justify-between text-xs text-gray-600 mb-1">
                    <span>응답 속도</span>
                    <span>
                      {(player.avg_response_time ||
                        player.avgResponseTime ||
                        0) > 3
                        ? '느림'
                        : (player.avg_response_time ||
                              player.avgResponseTime ||
                              0) > 2
                          ? '보통'
                          : '빠름'}
                    </span>
                  </div>
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-1000 ${
                        (player.avg_response_time ||
                          player.avgResponseTime ||
                          0) <= 2
                          ? 'bg-green-500'
                          : (player.avg_response_time ||
                                player.avgResponseTime ||
                                0) <= 4
                            ? 'bg-yellow-500'
                            : 'bg-red-500'
                      } rounded-full`}
                      style={{
                        width: `${Math.max(100 - ((player.avg_response_time || player.avgResponseTime || 0) / 6) * 100, 10)}%`,
                        animationDelay: `${index * 0.2 + 0.7}s`,
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* 특별 성취 (1위만) */}
              {player.rank === 1 && (
                <div className="mt-3 p-2 bg-yellow-50 border border-yellow-200 rounded-lg">
                  <div className="flex items-center text-sm text-yellow-800">
                    <span className="mr-2">🎉</span>
                    <span className="font-medium">끝말잇기 챔피언!</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 전체 순위 요약 */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <div className="text-2xl font-bold text-yellow-600">
              {(() => {
                const firstPlayer = sortedPlayers[0];
                if (!firstPlayer) return 0;
                return typeof firstPlayer.total_score === 'number'
                  ? firstPlayer.total_score
                  : typeof firstPlayer.totalScore === 'number'
                    ? firstPlayer.totalScore
                    : typeof firstPlayer.score === 'number'
                      ? firstPlayer.score
                      : 0;
              })()}
            </div>
            <div className="text-xs text-gray-600">최고 점수</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-green-600">
              {players.length > 0
                ? Math.min(
                    ...players.map((p) => {
                      const responseTime =
                        typeof p.avg_response_time === 'number'
                          ? p.avg_response_time
                          : typeof p.avgResponseTime === 'number'
                            ? p.avgResponseTime
                            : typeof p.response_time === 'number'
                              ? p.response_time
                              : 0;
                      return responseTime;
                    })
                  ).toFixed(1)
                : '0.0'}
            </div>
            <div className="text-xs text-gray-600">최단 응답시간 (초)</div>
          </div>
          <div>
            <div className="text-2xl font-bold text-purple-600">
              {players.length > 0
                ? Math.max(
                    ...players.map((p) => {
                      const longestWord = p.longest_word || p.longestWord || '';
                      return longestWord.length;
                    })
                  )
                : 0}
            </div>
            <div className="text-xs text-gray-600">최장 단어 길이</div>
          </div>
        </div>
      </div>

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(-30px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-slideIn {
          animation: slideIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default PlayerRanking;
