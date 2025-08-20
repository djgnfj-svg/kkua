import React, { useState, useRef, useEffect } from 'react';
import { Button, Card } from './ui';

interface ChatMessage {
  id: string;
  userId: number;
  nickname: string;
  message: string;
  timestamp: string;
  type?: 'user' | 'system' | 'game';
}

interface ChatPanelProps {
  messages: ChatMessage[];
  isConnected: boolean;
  currentUserId: number;
  onSendMessage: (message: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isConnected,
  currentUserId,
  onSendMessage
}) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 새 메시지가 올 때마다 스크롤을 맨 아래로
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = () => {
    if (!inputValue.trim() || !isConnected) return;
    
    onSendMessage(inputValue.trim());
    setInputValue('');
    inputRef.current?.focus();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('ko-KR', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMessageStyle = (message: ChatMessage) => {
    if (message.type === 'system') {
      return 'bg-yellow-50 border-l-4 border-yellow-400 text-yellow-800 px-3 py-2 text-sm';
    }
    if (message.type === 'game') {
      return 'bg-blue-50 border-l-4 border-blue-400 text-blue-800 px-3 py-2 text-sm';
    }
    if (message.userId === currentUserId) {
      return 'bg-blue-100 ml-8 rounded-lg p-2';
    }
    return 'bg-gray-100 mr-8 rounded-lg p-2';
  };

  return (
    <Card>
      <Card.Header>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">💬 채팅</h3>
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
        </div>
      </Card.Header>
      
      <Card.Body className="p-0">
        {/* 메시지 영역 */}
        <div className="h-48 overflow-y-auto p-3 space-y-2 bg-gray-50">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 text-sm py-8">
              아직 채팅 메시지가 없습니다
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={getMessageStyle(message)}>
                {message.type === 'user' ? (
                  <>
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-xs">
                        {message.userId === currentUserId ? '나' : message.nickname}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    <div className="text-sm break-words">
                      {message.message}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-sm">{message.message}</span>
                    <span className="text-xs opacity-60 ml-2">
                      {formatTime(message.timestamp)}
                    </span>
                  </div>
                )}
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="p-3 border-t bg-white">
          <div className="flex space-x-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "메시지를 입력하세요..." : "연결 끊김"}
              className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
              disabled={!isConnected}
              maxLength={200}
            />
            <Button
              onClick={handleSend}
              disabled={!isConnected || !inputValue.trim()}
              size="sm"
              className="px-3"
            >
              전송
            </Button>
          </div>
          
          {!isConnected && (
            <div className="mt-2 text-xs text-red-600 text-center">
              연결이 끊어졌습니다. 재연결을 기다리는 중...
            </div>
          )}
          
          <div className="mt-1 text-xs text-gray-500 text-right">
            {inputValue.length}/200
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ChatPanel;