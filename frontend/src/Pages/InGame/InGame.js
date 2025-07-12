import React from 'react';
import GameLayout from './components/GameLayout';
import GameControls from './components/GameControls';
import useGameLogic from './hooks/useGameLogic';
import useWordChain from './hooks/useWordChain';

function InGame() {
  const {
    itemList,
    quizMsg,
    timeOver,
    frozenTime,
    inputTimeLeft,
    catActive,
    players,
    specialPlayer,
    inputValue,
    message,
    showCount,
    typingText,
    timeLeft,
    time_gauge,
    setInputValue,
    setInputTimeLeft,
    setSpecialPlayer,
    handleTypingDone,
    crashKeyDown,
    crashMessage,
    handleClickFinish,
  } = useGameLogic();

  const {
    gameState: wordChainState,
    inputWord,
    isMyTurn,
    errorMessage,
    connected: wsConnected,
    participants: wsParticipants,
    handleInputChange,
    handleKeyPress,
    submitWord,
  } = useWordChain();

  return (
    <>
      <GameLayout
        // WebSocket 기반 실시간 데이터
        wordChainState={wordChainState}
        inputWord={inputWord}
        isMyTurn={isMyTurn}
        errorMessage={errorMessage}
        wsConnected={wsConnected}
        wsParticipants={wsParticipants}
        handleInputChange={handleInputChange}
        handleKeyPress={handleKeyPress}
        submitWord={submitWord}
        // 기존 mock 데이터 (fallback)
        typingText={typingText}
        handleTypingDone={handleTypingDone}
        quizMsg={wordChainState.lastCharacter || quizMsg}
        message={errorMessage || message}
        timeLeft={wordChainState.timeLeft > 0 ? wordChainState.timeLeft : (frozenTime ?? timeLeft)}
        timeOver={timeOver}
        itemList={wordChainState.usedWords.length > 0 ? wordChainState.usedWords.map(word => ({ word })) : itemList}
        showCount={showCount}
        players={wsParticipants.length > 0 ? wsParticipants.map(p => p.nickname) : players}
        specialPlayer={wordChainState.currentPlayerNickname || specialPlayer}
        setSpecialPlayer={setSpecialPlayer}
        inputValue={inputWord || inputValue}
        setInputValue={handleInputChange}
        crashKeyDown={handleKeyPress}
        crashMessage={() => submitWord(inputWord)}
        time_gauge={time_gauge}
        inputTimeLeft={wordChainState.timeLeft > 0 ? wordChainState.timeLeft : inputTimeLeft}
        setInputTimeLeft={setInputTimeLeft}
        catActive={catActive}
        frozenTime={frozenTime}
      />
      <GameControls handleClickFinish={handleClickFinish} />
    </>
  );
}

export default InGame;
