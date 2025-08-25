import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui';
import { getDueumInputHelp, checkDueumWordValidity } from '../utils/dueumRules';

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
  isMyTurn?: boolean;
  currentChar?: string;
  onSubmitWord?: (word: string) => void;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  isConnected,
  currentUserId,
  onSendMessage,
  isMyTurn = false,
  currentChar = '',
  onSubmitWord
}) => {
  const [inputValue, setInputValue] = useState('');
  const [wordValidation, setWordValidation] = useState<{ isValid: boolean; message?: string }>({ isValid: false });
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 실시간 단어 검증
  useEffect(() => {
    if (isMyTurn && currentChar && inputValue.trim()) {
      const result = checkDueumWordValidity(inputValue.trim(), currentChar);
      setWordValidation({
        isValid: result.isValid,
        message: result.message
      });
    } else {
      setWordValidation({ isValid: false });
    }
  }, [inputValue, currentChar, isMyTurn]);

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
    
    // 내 차례일 때는 단어 제출
    if (isMyTurn && onSubmitWord) {
      console.log('🎯 내 차례: 단어 제출 -', inputValue.trim());
      onSubmitWord(inputValue.trim());
    } else {
      console.log('💬 채팅 전송 -', inputValue.trim());
      onSendMessage(inputValue.trim());
    }
    
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
      return 'bg-gradient-to-r from-red-500/30 to-orange-500/30 border-2 border-red-400/50 text-red-200 px-4 py-3 text-sm backdrop-blur-sm rounded-xl shadow-lg shadow-red-500/20 animate-pulse';
    }
    if (message.type === 'game') {
      return 'bg-gradient-to-r from-green-500/30 to-emerald-500/30 border-2 border-green-400/50 text-green-200 px-4 py-3 text-sm backdrop-blur-sm rounded-xl shadow-lg shadow-green-500/20';
    }
    if (message.userId === currentUserId) {
      return 'bg-purple-500/20 ml-8 rounded-lg p-3 border border-purple-400/30 backdrop-blur-sm';
    }
    return 'bg-white/10 mr-8 rounded-lg p-3 border border-white/20 backdrop-blur-sm';
  };

  return (
    <div className="bg-purple-800/40 backdrop-blur-lg rounded-xl border border-white/20 overflow-hidden">
      <div className="bg-purple-700/40 p-3 border-b border-white/20">
        <div className="flex items-center justify-end">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-400 shadow-lg shadow-green-400/50' : 'bg-red-400 shadow-lg shadow-red-400/50'} animate-pulse`} />
        </div>
      </div>
      
      {/* 메시지 영역 */}
      <div className="h-40 overflow-y-auto p-3 space-y-3 bg-black/10 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent">
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
      <div className={`p-3 border-t border-white/20 backdrop-blur-sm ${
        isMyTurn ? 'bg-gradient-to-r from-green-500/10 to-emerald-500/10 border-green-400/30' : 'bg-white/5'
      }`}>
          
          
          <div className="flex space-x-3">
              <input
                ref={inputRef}
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={
                  isConnected ? 
                    (isMyTurn ? 
                      (currentChar ? getDueumInputHelp(currentChar) : '단어를 입력하세요...') : 
                      "메시지를 입력하세요..."
                    ) : 
                    "연결 끊김"
                }
                className={`flex-1 px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:border-transparent text-white placeholder-white/50 text-sm backdrop-blur-sm font-korean ${
                  isMyTurn 
                    ? (wordValidation.isValid 
                        ? 'bg-green-500/20 border-green-400/30 focus:ring-green-400' 
                        : inputValue.trim() 
                          ? 'bg-red-500/20 border-red-400/30 focus:ring-red-400'
                          : 'bg-blue-500/20 border-blue-400/30 focus:ring-blue-400')
                    : 'bg-white/10 border-white/20 focus:ring-purple-500'
                }`}
                disabled={!isConnected}
                maxLength={200}
              />
              <Button
                onClick={handleSend}
                disabled={!isConnected || !inputValue.trim() || (isMyTurn && !wordValidation.isValid)}
                size="sm"
                variant={isMyTurn ? "primary" : "primary"}
                className={`px-4 py-2 ${
                  isMyTurn 
                    ? (wordValidation.isValid 
                        ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700' 
                        : 'bg-gradient-to-r from-gray-500 to-gray-600 cursor-not-allowed')
                    : ''
                }`}
              >
                {isMyTurn ? '🚀 제출' : '전송'}
              </Button>
          </div>
          
          {!isConnected && (
            <div className="mt-2 text-xs text-red-300 text-center font-korean">
              연결이 끊어졌습니다. 재연결을 기다리는 중...
            </div>
          )}
          
      </div>
    </div>
  );
};

export default ChatPanel;