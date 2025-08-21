import React, { useEffect, useState } from 'react';
import { Button, Card, Loading } from './ui';
import { apiEndpoints } from '../utils/api';
import { useGameStore } from '../stores/useGameStore';
import type { GameRoom } from '../types/game';
import { useUserStore } from '../stores/useUserStore';
import { showToast } from './Toast';

interface GameRoomListProps {
  onJoinRoom: (roomId: string) => void;
  onCreateRoom: () => void;
}

const GameRoomList: React.FC<GameRoomListProps> = ({ onJoinRoom, onCreateRoom }) => {
  const { rooms, setRooms, isLoading, setLoading, setError } = useGameStore();
  const { user } = useUserStore();
  const [refreshing, setRefreshing] = useState(false);
  
  // 필터링 상태
  const [filters, setFilters] = useState({
    search: '',
    status: 'all' as 'all' | 'waiting' | 'playing',
    showFull: true
  });

  const fetchRooms = async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      setRefreshing(!showLoading);
      
      const response = await apiEndpoints.gameRooms.list();
      setRooms(response.data || []);
      setError(null);
    } catch (error: any) {
      const errorMessage = '방 목록을 불러오지 못했습니다';
      setError(errorMessage);
      showToast.error(errorMessage);
      console.error('Failed to fetch rooms:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleJoinRoom = async (room: GameRoom) => {
    if (room.currentPlayers >= room.maxPlayers) {
      showToast.warning(`방이 가득 찼습니다 (${room.currentPlayers}/${room.maxPlayers}명)`);
      return;
    }

    if (room.status === 'playing') {
      showToast.warning('이미 게임이 진행 중인 방입니다');
      return;
    }

    try {
      await apiEndpoints.gameRooms.join(room.id);
      onJoinRoom(room.id);
      showToast.success(`${room.name} 방에 입장했습니다`);
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || '방 입장에 실패했습니다';
      showToast.error(errorMessage);
      console.error('Failed to join room:', error);
    }
  };

  useEffect(() => {
    fetchRooms();
    
    // 5초마다 방 목록 새로고침
    const interval = setInterval(() => {
      fetchRooms(false);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'waiting': return 'text-green-600 bg-green-100';
      case 'playing': return 'text-yellow-600 bg-yellow-100';
      case 'finished': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'waiting': return '대기중';
      case 'playing': return '게임중';
      case 'finished': return '완료';
      default: return '알 수 없음';
    }
  };

  // 필터링된 방 목록
  const filteredRooms = rooms.filter(room => {
    // 검색어 필터
    const searchMatch = !filters.search || 
      room.name.toLowerCase().includes(filters.search.toLowerCase()) ||
      (room as any).hostNickname?.toLowerCase().includes(filters.search.toLowerCase());
    
    // 상태 필터
    const statusMatch = filters.status === 'all' || room.status === filters.status;
    
    // 가득찬 방 필터
    const fullMatch = filters.showFull || room.currentPlayers < room.maxPlayers;
    
    return searchMatch && statusMatch && fullMatch;
  });

  if (isLoading && rooms.length === 0) {
    return (
      <Card>
        <Card.Body className="text-center py-12">
          <Loading size="lg" text="방 목록을 불러오는 중..." />
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card>
      <Card.Header>
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-semibold text-white">게임 방 목록</h2>
            <p className="text-white/70 text-sm mt-1">
              {user?.nickname}님, 게임 방을 선택하거나 새로 만드세요
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => fetchRooms()}
              disabled={refreshing}
              variant="secondary"
              size="sm"
            >
              {refreshing ? '새로고침 중...' : '🔄 새로고침'}
            </Button>
            <Button
              onClick={onCreateRoom}
              variant="primary"
              size="sm"
            >
              ➕ 방 만들기
            </Button>
          </div>
        </div>
        
        {/* 필터링 UI */}
        <div className="space-y-3 pt-4 border-t">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
            {/* 검색 */}
            <div className="flex-1">
              <input
                type="text"
                placeholder="방 이름 또는 호스트 검색..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              />
            </div>
            
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center min-w-0 sm:min-w-max">
              {/* 상태 필터 */}
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value as any }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="all">모든 방</option>
                <option value="waiting">대기중만</option>
                <option value="playing">게임중만</option>
              </select>
              
              {/* 가득찬 방 표시 */}
              <label className="flex items-center space-x-2 text-sm">
                <input
                  type="checkbox"
                  checked={filters.showFull}
                  onChange={(e) => setFilters(prev => ({ ...prev, showFull: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span>가득찬 방 표시</span>
              </label>
            </div>
          </div>
          
          <div className="flex justify-between items-center text-sm text-gray-600">
            <span>총 {filteredRooms.length}개의 방 (전체 {rooms.length}개)</span>
            {filters.search || filters.status !== 'all' || !filters.showFull ? (
              <button
                onClick={() => setFilters({ search: '', status: 'all', showFull: true })}
                className="text-blue-600 hover:text-blue-800 underline"
              >
                필터 초기화
              </button>
            ) : null}
          </div>
        </div>
      </Card.Header>

      <Card.Body>
        {rooms.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🎮</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              아직 생성된 방이 없습니다
            </h3>
            <p className="text-gray-600 mb-4">
              첫 번째 방을 만들어 게임을 시작해보세요!
            </p>
            <Button onClick={onCreateRoom} variant="primary">
              첫 방 만들기
            </Button>
          </div>
        ) : filteredRooms.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              검색 결과가 없습니다
            </h3>
            <p className="text-gray-600 mb-4">
              다른 검색 조건을 시도해보세요
            </p>
            <button
              onClick={() => setFilters({ search: '', status: 'all', showFull: true })}
              className="text-blue-600 hover:text-blue-800 underline"
            >
              필터 초기화
            </button>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {filteredRooms.map((room) => (
              <div
                key={room.id}
                className="border rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex justify-between items-start mb-3">
                  <h3 className="font-semibold text-base sm:text-lg truncate pr-2">{room.name}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium whitespace-nowrap ${getStatusColor(room.status)}`}>
                    {getStatusText(room.status)}
                  </span>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">플레이어</span>
                    <span className="font-medium">
                      {room.currentPlayers}/{room.maxPlayers}명
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">생성시간</span>
                    <span className="text-gray-700 text-xs sm:text-sm">
                      {new Date(room.createdAt).toLocaleTimeString('ko-KR', {
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </span>
                  </div>
                </div>

                {room.players && room.players.length > 0 && (
                  <div className="mb-4">
                    <div className="text-xs text-gray-600 mb-1">참가자:</div>
                    <div className="flex flex-wrap gap-1">
                      {room.players.slice(0, 3).map((player) => (
                        <span
                          key={player.id}
                          className="px-2 py-1 bg-gray-100 rounded text-xs truncate max-w-20"
                          title={player.nickname + (player.isHost ? ' (방장)' : '')}
                        >
                          {player.nickname}
                          {player.isHost && ' 👑'}
                        </span>
                      ))}
                      {room.players.length > 3 && (
                        <span className="px-2 py-1 bg-gray-200 rounded text-xs text-gray-600">
                          +{room.players.length - 3}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                <Button
                  onClick={() => handleJoinRoom(room)}
                  className="w-full"
                  variant={room.status === 'waiting' ? 'primary' : 'secondary'}
                  disabled={
                    room.status === 'playing' || 
                    room.currentPlayers >= room.maxPlayers
                  }
                >
                  {room.status === 'waiting' ? '참가하기' : 
                   room.status === 'playing' ? '게임중' : '참가불가'}
                </Button>
              </div>
            ))}
          </div>
        )}
      </Card.Body>
    </Card>
  );
};

export default GameRoomList;