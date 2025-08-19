import React, { useEffect, useState } from 'react';
import './Loading.css';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../../contexts/ToastContext';
import TutoModal from './Modal/TutoModal';
import { lobbyUrl } from '../../utils/urls';
import { useAuth } from '../../contexts/AuthContext';

function Loading() {
  const [showModal, setShowModal] = useState(false);
  const [nickname, setNickname] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();
  const { isAuthenticated, login, loading } = useAuth();
  const toast = useToast();

  useEffect(() => {
    // AuthContext에서 이미 스마트 리다이렉트를 처리하므로 
    // 여기서는 추가 리다이렉트 로직을 제거
    // 사용자가 직접 루트 경로로 접근했을 때만 Loading 페이지 표시
  }, []);

  const handleQuickStart = async () => {
    try {
      setIsLoading(true);
      await login();
      // login 함수에서 자동으로 적절한 페이지로 리다이렉트됨
      setIsLoading(false);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '로그인에 실패했습니다.';
      toast.showError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleNicknameLogin = async () => {
    if (!nickname.trim()) {
      toast.showWarning('닉네임을 입력해주세요.');
      return;
    }

    try {
      setIsLoading(true);
      await login(nickname.trim());
      // login 함수에서 자동으로 적절한 페이지로 리다이렉트됨
      setIsLoading(false);
    } catch (error) {
      const errorMessage = error.response?.data?.detail || '로그인에 실패했습니다.';
      toast.showError(errorMessage);
      setIsLoading(false);
    }
  };

  const handleModalClose = () => {
    setShowModal(false);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-lg font-medium">
            게임을 불러오는 중...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        <div className="text-center mb-10">
          <div className="bg-white rounded-full w-24 h-24 mx-auto mb-6 flex items-center justify-center shadow-2xl">
            <img
              src="/imgs/logo/kkeua_logo.png"
              alt="끄아 로고"
              className="w-16 h-16 object-contain"
            />
          </div>
          <h1 className="text-5xl font-bold text-white mb-2 tracking-wide">
            끄아
          </h1>
          <p className="text-xl text-purple-200 font-medium">
            실시간 끝말잇기 게임
          </p>
          <div className="mt-4 flex justify-center space-x-2">
            <div className="w-2 h-2 bg-purple-400 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse delay-75"></div>
            <div className="w-2 h-2 bg-indigo-400 rounded-full animate-pulse delay-150"></div>
          </div>
        </div>

        <div className="bg-white/10 backdrop-blur-md rounded-2xl p-8 shadow-2xl border border-white/20">
          <div className="space-y-6">
            <button
              onClick={handleQuickStart}
              disabled={isLoading}
              className="w-full py-4 px-6 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100 shadow-lg"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                  게임 시작 중...
                </div>
              ) : (
                <div className="flex items-center justify-center">
                  <svg
                    className="w-5 h-5 mr-3"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 10V3L4 14h7v7l9-11h-7z"
                    />
                  </svg>
                  빠른 시작
                </div>
              )}
            </button>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-white/20"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-4 bg-white/10 text-white/80 rounded-full">
                  또는
                </span>
              </div>
            </div>

            <div className="space-y-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="닉네임을 입력하세요"
                  value={nickname}
                  onChange={(e) => setNickname(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleNicknameLogin()}
                  className="w-full py-4 px-6 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-400 focus:border-transparent text-white placeholder-white/60 transition-all duration-200"
                  maxLength={20}
                  disabled={isLoading}
                />
                <div className="absolute right-4 top-1/2 transform -translate-y-1/2">
                  <svg
                    className="w-5 h-5 text-white/60"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                </div>
              </div>

              <button
                onClick={handleNicknameLogin}
                disabled={isLoading || !nickname.trim()}
                className="w-full py-4 px-6 bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 disabled:from-gray-400 disabled:to-gray-500 text-white font-bold rounded-xl transition-all duration-200 transform hover:scale-105 disabled:scale-100 shadow-lg"
              >
                {isLoading ? (
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent mr-3"></div>
                    로그인 중...
                  </div>
                ) : (
                  <div className="flex items-center justify-center">
                    <svg
                      className="w-5 h-5 mr-3"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"
                      />
                    </svg>
                    게임 시작
                  </div>
                )}
              </button>
            </div>
          </div>

          <div className="mt-8 text-center">
            <p className="text-white/60 text-sm">
              친구들과 함께 즐기는 실시간 끝말잇기
            </p>
            <div className="mt-4 flex justify-center space-x-4 text-white/40 text-xs">
              <span>🎮 실시간 멀티플레이</span>
              <span>⚡ 빠른 매칭</span>
              <span>🏆 랭킹 시스템</span>
            </div>
          </div>
        </div>

        <div className="text-center mt-8">
          <p className="text-white/40 text-sm">KKUA v1.0.0 | Made with ❤️</p>
        </div>
      </div>

      {showModal && <TutoModal isOpen={showModal} onClose={handleModalClose} />}
    </div>
  );
}

export default Loading;
