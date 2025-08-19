import React from 'react';
import { useParams } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { useToast } from '../../contexts/ToastContext';
import ParticipantList from './components/ParticipantList';
import ChatWindow from './components/ChatWindow';
import ActionButtons from './components/ActionButtons';
import WebSocketStatus from '../../components/WebSocketStatus';
import useTestWebSocket from '../../hooks/useTestWebSocket';

function GameLobbyPage() {
  const { roomId } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  
  const { connected, messages, sendMessage } = useTestWebSocket(roomId);

  // 최신 참가자 목록 가져오기
  const participants = React.useMemo(() => {
    const participantMessages = messages
      .filter(msg => ['participant_joined', 'participant_left', 'ready_toggled'].includes(msg.type))
      .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    if (participantMessages.length > 0) {
      return participantMessages[0].participants || [];
    }
    return [];
  }, [messages]);

  // 모든 메시지를 채팅에 표시 (채팅 + 시스템 메시지)
  const chatMessages = messages;

  // 현재 연결된 사용자 정보 추출
  const currentUser = React.useMemo(() => {
    const connectedMsg = messages.find(msg => msg.type === 'connected');
    return connectedMsg?.user || null;
  }, [messages]);

  // 현재 사용자가 방장인지 확인
  const isOwner = React.useMemo(() => {
    if (!currentUser) return false;
    return currentUser.is_creator === true;
  }, [currentUser]);

  // 준비 상태 토글
  const handleToggleReady = () => {
    sendMessage({
      type: 'toggle_ready',
      timestamp: new Date().toISOString()
    });
  };

  // 채팅 메시지 전송
  const handleSendChat = (content) => {
    sendMessage({
      type: 'chat',
      message: content.trim(),
      timestamp: new Date().toISOString()
    });
  };

  // 방 나가기
  const handleLeaveRoom = () => {
    if (window.confirm('정말로 방을 나가시겠습니까?')) {
      window.history.back();
    }
  };

  // 게임 시작
  const handleStartGame = () => {
    // 나중에 구현할 게임 시작 로직
    alert('게임 시작 기능을 구현 중입니다!');
  };

  // WebSocket 연결 대기 중이면 로딩 표시
  if (!connected) {
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
            isReconnecting={false}
            connectionAttempts={0}
            maxAttempts={5}
            onReconnect={() => window.location.reload()}
            className="text-white"
          />
        </div>

        {/* 방 정보 */}
        <div className="bg-white/10 backdrop-blur-sm rounded-lg p-4 border border-white/20">
          <h1 className="text-2xl font-bold text-white mb-2">🎮 게임룸 {roomId}</h1>
          <p className="text-white/80">
            👥 참가자: {participants.length}명 | 
            {isOwner ? ' 👑 방장' : ' 👤 참가자'}
          </p>
        </div>

        {/* 액션 버튼들 */}
        <ActionButtons
          isOwner={isOwner}
          participants={participants}
          currentUser={currentUser}
          onToggleReady={handleToggleReady}
          onStartGame={handleStartGame}
          onLeaveRoom={handleLeaveRoom}
        />

        {/* 참가자 목록 */}
        <ParticipantList 
          participants={participants} 
          isOwner={isOwner}
          currentUser={currentUser}
        />
        
        {/* 채팅 */}
        <ChatWindow 
          messages={chatMessages} 
          sendMessage={handleSendChat} 
        />
      </div>
    </div>
  );
}

export default GameLobbyPage;