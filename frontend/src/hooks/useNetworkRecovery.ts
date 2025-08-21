import { useState, useEffect, useCallback, useRef } from 'react';
import { showToast } from '../components/Toast';

interface NetworkRecoveryOptions {
  maxRetries?: number;
  retryDelay?: number;
  onReconnected?: () => void;
  onConnectionLost?: () => void;
}

export const useNetworkRecovery = (options: NetworkRecoveryOptions = {}) => {
  const {
    maxRetries = 5,
    retryDelay = 2000,
    onReconnected,
    onConnectionLost
  } = options;

  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const retryTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // 네트워크 상태 감지
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setIsReconnecting(false);
      setRetryCount(0);
      
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
        retryTimeoutRef.current = null;
      }
      
      showToast.success('인터넷 연결이 복구되었습니다');
      onReconnected?.();
    };

    const handleOffline = () => {
      setIsOnline(false);
      showToast.error('인터넷 연결이 끊어졌습니다');
      onConnectionLost?.();
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [onReconnected, onConnectionLost]);

  // 수동 재연결 시도
  const attemptReconnection = useCallback(async () => {
    if (!isOnline || retryCount >= maxRetries) {
      return false;
    }

    setIsReconnecting(true);
    setRetryCount(prev => prev + 1);

    try {
      // 간단한 네트워크 테스트
      const response = await fetch('/api/health', { 
        method: 'HEAD',
        cache: 'no-cache'
      });
      
      if (response.ok) {
        setIsReconnecting(false);
        setRetryCount(0);
        onReconnected?.();
        return true;
      }
    } catch (error) {
      console.warn('Reconnection attempt failed:', error);
    }

    // 지수적 백오프로 재시도
    const delay = retryDelay * Math.pow(2, retryCount - 1);
    retryTimeoutRef.current = setTimeout(() => {
      attemptReconnection();
    }, delay);

    return false;
  }, [isOnline, retryCount, maxRetries, retryDelay, onReconnected]);

  // 에러 복구 헬퍼
  const withErrorRecovery = useCallback(async <T>(
    operation: () => Promise<T>,
    fallbackMessage?: string
  ): Promise<T | null> => {
    try {
      return await operation();
    } catch (error) {
      console.error('Operation failed:', error);
      
      if (!isOnline) {
        showToast.error('인터넷 연결을 확인해주세요');
        attemptReconnection();
      } else {
        showToast.error(fallbackMessage || '오류가 발생했습니다. 다시 시도해주세요');
      }
      
      return null;
    }
  }, [isOnline, attemptReconnection]);

  return {
    isOnline,
    isReconnecting,
    retryCount,
    attemptReconnection,
    withErrorRecovery
  };
};