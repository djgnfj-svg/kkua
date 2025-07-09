import React, { useState } from 'react';
import './Lobby.css';
import AddRoomModal from './Section/AddRoomModal';
import RoomList from './components/RoomList';
import Banner from './components/Banner';
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
    <div className="w-full h-screen flex justify-center bg-white">
      <div className="hidden md:flex w-[12%] h-[70%] bg-gray-500 mr-12 self-center"></div>
      <div className="flex flex-col w-full max-w-4xl bg-gray-200 shadow-lg relative">
        {isEntering && (
          <div className="absolute inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
            <div className="bg-white px-6 py-3 rounded-lg shadow-md text-gray-700 font-semibold text-lg">
              입장 중...
            </div>
          </div>
        )}
        <div className="w-full flex flex-col items-center mt-6 mb-2">
          <img
            src="/imgs/icon/default-avatar.png"
            alt="프로필 이미지"
            className="w-[50px] h-[50px] bg-white rounded-full object-cover mb-2"
          />
          <p className="text-lg font-semibold text-gray-700">
            {nickname || '게스트'}
          </p>
          <div className="md:hidden w-full flex justify-center py-2">
            <span className="text-sm text-gray-500">
              위에서 아래로 스와이프 시 새로고침
            </span>
          </div>
        </div>
        {!modalIsOpen && (
          <div
            className="hidden md:flex justify-center items-center absolute bottom-[100px] left-1/2 transform -translate-x-1/2 z-50"
            onClick={handleClickRefresh}
          >
            <div className="w-[50px] h-[50px] rounded-full border-2 border-gray-400 flex items-center justify-center cursor-pointer bg-white shadow-md">
              <img
                src={`${process.env.PUBLIC_URL || ''}/imgs/icon/refreshIcon.png`}
                alt="새로고침 아이콘"
                className="w-6 h-6"
              />
            </div>
          </div>
        )}
        <Banner />
        <div className="flex justify-end px-4 md:px-10 mt-2">
          <button
            className="text-white bg-blue-500 hover:bg-blue-600 font-bold py-3 px-6 rounded-full shadow-lg text-base"
            onClick={handleRandomEnter}
          >
            🎲 랜덤 입장
          </button>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center bg-white min-h-[20vh] border rounded-md mx-4 mt-6 mb-2 shadow-md">
            <p className="text-gray-500 text-center text-lg">로딩 중...</p>
          </div>
        ) : (
          <RoomList rooms={roomsData} onEnter={handleEnterGame} />
        )}

        <div
          className="w-full flex justify-center py-4 bg-gray-200 border-gray-300 relative"
          onClick={handleClickOpenModal}
        >
          <button className="w-full md:w-[80%] flex items-center justify-center gap-2 text-red-400 border-2 border-[#4178ED] rounded-full px-4 py-2 shadow-lg bg-white">
            <img
              src={`${process.env.PUBLIC_URL || ''}/imgs/icon/AddIconA.png`}
              alt="방 생성 아이콘"
              className="w-8 h-8"
            />
            방 생성하기
          </button>
        </div>

        {modalIsOpen && (
          <>
            <AddRoomModal isOpen={modalIsOpen} isClose={setModalIsOpen} />
          </>
        )}
      </div>
      <div className="hidden md:flex w-[12%] h-[70%] bg-gray-500 ml-12 self-center"></div>
    </div>
  );
}

export default Lobby;
