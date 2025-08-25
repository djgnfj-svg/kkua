import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui';

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
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // 두음법칙 대체 문자 표시 함수
  const getDueumAlternative = (char: string): string => {
    // 두음법칙으로 변환된 글자들 (이미 변환된 글자 → 원래 글자)
    const dueumMappings: Record<string, string> = {
      // ㄴ으로 시작 (원래 ㄹ)
      '나': '라', '낙': '락', '난': '란', '날': '랄', '남': '람',
      '납': '랍', '낭': '랑', '내': '래', '냉': '랭', '녹': '록',
      '논': '론', '농': '롱', '뇌': '뢰', '누': '루', '능': '릉',
      '님': '임', '닙': '입', '노': '로',
      
      // ㅇ으로 시작 (원래 ㄹ/ㄴ)
      '약': '략', '양': '량', '여': '려,녀', '역': '력,녁', '연': '련,년',
      '열': '렬', '염': '렴,념', '엽': '렵,녑', '영': '령,녕', '예': '례',
      '요': '료,뇨', '용': '룡', '유': '류,뉴', '육': '륙,뉵', '윤': '륜',
      '율': '률', '융': '륭', '음': '름', '이': '리,니', '인': '린',
      '임': '림', '입': '립',
      
      // ㄹ로 끝나는 글자 추가
      '라': '나', '락': '낙', '란': '난', '람': '남', '랑': '낭',
      '래': '내', '량': '양', '려': '여,녀', '력': '역,녁', '련': '연,년',
      '렬': '열', '렴': '염,념', '렵': '엽,녑', '령': '영,녕', '례': '예',
      '로': '노', '록': '녹', '론': '논', '료': '요,뇨', '룡': '용',
      '루': '누', '류': '유,뉴', '륙': '육,뉵', '륜': '윤', '률': '율',
      '륭': '융', '름': '음', '릉': '능', '리': '이,니', '린': '인',
      '림': '임,님', '립': '입,닙',
    };
    
    const alt = dueumMappings[char];
    if (alt) {
      const altChar = alt.split(',')[0];
      return `${char}(${altChar})`;
    }
    return char;
  };

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
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-white font-korean">
            {isMyTurn ? '🎯 단어 입력' : '입력'}
          </h3>
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
                    (currentChar ? `${getDueumAlternative(currentChar)}로 시작하는 단어...` : '단어를 입력하세요...') : 
                    "메시지를 입력하세요..."
                  ) : 
                  "연결 끊김"
              }
              className={`flex-1 px-4 py-2 border rounded-xl focus:outline-none focus:ring-2 focus:border-transparent text-white placeholder-white/50 text-sm backdrop-blur-sm font-korean ${
                isMyTurn 
                  ? 'bg-green-500/20 border-green-400/30 focus:ring-green-400' 
                  : 'bg-white/10 border-white/20 focus:ring-purple-500'
              }`}
              disabled={!isConnected}
              maxLength={200}
            />
            <Button
              onClick={handleSend}
              disabled={!isConnected || !inputValue.trim()}
              size="sm"
              variant={isMyTurn ? "primary" : "primary"}
              className={`px-4 py-2 ${
                isMyTurn 
                  ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700' 
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