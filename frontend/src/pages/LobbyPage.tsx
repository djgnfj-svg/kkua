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
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-shimmer-gradient bg-gradient-radial opacity-5 animate-shimmer"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-primary-200 rounded-full opacity-10 animate-float transform translate-x-1/2 -translate-y-1/2"></div>
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-secondary-200 rounded-full opacity-15 animate-float transform -translate-x-1/2 translate-y-1/2" style={{ animationDelay: '2s' }}></div>
      
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md shadow-glass border-b border-white/20 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-600 rounded-xl flex items-center justify-center shadow-glow-sm">
                  <span className="text-white font-bold text-lg">끄</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-600 to-secondary-700 bg-clip-text text-transparent font-korean">
                    끄아 (KKUA)
                  </h1>
                  <span className="inline-flex items-center px-2 py-0.5 bg-primary-100 text-primary-700 text-xs font-semibold rounded-full">
                    BETA
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm text-secondary-600 bg-white/60 backdrop-blur-sm rounded-xl px-4 py-2 border border-white/30">
                <span className="font-semibold text-secondary-900 font-korean">{user?.nickname}</span>
                <span className="font-korean">님 환영합니다! 👋</span>
              </div>
              <Button
                onClick={handleLogout}
                variant="ghost"
                size="md"
              >
                로그아웃
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 relative z-10">
        <div className="mb-12 text-center animate-slide-up">
          <h2 className="text-4xl font-bold bg-gradient-to-r from-primary-600 to-secondary-700 bg-clip-text text-transparent mb-4 font-korean">
            🎮 게임 로비
          </h2>
          <p className="text-xl text-secondary-600 font-korean">
            친구들과 함께 한국어 끝말잇기를 즐겨보세요!
          </p>
          <div className="mt-4 w-24 h-1 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full mx-auto"></div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-scale-in" style={{ animationDelay: '0.2s' }}>
          <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-glass border border-white/30 p-6 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-primary-100 to-primary-200 text-primary-600 shadow-inner">
                <span className="text-2xl">🏠</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-secondary-600 font-korean">활성 방</p>
                <p className="text-3xl font-bold text-secondary-900">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-glass border border-white/30 p-6 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-success-100 to-success-200 text-success-600 shadow-inner">
                <span className="text-2xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-secondary-600 font-korean">온라인 플레이어</p>
                <p className="text-3xl font-bold text-secondary-900">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/80 backdrop-blur-md rounded-2xl shadow-glass border border-white/30 p-6 hover:scale-105 transition-transform duration-300">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-warning-100 to-warning-200 text-warning-600 shadow-inner">
                <span className="text-2xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-secondary-600 font-korean">진행중인 게임</p>
                <p className="text-3xl font-bold text-secondary-900">-</p>
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
        <div className="mt-12 bg-gradient-to-br from-primary-500 via-primary-600 to-secondary-600 rounded-3xl shadow-glow-lg text-white p-10 relative overflow-hidden animate-fade-in" style={{ animationDelay: '0.6s' }}>
          {/* Background decoration */}
          <div className="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full transform translate-x-1/2 -translate-y-1/2"></div>
          <div className="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full transform -translate-x-1/2 translate-y-1/2"></div>
          
          <div className="max-w-4xl relative z-10">
            <div className="flex items-center mb-6">
              <div className="w-12 h-12 bg-white/20 rounded-2xl flex items-center justify-center mr-4">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="text-3xl font-bold font-korean">빠른 시작 가이드</h3>
            </div>
            
            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-3">🎯</span>
                  <h4 className="text-xl font-semibold font-korean">게임 방법</h4>
                </div>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">방을 만들거나 기존 방에 참가</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">차례대로 끝말잇기 단어 입력</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">30초 안에 답해야 함</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">마지막까지 살아남으면 승리!</span>
                  </li>
                </ul>
              </div>
              
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 border border-white/20">
                <div className="flex items-center mb-4">
                  <span className="text-2xl mr-3">💡</span>
                  <h4 className="text-xl font-semibold font-korean">게임 팁</h4>
                </div>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">어려운 끝말자로 끝나는 단어 사용</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">사전에 등록된 단어만 인정</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">이미 사용된 단어는 재사용 불가</span>
                  </li>
                  <li className="flex items-center">
                    <span className="w-2 h-2 bg-white/60 rounded-full mr-3"></span>
                    <span className="font-korean">한방단어(ㄴ, ㄹ 등)는 즉시 승리!</span>
                  </li>
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