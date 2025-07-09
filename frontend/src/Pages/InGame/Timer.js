import { useEffect, useState, useCallback } from 'react';

function Timer(initTime, onTimeOut) {
  const [timeLeft, setTimeLeft] = useState(initTime);

  const memoizedOnTimeOut = useCallback(() => {
    onTimeOut?.();
  }, [onTimeOut]);

  useEffect(() => {
    if (timeLeft <= 0) {
      memoizedOnTimeOut();
      return;
    }

    const timer = setTimeout(() => {
      setTimeLeft((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [timeLeft, memoizedOnTimeOut]);

  const resetTimer = () => setTimeLeft(initTime);
  return { timeLeft, resetTimer };
}

export default Timer;
