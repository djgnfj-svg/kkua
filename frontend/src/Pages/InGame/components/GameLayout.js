import React from 'react';
import TopMsgAni from '../TopMsg_Ani';

const GameLayout = ({
  typingText,
  handleTypingDone,
  quizMsg,
  message,
  timeLeft,
  timeOver,
  itemList,
  showCount,
  players,
  specialPlayer,
  setSpecialPlayer,
  inputValue,
  setInputValue,
  crashKeyDown,
  crashMessage,
  time_gauge,
  inputTimeLeft,
  setInputTimeLeft,
  catActive,
  frozenTime,
}) => {
  return (
    <div className="w-full h-screen bg-gradient-to-br from-blue-50 to-purple-50 overflow-hidden">
      {/* 상단 영역 - 게임 정보 및 메시지 */}
      <div className="h-1/5 flex flex-col items-center justify-center relative">
        <TopMsgAni
          typingText={typingText}
          onTypingDone={handleTypingDone}
          message={message}
        />
        
        {/* 타이머 영역 */}
        <div className="absolute top-4 right-4 text-center">
          <div className="text-sm text-gray-600 mb-1">남은 시간</div>
          <div className={`text-3xl font-bold ${timeLeft <= 10 ? 'text-red-500 animate-pulse' : 'text-gray-800'}`}>
            {timeLeft}초
          </div>
          {timeOver && <div className="text-red-500 text-sm mt-1 animate-bounce">시간 초과!</div>}
        </div>

        {/* 로고 */}
        <div className="absolute top-4 left-4">
          <img src="/imgs/logo/kkeua_logoA.png" alt="끄아 로고" className="h-12" />
        </div>
      </div>

      {/* 중앙 영역 - 게임 플레이 */}
      <div className="h-3/5 flex flex-col items-center justify-center px-4">
        {/* 현재 단어 표시 */}
        <div className="mb-8 text-center">
          <div className="text-lg text-gray-600 mb-2">다음 글자로 시작하는 단어를 입력하세요</div>
          <div className="text-6xl md:text-8xl font-bold text-purple-600 animate-pulse">
            {quizMsg}
          </div>
        </div>

        {/* 입력 영역 */}
        <div className="w-full max-w-md mb-6">
          <div className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={crashKeyDown}
              className="w-full px-6 py-4 text-2xl text-center border-4 border-purple-300 rounded-2xl focus:outline-none focus:border-purple-500 focus:shadow-lg transition-all duration-300"
              placeholder="단어를 입력하세요..."
              autoFocus
            />
            
            {/* 입력 시간 게이지 */}
            <div className="absolute -bottom-2 left-0 right-0 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-1000 ${
                  inputTimeLeft <= 3 ? 'bg-red-500 animate-pulse' : 'bg-green-500'
                }`}
                style={{ width: `${(inputTimeLeft / time_gauge) * 100}%` }}
              />
            </div>
          </div>

          <button
            onClick={crashMessage}
            className="w-full mt-4 py-3 bg-gradient-to-r from-purple-500 to-blue-500 text-white text-xl font-bold rounded-2xl hover:from-purple-600 hover:to-blue-600 transform hover:scale-105 transition-all duration-200 shadow-lg"
          >
            제출하기
          </button>
        </div>

        {/* 사용된 단어 미리보기 */}
        <div className="w-full max-w-2xl">
          <div className="text-sm text-gray-600 mb-2 text-center">최근 사용된 단어들</div>
          <div className="flex flex-wrap justify-center gap-2">
            {itemList.slice(-6).map((item, index) => (
              <div
                key={index}
                className="px-4 py-2 bg-white rounded-full shadow-md text-sm animate-fadeIn"
                style={{
                  animationDelay: `${index * 0.1}s`
                }}
              >
                {item.word}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 하단 영역 - 플레이어 정보 */}
      <div className="h-1/5 bg-white/80 backdrop-blur-sm border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          {/* 현재 플레이어 */}
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">현재 차례</div>
            <div className="flex items-center space-x-2">
              <div className="w-12 h-12 bg-purple-500 rounded-full flex items-center justify-center text-white font-bold">
                {specialPlayer.charAt(0)}
              </div>
              <span className="text-xl font-bold text-gray-800">{specialPlayer}</span>
            </div>
          </div>

          {/* 고양이 캐릭터 */}
          <div className="flex items-center">
            {catActive ? (
              <img
                src="/imgs/cat_runningA.gif"
                alt="Running Cat"
                className="w-16 h-16 md:w-20 md:h-20"
              />
            ) : (
              <img
                src="/imgs/cat_workingA.gif"
                alt="Working Cat"
                className="w-16 h-16 md:w-20 md:h-20"
              />
            )}
          </div>

          {/* 플레이어 목록 */}
          <div className="hidden md:flex items-center space-x-2">
            {players.map((player, index) => (
              <div
                key={index}
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                  player === specialPlayer
                    ? 'bg-purple-500 text-white scale-110 shadow-lg'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {player.charAt(0)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 애니메이션 스타일 */}
      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-fadeIn {
          animation: fadeIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default GameLayout;
