import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Lobby.css';
import { gameUrl } from '../../Component/urls';
import AddRoomModal from './Section/AddRoomModal';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';

function Lobby() {
  const navigate = useNavigate();
  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null); // 인터벌 참조 생성
  const [modalIsOpen , setModalIsOpen] = useState(false);
  const [roomsData,setRoomsData] = useState([
    {
      title:"",
      room_type:"",
      people:"",
      max_people:"",
      playing:"",
    }
  ])
  
  //   {/* 배너 이미지 */}
  //   // const slides = [
    //   //   { image: `/images/slide1.jpg` },
    //   //   { image: '/images/slide2.jpg' },
    //   //   { image: '/images/slide3.jpg' },
    //   // ];


  // api 를 통해 방정보 받아오기
  {/* 방 제목 / 게임 타입 / 진행중인 인원 */}
  useEffect(() => {
  const fetchRoom = async () => {
    try{
      const res= await axiosInstance.get(ROOM_API.get_ROOMS);
      setRoomsData(res.data)
    }catch(error){
      console.log("방 요총 실패 " + error);
    }
  }
  fetchRoom();
  },[])

  
  {/* 배너 이미지 */}
  const slides = [
    { color: `rgb(175, 142, 235)` },
    { color: `rgb(241, 69, 79)` },
    { color: `rgb(163, 235, 142)` },
    { color: `rgb(46, 45, 213)` },
    { color: `rgb(213, 128, 45)` },
  ];

  // url 이동
  const handleClickEnterGame = () =>{
    navigate(gameUrl)
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

  return (
    <div className="w-full h-screen flex justify-center bg-gray-100">
      <div className="hidden md:flex w-[12%] h-[70%] bg-red-500 mr-12 self-center"></div>
      <div className="flex flex-col w-full max-w-4xl bg-gray-200 shadow-lg overflow-hidden">
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

        {/* 새로고침 안내 */}
        <div className="text-center text-sm text-gray-500 py-2">위에서 아래로 스와이프 시 새로고침</div>

        {/* 방 목록 */}
        <div className="flex-1 overflow-y-auto text-left space-y-4 px-2 md:px-10 md:pt-16 pb-24">
          {roomsData.map((room, index) => (
            <div key={index} className="bg-white p-4 md:p-8 min-h-[12vh] md:min-h-[16vh] border-b shadow-md md:shadow-lg flex items-center justify-between">
              <div>
                <h3 className="font-bold mb-0.5 tracking-widest text-lg md:text-xl">{room.title}</h3>
                <p className="text-sm md:text-lg font-bold">{room.room_type} [ {room.people} / {room.max_people} ]</p>
              </div>
              {room.playing === false ? 
              <button className={`text-white px-3 py-1 rounded bg-red-500 `} onClick={(e) => handleClickEnterGame()} > 입장하기 </button>
              :
              <button className={`text-white px-3 py-1 rounded bg-gray-500 `} onClick={(e) => handleClickEnterGame()} > 끄아 중 </button>
            }
            </div>
          ))}
            <div className="bg-white p-4 min-h-[10vh] border-b shadow-md flex items-center justify-between">
            </div>
        </div>
       {/* 방 생성하기 버튼 */}
       <div className="w-full flex justify-center py-4 bg-gray-200  border-gray-300" onClick={(e) => setModalIsOpen(true)} >
          <button className="w-full md:w-[80%] flex items-center justify-center gap-2 text-red-400 border-2 border-[#4178ED] rounded-full px-4 py-2 shadow-lg bg-white">
          <img src={`${process.env.PUBLIC_URL || ''}/imgs/icon/AddIcon.png`}className="w-8 h-8" />
          방 생성하기
          </button>
        </div>
        {modalIsOpen && 
        <>
          <AddRoomModal isOpen={modalIsOpen} isClose={setModalIsOpen} />
        </>}
      </div>
      <div className="hidden md:flex w-[12%] h-[70%] bg-red-500 ml-12 self-center"></div>
    </div>
  );
}

export default Lobby;
