import React, { useEffect, useState } from 'react';
import './Lobby.css';

function Lobby() {

  const [activeIndex, setActiveIndex] = useState(0);


  let a = "앵무새 덕후쉑 모여라 ㅋ 귀여워";
  let b = "뉴비 환영 놀아줘";
  let c = "게임 친구 구해요.";

  let d = "4인 일반전"

  let e = "[ " + 2 + " / " + 4 + " ]"

  const rooms = [
    { title: a, type: d, players: e },
    { title: b, type: d, players: e },
    { title: c, type: d, players: e },
  ];

  const banners = {
    aType: "", bType: "", cType: "", dType: "", fType: ""
  }
  const slides = [
    { image: `/images/slide1.jpg` }, // 로컬 이미지 사용 시 경로 예시
    { image: '/images/slide2.jpg' },
    { image: '/images/slide3.jpg' },
    { image: '/images/slide4.jpg' },
    { image: '/images/slide5.jpg' },
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setActiveIndex((prevIndex) => (prevIndex + 1) % slides.length);
    }, 3000);

    return () => clearInterval(interval); // 컴포넌트 언마운트 시 인터벌 제거
  }, []);

  return (
    <div className="h-screen bg-gray-100 flex flex-col">

      {/* 상단 슬라이더 */}
      <div
        className={`w-full h-40 mt-20 flex items-center justify-center transition-all duration-500`}
        id="lobby__SlideBox"
        style={{
          backgroundImage: `url(${slides[activeIndex].image})`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
        }}
      >
        <div className="flex space-x-2 mt-40">
          {slides.map((_, index) => (
            <div
              key={index}
              className={`w-2 h-2 rounded-full ${activeIndex === index ? 'bg-white' : 'bg-gray-400'}`}
            ></div>
          ))}
        </div>

      </div>

      {/* 방 목록 */}
      <div className="flex-1 overflow-y-auto text-left mt-10 ">
        {rooms.map((room, index) => (
          <div key={index} className="bg-white p-8 2 0 8 border-b h-10vh shadow-md mb-3" id='lobby__list'>
            <h3 className="font-bold mb-0.5 tracking-widest">{room.title}</h3>
            <p className="text-sm h-393px font-bold">{room.type} {room.players}</p>
          </div>
        ))}
      </div>

      {/* 하단 버튼 */}
      <div className="p-4 flex justify-center space-x-4 border-t">
        <button className="bg-blue-400 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-md">
        </button>
        <button className="bg-orange-400 text-white w-12 h-12 rounded-full flex items-center justify-center shadow-md">
        </button>
      </div>
    </div>
  );
}

export default Lobby;
