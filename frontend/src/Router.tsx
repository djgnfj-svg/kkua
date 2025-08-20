import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useUserStore } from './stores/useUserStore';
import LoginPage from './pages/LoginPage';
import LobbyPage from './pages/LobbyPage';
import GameRoomPage from './pages/GameRoomPage';
import ToastProvider from './components/Toast';

const Router: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPageWrapper />} />
        <Route path="/lobby" element={<ProtectedRoute><LobbyPageWrapper /></ProtectedRoute>} />
        <Route path="/room/:roomId" element={<ProtectedRoute><GameRoomPageWrapper /></ProtectedRoute>} />
        <Route path="/" element={<HomePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <ToastProvider />
    </BrowserRouter>
  );
};

const HomePage: React.FC = () => {
  const { isAuthenticated } = useUserStore();
  
  if (isAuthenticated) {
    return <Navigate to="/lobby" replace />;
  } else {
    return <Navigate to="/login" replace />;
  }
};

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useUserStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <>{children}</>;
};

const LoginPageWrapper: React.FC = () => {
  const { isAuthenticated } = useUserStore();
  
  if (isAuthenticated) {
    return <Navigate to="/lobby" replace />;
  }
  
  return <LoginPage />;
};

const LobbyPageWrapper: React.FC = () => {
  return <LobbyPage />;
};

const GameRoomPageWrapper: React.FC = () => {
  return <GameRoomPage />;
};

export default Router;