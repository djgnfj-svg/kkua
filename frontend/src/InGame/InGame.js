import { useState } from 'react';

const time_gauge = 40; // 값이 올라가면 빨리 달림 70 되면 

function InGame() {
  const [items, setItems] = useState(['햄스터', '터널', '널뛰기']);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';

  return (
    <div className="min-h-screen bg-white p-4 flex flex-col items-center space-y-4 relative">
      <h1 className="text-2xl font-bold">120초</h1>
      <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-full text-center font-bold ">
        콤보콤보콤보
      </div>

      <div className="w-[80vw] max-w-sm space-y-4 tracking-wide">
        {items.slice(-3).map((item, index) => (
          <div key={index} className="p-3 rounded-full border shadow-lg flex items-center space-x-2 bg-white border-gray-300 drop-shadow-md">
            <div className={`w-6 h-6 ${index === 0 ? 'bg-blue-400' : index === 1 ? 'bg-green-400' : 'bg-purple-400'} rounded-full`}></div>
            <span className="font-bold text-black">
              {item.slice(0, -1)}<span className="text-red-500">{item.slice(-1)}</span>
            </span>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm h-4 bg-gray-200 rounded-lg">
        <div className="h-full bg-orange-400 w-1/4 relative z-10 rounded-lg">
            
            
            <img src={time_gauge <= 70 ? '/imgs/cat_walking.gif' : '/imgs/cat_running.gif'} className="absolute z-20 -top-2 -right-2 w-8 h-8 scale-x-[-1]" alt='cat_walking'></img>

        
        </div>
      </div>

      <div className="grid grid-cols-2 h-auto gap-4 w-[350px] max-w-md px-4">
        {players.map((player, index) => (
          <div
            key={index}
            className={`p-2 rounded-[20px] ${player === specialPlayer ? 'bg-orange-400' : 'bg-gray-200'} text-center font-bold h-auto`}
          >
            <div className="w-full h-[118px] bg-white rounded-[20px] shadow-inner"></div>
            <p className="mt-2 text-sm">{player}</p>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm flex items-center space-x-2 border-t pt-2 absolute bottom-4">
        <span className="font-bold">화살표</span>
        <input
          type="text"
          className="flex-1 p-2 border rounded-lg focus:outline-none"
          placeholder="즐거운 끄아와"
        />
      </div>
    </div>
  );
}

export default InGame;
