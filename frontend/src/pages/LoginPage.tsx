import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import LoginForm from '../components/LoginForm';
import BackendTest from '../components/BackendTest';

const LoginPage: React.FC = () => {
  const [showBackendTest, setShowBackendTest] = useState(false);
  const navigate = useNavigate();

  const handleLoginSuccess = () => {
    navigate('/lobby');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 via-white to-secondary-50 py-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 bg-shimmer-gradient bg-gradient-radial opacity-5 animate-shimmer"></div>
      <div className="absolute top-20 left-20 w-72 h-72 bg-primary-200 rounded-full opacity-20 animate-float"></div>
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-secondary-200 rounded-full opacity-20 animate-float" style={{ animationDelay: '1s' }}></div>
      
      <div className="container mx-auto px-4 relative z-10">
        <div className="text-center mb-12 animate-slide-up">
          <div className="inline-block mb-6">
            <div className="w-24 h-24 bg-gradient-to-br from-primary-500 to-primary-600 rounded-3xl flex items-center justify-center shadow-glow-md mb-4 mx-auto">
              <span className="text-3xl font-bold text-white">끄</span>
            </div>
          </div>
          
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-600 to-secondary-700 bg-clip-text text-transparent mb-4 font-korean">
            끄아 (KKUA)
          </h1>
          <p className="text-xl text-secondary-600 font-english font-medium tracking-wide">
            Korean Word Chain Game
          </p>
          <div className="mt-4 w-24 h-1 bg-gradient-to-r from-primary-500 to-primary-600 rounded-full mx-auto"></div>
        </div>
        
        <div className="animate-scale-in" style={{ animationDelay: '0.3s' }}>
          <LoginForm onSuccess={handleLoginSuccess} />
        </div>

        {/* Development Tools */}
        <div className="mt-12 text-center animate-fade-in" style={{ animationDelay: '0.6s' }}>
          <button
            onClick={() => setShowBackendTest(!showBackendTest)}
            className="text-sm text-secondary-500 hover:text-primary-600 transition-colors duration-200 underline decoration-2 underline-offset-4 hover:decoration-primary-600 font-korean"
          >
            {showBackendTest ? '백엔드 테스트 숨기기' : '백엔드 테스트 보기'}
          </button>
        </div>

        {showBackendTest && (
          <div className="max-w-4xl mx-auto mt-8 animate-slide-up">
            <BackendTest />
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;