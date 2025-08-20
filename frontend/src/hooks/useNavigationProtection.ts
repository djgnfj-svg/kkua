import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { showToast } from '../components/Toast';

interface NavigationProtectionOptions {
  when: boolean; // 보호 활성화 조건
  message?: string; // 사용자에게 보여줄 메시지
  onNavigationBlocked?: () => void; // 내비게이션이 차단되었을 때 콜백
  onBeforeUnload?: () => void; // 페이지 언로드 전 콜백
}

export const useNavigationProtection = ({
  when,
  message = '게임이 진행 중입니다. 정말 나가시겠습니까?',
  onNavigationBlocked,
  onBeforeUnload
}: NavigationProtectionOptions) => {
  const navigate = useNavigate();
  const blockerRef = useRef<(() => void) | null>(null);
  const isBlockingRef = useRef(false);

  useEffect(() => {
    if (!when) {
      // 보호 비활성화
      if (blockerRef.current) {
        blockerRef.current();
        blockerRef.current = null;
      }
      isBlockingRef.current = false;
      return;
    }

    isBlockingRef.current = true;

    // 1. beforeunload 이벤트 - 새로고침, 탭 닫기, 외부 사이트 이동 방지
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (when) {
        e.preventDefault();
        e.returnValue = message;
        onBeforeUnload?.();
        return message;
      }
    };

    // 2. popstate 이벤트 - 브라우저 뒤로가기/앞으로가기 방지
    const handlePopState = (e: PopStateEvent) => {
      if (when) {
        e.preventDefault();
        
        // 현재 URL을 다시 푸시하여 뒤로가기를 무효화
        window.history.pushState(null, '', window.location.href);
        
        showToast.warning(message);
        onNavigationBlocked?.();
      }
    };

    // 3. 페이지 로드 시 history state 설정
    const setupHistoryProtection = () => {
      // 현재 상태를 히스토리에 푸시
      window.history.pushState(null, '', window.location.href);
    };

    // 이벤트 리스너 등록
    window.addEventListener('beforeunload', handleBeforeUnload);
    window.addEventListener('popstate', handlePopState);
    setupHistoryProtection();

    // 클린업 함수 저장
    blockerRef.current = () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      window.removeEventListener('popstate', handlePopState);
    };

    // 컴포넌트 언마운트 시 클린업
    return () => {
      if (blockerRef.current) {
        blockerRef.current();
        blockerRef.current = null;
      }
      isBlockingRef.current = false;
    };
  }, [when, message, onNavigationBlocked, onBeforeUnload]);

  // 안전한 내비게이션 함수 제공
  const navigateSafely = (path: string, options?: { replace?: boolean }) => {
    // 보호 비활성화 후 내비게이션
    isBlockingRef.current = false;
    if (blockerRef.current) {
      blockerRef.current();
      blockerRef.current = null;
    }
    
    if (options?.replace) {
      navigate(path, { replace: true });
    } else {
      navigate(path);
    }
  };

  return {
    navigateSafely,
    isBlocking: isBlockingRef.current
  };
};

export default useNavigationProtection;