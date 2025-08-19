import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

function ProtectedRoute({ children, redirectTo = '/' }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

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

  // localStorage에 인증 정보가 있으면 무조건 통과 (서버 검증은 백그라운드)
  if (hasStoredAuth) {
    return children;
  }

  // localStorage에 정보가 없고 로딩 중이면 로딩 화면
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-4 border-white border-t-transparent mx-auto mb-4"></div>
          <p className="text-white text-lg font-medium">
            게임을 불러오는 중...
          </p>
        </div>
      </div>
    );
  }

  // localStorage에도 없고 서버에서도 인증 안 됨
  if (!isAuthenticated) {
    return <Navigate to={redirectTo} state={{ from: location.pathname }} replace />;
  }

  // 인증된 사용자에게 컨텐츠 렌더링
  return children;
}

export default ProtectedRoute;
