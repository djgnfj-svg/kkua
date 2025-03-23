import React, { useEffect, useState, useRef } from 'react';
import './Lobby.css';

function Lobby() {
  const [activeIndex, setActiveIndex] = useState(0);
  const intervalRef = useRef(null); // 인터벌 참조 생성

  {/* 방 제목 / 게임 타입 / 진행중인 인원 */}
  const a = "앵무새 덕후쉑 모여라 ㅋ 귀여워";
  const b = "뉴비 환영 놀아줘";
  const c = "게임 친구 구해요.";

  const d = "4인 일반전";

  const e = "[ " + 2 + " / " + 4 + " ]";

  {/* 방 리스트 */}
  const rooms = [
    { title: a, type: d, players: e },
    { title: b, type: d, players: e },
    { title: c, type: d, players: e },
  ];

  {/* 배너 이미지 */}
  // const slides = [
  //   { image: `/images/slide1.jpg` },
  //   { image: '/images/slide2.jpg' },
  //   { image: '/images/slide3.jpg' },
  // ];

    {/*  임시 컬러 배너 이미지 */}
  const slides = [
    { color: `rgb(175, 142, 235)` },
    { color: `rgb(241, 69, 79)` },
    { color: `rgb(163, 235, 142)` },
    { color: `rgb(46, 45, 213)` },
    { color: `rgb(213, 128, 45)` },
  ];
  

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
    <div className="h-screen bg-gray-100 flex flex-col">

      {/* 상단 슬라이더 */}
      <div
        className={`relative w-full h-40 mt-20 flex items-center justify-center transition-all duration-500`}
        id="lobby__SlideBox"
        style={{
           // backgroundImage: `url(${slides[activeIndex].image})`,
          backgroundColor:slides[activeIndex].color,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <button 
          onClick={handlePrevSlide} 
          className="absolute left-2 bg-gray-300 text-black w-8 h-8 rounded-full flex items-center justify-center shadow-md">
           {/* 좌측 화살표 추가 */}
        </button>
        <button 
          onClick={handleNextSlide} 
          className="absolute right-2 bg-gray-300 text-black w-8 h-8 rounded-full flex items-center justify-center shadow-md">
           {/* 우측 화살표 추가 */}
        </button>

        <div className="flex space-x-2 mt-40">
          {console.log(slides.length)}
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
      <div className="flex-1 overflow-y-auto text-left mt-10">
        {rooms.map((room, index) => (
          <div key={index} className="bg-white p-8 border-b h-10vh shadow-md mb-3" id='lobby__list'>
            <h3 className="font-bold mb-0.5 tracking-widest">{room.title}</h3>
            <p className="text-sm h-393px font-bold">{room.type} {room.players}</p>
          </div>
        ))}
         {/* 빈 박스 추가 */}
            <div className="bg-white p-8 border-b h-10vh shadow-md mb-3" id='lobby__list__empty'></div>
      </div>

     {/* 새로고침 & 위로가기 버튼 */}
      <div className="flex justify-center p-4 relative">
         <button 
           className="bg-blue-400 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-md">
          {/* 새로고침버튼 추가 */}
         </button>
         <button 
           className="absolute right-4 bg-orange-400 text-white w-8 h-8 rounded-full flex items-center justify-center shadow-md">
           {/* 위쪽 화살표 추가 */}
         </button>
       </div>
     </div>
   );
 }

export default Lobby;

