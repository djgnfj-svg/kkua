import React from 'react';
import { Link } from 'react-router-dom';

function NotFound() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
      <div className="text-center">
        <div className="mb-8">
          <h1 className="text-6xl font-bold text-white mb-4">404</h1>
          <h2 className="text-2xl font-semibold text-white mb-4">
            페이지를 찾을 수 없습니다
          </h2>
          <p className="text-gray-300 text-lg mb-8">
            요청하신 페이지가 존재하지 않거나 이동되었습니다.
          </p>
        </div>

        <div className="space-y-4">
          <Link
            to="/"
            className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-8 rounded-lg transition-colors duration-200"
          >
            홈으로 돌아가기
          </Link>

          <div className="text-gray-400 text-sm">
            또는{' '}
            <Link
              to="/lobby"
              className="text-blue-400 hover:text-blue-300 underline"
            >
              로비
            </Link>
            로 이동하세요
          </div>
        </div>
      </div>
    </div>
  );
}

export default NotFound;
