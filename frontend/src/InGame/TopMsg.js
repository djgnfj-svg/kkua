// TopMsg.js (로직 전용, 중복 검사 포함)
import { useState } from 'react';

export default function useTopMsg({ inputValue, itemList, usedLog, setItemList, setUsedLog, setMessage, setInputValue, setTypingText, setPendingItem }) {
  const crashMessage = () => {
    const trim = inputValue.trim();
    if (!trim) return;

    const isDuplicate = usedLog.includes(trim);

    if (isDuplicate) {
      setMessage(`이미 입력된 단어입니다: ${trim}`);
      setTimeout(() => setMessage(''), 3000);
      setInputValue('');
      return;
    }

    const db = itemList.find(item => item.word === trim);
    const desc = db ? db.desc : '아직 기본설명 부족. 데이터부족';

    // 애니메이션용 대기 데이터 저장
    setTypingText(trim);
    setPendingItem({ word: trim, desc });
    setMessage('');
    setInputValue('');
  };

  return { crashMessage };
}