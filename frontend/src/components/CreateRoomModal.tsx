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
      const response = await apiEndpoints.gameRooms.create(roomName.trim(), maxPlayers);
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
    setIsLoading(false);
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="새 게임 방 만들기" size="md">
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
          <label className="block text-sm font-medium text-gray-700 mb-2">
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
                    ? 'bg-primary-100 border-primary-500 text-primary-700'
                    : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {num}명
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            추천: 2-4명이 가장 재미있어요!
          </p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="font-medium text-blue-900 mb-2">🎯 게임 규칙</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• 한국어 끝말잇기 게임</li>
            <li>• 제한시간 30초 안에 단어 입력</li>
            <li>• 사전에 등록된 단어만 인정</li>
            <li>• 이미 사용된 단어는 사용 불가</li>
          </ul>
        </div>

        <div className="flex gap-3 pt-4">
          <Button
            type="button"
            onClick={handleClose}
            variant="secondary"
            className="flex-1"
            disabled={isLoading}
          >
            취소
          </Button>
          <Button
            type="submit"
            variant="primary"
            className="flex-1"
            loading={isLoading}
            disabled={!roomName.trim() || isLoading}
          >
            {isLoading ? '생성 중...' : '방 만들기'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};

export default CreateRoomModal;