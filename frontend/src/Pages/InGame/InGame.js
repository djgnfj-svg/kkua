import { useEffect, useState } from 'react';
import TopMsgAni from './TopMsg_Ani';
import useTopMsg from './TopMsg';
import Layout from './Layout';
import Timer from './Timer';
import userIsTrue from '../../Component/userIsTrue';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';
import { gameLobbyUrl, gameUrl } from '../../Component/urls';

const time_gauge = 40;

function InGame() {
  const [itemList, setItemList] = useState([]);

  // 퀴즈 제시어 
  const [quizMsg, setQuizMsg] = useState('햄'); // 초기 시작 단어

  const {gameid} = useParams();

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
  const [catActive, setCatActive] = useState(true);

  const { timeLeft, resetTimer } = Timer(120, () => {
    setMessage('게임종료!');
     // 3초 뒤 메시지 제거
    setTimeout(() => {
    setMessage('');
  }, 3000);
  });

  const [usedLog, setUsedLog] = useState([]);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const [specialPlayer, setSpecialPlayer] = useState('부러');
  const navigate = useNavigate()

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
      const currentIndex = players.indexOf(prev);
      const nextIndex = (currentIndex + 1) % players.length;
      return players[nextIndex];
    });
 
    setTypingText('');
    setPendingItem(null);
    setInputTimeLeft(12);
    setCatActive(true); // resume cat
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
        setCatActive(false); // 고양이 정지
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
      alert("5252 난아직 이 게임을 끝낼 생각이 없다고");
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
        frozenTime={frozenTime} // add this line
      />
      <div className="fixed bottom-4 left-4 z-50">
        <button
          onClick={handleClickFinish}
          className="bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:bg-red-600 transition"
        >
          게임 종료
        </button>
      </div>
    </>
  )
}

export default InGame;
