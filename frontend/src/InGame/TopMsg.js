import msgData from './MsgData';

export default function useTopMsg({
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
}) {
  const crashMessage = () => {
    const trim = inputValue.trim();
    if (!trim) return;

    // 중복 검사
    if (usedLog.includes(trim)) {
      setMessage(`이미 입력된 단어입니다: ${trim}`);
      setTimeout(() => setMessage(''), 2000);
      setInputValue('');
      return;
    }

    // msgData 내 존재하는 단어인지 확인
    const found = msgData.find(item => item.word === trim);
    if (!found) {
      setMessage(`올바르지 않은 단어입니다.`);
      setTimeout(() => setMessage(''), 2000);
      setInputValue('');
      return;
    }

    // 끝말잇기 규칙 검사
    const prevLastChar = quizMsg[quizMsg.length - 1];
    const inputFirstChar = trim[0];
    if (prevLastChar !== inputFirstChar) {
      setMessage(`시작 글자가 잘못 되었습니다! 제시어는 '${quizMsg}'`);
      setTimeout(() => setMessage(''), 2000);
      setInputValue('');
      return;
    }

    // 정답 처리
    setTypingText(trim);
    setPendingItem({ word: trim, desc: found.desc });
    setMessage('');
    setInputValue('');

    // 다음 제시어 무작위 선택 (중복 제외)
    const remaining = msgData.filter(item =>
      !usedLog.includes(item.word) && item.word !== trim
    );
    if (remaining.length > 0) {
      const next = remaining[Math.floor(Math.random() * remaining.length)];
      setQuizMsg(next.word);
    }
  };

  return { crashMessage };
}
