import React, { createContext, useContext, useReducer, useEffect } from 'react';
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
          loading: false, // localStorage에 유효한 정보가 있으면 바로 사용
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

  useEffect(() => {
    // localStorage에 유효한 정보가 있으면 백그라운드에서 검증만 수행
    // 없으면 정상적으로 로딩 상태에서 체크
    if (state.isAuthenticated && state.user && !state.loading) {
      // 백그라운드 검증 (사용자는 이미 인증된 상태로 보임)
      checkAuthStatusSilently();
    } else {
      // 정상적인 인증 상태 체크 (로딩 표시)
      checkAuthStatus();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // 초기 렌더링 시에만 실행

  const checkAuthStatus = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });

      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('TIMEOUT')), 5000); // 타임아웃 5초로 증가
      });

      const apiPromise = axiosInstance.get('/auth/status');
      const response = await Promise.race([apiPromise, timeoutPromise]);

      if (response.data.authenticated) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: response.data.guest });
      } else {
        // 서버에서 인증되지 않았다고 하면 로그아웃
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
      dispatch({ type: 'SET_LOADING', payload: false });
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
