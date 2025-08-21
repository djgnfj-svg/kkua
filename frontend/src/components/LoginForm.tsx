import React, { useState } from 'react';
import { Button, Input, Card } from './ui';
import { apiEndpoints } from '../utils/api';
import { useUserStore } from '../stores/useUserStore';
import { showToast } from './Toast';

interface LoginFormProps {
  onSuccess?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({ onSuccess }) => {
  const [nickname, setNickname] = useState('');
  const { setUser, setLoading, setError, isLoading } = useUserStore();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!nickname.trim()) {
      showToast.error('닉네임을 입력해주세요');
      return;
    }

    if (nickname.length < 2 || nickname.length > 12) {
      showToast.error('닉네임은 2-12자 사이여야 합니다');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiEndpoints.auth.loginGuest(nickname);
      const userData = response.data;
      
      setUser({
        id: userData.user_id || userData.id,
        nickname: userData.nickname,
        isGuest: true,
        sessionToken: userData.session_token
      });

      showToast.success(`환영합니다, ${nickname}님! 🎮`);
      onSuccess?.();
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          '로그인 중 오류가 발생했습니다';
      
      setError(errorMessage);
      showToast.error(errorMessage);
      console.error('Login error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full max-w-lg mx-auto" variant="glass" hover>
      <Card.Header>
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-3 font-korean">
            게임 시작
          </h2>
          <p className="text-white/70 font-korean">닉네임을 입력하고 게임에 참가하세요</p>
        </div>
      </Card.Header>

      <Card.Body>
        <form onSubmit={handleSubmit} className="space-y-6">
          <Input
            label="닉네임"
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="한글/영문 2-12자"
            maxLength={12}
            disabled={isLoading}
            autoFocus
            variant="glass"
            size="lg"
            icon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            }
          />
          
          <Button
            type="submit"
            variant="primary"
            size="xl"
            className="w-full mt-8"
            loading={isLoading}
            disabled={!nickname.trim() || isLoading}
            glow
          >
            {isLoading ? '로그인 중...' : '🎮 게임 시작하기'}
          </Button>
        </form>

        <div className="mt-8 text-center">
          <div className="inline-flex items-center justify-center space-x-6 text-sm text-white/70 bg-white/10 rounded-2xl px-6 py-4 backdrop-blur-sm border border-white/20">
            <div className="flex items-center space-x-2">
              <span className="text-lg">🎯</span>
              <span className="font-korean">멀티플레이어</span>
            </div>
            <div className="w-px h-4 bg-white/30"></div>
            <div className="flex items-center space-x-2">
              <span className="text-lg">⚡</span>
              <span className="font-korean">빠른 시작</span>
            </div>
            <div className="w-px h-4 bg-white/30"></div>
            <div className="flex items-center space-x-2">
              <span className="text-lg">🚀</span>
              <span className="font-korean">회원가입 없음</span>
            </div>
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default LoginForm;