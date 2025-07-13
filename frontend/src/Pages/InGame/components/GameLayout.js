import React from 'react';

const GameLayout = ({
  gameState,
  inputWord,
  isMyTurn,
  errorMessage,
  wsConnected,
  wsParticipants,
  handleInputChange,
  handleKeyPress,
  submitWord,
}) => {
  return (
    <div className="w-full h-screen bg-gradient-to-br from-blue-50 to-purple-50 overflow-hidden">
      <div className="h-1/5 flex flex-col items-center justify-center relative">
        <div className="absolute top-4 left-4 flex items-center space-x-4">
          <img src="/imgs/logo/kkeua_logoA.png" alt="끄아 로고" className="h-12" />
          {gameState && (
            <div className="text-sm text-gray-600">
              <div>라운드: {gameState.currentRound} / {gameState.maxRounds}</div>
              <div className={`${wsConnected ? 'text-green-600' : 'text-red-600'}`}>
                {wsConnected ? '연결됨' : '연결 끊김'}
              </div>
            </div>
          )}
        </div>

        {errorMessage ? (
          <div className="text-red-500 text-xl font-bold animate-bounce">
            {errorMessage}
          </div>
        ) : (
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-800">끝말잇기 게임</h2>
            {gameState.status === 'playing' && (
              <p className="text-gray-600 mt-2">
                현재 {gameState.currentPlayerNickname}님의 차례입니다
              </p>
            )}
          </div>
        )}
        
        <div className="absolute top-4 right-4 text-center">
          <div className="text-sm text-gray-600 mb-1">남은 시간</div>
          <div className={`text-3xl font-bold ${gameState.timeLeft <= 10 ? 'text-red-500 animate-pulse' : 'text-gray-800'}`}>
            {gameState.timeLeft}초
          </div>
          {gameState.timeLeft === 0 && <div className="text-red-500 text-sm mt-1 animate-bounce">시간 초과!</div>}
        </div>
      </div>

      <div className="h-3/5 flex flex-col items-center justify-center px-4">
        <div className="mb-8 text-center">
          <div className="text-lg text-gray-600 mb-2">
            {gameState?.lastCharacter ? 
              `"${gameState.lastCharacter}"로 시작하는 단어를 입력하세요` : 
              '다음 글자로 시작하는 단어를 입력하세요'}
          </div>
          <div className="text-6xl md:text-8xl font-bold text-purple-600 animate-pulse">
            {gameState?.lastCharacter || '시'}
          </div>
          {gameState?.currentWord && (
            <div className="text-lg text-gray-500 mt-2">
              이전 단어: <span className="font-semibold">{gameState.currentWord}</span>
            </div>
          )}
        </div>

        <div className="w-full max-w-md mb-6">
          <div className="relative">
            <input
              type="text"
              value={inputWord}
              onChange={(e) => handleInputChange(e.target.value)}
              onKeyDown={handleKeyPress}
              className={`w-full px-6 py-4 text-2xl text-center border-4 rounded-2xl focus:outline-none focus:shadow-lg transition-all duration-300 ${
                isMyTurn 
                  ? 'border-purple-300 focus:border-purple-500' 
                  : 'border-gray-300 bg-gray-100 cursor-not-allowed'
              }`}
              placeholder={isMyTurn ? "단어를 입력하세요..." : "다른 플레이어의 차례입니다..."}
              disabled={!isMyTurn}
              autoFocus={isMyTurn}
            />
            
            <div className="absolute -bottom-3 left-0 right-0 h-3 bg-gray-200 rounded-full overflow-hidden shadow-inner">
              <div
                className={`h-full transition-all ease-linear rounded-full relative ${
                  gameState.timeLeft <= 5 ? 'bg-red-500 animate-pulse' : 
                  gameState.timeLeft <= 10 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ 
                  width: `${gameState.turnTimeLimit 
                    ? Math.max(0, (gameState.timeLeft / gameState.turnTimeLimit) * 100)
                    : Math.max(0, (gameState.timeLeft / 30) * 100)}%`,
                  transitionDuration: '950ms'  // 1초보다 약간 빨라서 더 자연스럽게
                }}
              >
                {/* 진행바 그라데이션 효과 */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent rounded-full"></div>
                
                {/* 긴급 시간 경고 효과 */}
                {gameState.timeLeft <= 5 && gameState.timeLeft > 0 && (
                  <div className="absolute inset-0 bg-red-400 rounded-full animate-ping opacity-75"></div>
                )}
              </div>
              
              {/* 시간 표시 텍스트 */}
              <div className="absolute inset-0 flex items-center justify-center">
                <span className={`text-xs font-bold ${
                  gameState.timeLeft <= 10 ? 'text-white drop-shadow-md' : 'text-gray-600'
                }`}>
                  {gameState.timeLeft}초
                </span>
              </div>
            </div>
          </div>

          <button
            onClick={() => submitWord(inputWord)}
            disabled={!isMyTurn || !inputWord?.trim()}
            className={`w-full mt-4 py-3 text-xl font-bold rounded-2xl transform transition-all duration-200 shadow-lg ${
              isMyTurn && inputWord?.trim()
                ? 'bg-gradient-to-r from-purple-500 to-blue-500 text-white hover:from-purple-600 hover:to-blue-600 hover:scale-105'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            {!isMyTurn ? '대기 중...' : '제출하기'}
          </button>
        </div>

        <div className="w-full max-w-2xl">
          <div className="text-sm text-gray-600 mb-2 text-center">최근 사용된 단어들</div>
          <div className="flex flex-wrap justify-center gap-2">
            {gameState?.usedWords?.slice(-6).map((word, index) => (
              <div
                key={index}
                className="px-4 py-2 bg-white rounded-full shadow-md text-sm animate-fadeIn"
                style={{
                  animationDelay: `${index * 0.1}s`
                }}
              >
                {word}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="h-1/5 bg-white/80 backdrop-blur-sm border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="text-sm text-gray-600">현재 차례</div>
            <div className="flex items-center space-x-2">
              <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold ${
                isMyTurn ? 'bg-green-500 animate-pulse' : 'bg-purple-500'
              }`}>
                {gameState?.currentPlayerNickname?.charAt(0) || '?'}
              </div>
              <span className="text-xl font-bold text-gray-800">
                {gameState?.currentPlayerNickname || '대기 중'}
                {isMyTurn && <span className="text-green-500 ml-2">(나)</span>}
              </span>
            </div>
          </div>

          <div className="flex items-center">
            <img
              src="/imgs/cat_workingA.gif"
              alt="Working Cat"
              className="w-16 h-16 md:w-20 md:h-20"
            />
          </div>

          <div className="hidden md:flex items-center space-x-2">
            {wsParticipants.map((participant, index) => (
              <div
                key={index}
                className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 ${
                  participant?.nickname === gameState?.currentPlayerNickname
                    ? 'bg-purple-500 text-white scale-110 shadow-lg'
                    : 'bg-gray-200 text-gray-600'
                }`}
              >
                {participant.nickname?.charAt(0) || '?'}
              </div>
            ))}
          </div>
        </div>
      </div>

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
