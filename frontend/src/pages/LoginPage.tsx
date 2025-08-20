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
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            끄아 (KKUA)
          </h1>
          <p className="text-lg text-gray-600">
            Korean Word Chain Game
          </p>
        </div>
        
        <LoginForm onSuccess={handleLoginSuccess} />

        {/* Development Tools */}
        <div className="mt-8 text-center">
          <button
            onClick={() => setShowBackendTest(!showBackendTest)}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            {showBackendTest ? '백엔드 테스트 숨기기' : '백엔드 테스트 보기'}
          </button>
        </div>

        {showBackendTest && (
          <div className="max-w-4xl mx-auto mt-8">
            <BackendTest />
          </div>
        )}
      </div>
    </div>
  );
};

export default LoginPage;