// src/InGame/InGame.js
import { useEffect, useState } from 'react';
import TopMsgAni from './TopMsg_Ani';
import useTopMsg from './TopMsg';
import Layout from './Layout';

const time_gauge = 40;

function InGame() {
  const [items, setItems] = useState(['햄스터', '터널', '널뛰기']);
  const [subItems, subSetItems] = useState(['쥐과 동물이다', '지나갈 수 있는 커다란 구멍을 뜻한다. 특히 도로 위 자동차', '사람이 올라갈 수 있는 크기의 시소 모양 기구이다. 사람이 점프하여 일어난 반동으로 반대편에 힘 응애 췡췡 보냄']);
  const [players, setPlayers] = useState(['하우두유', '부러', '김밥', '후러']);
  const specialPlayer = '부러';

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
    setPendingItem
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

  return (
    <Layout
      typingText={typingText}
      handleTypingDone={handleTypingDone}
      message={message}
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
  )
}

export default InGame;
