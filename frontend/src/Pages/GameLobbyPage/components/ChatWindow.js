import React, { useRef, useEffect, useState } from 'react';
import guestStore from '../../../store/guestStore';

const ChatWindow = ({ messages, sendMessage }) => {
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
    <div className="w-full mt-4 border border-gray-300 rounded-lg bg-white flex flex-col h-[300px] overflow-hidden shadow-md">
      <div className="bg-slate-900 text-white text-center py-2 font-bold">
        채팅
      </div>

      <div
        className="flex-1 overflow-y-auto px-4 py-2 bg-gray-50 text-sm"
        ref={chatContainerRef}
      >
        {messages.length > 0 ? (
          messages.map((msg, i) => {
            const isSystem = msg.type === 'system';
            const isSelf =
              String(msg.guest_id) === String(guestStore.getState().guest_id);

            return (
              <div
                key={i}
                className={`mb-2 ${
                  isSystem ? 'text-center text-gray-600' : ''
                }`}
              >
                {isSystem ? (
                  <div>
                    <span className="text-blue-500 font-semibold">시스템</span>{' '}
                    <span className="text-xs text-gray-400 ml-1">
                      {new Date(msg.timestamp).toLocaleTimeString()}
                    </span>
                    <div>{msg.message}</div>
                  </div>
                ) : (
                  <div
                    className={`w-full flex mb-2 ${
                      isSelf ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    <div
                      className={`flex flex-col items-start max-w-[80%] text-sm ${
                        isSelf
                          ? 'items-end text-right'
                          : 'items-start text-left'
                      }`}
                    >
                      <span
                        className={`font-bold mb-1 ${
                          isSelf ? 'text-orange-500' : 'text-blue-600'
                        }`}
                      >
                        {msg.nickname || `게스트_${msg.guest_id}`}
                      </span>
                      <div className="bg-white border rounded px-2 py-1 shadow text-black break-words">
                        {msg.message || ''}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-center text-gray-400">
            아직 메시지가 없습니다
          </div>
        )}
      </div>

      <div className="flex border-t border-gray-300 p-2 bg-white">
        <input
          type="text"
          value={chatMessage}
          onChange={(e) => setChatMessage(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="채팅 메시지를 입력하세요..."
          className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none"
        />
        <button
          onClick={handleSendMessage}
          className="bg-blue-500 text-white px-4 py-2 rounded-r-md hover:bg-blue-600"
        >
          전송
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;
