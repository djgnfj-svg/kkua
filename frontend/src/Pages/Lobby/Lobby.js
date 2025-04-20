import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Lobby.css';
import { gameLobbyUrl, /* gameUrl, */ lobbyUrl } from '../../Component/urls';
import AddRoomModal from './Section/AddRoomModal';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';
import guestStore from '../../store/guestStore'
import userIsTrue from '../../Component/userIsTrue';
import { USER_API } from '../../Api/userApi';
import Cookies from 'js-cookie';

function Lobby() {
  const navigate = useNavigate();

  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null); // 인터벌 참조 생성
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const [roomsData, setRoomsData] = useState([
    {
      title: "",
      room_type: "",
      participant_count: "",
      max_people: "",
      playing: "",
    }
  ])

  const { uuid, nickname } = guestStore.getState();

  // 페이지 로드 시 게스트 정보 확인
  useEffect(() => {
    const checkGuestInfo = async () => {
      // 쿠키에서 UUID 가져오기
      const guestUuid = Cookies.get('kkua_guest_uuid');


      // 쿠키에 UUID가 있으면 로그인 시도
      if (guestUuid) {
        try {
          // 로그인 요청 
          const response = await axiosInstance.post(USER_API.GET_GUEST, {
            guest_uuid: guestUuid,
            nickname: null,
            device_info: navigator.userAgent
          });

          const data = response.data;
          console.log("게스트 로그인 응답:", data);
          console.log("게스트 정보 업데이트됨:", data.uuid);
          alert("로그인 되었습니다!");
        } catch (error) {
          console.error("게스트 로그인 실패:", error);
          // 로그인 페이지로 리디렉션
          alert("로그인에 실패했습니다. 메인 페이지로 이동합니다.");
          navigate('/');
        }
      } else {
        // UUID가 없으면 로그인 페이지로
        alert("로그인이 필요합니다. 메인 페이지로 이동합니다.");
        navigate('/');
      }
    };
    checkGuestInfo();
  }, [navigate]);

  // api 를 통해 방정보 받아오기
  {/* 방 제목 / 게임 타입 / 진행중인 인원 */ }
  useEffect(() => {
    fetchRoom();
  }, [])

  const fetchRoom = async () => {
    try {
      const res = await axiosInstance.get(ROOM_API.get_ROOMS);
      setRoomsData(res.data)
    } catch (error) {
      console.log("방 요청 실패 " + error);
    }
  }

  // uuid가 변경될 때마다 상태 확인 로직 실행되도록 의존성 추가
  useEffect(() => {
    const fetchGuestStatus = async () => {
      // 유효한 UUID가 있을 때만 API 호출
      const guestUuid = Cookies.get('kkua_guest_uuid');
      if (guestUuid) {
        console.log("게스트 상태 확인 중, UUID:", guestUuid);
        try {
          const res = await axiosInstance.get(USER_API.GET_GUEST_STATUS, {
            headers: {
              'uuid': guestUuid
            }
          });
          const roomId = res?.data?.room_id;
          if (roomId) {
            // 진행 중인 게임이 있으면 해당 방으로 이동
            alert("기존 방에 재입장합니다.");
            navigate(gameLobbyUrl(roomId));
          }
        } catch (err) {
          console.error("게스트 상태 확인 실패:", err);
        }
      } else {
        console.log("UUID가 없어 게스트 상태 확인을 건너뜁니다.");
      }
    };

    fetchGuestStatus();
  }, [uuid, navigate]); // uuid와 navigate를 의존성으로 추가

  {/* 배너 이미지 */}
  const slides = [
    { color: `rgb(175, 142, 235)` },
    { color: `rgb(241, 69, 79)` },
    { color: `rgb(163, 235, 142)` },
    { color: `rgb(46, 45, 213)` },
    { color: `rgb(213, 128, 45)` },
  ];

  // url 이동
  const handleClickEnterGame = async (room_id) => {
    try{
      await axiosInstance.post(ROOM_API.JOIN_ROOMS(room_id))
      alert("끄아하러 가요! ")
      navigate(gameLobbyUrl(room_id))
    }catch(err){
      alert("입장 불가능한 방입니다.");
    }
  }

  {/* 슬라이드 인터벌 초기화 함수 */}
  const resetInterval = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);

    intervalRef.current = setInterval(() => {
      setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    }, 3000);
  };

  {/* 슬라이드 자동 전환 */}
  useEffect(() => {
    resetInterval();
    return () => clearInterval(intervalRef.current); // 컴포넌트 언마운트 시 인터벌 제거
  }, [slides.length]);

  {/* 좌우 버튼 기능 추가 */}
  const handlePrevSlide = () => {
    setActiveIndex((prevIndex) => (prevIndex === 0 ? slides.length - 1 : prevIndex - 1));
    resetInterval(); // 버튼 클릭 시 인터벌 초기화
  }

  const handleNextSlide = () => {
    setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    resetInterval(); // 버튼 클릭 시 인터벌 초기화
  }

  {/* 점 클릭 시 슬라이드 이동 */}
  const handleDotClick = (index) => {
    setActiveIndex(index);
    resetInterval(); // 클릭 시 인터벌 초기화
  }
  //모달 열기
  const handleClickOpenModal = () => {
    setModalIsOpen(true)
  }
  //Refresh BTN
  const handleClickRefresh = () => {
    fetchRoom()
    alert("새 정보를 가져옵니다.");
  }

  return (
    <div className="w-full h-screen flex justify-center bg-white">
      <div className="hidden md:flex w-[12%] h-[70%] bg-gray-500 mr-12 self-center"></div>
      <div className="flex flex-col w-full max-w-4xl bg-gray-200 shadow-lg relative">
        {/* 중앙 원형 이미지 + 게스트 아이디 */}
        <div className="w-full flex flex-col items-center mt-6 mb-2">
          <img

            className="w-[50px] h-[50px] bg-white rounded-full object-cover mb-2"
          />
          <p className="text-lg font-semibold text-gray-700">{nickname || '게스트'}</p>

          {/* 모바일: 스와이프 새로고침 안내 */}
          <div className="md:hidden w-full flex justify-center py-2">
            <span className="text-sm text-gray-500">위에서 아래로 스와이프 시 새로고침</span>
          </div>
        </div>
        {/* 새로고침 안내 (게스트 닉네임 아래 중앙 정렬) */}
        <div className="hidden md:flex justify-center items-center absolute bottom-[100px] left-1/2 transform -translate-x-1/2 z-50" onClick={handleClickRefresh}>
          <div className="w-[50px] h-[50px] rounded-full border-2 border-gray-400 flex items-center justify-center cursor-pointer bg-white shadow-md">
            <img src={`${process.env.PUBLIC_URL || ''}/imgs/icon/refreshIcon.png`} alt="새로고침 아이콘" className="w-6 h-6" />
          </div>
        </div>
        {/* 상단 슬라이더 */}
        <div
          className="relative w-full h-[30vh] md:h-[40vh] mt-5 flex items-center justify-center transition-all duration-500 md:hidden"
          style={{ backgroundColor: slides[activeIndex].color }} >
          <button onClick={handlePrevSlide} className="absolute left-2 bg-gray-300 text-black w-8 h-8 rounded-full shadow-md"></button>
          <button onClick={handleNextSlide} className="absolute right-2 bg-gray-300 text-black w-8 h-8 rounded-full shadow-md"></button>

          <div className="absolute bottom-2 flex space-x-2">
            {slides.map((_, index) => (
              <div
                key={index}
                onClick={() => handleDotClick(index)}
                className={`w-2 h-2 rounded-full cursor-pointer ${activeIndex === index ? 'bg-white' : 'bg-gray-400'}`}
              ></div>
            ))}
          </div>
        </div>

        {/* 방 목록 */}
        {roomsData.length === 0 || roomsData[0].title === "" ? (
          <>
            <div className="flex items-center justify-center bg-white min-h-[20vh] border rounded-md mx-4 mt-6 mb-2 shadow-md">
              <p className="text-gray-500 text-center text-lg">방을 생성해주세요.</p>
            </div>
            <div className="flex-1" />
          </>
        ) : null}
        {roomsData.length > 0 && roomsData[0].title !== "" && (
          <div className="flex-1 overflow-y-auto text-left space-y-4 px-2 md:px-10 md:pt-16 pb-24">
            {[...roomsData].reverse().map((room, index) => (
              <div key={index} className="bg-white p-4 md:p-8 min-h-[12vh] md:min-h-[16vh] border-b shadow-md md:shadow-lg flex items-center justify-between">
                <div>
                  <h3 className="font-bold mb-0.5 tracking-widest text-lg md:text-xl">{room.title}</h3>
                  <p className="text-sm md:text-lg font-bold">{room.game_mode} [ {room.participant_count} / {room.max_players} ]</p>
                </div>
                {room.status === 'waiting' ?
                  <button className={`text-white px-3 py-1 rounded bg-red-500 `} onClick={(e) => handleClickEnterGame(room.room_id)} > 입장하기 </button>
                  :
                  <button className={`text-white px-3 py-1 rounded bg-gray-500 `} disabled={true}> 끄아 중 </button>
                }
              </div>
            ))}
            {roomsData.length > 5 && (
              <div className="bg-white p-4 min-h-[10vh] border-b shadow-md flex items-center justify-between">
              </div>
            )}
          </div>
        )}

        {/* 모바일: 방 생성하기 버튼 */}
        <div className="w-full flex justify-center py-4 bg-gray-200 border-gray-300 relative" onClick={(e) => handleClickOpenModal(e)} >
          <button className="w-full md:w-[80%] flex items-center justify-center gap-2 text-red-400 border-2 border-[#4178ED] rounded-full px-4 py-2 shadow-lg bg-white">
            <img src={`${process.env.PUBLIC_URL || ''}/imgs/icon/AddIcon.png`} className="w-8 h-8" />
            방 생성하기
          </button>
        </div>

        {modalIsOpen &&
          <>
            <AddRoomModal isOpen={modalIsOpen} isClose={setModalIsOpen} />
          </>}
      </div>
      <div className="hidden md:flex w-[12%] h-[70%] bg-gray-500 ml-12 self-center"></div>
    </div>
  );
}

export default Lobby;
