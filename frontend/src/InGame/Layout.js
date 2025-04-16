import TopMsgAni from './TopMsg_Ani';
import Timer from './Timer';

function Layout({
  quizMsg, 
  typingText,
  handleTypingDone,
  message,
  itemList,
  showCount,
  players,
  specialPlayer,
  inputValue,
  setInputValue,
  crashKeyDown,
  crashMessage,
  time_gauge,
  timeLeft
}) {
  return (
    <div className="w-full flex justify-center bg-white lg:pb-[100px]">
      <div className="min-h-screen px-2 py-2 flex flex-col md:flex-row md:space-x-6 md:justify-center md:items-start w-full max-w-[1024px]">

        {/* 왼쪽 고양이 */}
        <div className="hidden md:flex flex-col items-start mt-[220px] pl-4 space-y-6 w-[170px] shrink-0">
          <div className="text-sm font-bold ml-1">ㅋㅋ 그것도 모름?</div>
          <img src="/imgs/cat_book.png" alt="고양이" className="w-24 ml-2" />
        </div>

        {/* 중앙 타이핑 영역 */}
      <div className="flex-1 max-w-[600px] flex flex-col items-center space-y-4">
        
        {/* 남은 시간 */}
        <h1 className="text-3xl font-extrabold mt-4 mb-2">{timeLeft}초</h1>

        <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-full text-center font-bold shadow-lg bg-white text-xl leading-tight h-20 flex flex-col justify-center">
          {/* 항상 보이는 제시어 */}
          <div className="text-orange-500 text-lg">{quizMsg}</div>

          {/* 애니메이션 메시지 */}
          {typingText && <TopMsgAni text={typingText} onDone={handleTypingDone} />}

          {/* 피드백 메시지 (중복 등) */}
          {message && <div className="text-red-500 text-sm font-normal">{message}</div>}
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

        {/* 오른쪽 유저들 */}
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

        {/* 하단 입력창 */}
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

export default Layout;