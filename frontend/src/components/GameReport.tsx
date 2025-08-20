import React from 'react';
import { Button, Card } from './ui';

interface PlayerStats {
  rank: number;
  user_id: number;
  nickname: string;
  score: number;
  words_submitted: number;
  max_combo: number;
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-2 sm:p-4">
      <Card className="w-full max-w-4xl max-h-[95vh] sm:max-h-[90vh] overflow-y-auto">
        {/* 헤더 */}
        <div className="text-center p-4 sm:p-6 border-b">
          <div className="text-2xl sm:text-3xl font-bold mb-2">
            {isWinner ? '🏆 승리!' : '게임 완료!'}
          </div>
          <div className="text-base sm:text-lg text-gray-600">
            {winner && `${winner.nickname}님이 최종 우승했습니다!`}
          </div>
        </div>

        {/* 최종 순위 */}
        <div className="p-4 sm:p-6 border-b">
          <h3 className="text-lg sm:text-xl font-bold mb-4">🏆 최종 순위</h3>
          <div className="space-y-2">
            {finalRankings.map((player) => (
              <div
                key={player.user_id}
                className={`flex items-center justify-between p-3 rounded-lg ${
                  player.user_id === currentUserId
                    ? 'bg-blue-50 border-2 border-blue-200'
                    : 'bg-gray-50'
                } ${player.rank === 1 ? 'bg-yellow-50 border-yellow-200' : ''}`}
              >
                <div className="flex items-center space-x-3">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${
                    player.rank === 1 ? 'bg-yellow-400 text-white' :
                    player.rank === 2 ? 'bg-gray-400 text-white' :
                    player.rank === 3 ? 'bg-orange-400 text-white' :
                    'bg-gray-200 text-gray-600'
                  }`}>
                    {player.rank}
                  </div>
                  <div>
                    <div className="font-semibold flex items-center">
                      {player.nickname}
                      {player.user_id === currentUserId && (
                        <span className="ml-2 text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">나</span>
                      )}
                      {player.rank === 1 && <span className="ml-2">👑</span>}
                    </div>
                    <div className="text-sm text-gray-500">
                      {player.score.toLocaleString()}점
                    </div>
                  </div>
                </div>
                <div className="text-right text-sm text-gray-600">
                  <div>단어: {player.words_submitted}개</div>
                  <div>콤보: {player.max_combo}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 개인 통계 */}
        {currentPlayerStats && (
          <div className="p-6 border-b">
            <h3 className="text-xl font-bold mb-4">📊 나의 게임 통계</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {currentPlayerStats.score.toLocaleString()}
                </div>
                <div className="text-sm text-gray-600">총 점수</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-green-600">
                  {currentPlayerStats.words_submitted}
                </div>
                <div className="text-sm text-gray-600">제출한 단어</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {currentPlayerStats.max_combo}
                </div>
                <div className="text-sm text-gray-600">최대 콤보</div>
              </div>
              <div className="bg-orange-50 p-4 rounded-lg text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {currentPlayerStats.items_used}
                </div>
                <div className="text-sm text-gray-600">사용한 아이템</div>
              </div>
            </div>
          </div>
        )}

        {/* 단어 체인 */}
        <div className="p-6 border-b">
          <h3 className="text-xl font-bold mb-4">🔗 단어 체인</h3>
          <div className="bg-gray-50 p-4 rounded-lg max-h-32 overflow-y-auto">
            {wordChain.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {wordChain.map((word, index) => (
                  <span
                    key={index}
                    className="bg-white px-3 py-1 rounded-full border text-sm"
                  >
                    {word}
                  </span>
                ))}
              </div>
            ) : (
              <div className="text-gray-500 text-center">제출된 단어가 없습니다</div>
            )}
          </div>
          <div className="mt-2 text-sm text-gray-600 text-center">
            총 {wordChain.length}개의 단어
          </div>
        </div>

        {/* 게임 정보 */}
        {gameStats && (
          <div className="p-6 border-b">
            <h3 className="text-xl font-bold mb-4">ℹ️ 게임 정보</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="font-semibold">총 라운드:</span> {gameStats.totalRounds}
              </div>
              {gameStats.gameStart && (
                <div>
                  <span className="font-semibold">시작 시간:</span>{' '}
                  {new Date(gameStats.gameStart).toLocaleTimeString()}
                </div>
              )}
              {gameStats.gameEnd && (
                <div>
                  <span className="font-semibold">종료 시간:</span>{' '}
                  {new Date(gameStats.gameEnd).toLocaleTimeString()}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="p-6 flex flex-col sm:flex-row gap-3 justify-center">
          <Button
            onClick={onPlayAgain}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2"
          >
            🎮 다시 하기
          </Button>
          <Button
            onClick={onBackToLobby}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2"
          >
            🏠 로비로 돌아가기
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default GameReport;