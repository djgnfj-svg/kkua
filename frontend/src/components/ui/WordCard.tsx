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
      className={`relative group transition-all duration-500 hover:scale-105 ${
        isLatest ? 'animate-bounce-in' : ''
      }`}
      style={{
        animationDelay: `${index * 100}ms`
      }}
    >
      <div className={`
        bg-gradient-to-br ${getDifficultyColor(difficulty)}
        rounded-xl p-4 border-2 border-white/20 
        shadow-xl hover:shadow-2xl
        backdrop-blur-sm
        transform transition-all duration-300
        ${isLatest ? 'ring-2 ring-white/50 animate-pulse-slow' : ''}
      `}>
        {/* 단어 */}
        <div className="text-center mb-2">
          <h3 className="text-white font-bold text-lg drop-shadow-md">
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
          <div className="bg-white/10 rounded-lg p-2 mb-2">
            <p className="text-white/90 text-xs text-center">
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

      {/* 호버 시 글로우 효과 */}
      <div className={`
        absolute inset-0 bg-gradient-to-br ${getDifficultyColor(difficulty)} 
        opacity-0 group-hover:opacity-20 rounded-xl blur-xl transition-opacity duration-300
        -z-10
      `}></div>
    </div>
  );
};

export default WordCard;