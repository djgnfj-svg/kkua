import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const ActionButtons = ({ roomId }) => {
  const navigate = useNavigate();
  const [isSharing, setIsSharing] = useState(false);
  const [shareSuccess, setShareSuccess] = useState(false);

  const handlePlayAgain = () => {
    // 같은 방에서 다시 플레이
    navigate(`/gamelobby/${roomId}`);
  };

  const handleGoToLobby = () => {
    // 메인 로비로 이동
    navigate('/lobby');
  };

  const handleGoHome = () => {
    // 홈으로 이동
    navigate('/');
  };

  const handleShare = async () => {
    setIsSharing(true);
    
    try {
      // 결과 공유 기능 (Web Share API 또는 클립보드 복사)
      const shareData = {
        title: '끄아 게임 결과',
        text: `방 #${roomId}에서 끝말잇기 게임을 플레이했습니다! 🎮`,
        url: window.location.href
      };

      if (navigator.share && navigator.canShare(shareData)) {
        await navigator.share(shareData);
        setShareSuccess(true);
      } else {
        // 클립보드에 복사
        await navigator.clipboard.writeText(`끄아 게임 결과: ${window.location.href}`);
        setShareSuccess(true);
      }
    } catch (error) {
      console.error('공유 실패:', error);
    } finally {
      setIsSharing(false);
      if (shareSuccess) {
        setTimeout(() => setShareSuccess(false), 3000);
      }
    }
  };

  const handleDownloadResult = () => {
    // 게임 결과를 이미지나 PDF로 다운로드하는 기능 (추후 구현)
    alert('결과 다운로드 기능은 곧 추가될 예정입니다! 📄');
  };

  return (
    <div className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-lg p-6">
      <h3 className="text-xl font-bold text-gray-800 mb-6 text-center">
        🎮 게임이 끝났습니다! 무엇을 하시겠어요?
      </h3>

      {/* 주요 액션 버튼들 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <button
          onClick={handlePlayAgain}
          className="flex items-center justify-center space-x-3 p-4 bg-gradient-to-r from-purple-500 to-blue-500 text-white rounded-xl hover:from-purple-600 hover:to-blue-600 transform hover:scale-105 transition-all duration-200 shadow-lg"
        >
          <span className="text-2xl">🔄</span>
          <div className="text-left">
            <div className="font-bold">다시 플레이</div>
            <div className="text-sm opacity-90">같은 방에서 한 게임 더</div>
          </div>
        </button>

        <button
          onClick={handleGoToLobby}
          className="flex items-center justify-center space-x-3 p-4 bg-gradient-to-r from-green-500 to-teal-500 text-white rounded-xl hover:from-green-600 hover:to-teal-600 transform hover:scale-105 transition-all duration-200 shadow-lg"
        >
          <span className="text-2xl">🏠</span>
          <div className="text-left">
            <div className="font-bold">로비로 이동</div>
            <div className="text-sm opacity-90">다른 방 찾아보기</div>
          </div>
        </button>
      </div>

      {/* 보조 액션 버튼들 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <button
          onClick={handleShare}
          disabled={isSharing}
          className="flex flex-col items-center justify-center p-3 bg-blue-50 text-blue-700 rounded-lg hover:bg-blue-100 transition-colors border border-blue-200 disabled:opacity-50"
        >
          <span className="text-xl mb-1">
            {isSharing ? '📤' : shareSuccess ? '✅' : '📱'}
          </span>
          <span className="text-xs font-medium">
            {isSharing ? '공유중...' : shareSuccess ? '완료!' : '결과 공유'}
          </span>
        </button>

        <button
          onClick={handleDownloadResult}
          className="flex flex-col items-center justify-center p-3 bg-green-50 text-green-700 rounded-lg hover:bg-green-100 transition-colors border border-green-200"
        >
          <span className="text-xl mb-1">📄</span>
          <span className="text-xs font-medium">결과 저장</span>
        </button>

        <button
          onClick={() => window.location.reload()}
          className="flex flex-col items-center justify-center p-3 bg-yellow-50 text-yellow-700 rounded-lg hover:bg-yellow-100 transition-colors border border-yellow-200"
        >
          <span className="text-xl mb-1">🔄</span>
          <span className="text-xs font-medium">새로고침</span>
        </button>

        <button
          onClick={handleGoHome}
          className="flex flex-col items-center justify-center p-3 bg-gray-50 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors border border-gray-200"
        >
          <span className="text-xl mb-1">🏡</span>
          <span className="text-xs font-medium">홈으로</span>
        </button>
      </div>

      {/* 피드백 섹션 */}
      <div className="mt-6 pt-4 border-t border-gray-200 text-center">
        <div className="text-sm text-gray-600 mb-3">
          게임이 어떠셨나요? 피드백을 남겨주세요! 😊
        </div>
        
        <div className="flex justify-center space-x-2">
          {['😍', '😊', '😐', '😕', '😞'].map((emoji, index) => (
            <button
              key={index}
              className="text-2xl p-2 rounded-full hover:bg-gray-100 transition-colors"
              onClick={() => {
                // 피드백 수집 로직 (추후 구현)
                alert(`피드백 감사합니다! ${emoji}`);
              }}
            >
              {emoji}
            </button>
          ))}
        </div>
      </div>

      {/* 소셜 공유 버튼들 (선택사항) */}
      <div className="mt-4 flex justify-center space-x-3">
        <button
          onClick={() => {
            const text = `끄아에서 끝말잇기 게임을 플레이했어요! 방 #${roomId}`;
            const url = `https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(window.location.href)}`;
            window.open(url, '_blank');
          }}
          className="p-2 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
          title="트위터에 공유"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
          </svg>
        </button>

        <button
          onClick={() => {
            const url = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(window.location.href)}`;
            window.open(url, '_blank');
          }}
          className="p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors"
          title="페이스북에 공유"
        >
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
          </svg>
        </button>
      </div>

      {/* 공유 성공 메시지 */}
      {shareSuccess && (
        <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg text-center">
          <div className="text-green-700 text-sm font-medium">
            ✅ 결과가 성공적으로 공유되었습니다!
          </div>
        </div>
      )}
    </div>
  );
};

export default ActionButtons;