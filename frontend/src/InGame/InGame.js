// src/InGame/InGame.js
import { useEffect, useState } from 'react';
import TopMsgAni from './TopMsg_Ani';
import useTopMsg from './TopMsg';

const time_gauge = 40;

function InGame() {
  const [itemList, setItemList] = useState([
    { word: '햄스터', desc: '쥐과 동물이다' },
    { word: '터널', desc: '지나갈 수 있는 커다란 구멍을 뜻한다. 특히 도로 위 자동차' },
    { word: '널뛰기', desc: '사람이 올라갈 수 있는 크기의 시소 모양 기구이다. 사람이 점프하여 일어난 반동으로 반대편에 힘 응애 췡췡 보냄' }, 
    { word: '기분', desc: '심리적으로 느껴지는 뇌의 화학반응 활동' }  
  ]);

  const [usedLog, setUsedLog] = useState([]);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';

  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const [showCount, setShowCount] = useState(3);

  // 애니메이션 상태
  const [typingText, setTypingText] = useState('');
  const [pendingItem, setPendingItem] = useState(null);

  const { crashMessage } = useTopMsg({
    inputValue,
    itemList,
    usedLog,
    setItemList,
    setUsedLog,
    setMessage,
    setInputValue,
    setTypingText,
    setPendingItem
  });

  const handleTypingDone = () => {
    if (!pendingItem) return;
    setUsedLog(prev => [...prev, pendingItem.word]);
    setItemList(prev => [...prev, pendingItem]);
    setPendingItem(null);
    setTypingText('');
  };

  useEffect(() => {
    const updateCount = () => {
      const isWide = window.innerWidth >= 1024;
      setShowCount(isWide ? 4 : 3);
    };
    updateCount();
    window.addEventListener('resize', updateCount);
    return () => window.removeEventListener('resize', updateCount);
  }, []);

  const crashKeyDown = (e) => {
    if (e.key === 'Enter') {
      crashMessage();
    }
  };

  return (
    <div className="w-full flex justify-center bg-white lg:pb-[100px]">
      <div className="min-h-screen px-2 py-2 flex flex-col md:flex-row md:space-x-6 md:justify-center md:items-start w-full max-w-[1024px]">
        <div className="hidden md:flex flex-col items-start mt-[220px] pl-4 space-y-6 w-[170px] shrink-0">
          <div className="text-sm font-bold ml-1">ㅋㅋ 그것도 모름?</div>
          <img src="/imgs/cat_book.png" alt="고양이" className="w-24 ml-2" />
        </div>

        <div className="flex-1 max-w-[600px] flex flex-col items-center space-y-4">
          <h1 className="text-3xl font-extrabold mt-4 mb-2">120초</h1>
          <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-full text-center font-bold shadow-lg bg-white text-xl leading-tight">
            {typingText && (
              <TopMsgAni text={typingText} onDone={handleTypingDone} />
            )}
            {message && (
              <div className="text-red-500 text-sm font-normal mt-1">{message}</div>
            )}
          </div>

          <div className="w-full max-w-sm relative h-8">
            <div className="h-6 bg-gray-200 rounded-full">
              <div className="h-full bg-orange-400 w-1/4 relative z-10 rounded-full"></div>
            </div>
            <img
              src={time_gauge <= 70 ? '/imgs/cat_walking.gif' : '/imgs/cat_running.gif'}
              className="absolute z-20 -top-4 right-[10%] w-14 h-14 scale-x-[-1]"
              alt="cat_walking"
            />
          </div>

          <div className="w-full md:w-[540px] px-2 md:px-4 space-y-4 tracking-wide">
            <div className="bg-gray-100 p-6 rounded-xl space-y-4 pb-10 mb-2">
              {itemList.slice(-showCount).map((item, index) => (
                <div key={index} className="p-4 rounded-2xl border shadow-lg bg-white border-gray-300 drop-shadow-md">
                  <div className="flex items-center space-x-4 ml-2">
                    <div className={`w-8 h-8 ${index === 0 ? 'bg-blue-400' : index === 1 ? 'bg-green-400' : 'bg-purple-400'} rounded-full`}></div>
                    <span className="font-semibold text-lg text-black">
                      {item.word.slice(0, -1)}<span className="text-red-500">{item.word.slice(-1)}</span>
                    </span>
                  </div>
                  <div className="text-gray-500 text-sm ml-2 mt-2 break-words max-w-md text-left">
                    {item.desc}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="w-full flex justify-center md:justify-end mt-[20px] pr-4">
          <div className="grid grid-cols-2 md:grid-cols-1 gap-6 place-items-center max-w-fit">
            {players.map((player, index) => (
              <div key={index} className={`w-[150px] h-[150px] rounded-lg border-[3px] flex items-center justify-center font-bold text-base ${player === specialPlayer ? 'bg-orange-100 border-orange-400 text-orange-500' : 'bg-gray-100 border-gray-300 text-black'}`}>
                {player}
              </div>
            ))}
          </div>
        </div>

        <div style={{ height: "70" }}></div>
        <br /><br /><br />

        <div className="w-full max-w-xl mx-auto flex items-center space-x-2 px-4 py-4 fixed bottom-0 bg-white z-50 rounded-t-lg border-t border-gray">
          <span className="font-bold">⇈</span>
          <input
            type="text"
            className="flex-1 p-2 h-10 border rounded-lg focus:outline-none"
            placeholder="즐거운 끄아와"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={crashKeyDown}
          />
          <span className="font-bold" onClick={crashMessage}>전송</span>
        </div>
      </div>
    </div>
  );
}

export default InGame;