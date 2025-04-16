import { useEffect, useState } from 'react';
import TopMsgAni from './TopMsg_Ani';
import useTopMsg from './TopMsg';
import Layout from './Layout';
import Timer from './Timer';
import userIsTrue from '../Component/userIsTrue';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../Api/axiosInstance';
import { ROOM_API } from '../Api/roomApi';
import { gameLobbyUrl, gameUrl } from '../Component/urls';

const time_gauge = 40;

function InGame() {
  const [itemList, setItemList] = useState([
    { word: '햄스터', desc: '쥐과 동물이다' },
    { word: '터널', desc: '지나갈 수 있는 커다란 구멍을 뜻한다. 특히 도로 위 자동차' },
    { word: '널뛰기', desc: '사람이 올라갈 수 있는 크기의 시소 모양 기구이다. 사람이 점프하여 일어난 반동으로 반대편에 힘 응애 췡췡 보냄' }, 
    { word: '기분', desc: '심리적으로 느껴지는 뇌의 화학반응 활동' }  
  ]);

  // 퀴즈 제시어 
  const [quizMsg, setQuizMsg] = useState(''); // 초기값은 빈 문자열

  const {roomId , gameid} = useParams();

  useEffect(() => {
    if (itemList.length > 0) {
      const randomWord = itemList[Math.floor(Math.random() * itemList.length)].word;
      setQuizMsg(randomWord);
    }
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

  const { timeLeft, resetTimer } = Timer(120, () => {
    setMessage('게임종료!');
     // 3초 뒤 메시지 제거
    setTimeout(() => {
    setMessage('');
  }, 3000);
  });

  const [usedLog, setUsedLog] = useState([]);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';
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
        timeLeft={timeLeft}
        timeOver={timeOver}
        itemList={itemList}
        showCount={showCount}
        players={players}
        specialPlayer={specialPlayer}
        inputValue={inputValue}
        setInputValue={setInputValue}
        crashKeyDown={crashKeyDown}
        crashMessage={crashMessage}
        time_gauge={time_gauge}
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
