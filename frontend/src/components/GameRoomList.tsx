import React, { useEffect, useState } from 'react';
import { Button, Loading } from './ui';
import { apiEndpoints } from '../utils/api';
import { useGameStore } from '../stores/useGameStore';
import type { GameRoom } from '../types/game';
import { showToast } from './Toast';

interface GameRoomListProps {
  onJoinRoom: (roomId: string) => void;
  onCreateRoom: () => void;
}

const GameRoomList: React.FC<GameRoomListProps> = ({ onJoinRoom, onCreateRoom }) => {
  const { rooms, setRooms, isLoading, setLoading, setError } = useGameStore();
  const [refreshing, setRefreshing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState<{isOpen: boolean, roomId: string, roomName: string}>({
    isOpen: false,
    roomId: '',
    roomName: ''
  });
  const [passwordInput, setPasswordInput] = useState('');
  
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
      console.log('API 응답 전체:', response);
      console.log('방 목록 데이터:', response.data);
      
      // axios는 response.data에 실제 데이터를 담아서 반환
      const roomData = response.data || [];
      console.log('방 목록 업데이트:', roomData.length, '개 방');
      if (roomData.length > 0) {
        console.log('방 목록 상세:', roomData.map((room: any) => `${room.name}: ${room.currentPlayers}/${room.maxPlayers}`));
      }
      setRooms(roomData);
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

    // 비밀방인 경우 비밀번호 모달 표시
    if ((room as any).hasPassword || (room as any).isPrivate) {
      setShowPasswordModal({
        isOpen: true,
        roomId: room.id,
        roomName: room.name
      });
      return;
    }

    // 공개방인 경우 바로 입장
    await joinRoomWithPassword(room.id, room.name);
  };

  const joinRoomWithPassword = async (roomId: string, roomName: string, password?: string) => {
    try {
      await apiEndpoints.gameRooms.join(roomId, password);
      onJoinRoom(roomId);
      
      // 비밀번호 모달 닫기
      setShowPasswordModal({ isOpen: false, roomId: '', roomName: '' });
      setPasswordInput('');
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
      case 'waiting': return 'text-green-300 bg-green-500/20 border border-green-400/30';
      case 'playing': return 'text-yellow-300 bg-yellow-500/20 border border-yellow-400/30';
      case 'finished': return 'text-white/60 bg-white/10 border border-white/20';
      default: return 'text-white/60 bg-white/10 border border-white/20';
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
      <div className="text-center py-16 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
        <div className="text-6xl mb-4 animate-bounce">🔍</div>
        <Loading size="lg" text="게임 방을 찾고 있어요..." />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-white font-korean">🏠 게임 방 목록</h2>
          <p className="text-white/70 mt-1 font-korean">
            마음에 드는 방을 선택하세요
          </p>
        </div>
        <Button
          onClick={() => fetchRooms()}
          disabled={refreshing}
          variant="glass"
          size="sm"
          className="text-white border-white/30 hover:bg-white/20"
        >
          {refreshing ? '⏳' : '🔄'}
        </Button>
      </div>

      {/* 간단한 검색 */}
      {rooms.length > 3 && (
        <div className="mb-4">
          <input
            type="text"
            placeholder="🔍 방 이름 검색..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="w-full px-4 py-3 bg-white/10 backdrop-blur-sm border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-white/50 font-korean"
          />
        </div>
      )}
      
      <div>
        {rooms.length === 0 ? (
          <div className="text-center py-16 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
            <div className="text-8xl mb-6">🎮</div>
            <h3 className="text-2xl font-bold text-white mb-4 font-korean">
              첫 번째 방을 만들어보세요!
            </h3>
            <p className="text-white/70 mb-6 font-korean text-lg">
              친구들과 함께 끝말잇기를 즐겨보세요
            </p>
            <Button 
              onClick={onCreateRoom} 
              variant="primary"
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-pink-600 text-white px-8 py-4 text-lg rounded-2xl shadow-xl font-korean"
            >
              ✨ 첫 방 만들기
            </Button>
          </div>
        ) : filteredRooms.length === 0 ? (
          <div className="text-center py-12 bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10">
            <div className="text-6xl mb-4">🔍</div>
            <h3 className="text-lg font-semibold text-white mb-2 font-korean">
              검색 결과가 없습니다
            </h3>
            <p className="text-white/60 mb-4 font-korean">
              다른 검색어를 시도해보세요
            </p>
            <Button
              onClick={() => setFilters({ search: '', status: 'all', showFull: true })}
              variant="secondary"
              className="text-white"
            >
              전체 보기
            </Button>
          </div>
        ) : (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {filteredRooms.map((room) => {
              const isJoinable = room.status === 'waiting' && room.currentPlayers < room.maxPlayers;
              const isFull = room.currentPlayers >= room.maxPlayers;
              const isPlaying = room.status === 'playing';
              
              return (
                <div
                  key={room.id}
                  className={`bg-white/10 backdrop-blur-sm border border-white/20 rounded-2xl p-6 transition-all duration-300 ${
                    isJoinable ? 'hover:bg-white/20 hover:shadow-2xl hover:scale-105 cursor-pointer' : 'opacity-75'
                  }`}
                  onClick={isJoinable ? () => handleJoinRoom(room) : undefined}
                >
                  {/* 방 헤더 */}
                  <div className="flex justify-between items-start mb-4">
                    <div className="flex items-center space-x-2 flex-1 min-w-0">
                      <h3 className="font-bold text-xl text-white font-korean truncate max-w-[200px]" title={room.name}>
                        {room.name}
                      </h3>
                      {((room as any).hasPassword || (room as any).isPrivate) && (
                        <span className="text-yellow-400 flex-shrink-0" title="비밀방">🔒</span>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm font-semibold flex-shrink-0 ${getStatusColor(room.status)}`}>
                      {getStatusText(room.status)}
                    </span>
                  </div>

                  {/* 플레이어 정보 */}
                  <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-white/70 font-korean text-sm">플레이어</span>
                      <div className="flex items-center space-x-2">
                        <span className={`text-lg font-bold ${
                          isFull ? 'text-red-400' : isJoinable ? 'text-green-400' : 'text-white'
                        } font-korean`}>
                          {room.currentPlayers}/{room.maxPlayers}
                        </span>
                        <span className="text-white/60">👥</span>
                      </div>
                    </div>
                    
                      {/* 플레이어 현황 막대 */}
                    <div className="w-full bg-white/10 rounded-full h-2 overflow-hidden">
                      <div 
                        className={`h-full transition-all duration-500 ${
                          isFull ? 'bg-red-400' : isJoinable ? 'bg-green-400' : 'bg-yellow-400'
                        }`}
                        style={{ width: `${(room.currentPlayers / room.maxPlayers) * 100}%` }}
                      />
                    </div>
                  </div>

                  {/* 액션 버튼 */}
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleJoinRoom(room);
                    }}
                    className="w-full h-12 text-lg font-semibold"
                    variant={isJoinable ? 'primary' : 'secondary'}
                    disabled={!isJoinable}
                  >
                    {isJoinable ? (
                      <span className="flex items-center justify-center space-x-2">
                        <span>🚀</span>
                        <span className="font-korean">바로 참가</span>
                      </span>
                    ) : isFull ? (
                      <span className="flex items-center justify-center space-x-2">
                        <span>😞</span>
                        <span className="font-korean">방이 가득참</span>
                      </span>
                    ) : isPlaying ? (
                      <span className="flex items-center justify-center space-x-2">
                        <span>🎮</span>
                        <span className="font-korean">게임 진행중</span>
                      </span>
                    ) : (
                      <span className="font-korean">참가 불가</span>
                    )}
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </div>
      
      {/* 비밀번호 입력 모달 */}
      {showPasswordModal.isOpen && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-gray-900/95 backdrop-blur-md border border-white/20 rounded-2xl p-8 w-full max-w-md shadow-2xl">
            <h3 className="text-2xl font-bold text-white mb-4 font-korean text-center">
              🔒 비밀방 입장
            </h3>
            <p className="text-white/80 mb-6 font-korean text-center">
              "<span className="font-semibold text-purple-300">{showPasswordModal.roomName}</span>" 방의 비밀번호를 입력하세요
            </p>
            
            <form onSubmit={(e) => {
              e.preventDefault();
              if (passwordInput.trim()) {
                joinRoomWithPassword(showPasswordModal.roomId, showPasswordModal.roomName, passwordInput.trim());
              }
            }}>
              <div className="mb-6">
                <input
                  type="password"
                  value={passwordInput}
                  onChange={(e) => setPasswordInput(e.target.value)}
                  placeholder="비밀번호 입력"
                  className="w-full px-4 py-4 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-white/50 backdrop-blur-sm font-korean text-center text-lg"
                  autoFocus
                  maxLength={20}
                />
              </div>
              
              <div className="flex gap-3">
                <Button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal({ isOpen: false, roomId: '', roomName: '' });
                    setPasswordInput('');
                  }}
                  variant="secondary"
                  className="flex-1 py-3 font-korean"
                >
                  취소
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  className="flex-1 py-3 font-korean bg-gradient-to-r from-purple-600 to-pink-600"
                  disabled={!passwordInput.trim()}
                >
                  🚀 입장하기
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GameRoomList;