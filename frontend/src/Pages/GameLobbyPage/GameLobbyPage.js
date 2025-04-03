import React from 'react'
import { useNavigate } from 'react-router-dom'

function GameLobbyPage() {

    const navigate = useNavigate();

    const handleClickExit = () => {
      let res = window.confirm("로비로 나가시겠습니까?");
      if(res){
        navigate("/lobby");
      }else{
        
      }
    }
    

  return (
    <div className="w-full min-h-screen bg-white flex flex-col items-center pt-5 relative overflow-y-auto">
      {/* Close button */}
      <div className="absolute top-5 right-5 text-2xl cursor-pointer" onClick={() => handleClickExit()}>X</div>

      {/* Title */}
      <div className="text-center mb-5">
        <div className="font-bold text-lg">XX 게임 대기실</div>
        <div className="font-bold text-base">아케이드 [2 / 4]</div>
      </div>

      {/* Players */}
      <div className="flex flex-col gap-5 mb-auto">
        {[0, 1, 2, 3].map((index) => (
          <div
            key={index}
            className="w-[120px] h-[130px] bg-gray-300 rounded-2xl shadow-md flex flex-col items-center justify-center"
          >
            {index < 2 ? (
              <div className="flex flex-col items-center pt-2">
                <div className="w-[80px] h-[80px] bg-white rounded-2xl"></div>
                <div className="font-bold mt-2 mb-2">김밥</div>
              </div>
            ) : null}
          </div>
        ))}
      </div>

      {/* Bottom button list */}
      <div className="flex justify-between w-full bg-gray-200 pb-4 mt-auto">
        {Array.from({ length: 7 }).map((_, idx) => (
          <div
            key={idx}
            className="flex-1 py-4 text-center font-bold"
          >
            입티
          </div>
        ))}
      </div>
    </div>
  )
}

export default GameLobbyPage
