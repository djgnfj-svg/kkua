import React, { useState } from 'react';

const WordTimeline = ({ usedWords = [], players = [] }) => {
  const [showAll, setShowAll] = useState(false);
  const [selectedPlayer, setSelectedPlayer] = useState('all');

  // 플레이어별 색상 매핑
  const playerColors = {
    '부러': 'bg-blue-500 text-blue-700 border-blue-300',
    '하우두유': 'bg-green-500 text-green-700 border-green-300',
    '김밥': 'bg-yellow-500 text-yellow-700 border-yellow-300',
    '후러': 'bg-red-500 text-red-700 border-red-300',
  };

  // 플레이어 필터링 - player_name과 player 필드 모두 지원
  const filteredWords = selectedPlayer === 'all' 
    ? usedWords 
    : usedWords.filter(word => (word.player_name || word.player) === selectedPlayer);

  // 표시할 단어 수 결정
  const displayWords = showAll ? filteredWords : filteredWords.slice(0, 10);

  const getPlayerColor = (playerName) => {
    return playerColors[playerName] || 'bg-gray-500 text-gray-700 border-gray-300';
  };

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center">
          📖 단어 타임라인
        </h3>
        
        {/* 플레이어 필터 */}
        <div className="flex items-center space-x-2">
          <select
            value={selectedPlayer}
            onChange={(e) => setSelectedPlayer(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-lg text-sm focus:outline-none focus:border-purple-500"
          >
            <option value="all">전체 플레이어</option>
            {players.map(player => {
              const playerName = player.nickname || player.name || '플레이어';
              return (
                <option key={player.guest_id || player.name || playerName} value={playerName}>
                  {playerName}
                </option>
              );
            })}
          </select>
          
          <button
            onClick={() => setShowAll(!showAll)}
            className="px-4 py-1 bg-purple-500 text-white rounded-lg text-sm hover:bg-purple-600 transition-colors"
          >
            {showAll ? '접기' : '전체보기'}
          </button>
        </div>
      </div>

      {/* 통계 요약 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-lg font-bold text-blue-600">{filteredWords.length}</div>
          <div className="text-xs text-gray-600">총 단어</div>
        </div>
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-lg font-bold text-green-600">
            {(() => {
              const validResponseTimes = filteredWords
                .map(w => w.response_time || w.responseTime || 0)
                .filter(time => time > 0);
              return validResponseTimes.length > 0 
                ? (validResponseTimes.reduce((sum, time) => sum + time, 0) / validResponseTimes.length).toFixed(1)
                : '측정 중';
            })()}
          </div>
          <div className="text-xs text-gray-600">평균 응답시간</div>
        </div>
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-lg font-bold text-purple-600">
            {filteredWords.length > 0 ? Math.max(...filteredWords.map(w => w.word.length)) : 0}
          </div>
          <div className="text-xs text-gray-600">최장 단어</div>
        </div>
        <div className="text-center p-3 bg-yellow-50 rounded-lg">
          <div className="text-lg font-bold text-yellow-600">
            {(() => {
              const validResponseTimes = filteredWords
                .map(w => w.response_time || w.responseTime || 0)
                .filter(time => time > 0);
              return validResponseTimes.length > 0 
                ? Math.min(...validResponseTimes).toFixed(1)
                : '측정 중';
            })()}
          </div>
          <div className="text-xs text-gray-600">최단 시간</div>
        </div>
      </div>

      {/* 타임라인 */}
      <div className="relative">
        {/* 중앙 타임라인 선 */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-gray-300"></div>

        <div className="space-y-4">
          {displayWords.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              {selectedPlayer === 'all' ? '사용된 단어가 없습니다.' : `${selectedPlayer}님이 사용한 단어가 없습니다.`}
            </div>
          ) : (
            displayWords.map((wordData, index) => {
              const playerName = wordData.player_name || wordData.player || '알 수 없음';
              const colorClass = getPlayerColor(playerName);
              const isLongWord = wordData.word.length >= 4;
              const isFastResponse = (wordData.response_time || wordData.responseTime || 0) < 3;

              return (
                <div
                  key={index}
                  className="relative flex items-center animate-fadeIn"
                  style={{
                    animationDelay: `${index * 0.1}s`
                  }}
                >
                  {/* 타임라인 노드 */}
                  <div className={`w-4 h-4 rounded-full border-4 border-white shadow-md z-10 ${colorClass.split(' ')[0]}`} />

                  {/* 단어 카드 */}
                  <div className="ml-6 flex-1">
                    <div className={`p-4 rounded-lg border-2 bg-white hover:shadow-md transition-all duration-300 ${colorClass.split(' ').slice(2).join(' ')}`}>
                      <div className="flex items-center justify-between">
                        {/* 단어 정보 */}
                        <div className="flex items-center space-x-3">
                          <div className="text-2xl font-bold text-gray-800">
                            {wordData.word}
                          </div>
                          
                          {/* 특별 배지들 */}
                          <div className="flex space-x-1">
                            {isLongWord && (
                              <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
                                긴 단어
                              </span>
                            )}
                            {isFastResponse && (
                              <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                빠른 응답
                              </span>
                            )}
                          </div>
                        </div>

                        {/* 플레이어 및 시간 정보 */}
                        <div className="text-right">
                          <div className={`inline-block px-3 py-1 rounded-full text-sm font-medium bg-opacity-20 ${colorClass}`}>
                            {playerName}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {wordData.timestamp && new Date(wordData.timestamp).toLocaleTimeString()}
                          </div>
                          {(wordData.response_time || wordData.responseTime) && (
                            <div className="text-xs text-gray-500">
                              응답시간: {(wordData.response_time || wordData.responseTime).toFixed(1)}초
                            </div>
                          )}
                        </div>
                      </div>

                      {/* 단어 분석 */}
                      <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
                        <div className="flex items-center space-x-4">
                          <span>길이: {wordData.word.length}글자</span>
                          <span>순서: #{filteredWords.length - index}</span>
                        </div>
                        
                        {/* 난이도 표시 */}
                        <div className="flex items-center space-x-1">
                          <span>난이도:</span>
                          {Array.from({ length: 5 }).map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-2 rounded-full ${
                                i < Math.min(wordData.word.length - 1, 5) ? 'bg-orange-400' : 'bg-gray-200'
                              }`}
                            />
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* 더 보기 힌트 */}
      {!showAll && filteredWords.length > 10 && (
        <div className="text-center mt-6">
          <div className="text-sm text-gray-500 mb-2">
            +{filteredWords.length - 10}개의 단어가 더 있습니다
          </div>
          <button
            onClick={() => setShowAll(true)}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
          >
            모든 단어 보기
          </button>
        </div>
      )}

      {/* 단어 체인 시각화 (축약된 버전) */}
      {!showAll && displayWords.length > 0 && (
        <div className="mt-6 pt-4 border-t border-gray-200">
          <div className="text-sm font-medium text-gray-700 mb-2">단어 체인 미리보기</div>
          <div className="flex items-center space-x-1 overflow-x-auto pb-2">
            {displayWords.slice(-5).map((word, index) => (
              <React.Fragment key={index}>
                <span className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm font-medium whitespace-nowrap">
                  {word.word}
                </span>
                {index < displayWords.slice(-5).length - 1 && (
                  <svg className="w-4 h-4 text-gray-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      )}

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateX(-20px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.4s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default WordTimeline;