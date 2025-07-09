import React, { useEffect, useState } from 'react';
import './Loading.css';
import { useNavigate } from 'react-router-dom';
import TutoModal from './Modal/TutoModal';
import { lobbyUrl } from '../../Component/urls';
import { useAuth } from '../../contexts/AuthContext';
import WelcomeSection from './components/WelcomeSection';

function Loading() {
  const [showModal, setShowModal] = useState(false);
  const [nickname, setNickname] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { isAuthenticated, login, loading } = useAuth();

  useEffect(() => {
    // 이미 로그인된 경우 로비로 리다이렉트
    if (isAuthenticated) {
      navigate(lobbyUrl);
    }
  }, [isAuthenticated, navigate]);

  const handleQuickStart = async () => {
    try {
      setIsLoading(true);
      await login(); // 닉네임 없이 로그인 (자동 생성)
      setShowModal(true);
    } catch (error) {
      console.error('빠른 시작 실패:', error);
      alert('로그인에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNicknameLogin = async () => {
    if (!nickname.trim()) {
      alert('닉네임을 입력해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      await login(nickname.trim());
      setShowModal(true);
    } catch (error) {
      console.error('닉네임 로그인 실패:', error);
      const errorMessage =
        error.response?.data?.detail || '로그인에 실패했습니다.';
      alert(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleModalClose = () => {
    setShowModal(false);
    navigate(lobbyUrl);
  };

  // 인증 상태 로딩 중
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="Loading">
      <WelcomeSection />

      <div className="mt-8 space-y-4">
        {/* 빠른 시작 버튼 */}
        <button
          onClick={handleQuickStart}
          disabled={isLoading}
          className="w-full py-3 px-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold rounded-lg transition-colors"
        >
          {isLoading ? '로그인 중...' : '빠른 시작'}
        </button>

        {/* 구분선 */}
        <div className="flex items-center">
          <div className="flex-grow border-t border-gray-300"></div>
          <span className="mx-4 text-gray-500">또는</span>
          <div className="flex-grow border-t border-gray-300"></div>
        </div>

        {/* 닉네임으로 시작 */}
        <div className="space-y-2">
          <input
            type="text"
            placeholder="닉네임을 입력하세요"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleNicknameLogin()}
            className="w-full py-2 px-4 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            maxLength={20}
            disabled={isLoading}
          />
          <button
            onClick={handleNicknameLogin}
            disabled={isLoading || !nickname.trim()}
            className="w-full py-3 px-6 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-bold rounded-lg transition-colors"
          >
            {isLoading ? '로그인 중...' : '닉네임으로 시작'}
          </button>
        </div>
      </div>

      {showModal && <TutoModal isOpen={showModal} onClose={handleModalClose} />}
    </div>
  );
}

export default Loading;
