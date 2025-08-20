import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Card, Loading } from '../components/ui';
import { useUserStore } from '../stores/useUserStore';
import { useGameStore } from '../stores/useGameStore';
import { showToast } from '../components/Toast';
import { apiEndpoints } from '../utils/api';

const GameRoomPage: React.FC = () => {
  const { roomId } = useParams<{ roomId: string }>();
  const navigate = useNavigate();
  const { user } = useUserStore();
  const { currentRoom, setCurrentRoom, isLoading, setLoading } = useGameStore();
  const [roomNotFound, setRoomNotFound] = useState(false);

  useEffect(() => {
    if (!roomId) {
      navigate('/lobby');
      return;
    }

    // 방 정보 로드 (실제로는 방 참가 API 호출)
    loadRoomInfo();
  }, [roomId]);

  const loadRoomInfo = async () => {
    if (!roomId) return;
    
    setLoading(true);
    try {
      // 임시: 방 정보를 시뮬레이션
      // 실제로는 API에서 방 정보를 가져와야 함
      const mockRoom = {
        id: roomId,
        name: `게임룸 ${roomId.slice(-4)}`,
        maxPlayers: 4,
        currentPlayers: 1,
        status: 'waiting' as const,
        createdAt: new Date().toISOString(),
        players: [
          {
            id: user?.id || '1',
            nickname: user?.nickname || 'Unknown',
            isHost: true,
            isReady: false
          }
        ]
      };

      setCurrentRoom(mockRoom);
      showToast.success(`${mockRoom.name}에 입장했습니다! 🎮`);
      
    } catch (error: any) {
      console.error('Failed to load room:', error);
      setRoomNotFound(true);
      showToast.error('방을 찾을 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveRoom = async () => {
    try {
      if (roomId) {
        // 실제로는 방 나가기 API 호출
        await apiEndpoints.gameRooms.leave(roomId);
      }
      
      setCurrentRoom(null);
      showToast.info('로비로 돌아갔습니다');
      navigate('/lobby');
      
    } catch (error: any) {
      console.error('Failed to leave room:', error);
      // 에러가 발생해도 로비로 이동
      navigate('/lobby');
    }
  };

  if (!roomId) {
    return null;
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8">
          <Loading size="lg" text="게임룸을 불러오는 중..." />
        </Card>
      </div>
    );
  }

  if (roomNotFound) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Card className="p-8 text-center max-w-md">
          <div className="text-6xl mb-4">🔍</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            방을 찾을 수 없습니다
          </h2>
          <p className="text-gray-600 mb-6">
            방이 삭제되었거나 잘못된 링크일 수 있습니다.
          </p>
          <Button onClick={() => navigate('/lobby')}>
            로비로 돌아가기
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">끄아 (KKUA)</h1>
              <span className="ml-2 px-2 py-1 bg-yellow-100 text-yellow-700 text-xs rounded-full">
                게임룸
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{user?.nickname}</span>님
              </div>
              <Button
                onClick={handleLeaveRoom}
                variant="secondary"
                size="sm"
              >
                방 나가기
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            🎮 {currentRoom?.name || `게임룸 ${roomId}`}
          </h2>
          <p className="text-gray-600">
            방 ID: {roomId} | 플레이어: {currentRoom?.currentPlayers || 1}/{currentRoom?.maxPlayers || 4}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 게임 영역 */}
          <div className="lg:col-span-2">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold">게임 진행 (준비중)</h3>
              </Card.Header>
              <Card.Body>
                <div className="text-center py-16">
                  <div className="text-6xl mb-4">🎯</div>
                  <h4 className="text-xl font-semibold text-gray-900 mb-2">
                    게임 준비 중입니다
                  </h4>
                  <p className="text-gray-600 mb-6">
                    실제 게임 기능은 다음 단계에서 구현될 예정입니다.
                  </p>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left max-w-md mx-auto">
                    <h5 className="font-medium text-blue-900 mb-2">🚧 개발 중인 기능:</h5>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• WebSocket 실시간 통신</li>
                      <li>• 단어 입력 및 검증</li>
                      <li>• 턴 기반 게임 진행</li>
                      <li>• 타이머 및 점수 시스템</li>
                    </ul>
                  </div>
                </div>
              </Card.Body>
            </Card>
          </div>

          {/* 플레이어 목록 */}
          <div className="lg:col-span-1">
            <Card>
              <Card.Header>
                <h3 className="text-lg font-semibold">플레이어 목록</h3>
              </Card.Header>
              <Card.Body>
                {currentRoom?.players && currentRoom.players.length > 0 ? (
                  <div className="space-y-3">
                    {currentRoom.players.map((player, index) => (
                      <div
                        key={player.id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-primary-100 text-primary-600 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                            {index + 1}
                          </div>
                          <div>
                            <div className="flex items-center">
                              <span className="font-medium text-gray-900">
                                {player.nickname}
                              </span>
                              {player.isHost && (
                                <span className="ml-2 text-xs bg-yellow-100 text-yellow-700 px-2 py-1 rounded">
                                  👑 방장
                                </span>
                              )}
                            </div>
                            <span className="text-sm text-gray-600">
                              {player.isReady ? '✅ 준비완료' : '⏳ 대기중'}
                            </span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    플레이어 정보를 불러오는 중...
                  </div>
                )}

                {/* 게임 시작 버튼 (방장만) */}
                <div className="mt-6">
                  <Button
                    className="w-full"
                    variant="primary"
                    disabled={true}
                  >
                    게임 시작 (준비중)
                  </Button>
                  <p className="text-xs text-gray-500 text-center mt-2">
                    실제 게임 기능은 다음 단계에서 구현됩니다
                  </p>
                </div>
              </Card.Body>
            </Card>
          </div>
        </div>

        {/* 새로고침 안내 */}
        <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-medium text-green-900 mb-2">✅ 상태 유지 확인</h4>
          <p className="text-green-700 text-sm">
            이제 새로고침을 해도 현재 방 상태가 유지됩니다! URL에 방 ID가 포함되어 있어 
            브라우저를 닫고 다시 열어도 같은 방으로 돌아올 수 있습니다.
          </p>
        </div>
      </main>
    </div>
  );
};

export default GameRoomPage;