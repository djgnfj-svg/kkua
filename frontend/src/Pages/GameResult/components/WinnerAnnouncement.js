import React, { useState, useEffect } from 'react';

const WinnerAnnouncement = ({ winner }) => {
  const [showAnimation, setShowAnimation] = useState(false);
  const [showCrown, setShowCrown] = useState(false);

  useEffect(() => {
    if (winner) {
      // 애니메이션 시퀀스
      setTimeout(() => setShowAnimation(true), 500);
      setTimeout(() => setShowCrown(true), 1500);
    }
  }, [winner]);

  if (!winner) {
    return (
      <div className="text-center py-12 bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl">
        <div className="text-6xl mb-4">🤝</div>
        <div className="text-3xl font-bold text-gray-700">무승부!</div>
        <div className="text-lg text-gray-600 mt-2">모든 플레이어가 잘 싸웠습니다</div>
      </div>
    );
  }

  return (
    <div className="relative text-center py-16 bg-gradient-to-br from-yellow-50 to-orange-50 rounded-3xl shadow-xl overflow-hidden">
      {/* 배경 장식 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* 금색 파티클들 */}
        {Array.from({ length: 20 }).map((_, i) => (
          <div
            key={i}
            className="absolute w-2 h-2 bg-yellow-400 rounded-full animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`,
              animationDuration: `${3 + Math.random() * 2}s`
            }}
          />
        ))}
        
        {/* 별 장식 */}
        <div className="absolute top-8 left-8 text-4xl text-yellow-400 animate-pulse">⭐</div>
        <div className="absolute top-12 right-12 text-3xl text-yellow-500 animate-pulse" style={{ animationDelay: '0.5s' }}>✨</div>
        <div className="absolute bottom-16 left-16 text-5xl text-yellow-400 animate-pulse" style={{ animationDelay: '1s' }}>🌟</div>
        <div className="absolute bottom-20 right-20 text-3xl text-yellow-500 animate-pulse" style={{ animationDelay: '1.5s' }}>💫</div>
      </div>

      {/* 우승자 발표 */}
      <div className="relative z-10">
        {/* 왕관 아이콘 */}
        <div className={`transition-all duration-1000 ${showCrown ? 'scale-100 rotate-0' : 'scale-0 rotate-180'}`}>
          <div className="text-8xl mb-4 animate-bounce">👑</div>
        </div>

        {/* 우승 메시지 */}
        <div className={`transition-all duration-1000 delay-500 ${showAnimation ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <h1 className="text-5xl md:text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-600 to-orange-600 mb-4">
            🎉 승리! 🎉
          </h1>
        </div>

        {/* 우승자 이름 */}
        <div className={`transition-all duration-1000 delay-1000 ${showAnimation ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="relative inline-block">
            <div className="text-4xl md:text-5xl font-bold text-purple-700 mb-2 relative">
              {winner}
              {/* 이름 하이라이트 효과 */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-yellow-200 to-transparent opacity-30 animate-shimmer" />
            </div>
            <div className="text-xl text-gray-700 font-medium">님이 우승하셨습니다!</div>
          </div>
        </div>

        {/* 축하 메시지 */}
        <div className={`transition-all duration-1000 delay-1500 ${showAnimation ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}>
          <div className="mt-8 p-6 bg-white/60 backdrop-blur-sm rounded-2xl mx-auto max-w-md">
            <div className="text-lg text-gray-700 mb-2">🏆 끝말잇기 챔피언 🏆</div>
            <div className="text-sm text-gray-600">
              뛰어난 어휘력과 빠른 반응속도로<br />
              모든 플레이어를 제압했습니다!
            </div>
          </div>
        </div>

        {/* 트로피 애니메이션 */}
        <div className={`transition-all duration-1000 delay-2000 ${showAnimation ? 'opacity-100 scale-100' : 'opacity-0 scale-0'}`}>
          <div className="mt-6 text-6xl animate-bounce" style={{ animationDelay: '2s' }}>
            🏆
          </div>
        </div>

        {/* 사운드 이펙트 시뮬레이션 (이모지로 표현) */}
        <div className={`transition-all duration-500 delay-2500 ${showAnimation ? 'opacity-100' : 'opacity-0'}`}>
          <div className="mt-4 text-2xl space-x-2">
            <span className="animate-pulse">🎺</span>
            <span className="animate-pulse" style={{ animationDelay: '0.2s' }}>🎉</span>
            <span className="animate-pulse" style={{ animationDelay: '0.4s' }}>🎊</span>
            <span className="animate-pulse" style={{ animationDelay: '0.6s' }}>🎈</span>
          </div>
        </div>
      </div>

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
            opacity: 0.7;
          }
          50% {
            transform: translateY(-20px) rotate(180deg);
            opacity: 1;
          }
        }
        @keyframes shimmer {
          0% {
            transform: translateX(-100%);
          }
          100% {
            transform: translateX(100%);
          }
        }
        .animate-float {
          animation: float linear infinite;
        }
        .animate-shimmer {
          animation: shimmer 2s infinite;
        }
      `}</style>
    </div>
  );
};

export default WinnerAnnouncement;