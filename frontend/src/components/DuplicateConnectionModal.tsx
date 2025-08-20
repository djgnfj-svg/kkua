import React from 'react';
import { Button, Modal } from './ui';

interface DuplicateConnectionModalProps {
  isOpen: boolean;
  onContinue: () => void;
  onCancel: () => void;
  message?: string;
}

export const DuplicateConnectionModal: React.FC<DuplicateConnectionModalProps> = ({
  isOpen,
  onContinue,
  onCancel,
  message = "다른 탭에서 이미 게임에 참여 중입니다."
}) => {
  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onCancel} title="중복 연결 감지">
      <div className="p-6">
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            중복 연결이 감지되었습니다
          </h3>
          <p className="text-gray-600 mb-4">
            {message}
          </p>
          <p className="text-sm text-gray-500">
            현재 탭에서 계속하시겠습니까? 기존 연결이 끊어집니다.
          </p>
        </div>

        <div className="flex justify-center space-x-3">
          <Button 
            onClick={onCancel}
            variant="secondary"
            className="px-6"
          >
            취소
          </Button>
          <Button 
            onClick={onContinue}
            variant="primary"
            className="px-6"
          >
            현재 탭에서 계속
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DuplicateConnectionModal;