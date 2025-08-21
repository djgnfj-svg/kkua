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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Background effects */}
      <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-white/5 to-transparent"></div>
      <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-3xl animate-pulse transform translate-x-1/3 -translate-y-1/3"></div>
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-gradient-to-tr from-blue-500/20 to-purple-500/20 rounded-full blur-3xl animate-pulse transform -translate-x-1/3 translate-y-1/3" style={{ animationDelay: '2s' }}></div>
      
      {/* Header */}
      <header className="relative z-10 bg-white/10 backdrop-blur-md border-b border-white/20 shadow-2xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-2xl flex items-center justify-center shadow-xl shadow-purple-500/25">
                  <span className="text-white font-bold text-xl">끄</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent font-korean">
                    끄아 (KKUA)
                  </h1>
                  <span className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-purple-200 text-xs font-semibold rounded-full border border-purple-400/30">
                    BETA
                  </span>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="text-sm bg-white/10 backdrop-blur-sm rounded-xl px-4 py-2 border border-white/20">
                <span className="font-semibold text-white font-korean">{user?.nickname}</span>
                <span className="text-white/80 font-korean">님 환영합니다! 👋</span>
              </div>
              <Button
                onClick={handleLogout}
                variant="glass"
                size="md"
                className="text-white border-white/30 hover:bg-white/20"
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
          <h2 className="text-4xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent mb-4 font-korean">
            🎮 게임 로비
          </h2>
          <p className="text-xl text-white/80 font-korean">
            친구들과 함께 한국어 끝말잇기를 즐겨보세요!
          </p>
          <div className="mt-4 w-24 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto shadow-lg shadow-purple-500/50"></div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12 animate-scale-in" style={{ animationDelay: '0.2s' }}>
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6 hover:scale-105 transition-all duration-300 hover:bg-white/20">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-purple-500/20 to-purple-600/20 text-purple-300 shadow-inner border border-purple-400/30">
                <span className="text-2xl">🏠</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-white/70 font-korean">활성 방</p>
                <p className="text-3xl font-bold text-white">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6 hover:scale-105 transition-all duration-300 hover:bg-white/20">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-green-500/20 to-green-600/20 text-green-300 shadow-inner border border-green-400/30">
                <span className="text-2xl">👥</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-white/70 font-korean">온라인 플레이어</p>
                <p className="text-3xl font-bold text-white">-</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/10 backdrop-blur-md rounded-2xl border border-white/20 shadow-xl p-6 hover:scale-105 transition-all duration-300 hover:bg-white/20">
            <div className="flex items-center">
              <div className="p-4 rounded-2xl bg-gradient-to-br from-orange-500/20 to-orange-600/20 text-orange-300 shadow-inner border border-orange-400/30">
                <span className="text-2xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-semibold text-white/70 font-korean">진행중인 게임</p>
                <p className="text-3xl font-bold text-white">-</p>
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