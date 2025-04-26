import React from 'react';
import { useEffect, useRef, useState } from 'react';
import guestStore from '../store/guestStore';

export const socketRef = React.createRef();

export default function useGameRoomSocket(roomId) {
    const [connected, setConnected] = useState(false);
    const [messages, setMessages] = useState([]);
    const [participants, setParticipants] = useState([]);
    const [gameStatus, setGameStatus] = useState();
    const [roomUpdated, setRoomUpdated] = useState(false);
    const [isReady, setIsReady] = useState(false);
    const [finalResults, setFinalResults] = useState([]);

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
                setRoomUpdated(true);
            };

            socket.onmessage = (event) => {
                const data = JSON.parse(event.data);
                console.log('소켓 메시지 수신:', data);
                console.log('🧾 [소켓 전체 수신 로그] 받은 데이터:', data);
                if (data.type === 'chat') {
                  const { guest_id } = guestStore.getState();
                  console.log('내 guest_id:', guest_id);
                  console.log('수신 guest_id:', data.guest_id);
                  console.log('수신 message_id:', data.message_id);

                  const isOwnMessage = false;

                  const alreadyExists = data.message_id
                    ? messages.some(msg => msg.message_id === data.message_id)
                    : false;

                  if (!isOwnMessage && !alreadyExists) {
                    setMessages(prev => [...prev, {
                      nickname: data.nickname,
                      message: typeof data.message === 'string' ? data.message : JSON.stringify(data.message),
                      guest_id: data.guest_id,
                      timestamp: data.timestamp,
                      type: data.type,
                      message_id: data.message_id || `${data.guest_id}-${Date.now()}`
                    }]);
                  }

                  // Detect word_chain -> start_game in chat message
                  if (
                    typeof data.message === 'object' &&
                    data.message.type === 'word_chain' &&
                    data.message.action === 'start_game'
                  ) {
                    console.log("🎯 word_chain -> start_game 감지됨: 상태 'playing'으로 설정");
                    setGameStatus('playing');
                  }
                } else if (data.type === 'participants_update') {
                    // 참가자 목록 직접 업데이트 (API 호출 없음)
                    console.log('웹소켓으로 참가자 목록 업데이트:', data.participants);
                    if (data.participants && Array.isArray(data.participants)) {
                        // 웹소켓으로 받은 참가자 정보를 userInfo 상태로 직접 사용
                        setParticipants(data.participants);

                        // 시스템 메시지로 추가 (입장/퇴장 알림)
                        if (data.message) {
                            setMessages((prev) => [...prev, {
                                nickname: "시스템",
                                message: data.message,
                                type: 'system',
                                timestamp: data.timestamp || new Date().toISOString()
                            }]);
                        }

                        // 방 업데이트 플래그 설정 - GameLobbyPage에서 감지하도록
                        setRoomUpdated(true);
                    }
                } else if (data.type === 'status_update' || data.type === 'game_status') {
                    console.log("✅ status_update 수신 후 처리 시작");
                    console.log("📥 게임 상태 메시지 수신:", data);
                    setGameStatus(prev => {
                        console.log("🔁 이전 상태:", prev, "➡️ 새로운 상태:", data.status);
                        return data.status;
                    });
                    console.log("✅ setGameStatus 실행됨:", data.status);
                    console.log("📡 [게임 상태 수신] 타입: status_update, 상태:", data.status);

                    if (data.status === 'playing') {
                        // ✅ 참가자 상태 일괄 업데이트
                        setParticipants(prev =>
                            prev.map(p => ({
                                ...p,
                                status: 'PLAYING'
                            }))
                        );
                    }
                } else if (data.type === 'word_chain_started') {
                    console.log("🎯 끝말잇기 게임 시작 알림 수신");
                    setGameStatus('playing');

                    // 👉 참가자 상태를 모두 'PLAYING'으로 변경
                    setParticipants(prev =>
                      prev.map(p => ({
                        ...p,
                        status: 'PLAYING'
                      }))
                    );
                } else if (data.type === 'ready_status_changed') {
                    // 준비 상태 변경 처리
                    console.log("🔥 준비 상태 변경 수신:", data);

                    // 현재 사용자의 준비 상태인 경우 상태 업데이트
                    const { guest_id } = guestStore.getState();
                    if (String(data.guest_id) === String(guest_id)) {
                        console.log("📌 내 준비 상태 업데이트:", data.is_ready);
                        setIsReady(data.is_ready);
                    }
                    // 참가자 목록에서 해당 참가자의 status를 업데이트 (is_ready → status: 'READY' | 'WAITING')
                    setParticipants(prev => prev.map(p =>
                        p.guest_id === data.guest_id ? { ...p, status: data.is_ready ? 'READY' : 'WAITING' } : p
                    ));

                    // 방 업데이트 플래그 설정 - 참가자 목록 갱신 트리거
                    setRoomUpdated(true);

                    // 시스템 메시지로 추가
                    setMessages((prev) => [...prev, {
                        nickname: "시스템",
                        message: `${data.nickname || '플레이어'}님이 ${data.is_ready ? '준비완료' : '대기중'} 상태가 되었습니다.`,
                        type: 'system',
                        timestamp: data.timestamp || new Date().toISOString()
                    }]);
                } else if (data.type === 'ready_status_updated') {
                    // 자신의 준비 상태 업데이트 응답
                    setIsReady(data.is_ready);
                } else if (data.type === 'final_results') {
                    console.log("🏁 최종 결과 수신:", data.results);
                    if (Array.isArray(data.results)) {
                      setFinalResults(data.results);
                    }
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
          const { guest_id, nickname } = guestStore.getState();
          const messageData = {
            type: 'chat',
            message: message,
            guest_id: guest_id,
            nickname: nickname,
            timestamp: new Date().toISOString(),
            message_id: `${guest_id}-${Date.now()}`
          };
          socketRef.current.send(JSON.stringify(messageData));
        } else {
          console.error("웹소켓이 연결되지 않았습니다");
        }
      };

    // 준비 상태 토글 함수 추가
    const toggleReady = () => {
        if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
            socketRef.current.send(JSON.stringify({
                type: 'toggle_ready'
            }));
        } else {
            console.error("웹소켓이 연결되지 않았습니다");
        }
    };

    // 상태 업데이트 함수 (준비 또는 시작)
   
    // isReady 상태 디버깅용 useEffect 추가
    useEffect(() => {
        console.log("🟢 현재 isReady 상태:", isReady);
    }, [isReady, messages]);

    return {
        connected,
        messages,
        participants,
        gameStatus,
        isReady,
        sendMessage,
        toggleReady,
        roomUpdated,
        setRoomUpdated,
        finalResults,
        setFinalResults
    };
}