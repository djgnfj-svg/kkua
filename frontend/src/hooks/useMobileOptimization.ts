import { useEffect, useCallback, useState } from 'react';

export const useMobileOptimization = () => {
  const [isKeyboardOpen, setIsKeyboardOpen] = useState(false);
  const [orientation, setOrientation] = useState<'portrait' | 'landscape'>('portrait');

  // 가상 키보드 감지
  useEffect(() => {
    const handleResize = () => {
      const heightDiff = window.screen.height - window.innerHeight;
      setIsKeyboardOpen(heightDiff > 150); // 150px 이상 차이면 키보드 열림
    };

    const handleOrientationChange = () => {
      setOrientation(window.innerHeight > window.innerWidth ? 'portrait' : 'landscape');
    };

    window.addEventListener('resize', handleResize);
    window.addEventListener('orientationchange', handleOrientationChange);
    
    // 초기값 설정
    handleResize();
    handleOrientationChange();

    return () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('orientationchange', handleOrientationChange);
    };
  }, []);

  // 입력 필드 포커스 시 뷰포트 조정
  const handleInputFocus = useCallback((element: HTMLInputElement) => {
    setTimeout(() => {
      element.scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
      });
    }, 300); // 키보드 애니메이션 대기
  }, []);

  // 터치 이벤트 최적화
  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    // iOS Safari에서 더블탭 줌 방지
    if (e.touches.length > 1) {
      e.preventDefault();
    }
  }, []);

  return {
    isKeyboardOpen,
    orientation,
    handleInputFocus,
    handleTouchStart,
    isMobile: /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
  };
};