import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axiosInstance from '../Api/axiosInstance';

const AuthContext = createContext();

const getInitialState = () => {
  try {
    const savedAuth = localStorage.getItem('auth_state');
    if (savedAuth) {
      const parsedAuth = JSON.parse(savedAuth);

      // 저장된 인증 정보가 있으면 인증된 상태로 시작하되 loading은 false로 설정
      if (parsedAuth.user && parsedAuth.isAuthenticated) {
        return {
          isAuthenticated: true,
          user: parsedAuth.user,
          loading: false, // localStorage에 유효한 정보가 있으면 바로 사용 (서버 검증은 백그라운드에서)
          error: null,
        };
      }
    }
  } catch (error) {
    // localStorage 오류 시 초기화
    try {
      localStorage.removeItem('auth_state');
    } catch (removeError) {
      // localStorage 제거도 실패하면 조용히 처리
    }
  }

  return {
    isAuthenticated: false,
    user: null,
    loading: true, // 저장된 정보가 없을 때만 로딩 상태
    error: null,
  };
};

const initialState = getInitialState();

function authReducer(state, action) {
  let newState;

  switch (action.type) {
    case 'LOGIN_START':
      newState = { ...state, loading: true, error: null };
      break;
    case 'LOGIN_SUCCESS':
      newState = {
        ...state,
        isAuthenticated: true,
        user: action.payload,
        loading: false,
        error: null,
      };
      break;
    case 'LOGIN_FAILURE':
      newState = {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: action.payload,
      };
      break;
    case 'LOGOUT':
      newState = {
        ...state,
        isAuthenticated: false,
        user: null,
        loading: false,
        error: null,
      };
      break;
    case 'UPDATE_PROFILE':
      newState = {
        ...state,
        user: { ...state.user, ...action.payload },
      };
      break;
    case 'SET_LOADING':
      newState = { ...state, loading: action.payload };
      break;
    case 'CLEAR_ERROR':
      newState = { ...state, error: null };
      break;
    default:
      newState = state;
  }

  if (
    action.type === 'LOGIN_SUCCESS' ||
    action.type === 'LOGOUT' ||
    action.type === 'UPDATE_PROFILE'
  ) {
    try {
      localStorage.setItem(
        'auth_state',
        JSON.stringify({
          isAuthenticated: newState.isAuthenticated,
          user: newState.user,
        })
      );
    } catch (error) {
      // Failed to save auth state to localStorage - 조용히 처리
    }
  }

  return newState;
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const navigate = useNavigate();
  const location = useLocation();
  const isCheckingRef = React.useRef(false);

  useEffect(() => {
    // 이미 체크 중이면 중복 실행 방지
    if (isCheckingRef.current) return;
    
    // 초기 렌더링 시에만 인증 상태 확인
    const timer = setTimeout(() => {
      checkAuthStatus();
    }, 100); // 작은 딜레이를 추가하여 무한 루프 방지
    
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 초기 렌더링 시에만 실행

  const checkAuthStatus = async () => {
    // 중복 실행 방지
    if (isCheckingRef.current) return;
    isCheckingRef.current = true;
    
    try {
      // localStorage에 인증 정보가 있으면 loading 상태를 변경하지 않음
      const hasStoredAuth = localStorage.getItem('auth_state');
      if (!hasStoredAuth) {
        dispatch({ type: 'SET_LOADING', payload: true });
      }

      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('TIMEOUT')), 5000); // 타임아웃 5초로 증가
      });

      const apiPromise = axiosInstance.get('/auth/status');
      const response = await Promise.race([apiPromise, timeoutPromise]);

      if (response.data.authenticated) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: response.data.guest });
        
        // 스마트 리다이렉트: 루트 페이지에 있을 때만 서버 추천 URL로 이동
        // 현재 페이지가 보호된 경로라면 그대로 유지
        const protectedPaths = ['/lobby', '/kealobby', '/keaing', '/gamerooms', '/gameroom'];
        const isProtectedPath = protectedPaths.some(path => location.pathname.startsWith(path));
        
        // 리다이렉트를 더 제한적으로 만들기 - 루트 페이지에서만 실행
        if (location.pathname === '/' && response.data.redirect_url) {
          setTimeout(() => {
            navigate(response.data.redirect_url, { replace: true });
          }, 50); // 딜레이 추가
        }
        // 다른 경우에는 리다이렉트하지 않음
      } else {
        // 서버에서 인증되지 않았을 때
        // localStorage에 정보가 있으면 유지 (네트워크 문제일 수 있음)
        const savedAuth = localStorage.getItem('auth_state');
        if (savedAuth) {
          try {
            const parsedAuth = JSON.parse(savedAuth);
            if (parsedAuth.user && parsedAuth.isAuthenticated) {
              // localStorage 정보를 신뢰하고 유지
              console.log('서버 인증 실패했지만 localStorage 정보 유지');
              return;
            }
          } catch (e) {
            // 파싱 실패
          }
        }
        // localStorage에도 정보가 없으면 로그아웃
        localStorage.removeItem('auth_state');
        dispatch({ type: 'LOGOUT' });
      }
    } catch (error) {
      // Auth status check failed - 조용히 처리

      // 네트워크 에러나 타임아웃인 경우 저장된 정보 유지
      if (
        error.message === 'TIMEOUT' ||
        error.code === 'ECONNABORTED' ||
        error.code === 'ERR_NETWORK' ||
        error.response?.status >= 500
      ) {
        // 서버 연결 불가 - 저장된 사용자 정보 유지
        const savedAuth = localStorage.getItem('auth_state');
        if (savedAuth) {
          try {
            const parsedAuth = JSON.parse(savedAuth);
            if (parsedAuth.user) {
              // 저장된 정보로 로그인 상태 유지
              dispatch({ type: 'LOGIN_SUCCESS', payload: parsedAuth.user });
              return;
            }
          } catch (parseError) {
            // 저장된 인증 정보 파싱 실패 - 조용히 처리
          }
        }
      }

      // 401 에러나 기타 클라이언트 에러인 경우에만 로그아웃
      if (error.response?.status === 401 || error.response?.status === 403) {
        dispatch({ type: 'LOGOUT' });
      } else {
        // 서버 에러인 경우 현재 상태 유지
      }
    } finally {
      // localStorage에 정보가 없었을 때만 loading 상태 해제
      const hasStoredAuth = localStorage.getItem('auth_state');
      if (!hasStoredAuth) {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
      isCheckingRef.current = false;
    }
  };

  // 백그라운드에서 조용히 인증 상태 검증 (로딩 상태 변경 없음)
  const checkAuthStatusSilently = async () => {
    try {
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('TIMEOUT')), 3000); // 더 짧은 타임아웃
      });

      const apiPromise = axiosInstance.get('/auth/status');
      const response = await Promise.race([apiPromise, timeoutPromise]);

      if (!response.data.authenticated) {
        // 서버에서 인증되지 않았다고 하면 로그아웃
        dispatch({ type: 'LOGOUT' });
      } else if (response.data.guest) {
        // 서버 정보로 사용자 정보 업데이트 (로딩 상태 변경 없음)
        dispatch({ type: 'UPDATE_PROFILE', payload: response.data.guest });
      }
    } catch (error) {
      // Silent auth check failed - 조용히 처리
      // 에러 발생 시 현재 상태 유지 (사용자 경험 방해하지 않음)
      // 401/403 에러인 경우에만 로그아웃
      if (error.response?.status === 401 || error.response?.status === 403) {
        dispatch({ type: 'LOGOUT' });
      }
    }
  };

  const login = async (nickname = null) => {
    try {
      dispatch({ type: 'LOGIN_START' });

      const response = await axiosInstance.post('/auth/login', {
        nickname: nickname,
      });

      dispatch({ type: 'LOGIN_SUCCESS', payload: response.data });
      
      // 로그인 후 적절한 페이지로 리다이렉트 (auth/status 호출해서 redirect_url 확인)
      try {
        const statusResponse = await axiosInstance.get('/auth/status');
        if (statusResponse.data.authenticated && statusResponse.data.redirect_url) {
          navigate(statusResponse.data.redirect_url, { replace: true });
        }
      } catch (statusError) {
        // 상태 확인 실패 시 기본 로비로 이동
        navigate('/lobby', { replace: true });
      }
      
      return response.data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || '로그인에 실패했습니다.';
      dispatch({ type: 'LOGIN_FAILURE', payload: errorMessage });
      throw error;
    }
  };

  const logout = async () => {
    try {
      await axiosInstance.post('/auth/logout');
    } catch (error) {
      // Logout error - 조용히 처리
    } finally {
      try {
        localStorage.removeItem('auth_state');
      } catch (error) {
        // Failed to clear auth state from localStorage - 조용히 처리
      }
      dispatch({ type: 'LOGOUT' });
    }
  };

  const updateProfile = async (nickname) => {
    try {
      const response = await axiosInstance.put('/auth/me', { nickname });
      dispatch({ type: 'UPDATE_PROFILE', payload: response.data });
      return response.data;
    } catch (error) {
      const errorMessage =
        error.response?.data?.detail || '프로필 업데이트에 실패했습니다.';
      throw new Error(errorMessage);
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value = {
    ...state,
    login,
    logout,
    updateProfile,
    checkAuthStatus,
    checkAuthStatusSilently,
    clearError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
