import React, { useState } from 'react';
import { Button, Input, Modal } from './ui';
import { apiEndpoints } from '../utils/api';
import { showToast } from './Toast';

interface CreateRoomModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (roomId: string) => void;
}

const CreateRoomModal: React.FC<CreateRoomModalProps> = ({
  isOpen,
  onClose,
  onSuccess
}) => {
  const [roomName, setRoomName] = useState('');
  const [maxPlayers, setMaxPlayers] = useState(4);
  const [password, setPassword] = useState('');
  const [isPrivate, setIsPrivate] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!roomName.trim()) {
      showToast.error('방 이름을 입력해주세요');
      return;
    }

    if (roomName.length < 2 || roomName.length > 20) {
      showToast.error('방 이름은 2-20자 사이여야 합니다');
      return;
    }

    if (maxPlayers < 2 || maxPlayers > 8) {
      showToast.error('플레이어 수는 2-8명 사이여야 합니다');
      return;
    }

    setIsLoading(true);

    try {
      const response = await apiEndpoints.gameRooms.create(
        roomName.trim(), 
        maxPlayers,
        password.trim() || null,
        isPrivate
      );
      const roomId = response.data.room_id || response.data.id;
      
      showToast.success(`${roomName} 방이 생성되었습니다! 🎉`);
      onSuccess(roomId);
      handleClose();
      
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          '방 생성에 실패했습니다';
      
      showToast.error(errorMessage);
      console.error('Failed to create room:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setRoomName('');
    setMaxPlayers(4);
    setPassword('');
    setIsPrivate(false);
    setShowPassword(false);
    setIsLoading(false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="🎮 새 게임 방 만들기" size="md">
      <form onSubmit={handleSubmit} className="space-y-6">
        <Input
          label="방 이름"
          type="text"
          value={roomName}
          onChange={(e) => setRoomName(e.target.value)}
          placeholder="예: 끄아 초보방, 빠른게임"
          maxLength={20}
          disabled={isLoading}
          autoFocus
        />

        <div>
          <label className="block text-sm font-medium text-white mb-2 font-korean">
            최대 플레이어 수
          </label>
          <div className="grid grid-cols-4 gap-2">
            {[2, 3, 4, 6].map((num) => (
              <button
                key={num}
                type="button"
                onClick={() => setMaxPlayers(num)}
                disabled={isLoading}
                className={`p-2 border rounded-lg text-center font-medium transition-colors ${
                  maxPlayers === num
                    ? 'bg-purple-600 border-purple-500 text-white'
                    : 'bg-white/10 border-white/30 text-white hover:bg-white/20'
                }`}
              >
                {num}명
              </button>
            ))}
          </div>
          <p className="text-xs text-white/60 mt-2 font-korean">
            추천: 2-4명이 가장 재미있어요!
          </p>
        </div>

        {/* 방 보안 설정 */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="block text-sm font-medium text-white font-korean">
              🔒 방 보안 설정
            </label>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-white/70 font-korean">비공개방</span>
              <button
                type="button"
                onClick={() => setIsPrivate(!isPrivate)}
                disabled={isLoading || password.length > 0}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 ${
                  isPrivate || password.length > 0 
                    ? 'bg-purple-600' 
                    : 'bg-white/20'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    isPrivate || password.length > 0 ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-white/90 font-korean">
              비밀번호 (선택사항)
            </label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  // 비밀번호가 있으면 자동으로 비공개방 설정
                  if (e.target.value.length > 0) {
                    setIsPrivate(true);
                  }
                }}
                placeholder="비밀번호를 설정하면 입장 시 필요합니다"
                className="w-full px-4 py-2 pr-12 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-white/50 text-sm backdrop-blur-sm font-korean"
                disabled={isLoading}
                maxLength={20}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-white/60 hover:text-white"
                disabled={isLoading}
              >
                {showPassword ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.878 9.878L3 3m6.878 6.878L21 21" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                  </svg>
                )}
              </button>
            </div>
            <p className="text-xs text-white/60 font-korean">
              {password.length > 0 
                ? `🔒 비밀번호 설정됨 - 비공개방으로 자동 전환` 
                : `공개방으로 설정하면 누구나 입장할 수 있습니다`
              }
            </p>
          </div>
        </div>

        <div className="bg-gradient-to-r from-purple-500/20 to-pink-500/20 backdrop-blur-sm border border-purple-400/30 rounded-xl p-4">
          <div className="flex items-center mb-3">
            <span className="text-2xl mr-2">🎯</span>
            <h4 className="font-semibold text-white font-korean">게임 규칙</h4>
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm text-white/90">
            <div className="flex items-center space-x-2">
              <span>✅</span>
              <span className="font-korean">한국어 끝말잇기</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>⏱️</span>
              <span className="font-korean">30초 제한시간</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>📚</span>
              <span className="font-korean">사전 등록 단어</span>
            </div>
            <div className="flex items-center space-x-2">
              <span>🙅</span>
              <span className="font-korean">단어 중복 금지</span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 pt-6">
          <Button
            type="button"
            onClick={handleClose}
            variant="secondary"
            className="flex-1 py-3"
            disabled={isLoading}
          >
            취소
          </Button>
          <Button
            type="submit"
            variant="primary"
            className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700 font-korean"
            loading={isLoading}
            disabled={!roomName.trim() || isLoading}
          >
            {isLoading ? '🔄 생성 중...' : '🎉 방 만들기'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default CreateRoomModal;