import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui';
import { useUserStore } from '../stores/useUserStore';
import GameRoomList from '../components/GameRoomList';
import CreateRoomModal from '../components/CreateRoomModal';
import { showToast } from '../components/Toast';

const LobbyPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useUserStore();
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const handleLogout = () => {
    logout();
    localStorage.removeItem('kkua-current-room'); // 방 상태도 정리
    showToast.info('로그아웃되었습니다');
    navigate('/login');
  };

  const handleCreateRoom = () => {
    setIsCreateModalOpen(true);
  };

  const handleRoomCreated = (roomId: string) => {
    setIsCreateModalOpen(false);
    navigate(`/room/${roomId}`);
  };

  const handleJoinRoom = (roomId: string) => {
    navigate(`/room/${roomId}`);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-primary-600">끄아 (KKUA)</h1>
              <span className="ml-2 px-2 py-1 bg-primary-100 text-primary-700 text-xs rounded-full">
                BETA
              </span>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium text-gray-900">{user?.nickname}</span>님 환영합니다!
              </div>
              <Button
                onClick={handleLogout}
                variant="secondary"
                size="sm"
              >
                로그아웃
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            🎮 게임 로비
          </h2>
          <p className="text-gray-600">
            친구들과 함께 한국어 끝말잇기를 즐겨보세요!
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-primary-100 text-primary-600">
                🏠
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">활성 방</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100 text-green-600">
                👥
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">온라인 플레이어</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100 text-yellow-600">
                🎯
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">진행중인 게임</p>
                <p className="text-2xl font-semibold text-gray-900">-</p>
              </div>
            </div>
          </div>
        </div>

        {/* Game Room List */}
        <GameRoomList
          onJoinRoom={handleJoinRoom}
          onCreateRoom={handleCreateRoom}
        />

        {/* Quick Start Section */}
        <div className="mt-8 bg-gradient-to-r from-primary-500 to-blue-600 rounded-lg shadow-lg text-white p-8">
          <div className="max-w-3xl">
            <h3 className="text-2xl font-bold mb-4">🚀 빠른 시작 가이드</h3>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">🎯 게임 방법</h4>
                <ul className="space-y-1 text-sm opacity-90">
                  <li>• 방을 만들거나 기존 방에 참가</li>
                  <li>• 차례대로 끝말잇기 단어 입력</li>
                  <li>• 30초 안에 답해야 함</li>
                  <li>• 마지막까지 살아남으면 승리!</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">💡 게임 팁</h4>
                <ul className="space-y-1 text-sm opacity-90">
                  <li>• 어려운 끝말자로 끝나는 단어 사용</li>
                  <li>• 사전에 등록된 단어만 인정</li>
                  <li>• 이미 사용된 단어는 재사용 불가</li>
                  <li>• 한방단어(ㄴ, ㄹ 등)는 즉시 승리!</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* Create Room Modal */}
      <CreateRoomModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleRoomCreated}
      />
    </div>
  );
};

export default LobbyPage;