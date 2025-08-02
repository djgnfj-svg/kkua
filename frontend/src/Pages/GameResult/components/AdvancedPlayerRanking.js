import React, { useState } from 'react';

const AdvancedPlayerRanking = ({ players = [], currentUserId }) => {
  const [expandedPlayer, setExpandedPlayer] = useState(null);
  
  if (!players || players.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <div className="text-4xl mb-4">📊</div>
        <p>플레이어 정보가 없습니다.</p>
      </div>
    );
  }

  // 순위별 색상 및 아이콘
  const getRankDisplay = (rank) => {
    const rankConfig = {
      1: { icon: '🥇', color: 'text-yellow-600', bg: 'bg-yellow-50 border-yellow-200' },
      2: { icon: '🥈', color: 'text-gray-600', bg: 'bg-gray-50 border-gray-200' },
      3: { icon: '🥉', color: 'text-orange-600', bg: 'bg-orange-50 border-orange-200' },
    };
    
    return rankConfig[rank] || { 
      icon: `${rank}위`, 
      color: 'text-blue-600', 
      bg: 'bg-blue-50 border-blue-200' 
    };
  };

  // 성과 배지 표시
  const renderAchievements = (achievements) => {
    if (!achievements || achievements.length === 0) return null;

    return (
      <div className="mt-2 flex flex-wrap gap-1">
        {achievements.map((achievement, index) => (
          <div
            key={index}
            className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-medium flex items-center"
            title={achievement.description}
          >
            <span className="mr-1">🏆</span>
            <span>{achievement.name}</span>
            <span className="ml-1 font-bold">+{achievement.bonus}</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
        <span className="text-2xl mr-2">🏆</span>
        최종 순위 (고급 점수 시스템)
      </h3>
      
      {players.map((player) => {
        const rankDisplay = getRankDisplay(player.rank);
        const isCurrentUser = player.guest_id === currentUserId;
        const isExpanded = expandedPlayer === player.guest_id;
        const hasAchievements = player.performance_bonus?.achievements?.length > 0;
        
        return (
          <div
            key={player.guest_id}
            className={`
              border-2 rounded-lg p-4 transition-all duration-200
              ${rankDisplay.bg}
              ${isCurrentUser ? 'ring-2 ring-blue-400 shadow-lg' : 'hover:shadow-md'}
            `}
          >
            {/* 기본 정보 */}
            <div 
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedPlayer(isExpanded ? null : player.guest_id)}
            >
              <div className="flex items-center">
                <div className={`text-2xl mr-3 ${rankDisplay.color}`}>
                  {rankDisplay.icon}
                </div>
                <div>
                  <div className="flex items-center">
                    <span className={`font-bold text-lg ${isCurrentUser ? 'text-blue-600' : 'text-gray-800'}`}>
                      {player.nickname}
                    </span>
                    {isCurrentUser && (
                      <span className="ml-2 bg-blue-500 text-white px-2 py-1 rounded-full text-xs">
                        나
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-600">
                    {player.words_submitted}개 단어 제출
                  </div>
                </div>
              </div>
              
              <div className="text-right">
                <div className="flex items-center space-x-3">
                  <div>
                    <div className="text-lg font-bold text-gray-800">
                      {player.final_score}점
                    </div>
                    {player.performance_bonus?.total_bonus > 0 && (
                      <div className="text-sm text-green-600">
                        기본 {player.score}점 + 보너스 {player.performance_bonus.total_bonus}점
                      </div>
                    )}
                  </div>
                  <button className="text-gray-400 hover:text-gray-600">
                    <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                      ▼
                    </span>
                  </button>
                </div>
              </div>
            </div>

            {/* 성과 배지 (항상 표시) */}
            {hasAchievements && renderAchievements(player.performance_bonus.achievements)}

            {/* 상세 정보 (확장 시) */}
            {isExpanded && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div className="bg-white rounded p-3">
                    <div className="text-gray-600">평균 응답시간</div>
                    <div className="font-bold text-lg">
                      {player.average_response_time?.toFixed(1) || 0}초
                    </div>
                  </div>
                  
                  <div className="bg-white rounded p-3">
                    <div className="text-gray-600">최장 단어</div>
                    <div className="font-bold text-lg">
                      {player.longest_word || '-'}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded p-3">
                    <div className="text-gray-600">최단 응답</div>
                    <div className="font-bold text-lg">
                      {player.fastest_response === null || player.fastest_response === undefined 
                        ? '-' 
                        : `${player.fastest_response.toFixed(1)}초`}
                    </div>
                  </div>
                  
                  <div className="bg-white rounded p-3">
                    <div className="text-gray-600">연속 성공</div>
                    <div className="font-bold text-lg">
                      {player.consecutive_success || 0}회
                    </div>
                  </div>
                </div>

                {/* 점수 내역 */}
                {player.score_history && player.score_history.length > 0 && (
                  <div className="mt-4">
                    <h5 className="font-semibold text-gray-700 mb-2">🎯 점수 내역</h5>
                    <div className="max-h-40 overflow-y-auto space-y-1">
                      {player.score_history.slice(-5).map((entry, index) => (
                        <div key={index} className="bg-white rounded p-2 text-xs flex justify-between">
                          <span>
                            <strong>{entry.word}</strong>
                            {entry.score_info.bonuses.is_fast && <span className="ml-1">⚡</span>}
                            {entry.score_info.bonuses.is_combo && <span className="ml-1">🔥</span>}
                            {entry.score_info.bonuses.is_rare && <span className="ml-1">💎</span>}
                          </span>
                          <span className="font-bold text-green-600">
                            +{entry.score_info.final_score}점
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AdvancedPlayerRanking;