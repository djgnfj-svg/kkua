import React from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();

  const handleLoginSuccess = () => {
    navigate('/lobby');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 py-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-white/5 to-transparent"></div>
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl animate-pulse"></div>
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center mb-12 animate-slide-up">
          <div className="inline-block mb-6">
            <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-500 rounded-3xl flex items-center justify-center shadow-xl shadow-purple-500/25 mb-4 mx-auto">
              <span className="text-3xl font-bold text-white">끄</span>
            </div>
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-white to-purple-200 bg-clip-text text-transparent mb-4 font-korean">
            끄아 (KKUA)
          </h1>
          <p className="text-xl text-white/70 font-english font-medium tracking-wide">
            Korean Word Chain Game
          </p>
          <div className="mt-4 w-24 h-1 bg-gradient-to-r from-purple-500 to-pink-500 rounded-full mx-auto shadow-lg shadow-purple-500/50"></div>
        </div>
        
        <div className="animate-scale-in" style={{ animationDelay: '0.3s' }}>
          <LoginForm onSuccess={handleLoginSuccess} />
        </div>
      </div>
    </div>
  );
};

export default LoginPage;