import { useEffect, useState } from 'react';
import TopMsgAni from './Section/TopMsg_Ani';
import useTopMsg from './Section/TopMsg';
import Layout from './Section/Layout';
import Timer from './Section/Timer';
import userIsTrue from '../../Component/userIsTrue';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';
import { gameLobbyUrl, gameUrl } from '../../Component/urls';
import useGameRoomSocket from '../../hooks/useGameRoomSocket';
import guestStore from '../../store/guestStore';

const time_gauge = 40;

function InGame() {
  const [itemList, setItemList] = useState([]);

  // 퀴즈 제시어 
  const [quizMsg, setQuizMsg] = useState('햄'); // 초기 시작 단어

  const {gameid} = useParams();

  const {
    participants: socketParticipants,
    gameStatus,
    isReady,
    sendMessage,
    toggleReady,
    updateStatus,
    roomUpdated,
    setRoomUpdated,
    finalResults,
    setFinalResults
  } = useGameRoomSocket(gameid);

  const setRandomQuizWord = () => {
    if (itemList.length > 0) {
      const randomWord = itemList[Math.floor(Math.random() * itemList.length)].word;
      setQuizMsg(randomWord);
    }
  };

  useEffect(() => {
    setRandomQuizWord();
  }, []);
  
  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (!result) {
        alert("어멋 어딜들어오세요 Cut !");
        navigate("/")
      }
    };
    checkGuest();
  }, []);

  const [timeOver, setTimeOver] = useState(false);
  const [frozenTime, setFrozenTime] = useState(null);
  const [inputTimeLeft, setInputTimeLeft] = useState(12);

  const { timeLeft, resetTimer } = Timer(120, () => {
    setMessage('게임종료!');
     // 3초 뒤 메시지 제거
    setTimeout(() => {
    setMessage('');
  }, 3000);
  });

  const [usedLog, setUsedLog] = useState([]);
  const [specialPlayer, setSpecialPlayer] = useState('부러');
  const navigate = useNavigate()

  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const [showCount, setShowCount] = useState(3);

  // 애니메이션 상태
  const [typingText, setTypingText] = useState('');
  const [pendingItem, setPendingItem] = useState(null);

  const [reactionTimes, setReactionTimes] = useState([]);

  const { crashMessage } = useTopMsg({
    inputValue,
    itemList,
    usedLog,
    setItemList,
    setUsedLog,
    setMessage,
    setInputValue,
    setTypingText,
    setPendingItem,
    quizMsg,
    setQuizMsg
  });

  const handleTypingDone = () => {
    if (!pendingItem) return;
 
    setUsedLog(prev => {
      if (!prev.includes(pendingItem.word)) {
        return [...prev, pendingItem.word];
      }
      return prev;
    });
 
    setItemList(prev => {
      if (!prev.find(item => item.word === pendingItem.word)) {
        return [...prev, pendingItem];
      }
      return prev;
    });
 
    setQuizMsg(pendingItem.word.charAt(pendingItem.word.length - 1));
 
    setSpecialPlayer(prev => {
      const currentIndex = socketParticipants.map(p => p.nickname).indexOf(prev);
      const nextIndex = (currentIndex + 1) % socketParticipants.length;
      return socketParticipants[nextIndex]?.nickname || prev;
    });
 
    setTypingText('');
    setPendingItem(null);
    setInputTimeLeft(12);

    setReactionTimes(prev => [...prev, 12 - inputTimeLeft]);
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

  useEffect(() => {
    const timer = setInterval(() => {
      setInputTimeLeft(prev => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, []);
  
  useEffect(() => {
    if (inputTimeLeft === 0 && inputValue.trim() === '' && typingText === '') {
      setTimeout(() => {
        setMessage('게임종료!');
        setFrozenTime(timeLeft);
        setRandomQuizWord();
        resetTimer(); // 상단 타이머 종료
      }, 500); // Wait for gauge and cat animation to visibly finish
    }
  }, [inputTimeLeft, inputValue, typingText]);

  const crashKeyDown = (e) => {
    if (e.key === 'Enter') {
      crashMessage();
    }
  };

  const handleClickFinish = async () => {
    try{
      await axiosInstance.post(ROOM_API.END_ROOMS(gameid))
      navigate(gameLobbyUrl(gameid))
    }catch(error){
      console.log(error)
      alert("종료된 게임이 아닙니다.");
    }
  }

  return (
    <>
      <Layout
        typingText={typingText}
        handleTypingDone={handleTypingDone}
        //message={message}
        quizMsg={quizMsg}
        message={timeOver ? '시간 초과!' : message}
        timeLeft={frozenTime ?? timeLeft}
        timeOver={timeOver}
        itemList={itemList}
        showCount={showCount}
        players={socketParticipants.map(p => p.nickname)}
        specialPlayer={specialPlayer}
        setSpecialPlayer={setSpecialPlayer}
        inputValue={inputValue}
        setInputValue={setInputValue}
        crashKeyDown={crashKeyDown}
        crashMessage={crashMessage}
        time_gauge={time_gauge}
        inputTimeLeft={inputTimeLeft}
        setInputTimeLeft={setInputTimeLeft}
        socketParticipants={socketParticipants}
        finalResults={finalResults}
        usedLog={usedLog}
        reactionTimes={reactionTimes}
        handleClickFinish={handleClickFinish}
      />
      {socketParticipants.length > 0 && (
        <div className="fixed bottom-4 left-4 z-50">
          {guestStore.getState().guest_id === socketParticipants.find(p => p.is_owner)?.guest_id ? (
            <button
              onClick={handleClickFinish}
              className="bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:bg-red-600 transition"
            >
              게임 종료
            </button>
          ) : (
            <button
              onClick={() => navigate(gameLobbyUrl(gameid))}
              className="bg-gray-500 text-white px-4 py-2 rounded-lg shadow hover:bg-gray-600 transition"
            >
              로비 이동
            </button>
          )}
        </div>
      )}
    </>
  )
}

export default InGame;
