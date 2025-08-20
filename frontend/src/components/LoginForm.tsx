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
    <Card className="w-full max-w-md mx-auto">
      <Card.Header>
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">끄아 게임 시작</h2>
          <p className="text-gray-600">닉네임을 입력하고 게임에 참가하세요</p>
        </div>
      </Card.Header>

      <Card.Body>
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="닉네임"
            type="text"
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="한글/영문 2-12자"
            maxLength={12}
            disabled={isLoading}
            autoFocus
          />
          
          <Button
            type="submit"
            variant="primary"
            size="lg"
            className="w-full"
            loading={isLoading}
            disabled={!nickname.trim() || isLoading}
          >
            {isLoading ? '로그인 중...' : '게임 시작하기'}
          </Button>
        </form>

        <div className="mt-6 text-center text-sm text-gray-500">
          <p>🎯 한국어 끝말잇기 멀티플레이어 게임</p>
          <p className="mt-1">별도 회원가입 없이 바로 시작!</p>
        </div>
      </Card.Body>
    </Card>
  );
};

export default LoginForm;