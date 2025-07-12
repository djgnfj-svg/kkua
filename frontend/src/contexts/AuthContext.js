import React, { createContext, useContext, useReducer, useEffect } from 'react';
import axiosInstance from '../Api/axiosInstance';

const AuthContext = createContext();

const getInitialState = () => {
  try {
    const savedAuth = localStorage.getItem('auth_state');
    if (savedAuth) {
      const parsedAuth = JSON.parse(savedAuth);
      return {
        isAuthenticated: false,
        user: parsedAuth.user || null,
        loading: true,
        error: null,
      };
    }
  } catch (error) {
    console.warn('Failed to parse saved auth state:', error);
  }
  
  return {
    isAuthenticated: false,
    user: null,
    loading: true,
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
  
  if (action.type === 'LOGIN_SUCCESS' || action.type === 'LOGOUT' || action.type === 'UPDATE_PROFILE') {
    try {
      localStorage.setItem('auth_state', JSON.stringify({
        isAuthenticated: newState.isAuthenticated,
        user: newState.user,
      }));
    } catch (error) {
      console.warn('Failed to save auth state to localStorage:', error);
    }
  }
  
  return newState;
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  useEffect(() => {
    checkAuthStatus();
  }, []);

  const checkAuthStatus = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('TIMEOUT')), 3000);
      });
      
      const apiPromise = axiosInstance.get('/auth/status');
      const response = await Promise.race([apiPromise, timeoutPromise]);
      
      if (response.data.authenticated) {
        dispatch({ type: 'LOGIN_SUCCESS', payload: response.data.guest });
      } else {
        dispatch({ type: 'LOGOUT' });
      }
    } catch (error) {
      console.error('Auth status check failed:', error);
      
      if (error.message === 'TIMEOUT' || error.code === 'ECONNABORTED' || error.code === 'ERR_NETWORK') {
        console.log('서버 연결 불가 - 저장된 사용자 정보 유지');
        const savedAuth = localStorage.getItem('auth_state');
        if (savedAuth) {
          try {
            const parsedAuth = JSON.parse(savedAuth);
            if (parsedAuth.user) {
              dispatch({ type: 'LOGIN_SUCCESS', payload: parsedAuth.user });
              return;
            }
          } catch (parseError) {
            console.warn('저장된 인증 정보 파싱 실패:', parseError);
          }
        }
      }
      
      dispatch({ type: 'LOGOUT' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
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
      console.error('Logout error:', error);
    } finally {
      try {
        localStorage.removeItem('auth_state');
      } catch (error) {
        console.warn('Failed to clear auth state from localStorage:', error);
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
