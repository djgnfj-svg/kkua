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

  // 새 메시지가 올 때마다 스크롤을 맨 아래로 (부드럽게)
  useEffect(() => {
    const scrollToBottom = () => {
      if (messagesEndRef.current) {
        messagesEndRef.current.scrollIntoView({ 
          behavior: 'smooth',
          block: 'end'
        });
      }
    };
    
    // 약간의 지연을 두어 DOM이 업데이트된 후 스크롤
    const timeoutId = setTimeout(scrollToBottom, 100);
    return () => clearTimeout(timeoutId);
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
      return 'bg-yellow-500/20 border-l-4 border-yellow-400 text-yellow-300 px-3 py-2 text-sm backdrop-blur-sm';
    }
    if (message.type === 'game') {
      return 'bg-blue-500/20 border-l-4 border-blue-400 text-blue-300 px-3 py-2 text-sm backdrop-blur-sm';
    }
    if (message.userId === currentUserId) {
      return 'bg-purple-500/20 ml-8 rounded-lg p-3 border border-purple-400/30 backdrop-blur-sm';
    }
    return 'bg-white/10 mr-8 rounded-lg p-3 border border-white/20 backdrop-blur-sm';
  };

  return (
    <Card>
      <Card.Header>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white font-korean">💬 채팅</h3>
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'} animate-pulse`} />
        </div>
      </Card.Header>
      
      <Card.Body className="p-0">
        {/* 메시지 영역 */}
        <div className="h-48 overflow-y-auto p-3 space-y-3 bg-black/10 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
          {messages.length === 0 ? (
            <div className="text-center text-white/60 text-sm py-8 font-korean">
              아직 채팅 메시지가 없습니다
            </div>
          ) : (
            messages.map((message) => (
              <div 
                key={message.id} 
                className={`${getMessageStyle(message)} transform transition-all duration-300 hover:scale-[1.02]`}
              >
                {message.type === 'user' ? (
                  <>
                    <div className="flex items-center justify-between mb-2">
                      <span className={`font-semibold text-xs font-korean ${
                        message.userId === currentUserId ? 'text-purple-300' : 'text-white'
                      }`}>
                        {message.userId === currentUserId ? '나' : message.nickname}
                      </span>
                      <span className="text-xs text-white/50">
                        {formatTime(message.timestamp)}
                      </span>
                    </div>
                    <div className={`text-sm break-words font-korean ${
                      message.userId === currentUserId ? 'text-white' : 'text-white/90'
                    }`}>
                      {message.message}
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-korean">{message.message}</span>
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
        <div className="p-4 border-t border-white/20 bg-white/5 backdrop-blur-sm">
          <div className="flex space-x-3">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={isConnected ? "메시지를 입력하세요..." : "연결 끊김"}
              className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-white placeholder-white/50 text-sm backdrop-blur-sm font-korean"
              disabled={!isConnected}
              maxLength={200}
            />
            <Button
              onClick={handleSend}
              disabled={!isConnected || !inputValue.trim()}
              size="sm"
              variant="primary"
              className="px-4 py-2"
            >
              전송
            </Button>
          </div>
          
          {!isConnected && (
            <div className="mt-2 text-xs text-red-300 text-center font-korean">
              연결이 끊어졌습니다. 재연결을 기다리는 중...
            </div>
          )}
          
          <div className="mt-2 text-xs text-white/50 text-right">
            {inputValue.length}/200
          </div>
        </div>
      </Card.Body>
    </Card>
  );
};

export default ChatPanel;