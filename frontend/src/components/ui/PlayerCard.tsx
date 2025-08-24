import React from 'react';

interface PlayerCardProps {
  id: string;
  nickname: string;
  isHost?: boolean;
  isReady?: boolean;
  isCurrentTurn?: boolean;
  isMe?: boolean;
  score?: number;
  isConnected?: boolean;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({
  id,
  nickname,
  isHost = false,
  isReady = false,
  isCurrentTurn = false,
  isMe = false,
  score,
  isConnected = true
}) => {
  const getCardStyle = () => {
    if (isCurrentTurn) {
      return 'bg-gradient-to-br from-green-500/30 to-emerald-600/30 border-green-400/50 shadow-lg shadow-green-400/20 animate-pulse-slow';
    }
    if (isReady) {
      return 'bg-gradient-to-br from-blue-500/20 to-purple-600/20 border-blue-400/30 shadow-lg shadow-blue-400/10';
    }
    if (isMe) {
      return 'bg-gradient-to-br from-purple-500/20 to-pink-600/20 border-purple-400/30';
    }
    return 'bg-gradient-to-br from-gray-500/10 to-gray-600/10 border-white/10';
  };

  const getAvatarBg = () => {
    if (isCurrentTurn) return 'from-green-400 to-emerald-500';
    if (isHost) return 'from-yellow-400 to-orange-500';
    if (isMe) return 'from-purple-400 to-pink-500';
    return 'from-blue-400 to-indigo-500';
  };

  const getStatusIcon = () => {
    if (!isConnected) return '🔌';
    if (isCurrentTurn) return '🎯';
    if (isReady) return '✅';
    if (isHost) return '👑';
    return '👤';
  };

  return (
    <div className={`
      relative p-4 rounded-xl border-2 transition-all duration-300 
      transform hover:scale-105 hover:shadow-xl
      ${getCardStyle()}
    `}>
      {/* 현재 턴 효과 */}
      {isCurrentTurn && (
        <>
          <div className="absolute -inset-1 bg-gradient-to-r from-green-400 to-emerald-500 rounded-xl blur opacity-30 animate-pulse"></div>
          <div className="absolute top-2 right-2">
            <div className="w-3 h-3 bg-green-400 rounded-full animate-ping"></div>
            <div className="absolute top-0 w-3 h-3 bg-green-300 rounded-full"></div>
          </div>
        </>
      )}

      <div className="relative flex items-center space-x-3">
        {/* 아바타 */}
        <div className={`
          w-12 h-12 bg-gradient-to-br ${getAvatarBg()} 
          rounded-full flex items-center justify-center
          shadow-lg ring-2 ring-white/20
          ${isCurrentTurn ? 'animate-bounce' : ''}
        `}>
          <span className="text-white font-bold text-lg">
            {getStatusIcon()}
          </span>
        </div>

        {/* 플레이어 정보 */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2 mb-1">
            <span className={`font-bold text-sm truncate ${
              isCurrentTurn ? 'text-green-200' : 
              isMe ? 'text-purple-200' : 'text-white'
            }`}>
              {nickname}
              {isMe && ' (나)'}
            </span>
            
            {/* 상태 배지들 */}
            <div className="flex items-center space-x-1">
              {isHost && (
                <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-300 text-xs rounded-full border border-yellow-400/30">
                  방장
                </span>
              )}
              {isCurrentTurn && (
                <span className="px-2 py-0.5 bg-green-500/30 text-green-200 text-xs rounded-full border border-green-400/40 animate-pulse">
                  턴
                </span>
              )}
            </div>
          </div>

          {/* 점수 및 상태 */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              {score !== undefined && (
                <span className="text-white/80 text-xs">
                  🏆 {score}점
                </span>
              )}
              
              <div className="flex items-center space-x-1">
                <div className={`w-2 h-2 rounded-full ${
                  !isConnected ? 'bg-red-400 animate-pulse' :
                  isReady ? 'bg-green-400' : 'bg-yellow-400'
                }`}></div>
                <span className="text-white/60 text-xs">
                  {!isConnected ? '연결끊김' :
                   isReady ? '준비완료' : '대기중'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 호버 글로우 효과 */}
      <div className={`
        absolute inset-0 bg-gradient-to-br ${getAvatarBg()} 
        opacity-0 hover:opacity-10 rounded-xl transition-opacity duration-300
        -z-10 blur-xl
      `}></div>
    </div>
  );
};

export default PlayerCard;