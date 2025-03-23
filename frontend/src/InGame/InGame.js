import { useState } from 'react';

function InGame() {
  const [items, setItems] = useState(['넘뛰기', '터널', '햄스터']);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';

  return (
    <div className="min-h-screen bg-white p-4 flex flex-col items-center space-y-4 relative">
      <h1 className="text-2xl font-bold">120초</h1>
      <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-lg text-center font-bold">
        콤보콤보콤보
      </div>

      <div className="w-[80vw] max-w-sm space-y-2">
        {items.slice(-3).map((item, index) => (
          <div key={index} className="p-2 rounded-lg border shadow flex items-center space-x-2">
            <div className={`w-4 h-4 ${item === '넘뛰기' ? 'bg-red-400' : item === '터널' ? 'bg-orange-400' : 'bg-yellow-400'} rounded-full`}></div>
            <span className={`${item === '넘뛰기' ? 'text-red-500' : item === '터널' ? 'text-orange-500' : 'text-yellow-500'} font-bold`}>{item}</span>
          </div>
        ))}
      </div>

      <div className="w-full max-w-sm h-4 bg-gray-200 rounded-lg overflow-hidden">
        <div className="h-full bg-orange-400 w-1/4 relative">
          <div className="absolute top-0 -right-2 w-6 h-6 bg-white border border-orange-400 rounded-full">
            🐾
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 h-auto gap-4 w-full max-w-md px-4">
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

      <div className="w-full max-w-sm flex items-center space-x-2 border-t pt-2 absolute bottom-5">
        <span className="font-bold">화살표</span>
        <input
          type="text"
          className="flex-1 p-2 border rounded-lg focus:outline-none"
          placeholder="기미"
        />
      </div>
    </div>
  );
}

export default InGame;
