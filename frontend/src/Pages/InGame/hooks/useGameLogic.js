import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { gameLobbyUrl } from '../../../Component/urls';
import userIsTrue from '../../../Component/userIsTrue';
import Timer from '../Timer';
import useTopMsg from '../TopMsg';

const time_gauge = 40;

const useGameLogic = () => {
  const { gameid } = useParams();
  const navigate = useNavigate();

  const [itemList, setItemList] = useState([]);
  const [quizMsg, setQuizMsg] = useState('햄');
  const [timeOver] = useState(false);
  const [frozenTime, setFrozenTime] = useState(null);
  const [inputTimeLeft, setInputTimeLeft] = useState(12);
  const [catActive, setCatActive] = useState(true);
  const [usedLog, setUsedLog] = useState([]);
  const [players] = useState(['하우두유', '부러', '김밥', '후러']);
  const [specialPlayer, setSpecialPlayer] = useState('부러');
  const [inputValue, setInputValue] = useState('');
  const [message, setMessage] = useState('');
  const [showCount, setShowCount] = useState(3);
  const [typingText, setTypingText] = useState('');
  const [pendingItem, setPendingItem] = useState(null);

  const { timeLeft, resetTimer } = Timer(120, () => {
    setMessage('게임종료!');
    setTimeout(() => {
      setMessage('');
    }, 3000);
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
    setQuizMsg,
  });

  const setRandomQuizWord = useCallback(() => {
    if (itemList.length > 0) {
      const randomWord =
        itemList[Math.floor(Math.random() * itemList.length)].word;
      setQuizMsg(randomWord);
    }
  }, [itemList]);

  useEffect(() => {
    setRandomQuizWord();
  }, [setRandomQuizWord]);

  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (!result) {
        alert('어멋 어딜들어오세요 Cut !');
        navigate('/');
      }
    };
    checkGuest();
  }, [navigate]);

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
      setInputTimeLeft((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
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
  }, [inputTimeLeft, inputValue, typingText, timeLeft, resetTimer, setRandomQuizWord]);

  const handleTypingDone = () => {
    if (!pendingItem) return;

    setItemList((prev) => {
      if (!prev.find((item) => item.word === pendingItem.word)) {
        return [...prev, pendingItem];
      }
      return prev;
    });

    setUsedLog((prev) => {
      if (!prev.includes(pendingItem.word)) {
        return [...prev, pendingItem.word];
      }
      return prev;
    });

    setQuizMsg(pendingItem.word.charAt(pendingItem.word.length - 1));

    setSpecialPlayer((prev) => {
      const currentIndex = players.indexOf(prev);
      const nextIndex = (currentIndex + 1) % players.length;
      return players[nextIndex];
    });

    setTypingText('');
    setPendingItem(null);
    setInputTimeLeft(12);
    setCatActive(true);
  };

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
      console.log(error);
      alert('5252 난아직 이 게임을 끝낼 생각이 없다고');
    }
  };

  return {
    itemList,
    quizMsg,
    timeOver,
    frozenTime,
    inputTimeLeft,
    catActive,
    usedLog,
    players,
    specialPlayer,
    inputValue,
    message,
    showCount,
    typingText,
    pendingItem,
    timeLeft,
    time_gauge,
    setInputValue,
    setInputTimeLeft,
    setSpecialPlayer,
    handleTypingDone,
    crashKeyDown,
    crashMessage,
    handleClickFinish,
  };
};

export default useGameLogic;
