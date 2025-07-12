import React from 'react';

const PlayerDisplay = ({ players, currentPlayer, playerStats = {} }) => {
  // 플레이어별 색상 배열
  const playerColors = [
    'bg-blue-500',
    'bg-green-500',
    'bg-yellow-500',
    'bg-red-500',
    'bg-purple-500',
    'bg-pink-500',
    'bg-indigo-500',
    'bg-teal-500'
  ];

  return (
    <div className="w-full bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <h3 className="text-lg font-bold text-gray-800 mb-4">참가자</h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {players.map((player, index) => {
          const isCurrentTurn = player === currentPlayer;
          const stats = playerStats[player] || { wordsSubmitted: 0, lastWord: '' };
          const colorClass = playerColors[index % playerColors.length];
          
          return (
            <div
              key={player}
              className={`relative p-4 rounded-xl transition-all duration-300 ${
                isCurrentTurn 
                  ? 'bg-gradient-to-br from-purple-100 to-blue-100 border-2 border-purple-400 scale-105 shadow-xl' 
                  : 'bg-gray-50 border border-gray-200'
              }`}
            >
              {/* 현재 턴 인디케이터 */}
              {isCurrentTurn && (
                <div className="absolute -top-2 -right-2 w-6 h-6 bg-purple-500 rounded-full animate-pulse flex items-center justify-center">
                  <div className="w-3 h-3 bg-white rounded-full"></div>
                </div>
              )}
              
              {/* 플레이어 아바타 */}
              <div className="flex items-center space-x-3 mb-2">
                <div className={`w-12 h-12 ${colorClass} rounded-full flex items-center justify-center text-white font-bold text-lg`}>
                  {player.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1">
                  <div className={`font-bold ${isCurrentTurn ? 'text-purple-700' : 'text-gray-700'}`}>
                    {player}
                  </div>
                  {isCurrentTurn && (
                    <div className="text-xs text-purple-600 animate-pulse">차례</div>
                  )}
                </div>
              </div>
              
              {/* 플레이어 통계 */}
              <div className="text-xs text-gray-600 space-y-1">
                <div className="flex justify-between">
                  <span>제출 단어:</span>
                  <span className="font-semibold">{stats.wordsSubmitted}개</span>
                </div>
                {stats.lastWord && (
                  <div className="truncate text-gray-500">
                    마지막: {stats.lastWord}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
      
      {/* 턴 순서 표시 (모바일에서는 숨김) */}
      <div className="hidden md:flex items-center justify-center mt-6 space-x-2">
        <div className="text-sm text-gray-600">턴 순서:</div>
        {players.map((player, index) => (
          <React.Fragment key={player}>
            <div 
              className={`px-3 py-1 rounded-full text-sm font-medium transition-all duration-300 ${
                player === currentPlayer 
                  ? 'bg-purple-500 text-white shadow-lg scale-110' 
                  : 'bg-gray-200 text-gray-600'
              }`}
            >
              {player}
            </div>
            {index < players.length - 1 && (
              <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default PlayerDisplay;