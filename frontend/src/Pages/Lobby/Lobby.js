import React, { useState } from 'react';
import './Lobby.css';
import AddRoomModal from './Section/AddRoomModal';
import RoomList from './components/RoomList';
import useLobbyData from './hooks/useLobbyData';

function Lobby() {
  const {
    roomsData,
    isLoading,
    isEntering,
    nickname,
    fetchRoom,
    handleEnterGame,
    handleRandomEnter,
  } = useLobbyData();

  const [modalIsOpen, setModalIsOpen] = useState(false);

  const handleClickOpenModal = () => {
    setModalIsOpen(true);
  };

  const handleClickRefresh = () => {
    fetchRoom();
    alert('새 정보를 가져옵니다.');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex">
      {/* 왼쪽 사이드바 - 온라인 사용자 */}
      <div className="hidden lg:flex w-64 bg-white/10 backdrop-blur-md border-r border-white/20 flex-col p-4">
        <h3 className="text-white font-bold text-lg mb-4">🎮 온라인 사용자</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2 p-2 bg-white/5 rounded-lg">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">A</span>
            </div>
            <span className="text-white text-sm">Anonymous User</span>
          </div>
          <div className="flex items-center space-x-2 p-2 bg-white/5 rounded-lg">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-xs font-bold">G</span>
            </div>
            <span className="text-white text-sm">Guest Player</span>
          </div>
        </div>
        
        <div className="mt-8">
          <h4 className="text-white/80 font-semibold text-sm mb-3">📊 게임 통계</h4>
          <div className="space-y-2">
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-white/60 text-xs">활성 게임</div>
              <div className="text-white text-lg font-bold">12</div>
            </div>
            <div className="bg-white/5 rounded-lg p-3">
              <div className="text-white/60 text-xs">총 플레이어</div>
              <div className="text-white text-lg font-bold">48</div>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 콘텐츠 */}
      <div className="flex-1 flex flex-col bg-white/5 backdrop-blur-md mx-4 lg:mx-8 my-4 rounded-2xl border border-white/20 shadow-2xl relative overflow-hidden">
        {isEntering && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
            <div className="bg-white px-6 py-3 rounded-lg shadow-md text-gray-700 font-semibold text-lg">
              입장 중...
            </div>
          </div>
        )}
        {/* 상단 프로필 섹션 */}
        <div className="flex flex-col items-center p-6 border-b border-white/10">
          <div className="relative mb-4">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-blue-500 rounded-full flex items-center justify-center shadow-lg border-4 border-white/20">
              <span className="text-white text-2xl font-bold">
                {(nickname || '게스트').charAt(0).toUpperCase()}
              </span>
            </div>
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full border-2 border-white"></div>
          </div>
          
          <h2 className="text-white text-xl font-bold mb-1">{nickname || '게스트'}</h2>
          <div className="flex items-center space-x-4 text-white/70 text-sm mb-3">
            <span className="flex items-center">
              <span className="w-2 h-2 bg-yellow-400 rounded-full mr-1"></span>
              레벨 1
            </span>
            <span className="flex items-center">
              <span className="w-2 h-2 bg-blue-400 rounded-full mr-1"></span>
              승률 0%
            </span>
          </div>
          
          <div className="flex space-x-2">
            <button className="px-4 py-2 bg-white/10 backdrop-blur-md rounded-lg text-white text-sm hover:bg-white/20 transition-colors border border-white/20">
              프로필 편집
            </button>
            <button 
              onClick={handleClickRefresh}
              className="px-4 py-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg text-white text-sm hover:from-purple-600 hover:to-blue-600 transition-colors shadow-lg"
            >
              🔄 새로고침
            </button>
          </div>
        </div>
        {/* 액션 버튼 영역 */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-white/10">
          <div className="flex items-center space-x-2 text-white/70">
            <span className="text-sm">🏆 활성 게임</span>
            <span className="text-white font-semibold">{roomsData.length}개</span>
          </div>
          <button
            className="px-6 py-3 bg-gradient-to-r from-green-500 to-teal-500 hover:from-green-600 hover:to-teal-600 text-white font-bold rounded-xl shadow-lg transition-all duration-200 transform hover:scale-105"
            onClick={handleRandomEnter}
          >
            🎲 랜덤 입장
          </button>
        </div>
        {/* 메인 콘텐츠 영역 */}
        <div className="flex-1 overflow-hidden">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-4 border-white border-t-transparent mx-auto mb-4"></div>
                <p className="text-white/70 text-lg">방 목록을 불러오는 중...</p>
              </div>
            </div>
          ) : (
            <RoomList rooms={roomsData} onEnter={handleEnterGame} />
          )}
        </div>

        {/* 하단 방 생성 버튼 */}
        <div className="p-6 border-t border-white/10">
          <button 
            onClick={handleClickOpenModal}
            className="w-full py-4 bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 text-white font-bold rounded-xl shadow-lg transition-all duration-200 transform hover:scale-[1.02] flex items-center justify-center space-x-2"
          >
            <span className="text-2xl">➕</span>
            <span>새 게임방 만들기</span>
          </button>
        </div>

        {modalIsOpen && (
          <AddRoomModal isOpen={modalIsOpen} isClose={setModalIsOpen} />
        )}
      </div>
      
      {/* 오른쪽 사이드바 - 게임 가이드 */}
      <div className="hidden lg:flex w-64 bg-white/10 backdrop-blur-md border-l border-white/20 flex-col p-4">
        <h3 className="text-white font-bold text-lg mb-4">🎯 게임 가이드</h3>
        <div className="space-y-3">
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-white font-semibold text-sm mb-1">끝말잇기 규칙</div>
            <div className="text-white/70 text-xs">이전 단어의 마지막 글자로 시작하는 단어를 입력하세요</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-white font-semibold text-sm mb-1">아이템 사용</div>
            <div className="text-white/70 text-xs">특별한 아이템으로 게임을 더 재미있게!</div>
          </div>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-white font-semibold text-sm mb-1">승리 조건</div>
            <div className="text-white/70 text-xs">가장 많은 점수를 획득한 플레이어가 승리</div>
          </div>
        </div>
        
        <div className="mt-8">
          <h4 className="text-white/80 font-semibold text-sm mb-3">🚀 최근 업데이트</h4>
          <div className="bg-white/5 rounded-lg p-3">
            <div className="text-white/60 text-xs mb-1">v1.0.0</div>
            <div className="text-white text-sm">새로운 아이템 시스템 추가</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Lobby;
