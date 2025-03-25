import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import './Lobby.css';

function Lobby() {
  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null); // 인터벌 참조 생성
  const navigate = useNavigate()

  {/* 방 제목 / 게임 타입 / 진행중인 인원 */}
  const rooms = [
    { title: "앵무새 덕후쉑 모여라 ㅋ 귀여워", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장 불가", color: "bg-gray-400" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
    { title: "뉴비 환영 놀아줘", type: "4인 일반전", players: "[ 2 / 4 ]", status: "입장", color: "bg-blue-500" },
  ];
//   {/* 배너 이미지 */}
//   // const slides = [
//   //   { image: `/images/slide1.jpg` },
//   //   { image: '/images/slide2.jpg' },
//   //   { image: '/images/slide3.jpg' },
//   // ];

  {/* 배너 이미지 */}
  const slides = [
    { color: `rgb(175, 142, 235)` },
    { color: `rgb(241, 69, 79)` },
    { color: `rgb(163, 235, 142)` },
    { color: `rgb(46, 45, 213)` },
    { color: `rgb(213, 128, 45)` },
  ];

  const handleClickEnterGame = () =>{
    
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
  };

  const handleNextSlide = () => {
    setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    resetInterval(); // 버튼 클릭 시 인터벌 초기화
  };

  {/* 점 클릭 시 슬라이드 이동 */}
  const handleDotClick = (index) => {
    setActiveIndex(index);
    resetInterval(); // 클릭 시 인터벌 초기화
  };

  return (
    <div className="h-screen bg-gray-100 flex flex-col" style={{fontFamily:"Apple SD Gothic Neo"}}>
      {/* 상단 슬라이더 */}
      <div
        className="relative w-full h-56 mt-5 flex items-center justify-center transition-all duration-500"
        style={{ backgroundColor: slides[activeIndex].color }}
      >
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
      <div className="flex-1 overflow-y-auto text-left space-y-4">
        {rooms.map((room, index) => (
          <div key={index} className="bg-white p-4 min-h-[12vh] border-b shadow-md flex items-center justify-between">
            <div>
              <h3 className="font-bold mb-0.5 tracking-widest">{room.title}</h3>
              <p className="text-sm font-bold">{room.type} {room.players}</p>
            </div>
            <button className={`text-white px-3 py-1 rounded ${room.color}`} onClick={(e) => handleClickEnterGame()} >{room.status}</button>
          </div>
        ))}
          <div className="bg-white p-4 min-h-[10vh] border-b shadow-md flex items-center justify-between">
            
          </div>
      </div>
     {/* 방 생성하기 버튼 */}
     <div className="fixed bottom-5 w-full bg-white flex justify-center text-center">
        <button className="w-full flex items-center justify-center gap-2 text-red-400 border-2 border-[#4178ED] rounded-full px-4 py-2 shadow-lg">
        <img src={`${process.env.PUBLIC_URL || ''}/imgs/icon/AddIcon.png`} alt="고양이" className="w-8 h-8" />
        방 생성하기
        </button>
      </div>
    </div>
  );
}

export default Lobby;
