import React, { useEffect, useCallback } from 'react';

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
  // 글자별 소리 재생 함수
  const playCharSound = useCallback((charIndex: number) => {
    try {
      // AudioContext 지원 여부 확인
      if (!window.AudioContext && !(window as any).webkitAudioContext) {
        return;
      }

      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
      
      // AudioContext 상태 확인 및 재개
      if (audioContext.state === 'suspended') {
        audioContext.resume().then(() => {
          playActualSound(audioContext, charIndex);
        }).catch(() => {
          // 재개 실패시 조용히 무시
        });
      } else {
        playActualSound(audioContext, charIndex);
      }
      
    } catch (error) {
      // 사운드 재생 실패시 무시
    }
  }, []);

  const playActualSound = useCallback((audioContext: AudioContext, charIndex: number) => {
    try {
      const oscillator = audioContext.createOscillator();
      const gainNode = audioContext.createGain();
      
      oscillator.connect(gainNode);
      gainNode.connect(audioContext.destination);
      
      // 글자별로 다른 음높이 (더 쾌적한 소리)
      const baseFreq = 600 + (charIndex * 100);
      oscillator.frequency.setValueAtTime(baseFreq, audioContext.currentTime);
      oscillator.frequency.exponentialRampToValueAtTime(baseFreq * 1.5, audioContext.currentTime + 0.05);
      
      gainNode.gain.setValueAtTime(0.05, audioContext.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.08);
      
      oscillator.start(audioContext.currentTime);
      oscillator.stop(audioContext.currentTime + 0.08);
      
      // AudioContext 정리
      setTimeout(() => {
        try {
          audioContext.close();
        } catch (e) {
          // 정리 실패시 무시
        }
      }, 200);
      
    } catch (error) {
      // 실제 사운드 재생 실패시 무시
    }
  }, []);

  // 최신 카드인 경우 글자별 소리 재생 - 단어 체인에만 적용
  useEffect(() => {
    if (isLatest) {
      word.split('').forEach((_, charIndex) => {
        setTimeout(() => {
          playCharSound(charIndex);
        }, index * 50 + charIndex * 80);
      });
    }
  }, [isLatest, word, index, playCharSound]);
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
          <h3 className="text-white font-bold text-base drop-shadow-md flex justify-center">
            {word.split('').map((char, charIndex) => (
              <span
                key={charIndex}
                className={`inline-block transition-all duration-300 ${
                  isLatest ? 'animate-bounce-in-char' : ''
                }`}
                style={{
                  animationDelay: `${index * 50 + charIndex * 80}ms`
                }}
              >
                {char}
              </span>
            ))}
          </h3>
          {score && (
            <div className="flex items-center justify-center space-x-1 mt-1">
              <span 
                className={`text-white/90 text-sm transition-all duration-300 ${
                  isLatest ? 'animate-bounce-in-score' : ''
                }`}
                style={{
                  animationDelay: `${index * 50 + word.length * 80 + 100}ms`
                }}
              >
                ✨
              </span>
              <span 
                className={`text-white font-medium text-sm transition-all duration-300 ${
                  isLatest ? 'animate-bounce-in-score' : ''
                }`}
                style={{
                  animationDelay: `${index * 50 + word.length * 80 + 150}ms`
                }}
              >
                {score}점
              </span>
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