import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache, no-store, must-revalidate', // HTTP 캐시 방지
    Pragma: 'no-cache',
    Expires: '0',
  },
  timeout: 10000,
  withCredentials: true,
});

// 자동 재로그인을 위한 변수
let isRelogging = false;

// 자동 재로그인 함수
const autoRelogin = async () => {
  if (isRelogging) {
    return Promise.reject(new Error('Already relogging'));
  }

  try {
    isRelogging = true;
    
    // localStorage에서 사용자 정보 확인
    const savedAuth = localStorage.getItem('auth_state');
    if (!savedAuth) {
      throw new Error('No saved auth data');
    }

    const parsedAuth = JSON.parse(savedAuth);
    if (!parsedAuth.user || !parsedAuth.user.nickname) {
      throw new Error('Invalid saved auth data');
    }

    // 같은 닉네임으로 재로그인 시도
    const response = await axios.post(
      `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/auth/login`,
      {
        nickname: parsedAuth.user.nickname
      },
      {
        withCredentials: true,
        timeout: 5000
      }
    );

    if (response.data.success) {
      console.log('자동 재로그인 성공:', parsedAuth.user.nickname);
      
      // localStorage 업데이트
      localStorage.setItem('auth_state', JSON.stringify({
        isAuthenticated: true,
        user: response.data.guest
      }));
      
      return response.data;
    } else {
      throw new Error('Auto relogin failed');
    }
  } catch (error) {
    console.error('자동 재로그인 실패:', error);
    // localStorage 정리
    localStorage.removeItem('auth_state');
    throw error;
  } finally {
    isRelogging = false;
  }
};

// 요청 인터셉터
axiosInstance.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 응답 인터셉터 - 자동 재로그인 로직 추가
axiosInstance.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // 401 에러이고 자동 재로그인을 시도하지 않은 요청인 경우
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // 로그인/상태확인 엔드포인트는 자동 재로그인 시도하지 않음
      const skipAutoRelogin = ['/auth/login', '/auth/status'].some(path => 
        originalRequest.url?.includes(path)
      );

      if (!skipAutoRelogin) {
        try {
          await autoRelogin();
          
          // 재로그인 성공 후 원래 요청 재시도
          return axiosInstance(originalRequest);
        } catch (reloginError) {
          console.error('자동 재로그인 실패, 로그인 페이지로 이동 필요');
          
          // 현재 페이지가 게임 관련 페이지라면 로비로 리다이렉트
          if (window.location.pathname.includes('/gameroom') || 
              window.location.pathname.includes('/lobby')) {
            setTimeout(() => {
              window.location.href = '/';
            }, 1000);
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export default axiosInstance;
