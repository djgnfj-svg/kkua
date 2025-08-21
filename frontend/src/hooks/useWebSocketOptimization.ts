import { useRef, useCallback } from 'react';

interface BatchedMessage {
  type: string;
  data: any;
  timestamp: number;
}

export const useWebSocketOptimization = () => {
  const messageQueue = useRef<BatchedMessage[]>([]);
  const batchTimeout = useRef<NodeJS.Timeout | null>(null);

  const sendBatchedMessage = useCallback((ws: WebSocket | null, type: string, data: any) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;

    // 중요한 메시지는 즉시 전송
    const immediateTypes = ['submit_word', 'use_item', 'leave_room'];
    if (immediateTypes.includes(type)) {
      ws.send(JSON.stringify({ type, ...data }));
      return;
    }

    // 일반 메시지는 배칭
    messageQueue.current.push({
      type,
      data,
      timestamp: Date.now()
    });

    // 배치 타이머 설정
    if (batchTimeout.current) {
      clearTimeout(batchTimeout.current);
    }

    batchTimeout.current = setTimeout(() => {
      if (messageQueue.current.length > 0 && ws.readyState === WebSocket.OPEN) {
        // 최근 100ms 내의 메시지만 전송
        const now = Date.now();
        const recentMessages = messageQueue.current.filter(
          msg => now - msg.timestamp < 100
        );

        if (recentMessages.length > 0) {
          ws.send(JSON.stringify({
            type: 'batched_messages',
            messages: recentMessages
          }));
        }

        messageQueue.current = [];
      }
    }, 50); // 50ms 배치 간격
  }, []);

  return { sendBatchedMessage };
};