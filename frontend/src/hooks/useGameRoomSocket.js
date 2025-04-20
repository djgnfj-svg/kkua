import { useEffect, useRef, useState } from 'react';
import guestStore from '../store/guestStore';

// 웹소켓 URL
const GAMEROOM_SOCKET_URL = (roomId, guestId) => `ws://localhost:8000/ws/gamerooms/${roomId}/${guestId}`;

export default function useGameRoomSocket(roomId) {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [gameStatus, setGameStatus] = useState('waiting');
    const socketRef = useRef(null);

    useEffect(() => {
        if (roomId) {
            // guestStore에서 UUID 가져오기
            const { uuid } = guestStore.getState();

            if (!uuid) {
                console.error("UUID가 없습니다. 로그인이 필요합니다.");
                return;
            }

            console.log(`웹소켓 연결 시도: /ws/gamerooms/${roomId}/${uuid}`);

            // 웹소켓 연결 생성
            const socket = new WebSocket(`${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/gamerooms/${roomId}/${uuid}`);
            socketRef.current = socket;

            socket.onopen = () => {
                console.log("웹소켓 연결 성공!");
                setConnected(true);
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log("메시지 수신:", data);

                    // 메시지 유형에 따라 처리
                    if (data.type === 'chat') {
                        // 서버에서 오는 메시지 형식 확인 후 처리
                        const messageContent = data.content || data.message || data;
                        // 로그로 실제 데이터 형식 확인
                        console.log("채팅 메시지 데이터:", messageContent);

                        // 다양한 형식 지원
                        const formattedMessage = typeof messageContent === 'string'
                            ? { message: messageContent }
                            : messageContent;

                        setMessages(prev => [...prev, formattedMessage]);
                    } else if (data.type === 'user_update') {
                        setParticipants(data.participants || []);
                    } else if (data.type === 'game_status') {
                        setGameStatus(data.status);
                    }
                } catch (error) {
                    console.error("메시지 처리 오류:", error);
                }
            };

            socket.onclose = (event) => {
                console.log("웹소켓 연결 종료:", event.code, event.reason);
                setConnected(false);
            };

            socket.onerror = (error) => {
                console.error("웹소켓 오류:", error);
                setConnected(false);
            };
        }

        return () => {
            // 컴포넌트 언마운트 시 소켓 닫기
            if (socketRef.current) {
                socketRef.current.close();
            }
        };
    }, [roomId]); // UUID는 변경될 수 있지만 페이지가 로드될 때 한 번만 연결

    // 메시지 전송 함수
    const sendMessage = (message) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'chat',
                message
            }));
        } else {
            console.error("웹소켓이 연결되지 않았습니다");
        }
    };

    // 상태 업데이트 함수 (준비 또는 시작)
    const updateStatus = (status) => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'status',
                status
            }));
        } else {
            console.error("웹소켓이 연결되지 않았습니다");
        }
    };

    return {
        connected,
        messages,
        participants,
        gameStatus,
        sendMessage,
        updateStatus
    };
} 