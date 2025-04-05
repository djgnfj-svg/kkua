import { useState } from 'react';

const time_gauge = 40; // 값이 올라가면 빨리 달림 70 되면 

function InGame() {
  const [itemList, setItemList] = useState([
    { word: '햄스터', desc: '쥐과 동물이다' },
    { word: '터널', desc: '지나갈 수 있는 커다란 구멍을 뜻한다. 특히 도로 위 자동차' },
    { word: '널뛰기', desc: '사람이 올라갈 수 있는 크기의 시소 모양 기구이다. 사람이 점프하여 일어난 반동으로 반대편에 힘 응애 췡췡 보냄' }
  ]);

  const [usedLog, setUsedLog] = useState([]); // 🆕 사용자 입력 히스토리


  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';

  const [inputValue, setInputValue] = useState(''); 
  const [message, setMessage] = useState(''); 

  
  //input 전송버튼 쪽에 연결함. 
  const crashMessage = () => {
    const trim = inputValue.trim(); 
    if(!trim) return; 

     // 오직 사용자가 이미 입력했던 단어만 중복으로 취급
    const usedLogCheck = usedLog.includes(trim); 

    if (usedLogCheck) {
      setMessage(`이미 입력된 단어입니다: ${trim}`);
      setTimeout(() => setMessage(''), 3000); 
    } else {
      const db = itemList.find(item => item.word === trim);
      const desc = db ? db.desc : '아직 기본설명 부족. 데이터부족';

      setUsedLog([...usedLog, trim]);
      setItemList([...itemList, { word: trim, desc }]);
      setMessage('');
    }

    setInputValue(''); 
  };

  //input바 쪽에 연결함. 
  const crashKeyDown = (e) => {
    if(e.key === 'Enter') {
      crashMessage(); 
    }
  }

  //아래 message는 오류용으로 
  //빨강 글씨. 일정 시간 지나면 사라져도 좋고 
  return (
  <div className="w-full flex justify-center bg-white">
    <div className="min-h-screen px-2 py-2 flex flex-col md:flex-row md:space-x-6 md:justify-center md:items-start w-full max-w-[1024px]">
      <div className="hidden md:flex flex-col items-start mt-[220px] pl-4 space-y-6 w-[170px] shrink-0">
        <div className="text-sm font-bold ml-1">ㅋㅋ 그것도 모름?</div>
        <img src="/imgs/cat_book.png" alt="고양이" className="w-24 ml-2" />
      </div>

      <div className="flex-1 max-w-[600px] flex flex-col items-center space-y-4">
        <h1 className="text-3xl font-extrabold mt-4 mb-2">120초</h1>
        <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-full text-center font-bold shadow-lg bg-white text-xl">
          콤보콤보콤보
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
          <div className="bg-gray-100 p-6 rounded-xl space-y-4">
            {items.slice(-3).map((item, index) => (
              <div
                key={index}
                className="p-4 rounded-2xl border shadow-lg bg-white border-gray-300 drop-shadow-md"
              >
                {/* 아이템 줄 (가로 정렬) */}
                <div className="flex items-center space-x-4 ml-2">
                  <div
                    className={`w-8 h-8 ${
                      index === 0 ? 'bg-blue-400' : index === 1 ? 'bg-green-400' : 'bg-purple-400'
                    } rounded-full`}
                  ></div>
                  <span className="font-semibold text-lg text-black">
                    {item.slice(0, -1)}
                    <span className="text-red-500">{item.slice(-1)}</span>
                  </span>
                </div>

                {/* 설명 줄 (아래로 줄바꿈됨) */}
                <div className="text-gray-500 text-sm ml-2 mt-2 break-words max-w-md text-left">
                  {subItems[index]}
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

      <div className="w-full flex justify-center md:justify-end mt-[20px] pr-4">
        <div className="grid grid-cols-2 md:grid-cols-1 gap-6 place-items-center max-w-fit">
          {players.map((player, index) => (
            <div key={index} className={`w-[150px] h-[150px] rounded-lg border-[3px] flex items-center justify-center font-bold text-base ${
              player === specialPlayer ? 'bg-orange-100 border-orange-400 text-orange-500' : 'bg-gray-100 border-gray-300 text-black'
            }`}>
              {player}
            </div>
          ))}
        </div>
      </div>

      <div style={{height:"70"}}>
      </div>
      <br></br>
      <br></br>
      <br></br>
    
      <div className="w-full max-w-xl mx-auto flex items-center space-x-2 px-4 py-4 fixed bottom-0 bg-white z-50 rounded-t-lg border-t border-gray">
        <span className="font-bold">⇈</span>
        <input
          type="text"
          className="flex-1 p-2 h-10 border rounded-lg focus:outline-none"
          placeholder="즐거운 끄아와"
        />
        <span className="font-bold" onClick={crashMessage}>전송</span>
      </div>
    </div>
  </div>
  );
}

export default InGame;  
