import React from 'react';

interface WordCardProps {
  word: string;
  definition?: string;
  difficulty?: number;
  score?: number;
  isLatest?: boolean;
  index: number;
}

export const WordCard: React.FC<WordCardProps> = ({ 
  word, 
  definition, 
  difficulty = 1, 
  score, 
  isLatest = false,
  index 
}) => {
  const getDifficultyColor = (diff: number) => {
    switch (diff) {
      case 1: return 'from-green-400 to-emerald-500';
      case 2: return 'from-yellow-400 to-orange-500';
      case 3: return 'from-red-400 to-pink-500';
      default: return 'from-blue-400 to-indigo-500';
    }
  };

  const getDifficultyText = (diff: number) => {
    switch (diff) {
      case 1: return '쉬움';
      case 2: return '보통';
      case 3: return '어려움';
      default: return '일반';
    }
  };

  return (
    <div 
      className={`relative transition-all duration-300 ${
        isLatest ? 'animate-bounce-in' : ''
      }`}
      style={{
        animationDelay: `${index * 100}ms`
      }}
    >
      <div className={`
        bg-gradient-to-br ${getDifficultyColor(difficulty)}
        rounded-lg p-2 border border-white/20 
        shadow-lg backdrop-blur-sm
        ${isLatest ? 'ring-1 ring-white/50 animate-pulse-slow' : ''}
      `}>
        {/* 단어 */}
        <div className="text-center mb-1">
          <h3 className="text-white font-bold text-base drop-shadow-md">
            {word}
          </h3>
          {score && (
            <div className="flex items-center justify-center space-x-1 mt-1">
              <span className="text-white/90 text-sm">✨</span>
              <span className="text-white font-medium text-sm">{score}점</span>
            </div>
          )}
        </div>

        {/* 뜻 (있는 경우) */}
        {definition && definition !== `${word}의 뜻` && (
          <div className="bg-white/10 rounded p-1 mb-1">
            <p className="text-white/90 text-xs text-center leading-tight">
              {definition}
            </p>
          </div>
        )}

        {/* 난이도 표시 */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-1">
            <span className="text-white/80 text-xs">난이도:</span>
            <span className="text-white font-medium text-xs">
              {getDifficultyText(difficulty)}
            </span>
          </div>
          <div className="text-white/60 text-xs">
            {word.length}글자
          </div>
        </div>

        {/* 반짝이는 효과 */}
        {isLatest && (
          <>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-400 rounded-full animate-ping"></div>
            <div className="absolute -top-1 -right-1 w-3 h-3 bg-yellow-300 rounded-full"></div>
          </>
        )}
      </div>

    </div>
  );
};

export default WordCard;