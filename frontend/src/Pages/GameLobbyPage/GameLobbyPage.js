import React from 'react';
import { useParams } from 'react-router-dom';
import ParticipantList from './components/ParticipantList';
import ChatWindow from './components/ChatWindow';
import WebSocketStatus from '../../components/WebSocketStatus';
import useSimpleGameRoom from '../../hooks/useSimpleGameRoom';

function GameLobbyPage() {
  const { roomId } = useParams();
  
  const {
    connected,
    participants,
    messages,
    isReconnecting,
    participantCount,
    sendChatMessage,
    toggleReady,
    manualReconnect,
    isOwner,
    connectionAttempts,
    maxReconnectAttempts
  } = useSimpleGameRoom(roomId);

  // 간소화: WebSocket 연결 대기 중이면 로딩 표시
  if (!connected && !isReconnecting) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        <div className="text-center text-2xl font-bold text-white animate-pulse">
          🔌 서버 연결 중...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex flex-col items-center pt-5 relative overflow-y-auto">
      <div className="max-w-6xl w-full px-4 space-y-6">
        {/* 연결 상태 */}
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-3 border border-white/20">
          <WebSocketStatus
            connected={connected}
            isReconnecting={isReconnecting}
            connectionAttempts={connectionAttempts}
            maxAttempts={maxReconnectAttempts}
            onReconnect={manualReconnect}
            className="text-white"
          />
        </div>

        {/* 간소화된 방 정보 */}
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <h1 className="text-2xl font-bold text-white mb-2">🎮 게임룸 {roomId}</h1>
          <p className="text-white/80">
            👥 참가자: {participantCount}명 | 
            {isOwner ? ' 👑 방장' : ' 👤 참가자'}
          </p>
        </div>

        {/* 간소화된 액션 버튼들 */}
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <div className="flex gap-4">
            <button
              onClick={toggleReady}
              className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors"
            >
              ✅ 준비완료
            </button>
            <button
              onClick={() => window.history.back()}
              className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors"
            >
              🚪 나가기
            </button>
          </div>
        </div>

        {/* 참가자 목록 (강퇴 기능 제거) */}
        <ParticipantList 
          participants={participants} 
          isOwner={isOwner}
        />
        
        {/* 채팅 */}
        <ChatWindow 
          messages={messages} 
          sendMessage={sendChatMessage} 
        />
      </div>
    </div>
  );
}

export default GameLobbyPage;
