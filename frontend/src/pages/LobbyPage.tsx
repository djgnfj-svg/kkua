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
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 relative z-10">
        <div className="mb-8 text-center animate-slide-up">
          <h2 className="text-3xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent mb-2 font-korean">
            🎮 게임 로비
          </h2>
          <p className="text-lg text-white/80 font-korean">
            방을 만들거나 참가해서 끝말잇기를 시작하세요!
          </p>
        </div>

        {/* 빠른 시작 버튼 */}
        <div className="mb-8 text-center">
          <Button
            onClick={handleCreateRoom}
            variant="primary"
            size="lg"
            className="bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 text-white text-lg px-8 py-4 rounded-2xl shadow-xl shadow-purple-500/25 transform hover:scale-105 transition-all duration-300 font-korean"
          >
            ➕ 새 게임 방 만들기
          </Button>
          <p className="mt-2 text-white/60 text-sm font-korean">가장 빠른 시작 방법!</p>
        </div>

        {/* 게임 방법 간단 안내 */}
        <div className="mb-8 bg-white/10 backdrop-blur-sm rounded-2xl border border-white/20 p-6 text-center">
          <h3 className="text-lg font-semibold text-white mb-3 font-korean">🎯 게임 방법</h3>
          <div className="flex flex-wrap justify-center gap-4 text-sm text-white/80">
            <span className="bg-white/10 px-3 py-1 rounded-full font-korean">1️⃣ 방 참가</span>
            <span className="bg-white/10 px-3 py-1 rounded-full font-korean">2️⃣ 끝말잇기</span>
            <span className="bg-white/10 px-3 py-1 rounded-full font-korean">3️⃣ 30초 제한</span>
            <span className="bg-white/10 px-3 py-1 rounded-full font-korean">4️⃣ 최후 1인</span>
          </div>
        </div>


        {/* Game Room List */}
        <GameRoomList
          onJoinRoom={handleJoinRoom}
          onCreateRoom={handleCreateRoom}
        />

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