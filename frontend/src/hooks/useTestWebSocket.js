import { useState, useEffect, useRef } from 'react';

function useTestWebSocket(roomId) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const socketRef = useRef(null);

  useEffect(() => {
    if (!roomId) return;

    const wsUrl = `ws://localhost:8000/ws/test/gamerooms/${roomId}`;
    console.log('🔌 Connecting to:', wsUrl);

    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
      console.log('✅ Connected!');
      setConnected(true);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log('📨 Message:', data);
      
      // 게임 시작 메시지 처리
      if (data.type === 'game_started') {
        // 게임 페이지로 이동
        setTimeout(() => {
          window.location.href = `/keaing/${data.room_id}`;
        }, 2000);
      }
      
      setMessages(prev => [...prev, data]);
    };

    socket.onerror = (error) => {
      console.error('❌ Error:', error);
    };

    socket.onclose = () => {
      console.log('🔌 Disconnected');
      setConnected(false);
    };

    socketRef.current = socket;

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [roomId]);

  const sendMessage = (message) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    }
  };

  return { connected, messages, sendMessage };
}

export default useTestWebSocket;