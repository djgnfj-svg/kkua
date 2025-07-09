import React, { useRef, useEffect, useState } from 'react';
import { useAuth } from '../../../contexts/AuthContext';

const ChatWindow = ({ messages, sendMessage }) => {
  const { user } = useAuth();
  const [chatMessage, setChatMessage] = useState('');
  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop =
        chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (chatMessage.trim() === '') return;

    if (sendMessage) {
      sendMessage(chatMessage);
      setChatMessage('');
    }
  };

  return (
    <div className="w-full bg-white/10 backdrop-blur-md rounded-xl border border-white/20 shadow-lg flex flex-col h-[400px] overflow-hidden">
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white text-center py-3 font-bold rounded-t-xl">
        💬 채팅
      </div>

      <div
        className="flex-1 overflow-y-auto px-4 py-3 bg-white/5 text-sm"
        ref={chatContainerRef}
      >
        {messages.length > 0 ? (
          messages.map((msg, i) => {
            const isSystem = msg.type === 'system';
            const isSelf = String(msg.guest_id) === String(user?.guest_id);

            return (
              <div
                key={i}
                className={`mb-3 ${
                  isSystem ? 'text-center' : ''
                }`}
              >
                {isSystem ? (
                  <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20">
                    <div className="flex items-center justify-center space-x-2 mb-1">
                      <span className="text-blue-300 font-semibold">🔔 시스템</span>
                      <span className="text-xs text-white/60">
                        {new Date(msg.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <div className="text-white/90 text-sm">{msg.message}</div>
                  </div>
                ) : (
                  <div
                    className={`w-full flex mb-2 ${
                      isSelf ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`flex flex-col max-w-[80%] text-sm ${
                        isSelf ? 'items-end' : 'items-start'
                      }`}
                    >
                      <span
                        className={`font-bold mb-1 text-xs ${
                          isSelf ? 'text-orange-300' : 'text-blue-300'
                        }`}
                      >
                        {msg.nickname || `게스트_${msg.guest_id}`}
                      </span>
                      <div
                        className={`rounded-lg px-3 py-2 shadow-lg break-words ${
                          isSelf
                            ? 'bg-gradient-to-r from-orange-500 to-orange-600 text-white'
                            : 'bg-white/90 text-gray-800'
                        }`}
                      >
                        {msg.message || ''}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center text-white/60 mt-8">
            <div className="text-4xl mb-2">💬</div>
            <div>아직 메시지가 없습니다</div>
            <div className="text-xs mt-1">첫 번째 메시지를 보내보세요!</div>
          </div>
        )}
      </div>

      <div className="flex border-t border-white/20 p-3 bg-white/5">
        <input
          type="text"
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="채팅 메시지를 입력하세요..."
          className="flex-1 px-4 py-2 bg-white/10 backdrop-blur-sm border border-white/20 rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-400 text-white placeholder-white/60"
        />
        <button
          onClick={handleSendMessage}
          className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-6 py-2 rounded-r-lg transition-all duration-200 transform hover:scale-105 shadow-lg"
        >
          📤
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
