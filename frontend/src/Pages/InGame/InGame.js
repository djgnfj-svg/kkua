import React from 'react';
import GameLayout from './components/GameLayout';
import GameControls from './components/GameControls';
import useGameLogic from './hooks/useGameLogic';

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
    setSpecialPlayer,
    handleTypingDone,
    crashKeyDown,
    crashMessage,
    handleClickFinish,
  } = useGameLogic();

  return (
    <>
      <GameLayout
        typingText={typingText}
        handleTypingDone={handleTypingDone}
        quizMsg={quizMsg}
        message={message}
        timeLeft={frozenTime ?? timeLeft}
        timeOver={timeOver}
        itemList={itemList}
        showCount={showCount}
        players={players}
        specialPlayer={specialPlayer}
        setSpecialPlayer={setSpecialPlayer}
        inputValue={inputValue}
        setInputValue={setInputValue}
        crashKeyDown={crashKeyDown}
        crashMessage={crashMessage}
        time_gauge={time_gauge}
        inputTimeLeft={inputTimeLeft}
        setInputTimeLeft={setInputTimeLeft}
        catActive={catActive}
        frozenTime={frozenTime}
      />
      <GameControls handleClickFinish={handleClickFinish} />
    </>
  );
}

export default InGame;
