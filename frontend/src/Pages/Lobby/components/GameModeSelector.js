import React, { useState, useEffect } from 'react';
import { gameModeApi } from '../../../Api/gameModeApi';

const GameModeSelector = ({ selectedMode, onModeChange, disabled = false }) => {
  const [gameModes, setGameModes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchGameModes = async () => {
      try {
        setLoading(true);
        const modesData = await gameModeApi.getAllModes();
        setGameModes(modesData.modes || []);
        
        // 기본 모드 설정
        if (!selectedMode && modesData.modes.length > 0) {
          const defaultMode = modesData.modes.find(mode => mode.is_default) || modesData.modes[0];
          onModeChange(defaultMode);
        }
      } catch (err) {
        console.error('게임 모드 로딩 실패:', err);
        setError('게임 모드를 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    fetchGameModes();
  }, []);

  // 모드별 아이콘 매핑
  const getModeIcon = (modeName) => {
    const iconMap = {
      classic: '🎯',
      blitz: '⚡',
      marathon: '🏃‍♂️',
      speed: '🚀'
    };
    return iconMap[modeName] || '🎮';
  };

  // 모드별 색상 매핑
  const getModeColor = (modeName) => {
    const colorMap = {
      classic: 'border-blue-300 bg-blue-50 hover:bg-blue-100',
      blitz: 'border-yellow-300 bg-yellow-50 hover:bg-yellow-100',
      marathon: 'border-green-300 bg-green-50 hover:bg-green-100',
      speed: 'border-red-300 bg-red-50 hover:bg-red-100'
    };
    return colorMap[modeName] || 'border-gray-300 bg-gray-50 hover:bg-gray-100';
  };

  if (loading) {
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-800">게임 모드</h3>
        <div className="animate-pulse">
          <div className="grid grid-cols-2 gap-3">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-800">게임 모드</h3>
        <div className="text-center py-4 text-red-600 bg-red-50 rounded-lg">
          <div className="text-2xl mb-2">⚠️</div>
          <div className="text-sm">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold text-gray-800 flex items-center">
        <span className="text-2xl mr-2">🎮</span>
        게임 모드
      </h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {gameModes.map((mode) => {
          const isSelected = selectedMode?.mode_id === mode.mode_id;
          
          return (
            <button
              key={mode.mode_id}
              onClick={() => !disabled && onModeChange(mode)}
              disabled={disabled}
              className={`
                relative border-2 rounded-lg p-4 text-left transition-all duration-200
                ${getModeColor(mode.name)}
                ${isSelected 
                  ? 'ring-2 ring-blue-400 border-blue-400' 
                  : 'hover:shadow-md'
                }
                ${disabled 
                  ? 'opacity-50 cursor-not-allowed' 
                  : 'cursor-pointer'
                }
              `}
            >
              {/* 선택 표시 */}
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                  <span className="text-white text-xs">✓</span>
                </div>
              )}
              
              {/* 모드 정보 */}
              <div className="flex items-start space-x-3">
                <div className="text-2xl">
                  {getModeIcon(mode.name)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="font-semibold text-gray-900 mb-1">
                    {mode.display_name}
                  </div>
                  
                  <div className="text-xs text-gray-600 mb-2 leading-relaxed">
                    {mode.description}
                  </div>
                  
                  {/* 설정 요약 */}
                  <div className="flex flex-wrap gap-2 text-xs">
                    <div className="bg-white bg-opacity-70 px-2 py-1 rounded">
                      ⏱️ {mode.turn_time_limit}초
                    </div>
                    <div className="bg-white bg-opacity-70 px-2 py-1 rounded">
                      🎯 {mode.max_rounds}라운드
                    </div>
                    {mode.score_multiplier !== 1.0 && (
                      <div className="bg-white bg-opacity-70 px-2 py-1 rounded">
                        ⭐ ×{mode.score_multiplier}
                      </div>
                    )}
                    {mode.min_word_length > 2 && (
                      <div className="bg-white bg-opacity-70 px-2 py-1 rounded">
                        📝 {mode.min_word_length}글자+
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              {/* 특수 규칙 배지 */}
              {mode.special_rules && Object.keys(mode.special_rules).length > 0 && (
                <div className="mt-2 pt-2 border-t border-gray-200">
                  <div className="flex flex-wrap gap-1">
                    {mode.special_rules.fast_paced && (
                      <span className="bg-yellow-200 text-yellow-800 px-2 py-1 rounded-full text-xs">
                        빠른 게임
                      </span>
                    )}
                    {mode.special_rules.long_words_only && (
                      <span className="bg-green-200 text-green-800 px-2 py-1 rounded-full text-xs">
                        긴 단어만
                      </span>
                    )}
                    {mode.special_rules.ultra_fast && (
                      <span className="bg-red-200 text-red-800 px-2 py-1 rounded-full text-xs">
                        초고속
                      </span>
                    )}
                  </div>
                </div>
              )}
            </button>
          );
        })}
      </div>
      
      {/* 선택된 모드 상세 정보 */}
      {selectedMode && (
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center mb-2">
            <span className="text-lg mr-2">{getModeIcon(selectedMode.name)}</span>
            <span className="font-semibold text-blue-900">{selectedMode.display_name}</span>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <div className="text-gray-600">턴 시간</div>
              <div className="font-semibold">{selectedMode.turn_time_limit}초</div>
            </div>
            <div>
              <div className="text-gray-600">라운드</div>
              <div className="font-semibold">{selectedMode.max_rounds}라운드</div>
            </div>
            <div>
              <div className="text-gray-600">단어 길이</div>
              <div className="font-semibold">{selectedMode.min_word_length}-{selectedMode.max_word_length}글자</div>
            </div>
            <div>
              <div className="text-gray-600">점수 배수</div>
              <div className="font-semibold">×{selectedMode.score_multiplier}</div>
            </div>
          </div>
          
          {selectedMode.special_rules?.bonus_description && (
            <div className="mt-2 p-2 bg-yellow-100 rounded text-sm text-yellow-800">
              💡 {selectedMode.special_rules.bonus_description}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default GameModeSelector;