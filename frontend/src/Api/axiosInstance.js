import axios from 'axios';
import { getErrorMessage, ERROR_MESSAGES } from '../utils/errorMessages';
import cacheManager, { invalidateCache } from '../utils/cacheManager';

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate', // HTTP 캐시 방지
    'Pragma': 'no-cache',
    'Expires': '0'
  },
  timeout: 10000,
  withCredentials: true,
});

// 요청 인터셉터 (캐시 무효화 및 Rate Limiting 대응)
axiosInstance.interceptors.request.use(
  (config) => {
    // POST, PUT, DELETE 요청 시 관련 캐시 무효화
    if (['post', 'put', 'delete'].includes(config.method?.toLowerCase())) {
      const url = config.url || '';
      
      // 방 관련 변경 시 캐시 무효화
      if (url.includes('/gamerooms/')) {
        const roomIdMatch = url.match(/\/gamerooms\/(\d+)/);
        if (roomIdMatch) {
          const roomId = roomIdMatch[1];
          invalidateCache.room(roomId);
        }
      }
      
      // 인증 관련 변경 시 사용자 캐시 무효화
      if (url.includes('/auth/')) {
        if (url.includes('/logout')) {
          invalidateCache.all();
        } else {
          invalidateCache.user();
        }
      }
    }
    
    // 타임스탬프 추가로 브라우저 캐시 방지
    if (config.method?.toLowerCase() === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now()
      };
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 (에러 핸들링 표준화)
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // 사용자 친화적 에러 메시지로 변환
    const userFriendlyMessage = getErrorMessage(error);
    
    // 에러 객체에 표준화된 메시지 추가
    error.userMessage = userFriendlyMessage;
    
    // 인증 에러의 경우 특별 처리
    if (error.response?.status === 401) {
      // 세션 만료 시 로그아웃 처리
      if (error.response.data?.error_code === 'SESSION_EXPIRED') {
        // 게스트 스토어 초기화 (필요시 여기서 처리)
      }
    }
    
    // Rate Limiting 에러 처리
    if (error.response?.status === 429) {
      error.userMessage = ERROR_MESSAGES.RATE_LIMIT_EXCEEDED;
    }
    
    // 네트워크 에러 처리
    if (!error.response) {
      error.userMessage = ERROR_MESSAGES.NETWORK_ERROR;
    }
    
    return Promise.reject(error);
  }
);

export default axiosInstance;
