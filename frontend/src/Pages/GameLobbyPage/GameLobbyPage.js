import React from 'react';
import RoomInfo from './components/RoomInfo';
import ParticipantList from './components/ParticipantList';
import ChatWindow from './components/ChatWindow';
import ActionButtons from './components/ActionButtons';
import useGameLobby from './hooks/useGameLobby';

function GameLobbyPage() {
  const {
    roomInfo,
    participants,
    isLoading,
    isOwner,
    redirectingToGame,
    connected,
    messages,
    isReady,
    sendMessage,
    toggleReady,
    handleClickExit,
    handleClickStartBtn,
  } = useGameLobby();

  if (redirectingToGame) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-white">
        <div className="text-center text-2xl font-extrabold text-red-600 animate-pulse leading-relaxed">
          게임을 이미 시작하셨습니다.
          <br />
          게임페이지로 이동 중입니다...
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-white">
        <div className="text-center text-2xl font-bold animate-pulse">
          로딩 중...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-white flex flex-col items-center pt-5 relative overflow-y-auto">
      <RoomInfo
        roomInfo={roomInfo}
        participants={participants}
        connected={connected}
      />
      <ActionButtons
        isOwner={isOwner}
        participants={participants}
        handleClickExit={handleClickExit}
        handleClickStartBtn={handleClickStartBtn}
        handleReady={toggleReady}
        isReady={isReady}
      />
      <ParticipantList participants={participants} />
      <ChatWindow messages={messages} sendMessage={sendMessage} />
    </div>
  );
}

export default GameLobbyPage;
