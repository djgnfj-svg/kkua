import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../Api/axiosInstance';
import { ROOM_API } from '../../Api/roomApi';
import { gameLobbyUrl } from '../../Component/urls';
import Layout from './Layout';
import Timer from './Timer';
import useTopMsg from './TopMsg';
import TopMsgAni from './TopMsg_Ani';

import { connectSocket } from './Socket/mainSocket';
import { sendWordToServer } from './Socket/kdataSocket';

const time_gauge = 40;

function InGame() {
  const [itemList, setItemList] = useState([]);
  const [quizMsg, setQuizMsg] = useState('햄');
  const { gameid } = useParams();
  const navigate = useNavigate();

  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const [typingText, setTypingText] = useState('');
  const [pendingItem, setPendingItem] = useState(null);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const [specialPlayer, setSpecialPlayer] = useState('부러');
  const [timeOver, setTimeOver] = useState(false);
  const [frozenTime, setFrozenTime] = useState(null);
  const [inputTimeLeft, setInputTimeLeft] = useState(12);
  const [catActive, setCatActive] = useState(true);
  const [showCount, setShowCount] = useState(3);
  const [usedLog, setUsedLog] = useState([]);

  const { timeLeft, resetTimer } = Timer(120, () => {
    setMessage('게임종료!');
    setTimeout(() => setMessage(''), 3000);
  });

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

  useEffect(() => {
    async function prepareGuestAndConnect() {
      try {
        let guestUuid = document.cookie
          .split('; ')
          .find(row => row.startsWith('kkua_guest_uuid='))
          ?.split('=')[1];
    
        if (!guestUuid) {
          console.log("✅ 게스트 UUID 없음 -> 로그인 요청");
          const loginRes = await axiosInstance.post('/guests/login');
          guestUuid = loginRes.data.uuid;
          document.cookie = `kkua_guest_uuid=${guestUuid}; path=/`;
        }
    
        console.log("✅ 방 입장 시도:", guestUuid, gameid);
    
        const joinRes = await axiosInstance.post(`/gamerooms/${gameid}/join`, {
          guest_uuid: guestUuid,
        });
    
        if (joinRes.status !== 200 && joinRes.status !== 201) {
          console.error('❌ 방 입장 실패: 응답코드', joinRes.status);
          alert("방 입장 실패! 서버 점검중일 수 있습니다.");
          navigate("/");
          return; // 🚫 여기서 아예 끊어
        }
    
        console.log("✅ 방 입장 성공:", joinRes.data);
        console.log("✅ 소켓 연결 시도");
        connectSocket(gameid);
    
      } catch (error) {
        console.error("❌ 방 입장 API 에러:", error.response?.data || error.message);
        alert("방 입장 실패 또는 서버 연결 실패");
        navigate("/");
      }
    }
  
    if (gameid) {
      prepareGuestAndConnect();
    }
  }, [gameid, navigate]);

  // 나머지 게임 로직은 기존 그대로 ↓↓↓
  const setRandomQuizWord = () => {
    if (itemList.length > 0) {
      const randomWord = itemList[Math.floor(Math.random() * itemList.length)].word;
      setQuizMsg(randomWord);
    }
  };

  useEffect(() => {
    setRandomQuizWord();
  }, []);

  const handleTypingDone = () => {
    if (!pendingItem) return;

    setUsedLog(prev => (!prev.includes(pendingItem.word) ? [...prev, pendingItem.word] : prev));
    setItemList(prev => (!prev.find(item => item.word === pendingItem.word) ? [...prev, pendingItem] : prev));
    setQuizMsg(pendingItem.word.charAt(pendingItem.word.length - 1));

    setSpecialPlayer(prev => {
      const currentIndex = players.indexOf(prev);
      return players[(currentIndex + 1) % players.length];
    });

    sendWordToServer({
      user: specialPlayer,
      word: pendingItem.word,
      itemUsed: false,
    });

    setTypingText('');
    setPendingItem(null);
    setInputTimeLeft(12);
    setCatActive(true);
  };

  useEffect(() => {
    const updateCount = () => setShowCount(window.innerWidth >= 1024 ? 4 : 3);
    updateCount();
    window.addEventListener('resize', updateCount);
    return () => window.removeEventListener('resize', updateCount);
  }, []);

  useEffect(() => {
    const timer = setInterval(() => setInputTimeLeft(prev => (prev > 0 ? prev - 1 : 0)), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (inputTimeLeft === 0 && inputValue.trim() === '' && typingText === '') {
      setTimeout(() => {
        setMessage('게임종료!');
        setFrozenTime(timeLeft);
        setRandomQuizWord();
        setCatActive(false);
        resetTimer();
      }, 500);
    }
  }, [inputTimeLeft, inputValue, typingText, timeLeft, resetTimer]);

  const crashKeyDown = (e) => {
    if (e.key === 'Enter') {
      crashMessage();
    }
  };

  const handleClickFinish = async () => {
    try {
      await axiosInstance.post(ROOM_API.END_ROOMS(gameid));
      navigate(gameLobbyUrl(gameid));
    } catch (error) {
      console.error(error);
      alert('5252 난 아직 이 게임을 끝낼 생각이 없다고');
    }
  };

  return (
    <>
      <Layout
        typingText={typingText}
        handleTypingDone={handleTypingDone}
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
        frozenTime={frozenTime}
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
  );
}

export default InGame;
