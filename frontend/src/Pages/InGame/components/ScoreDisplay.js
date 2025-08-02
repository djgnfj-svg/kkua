import React, { useState, useEffect } from 'react';

const ScoreDisplay = ({ 
  scoreInfo, 
  playerTotalScore, 
  scoreBreakdownMessage, 
  playerNickname,
  onAnimationComplete 
}) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    if (scoreInfo) {
      setIsVisible(true);
      
      // 5초 후 자동으로 사라짐
      const hideTimer = setTimeout(() => {
        setIsVisible(false);
        onAnimationComplete?.();
      }, 5000);

      return () => clearTimeout(hideTimer);
    }
  }, [scoreInfo, onAnimationComplete]);

  if (!scoreInfo || !isVisible) {
    return null;
  }

  const { base_score, final_score, total_multiplier, breakdown, bonuses } = scoreInfo;

  // 보너스 아이콘 매핑
  const getBonusIcon = (type) => {
    const iconMap = {
      speed: '⚡',
      combo: '🔥',
      rarity: '💎',
      special: '🌟'
    };
    return iconMap[type] || '⭐';
  };

  // 보너스 표시 여부 확인
  const activeBonuses = [
    { type: 'speed', active: bonuses.is_fast, multiplier: breakdown.speed_multiplier, label: '빠른 응답' },
    { type: 'combo', active: bonuses.is_combo, multiplier: breakdown.combo_multiplier, label: `${bonuses.consecutive_success}연속 콤보` },
    { type: 'rarity', active: bonuses.is_rare, multiplier: breakdown.rarity_multiplier, label: '긴 단어' },
    { type: 'special', active: bonuses.is_special, multiplier: breakdown.special_multiplier, label: '특수 단어' }
  ].filter(bonus => bonus.active && bonus.multiplier > 1.0);

  return (
    <div className={`
      fixed top-20 right-4 z-50 max-w-sm transition-all duration-500 transform
      ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
    `}>
      <div className="bg-white rounded-lg shadow-2xl border-2 border-yellow-300 overflow-hidden">
        {/* 헤더 */}
        <div className="bg-gradient-to-r from-yellow-400 to-orange-400 text-white p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className="text-xl">🎯</span>
              <span className="ml-2 font-bold">{playerNickname}님 득점!</span>
            </div>
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="text-white hover:text-yellow-200 transition-colors"
            >
              <span className={`transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}>
                ▼
              </span>
            </button>
          </div>
        </div>

        {/* 점수 정보 */}
        <div className="p-4">
          {/* 기본 점수 표시 */}
          <div className="text-center mb-3">
            <div className="text-2xl font-bold text-gray-800">
              {base_score} → <span className="text-green-600">{final_score}점</span>
            </div>
            {total_multiplier > 1.0 && (
              <div className="text-sm text-gray-600">
                총 배수: ×{total_multiplier}
              </div>
            )}
            <div className="text-lg font-semibold text-blue-600 mt-1">
              총점: {playerTotalScore}점
            </div>
          </div>

          {/* 활성 보너스 표시 */}
          {activeBonuses.length > 0 && (
            <div className="flex flex-wrap justify-center gap-2 mb-3">
              {activeBonuses.map((bonus, index) => (
                <div
                  key={index}
                  className="bg-yellow-100 text-yellow-800 px-2 py-1 rounded-full text-xs font-medium flex items-center"
                >
                  <span className="mr-1">{getBonusIcon(bonus.type)}</span>
                  <span>{bonus.label}</span>
                  <span className="ml-1 font-bold">×{bonus.multiplier}</span>
                </div>
              ))}
            </div>
          )}

          {/* 상세 정보 (확장 시) */}
          {isExpanded && (
            <div className="border-t pt-3 mt-3">
              <div className="text-xs text-gray-600 space-y-1">
                <div>📊 기본 점수: {base_score}점</div>
                <div>⏱️ 응답 시간: {bonuses.response_time}초</div>
                <div>📏 단어 길이: {bonuses.word_length}글자</div>
                {bonuses.consecutive_success > 0 && (
                  <div>🔥 연속 성공: {bonuses.consecutive_success}회</div>
                )}
              </div>
              
              {scoreBreakdownMessage && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-xs whitespace-pre-line">
                  {scoreBreakdownMessage}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 닫기 버튼 */}
        <div className="px-4 pb-3">
          <button
            onClick={() => setIsVisible(false)}
            className="w-full text-center text-xs text-gray-500 hover:text-gray-700 transition-colors"
          >
            닫기
          </button>
        </div>
      </div>
    </div>
  );
};

export default ScoreDisplay;