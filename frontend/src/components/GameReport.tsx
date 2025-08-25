import React from 'react';
import { Button, Card } from './ui';

interface PlayerStats {
  rank: number;
  user_id: number;
  nickname: string;
  score: number;
  words_submitted: number;
  items_used: number;
}

interface GameReportProps {
  finalRankings: PlayerStats[];
  currentUserId: number;
  wordChain: string[];
  gameStats?: {
    totalRounds: number;
    gameStart?: string;
    gameEnd?: string;
  };
  onPlayAgain?: () => void;
  onBackToLobby?: () => void;
}

export const GameReport: React.FC<GameReportProps> = ({
  finalRankings,
  currentUserId,
  wordChain,
  gameStats,
  onPlayAgain,
  onBackToLobby
}) => {
  const winner = finalRankings[0];
  const currentPlayerStats = finalRankings.find(player => player.user_id === currentUserId);
  const isWinner = currentPlayerStats?.rank === 1;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md max-h-[80vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="text-center p-4 border-b border-gray-200">
          <div className="text-xl font-bold mb-1">
            {isWinner ? '🏆 승리!' : '🎮 게임 완료!'}
          </div>
          <div className="text-sm text-gray-600">
            {winner && `${winner.nickname}님이 우승했습니다!`}
          </div>
        </div>

        {/* 최종 순위 (간단히) */}
        <div className="p-4">
          <h3 className="text-base font-bold mb-3 text-center">🏆 최종 순위</h3>
          <div className="space-y-2">
            {finalRankings.slice(0, 3).map((player) => (
              <div
                key={player.user_id}
                className={`flex items-center justify-between p-2 rounded-lg text-sm ${
                  player.user_id === currentUserId
                    ? 'bg-purple-100 border border-purple-300'
                    : 'bg-gray-50'
                } ${player.rank === 1 ? 'bg-yellow-100 border-yellow-300' : ''}`}
              >
                <div className="flex items-center space-x-2">
                  <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    player.rank === 1 ? 'bg-yellow-500 text-white' :
                    player.rank === 2 ? 'bg-gray-400 text-white' :
                    player.rank === 3 ? 'bg-orange-400 text-white' :
                    'bg-gray-300 text-gray-600'
                  }`}>
                    {player.rank}
                  </div>
                  <div>
                    <div className="font-semibold flex items-center">
                      {player.nickname}
                      {player.user_id === currentUserId && (
                        <span className="ml-1 text-xs bg-purple-200 text-purple-800 px-1 py-0.5 rounded">나</span>
                      )}
                      {player.rank === 1 && <span className="ml-1">👑</span>}
                    </div>
                  </div>
                </div>
                <div className="text-right text-xs text-gray-600">
                  <div className="font-medium">{player.score}점</div>
                  <div>{player.words_submitted}개 단어</div>
                </div>
              </div>
            ))}
            {finalRankings.length > 3 && (
              <div className="text-center text-xs text-gray-500">
                +{finalRankings.length - 3}명 더
              </div>
            )}
          </div>
        </div>

        {/* 내 통계 (간단히) */}
        {currentPlayerStats && (
          <div className="p-4 border-t border-gray-100">
            <h3 className="text-base font-bold mb-2 text-center">📊 내 결과</h3>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="bg-blue-50 p-2 rounded-lg">
                <div className="text-lg font-bold text-blue-600">
                  {currentPlayerStats.score}
                </div>
                <div className="text-xs text-gray-600">점수</div>
              </div>
              <div className="bg-green-50 p-2 rounded-lg">
                <div className="text-lg font-bold text-green-600">
                  {currentPlayerStats.words_submitted}
                </div>
                <div className="text-xs text-gray-600">단어</div>
              </div>
              <div className="bg-orange-50 p-2 rounded-lg">
                <div className="text-lg font-bold text-orange-600">
                  {currentPlayerStats.rank}
                </div>
                <div className="text-xs text-gray-600">등수</div>
              </div>
            </div>
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="p-4 border-t border-gray-100">
          <div className="space-y-2">
            <Button
              onClick={onPlayAgain}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded-lg text-sm font-medium"
            >
              🎮 다시 게임하기
            </Button>
            <Button
              onClick={onBackToLobby}
              className="w-full bg-gray-500 hover:bg-gray-600 text-white py-2 rounded-lg text-sm font-medium"
            >
              ✅ 확인
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameReport;