import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children, redirectTo = '/' }) {
  const { isAuthenticated, loading } = useAuth();

  // localStorage 확인하여 빠른 초기 판단
  const hasStoredAuth = React.useMemo(() => {
    try {
      const savedAuth = localStorage.getItem('auth_state');
      if (savedAuth) {
        const parsedAuth = JSON.parse(savedAuth);
        return parsedAuth.isAuthenticated && parsedAuth.user;
      }
    } catch (error) {
      // localStorage 접근 실패 시 조용히 처리
    }
    return false;
  }, []);

  // 로딩 중이면서 localStorage에 인증 정보가 있으면 일단 컨텐츠 렌더링
  if (loading) {
    if (hasStoredAuth) {
      // localStorage에 인증 정보가 있으면 바로 렌더링 (백그라운드에서 검증 중)
      return children;
    }
    
    // localStorage에 정보가 없으면 로딩 화면 표시
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-lg font-medium">
            인증 정보를 확인하는 중...
          </p>
        </div>
      </div>
    );
  }

  // 로딩이 완료된 후 최종 인증 상태로 판단
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} />;
  }

  // 인증된 사용자에게 컨텐츠 렌더링
  return children;
}

export default ProtectedRoute;
