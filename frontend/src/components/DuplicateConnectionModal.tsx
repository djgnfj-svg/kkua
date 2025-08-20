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
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-warning-100 rounded-full mb-6">
          <div className="text-3xl">⚠️</div>
        </div>
        
        <h3 className="text-xl font-bold text-secondary-900 mb-3 font-korean">
          중복 연결이 감지되었습니다
        </h3>
        
        <p className="text-secondary-600 mb-4 font-korean leading-relaxed">
          {message}
        </p>
        
        <p className="text-sm text-secondary-500 mb-8 font-korean">
          현재 탭에서 계속하시겠습니까? 기존 연결이 끊어집니다.
        </p>

        <div className="flex justify-center space-x-4">
          <Button 
            onClick={onCancel}
            variant="secondary"
            size="lg"
            className="px-8"
          >
            취소
          </Button>
          <Button 
            onClick={onContinue}
            variant="primary"
            size="lg"
            className="px-8"
            glow
          >
            현재 탭에서 계속
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default DuplicateConnectionModal;