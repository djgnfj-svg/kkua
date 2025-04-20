import { useEffect, useState } from 'react';
import TopMsgAni from './TopMsg_Ani';
import Timer from './Timer';
import msgData from './MsgData';

function Layout({
  quizMsg, 
  typingText,
  handleTypingDone,
  message,
  itemList,
  showCount,
  players,
  specialPlayer,
  setSpecialPlayer,
  inputValue,
  setInputValue,
  crashKeyDown,
  crashMessage,
  timeLeft, // Added timeLeft prop
  inputTimeLeft, // Added inputTimeLeft prop
  setInputTimeLeft,
  setRandomQuizWord,
  setPendingItem, // Added setter here
  catActive, // Added catActive prop
  frozenTime, // add this line
}) {
  

  return (
    <div className="w-screen flex justify-center bg-white lg:pb-[100px] px-4">
      <div className="min-h-screen py-4 flex flex-col md:flex-row md:space-x-8 md:justify-center md:items-start w-full max-w-[1920px]">

        {/* 왼쪽 고양이 */}
        <div className="hidden md:flex flex-col items-start mt-[220px] pl-4 space-y-6 w-[170px] shrink-0">
          <div className="text-sm font-bold ml-1">ㅋㅋ 그것도 모름?</div>
          <img src="/imgs/icon/AddIcon.png" alt="고양이" className="w-24 ml-2" />
        </div>

        {/* 중앙 타이핑 영역 */}
      <div className="w-full flex flex-col items-center space-y-4 px-[5%]">
        
        {/* 남은 시간 */}
        <h1 className="text-3xl font-extrabold mt-4 mb-2">{frozenTime ?? timeLeft}초</h1>

        <div className="w-full max-w-sm p-4 border-4 border-orange-400 rounded-full text-center font-bold shadow-lg bg-white text-xl leading-tight h-16 flex flex-col justify-center">
          {/* 항상 보이는 제시어 */}
          <div className="text-orange-500 text-lg">
            {quizMsg.length > 1 && !msgData.find(item => item.word === quizMsg)
              ? quizMsg
              : quizMsg.charAt(quizMsg.length - 1)}
          </div>

          {/* 애니메이션 메시지 */}
          {typingText && <TopMsgAni text={typingText} onDone={handleTypingDone} />}

          {/* 피드백 메시지 (중복 등) */}
          {message && !typingText && (
            <div className="text-red-500 text-sm font-normal">
              {message}
            </div>
          )}
        </div>

          <div className="w-full md:w-[750px] px-2 md:px-4 space-y-4 tracking-wide">
            <div className="bg-gray-100 p-6 rounded-xl space-y-4 pb-10 mb-2 min-h-[480px]">
              {itemList.slice(-showCount).map((item, index) => (
                <div key={index} className="p-4 rounded-2xl border shadow-lg bg-white border-gray-300 drop-shadow-md">
                  <div className="flex items-center space-x-4 ml-2">
                    <div className={`w-8 h-8 ${index === 0 ? 'bg-blue-400' : index === 1 ? 'bg-green-400' : 'bg-purple-400'} rounded-full`}></div>
                    <span className="font-semibold text-lg text-black">
                      {item.word.slice(0, -1)}<span className="text-red-500">{item.word.charAt(item.word.length - 1)}</span>
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
        <div className="flex justify-center md:justify-end mt-[100px] pr-4">
          <div className="grid grid-cols-2 md:grid-cols-1 gap-6 place-items-center max-w-fit">
            {players.map((player, index) => (
              <div key={index} className="flex flex-col items-center space-y-2">
                <div
                  className={`w-[220px] h-[60px] px-2 rounded-lg border-[3px] flex items-center justify-between font-bold text-base space-x-3 ${
                    player === specialPlayer
                      ? 'bg-orange-100 border-orange-400 text-orange-500'
                      : 'bg-gray-100 border-gray-300 text-black'
                  }`}
                >
                  <div className="ml-2">{player}</div>
                  <div className="flex gap-1 mr-1">
                    {[0, 1, 2, 3].map((slot) => (
                      <div
                        key={slot}
                        className="w-5 h-5 rounded-[6px] border-2 border-orange-300 shadow-md"
                      ></div>
                    ))}
                  </div>
                </div>

                {/* 아이템리스트를 마지막 유저 아래에만 출력 */}
                {index === players.length - 1 && (
                  <div className="text-center mt-4">
                    <div className="text-base text-orange-500 font-bold mb-2">내 아이템</div>
                    <div className="grid grid-cols-2 gap-4 px-2">
                      {[0, 1, 2, 3].map((slot) => (
                        <div
                          key={slot}
                          className="w-16 h-16 rounded-[16px] border-[4px] border-orange-300 shadow-md bg-white"
                        ></div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        <div style={{ height: "70" }}></div>
        <br /><br /><br />

        {/* 하단 입력창 */}
        <div className="w-full fixed bottom-0 bg-white z-50 border-t border-gray">
          {/* 게이지 bar */}
          <div className={`relative h-1.5 w-full bg-gray-200`}>
            <div
              className={`absolute top-0 left-0 h-full ${inputTimeLeft <= 3 ? 'bg-red-400' : 'bg-orange-400'} rounded-r-full ${inputTimeLeft === 12 ? '' : 'transition-all duration-1000'}`}
              style={{
                width: `${(inputTimeLeft / 12) * 100}%`,
                transition: inputTimeLeft === 12 ? 'none' : 'width 1s linear',
              }}
            ></div>
            <img
              src={process.env.PUBLIC_URL + '/imgs/cat_working.gif'}
              alt="고양이"
              className={`absolute top-1/2 w-6 h-6 z-10 ${inputTimeLeft === 12 ? '' : 'transition-[left] ease-linear duration-1000'}`}
              style={{
                left: `${inputTimeLeft === 12 ? '100%' : (inputTimeLeft / 12) * 100 + '%'}`,
                transform: 'translate(-50%, -50%)',
              }}
            />
          </div>

          {/* 입력창 */}
          <div className="w-full px-[5%] flex items-center space-x-2 py-4">
            <span className="font-bold">⇈</span>
            <input
              type="text"
              className="flex-1 p-2 h-12 border rounded-lg focus:outline-none text-lg"
              placeholder="즐거운 끄아와"
              value={inputValue}
              onChange={(e) => {
                if (!typingText) {
                  setInputValue(e.target.value);
                }
              }}
              onKeyDown={crashKeyDown}
            />
            <span className="font-bold" onClick={crashMessage}>전송</span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Layout;