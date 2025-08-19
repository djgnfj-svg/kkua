import React, { useState } from 'react';

const KickPlayerModal = ({ player, onConfirm, onCancel }) => {
  const [reason, setReason] = useState('');

  const handleConfirm = () => {
    onConfirm(reason.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleConfirm();
    } else if (e.key === 'Escape') {
      onCancel();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6">
        {/* 모달 헤더 */}
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-800">플레이어 강퇴</h2>
          <button
            onClick={onCancel}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* 플레이어 정보 */}
        <div className="mb-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 bg-gradient-to-br from-red-400 to-red-600 rounded-full flex items-center justify-center text-white text-lg font-bold">
              {player.nickname?.charAt(0)?.toUpperCase() || 'G'}
            </div>
            <div>
              <div className="font-semibold text-gray-800">
                {player.nickname || `Guest_${player.guest_id}`}
              </div>
              <div className="text-sm text-gray-600">ID: {player.guest_id}</div>
            </div>
          </div>
        </div>

        {/* 확인 메시지 */}
        <div className="mb-4">
          <p className="text-gray-700 mb-2">
            <strong>{player.nickname || `Guest_${player.guest_id}`}</strong>님을 강퇴하시겠습니까?
          </p>
          <p className="text-sm text-gray-500">
            강퇴당한 플레이어는 즉시 방에서 나가게 됩니다.
          </p>
        </div>

        {/* 강퇴 사유 입력 */}
        <div className="mb-6">
          <label htmlFor="kick-reason" className="block text-sm font-medium text-gray-700 mb-2">
            강퇴 사유 (선택사항)
          </label>
          <input
            id="kick-reason"
            type="text"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="강퇴 사유를 입력하세요"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500"
            maxLength={200}
            autoFocus
          />
          <div className="text-xs text-gray-500 mt-1">
            {reason.length}/200자
          </div>
        </div>

        {/* 버튼 */}
        <div className="flex space-x-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 font-semibold transition-colors duration-200"
          >
            취소
          </button>
          <button
            onClick={handleConfirm}
            className="flex-1 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 font-semibold transition-colors duration-200 shadow-md hover:shadow-lg"
          >
            강퇴하기
          </button>
        </div>
      </div>
    </div>
  );
};

export default KickPlayerModal;