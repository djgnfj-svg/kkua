import React from 'react';

const WebSocketStatus = ({
  connected,
  isReconnecting,
  connectionAttempts,
  maxAttempts = 5,
  onReconnect,
  className = '',
}) => {
  if (connected) {
    return (
      <div className={`flex items-center text-sm text-green-600 ${className}`}>
        <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
        실시간 연결됨
      </div>
    );
  }

  if (isReconnecting) {
    return (
      <div className={`flex items-center text-sm text-yellow-600 ${className}`}>
        <div className="w-2 h-2 bg-yellow-500 rounded-full mr-2 animate-pulse"></div>
        재연결 중... ({connectionAttempts}/{maxAttempts})
      </div>
    );
  }

  return (
    <div className={`flex items-center text-sm text-red-600 ${className}`}>
      <div className="w-2 h-2 bg-red-500 rounded-full mr-2"></div>
      연결 끊김
      {onReconnect && (
        <button
          onClick={onReconnect}
          className="ml-2 px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded border text-red-700 transition"
        >
          재연결
        </button>
      )}
    </div>
  );
};

export default WebSocketStatus;
