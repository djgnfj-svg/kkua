import { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';

/**
 * 간소화된 게임룸 훅 - 모든 기능을 하나로 통합
 * 복잡한 상태 동기화 제거, WebSocket 중심의 단순한 아키텍처
 */
const useSimpleGameRoom = (roomId) => {
  // 기본 상태
  const [connected, setConnected] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [messages, setMessages] = useState([]);
  const [isReconnecting, setIsReconnecting] = useState(false);
  
  // Refs
  const socketRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const connectionAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  
  // Hooks
  const { user, isAuthenticated } = useAuth();
  const toast = useToast();

  // 🔌 WebSocket 연결
  const connectWebSocket = useCallback(() => {
    if (!roomId || !isAuthenticated || !user) {
      console.log('❌ WebSocket 연결 불가:', { roomId, isAuthenticated, user: !!user });
      return;
    }

    try {
      const wsUrl = `${process.env.REACT_APP_WS_BASE_URL || 'ws://localhost:8000'}/ws/test/gamerooms/${roomId}`;
      console.log('🔌 WebSocket 연결 시도:', wsUrl);
      
      const socket = new WebSocket(wsUrl);
      
      socket.onopen = () => {
        console.log('✅ WebSocket 연결 성공!');
        setConnected(true);
        setIsReconnecting(false);
        connectionAttempts.current = 0;
        
        if (toast) {
          toast.showSuccess('실시간 연결되었습니다!');
        }
      };
      
      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📨 WebSocket 메시지 받음:', data);
          
          switch (data.type) {
            case 'connected':
              console.log('🎉 연결 확인:', data.message);
              break;
              
            case 'participant_joined':
            case 'participant_left':
              // 참가자 목록 업데이트
              console.log('👥 참가자 목록 업데이트:', data.participants);
              setParticipants(data.participants || []);
              
              if (data.message && toast) {
                toast.showInfo(data.message);
              }
              break;
              
            case 'chat':
              // 채팅 메시지 추가
              console.log('💬 채팅 메시지:', data);
              const chatMessage = {
                id: Date.now(),
                type: 'chat',
                user: data.user,
                content: data.content,
                timestamp: data.timestamp
              };
              setMessages(prev => [...prev, chatMessage]);
              break;
              
            case 'ready_toggled':
              console.log('✅ 준비 상태 변경:', data.nickname);
              if (toast) {
                toast.showInfo(`${data.nickname}님이 준비 상태를 변경했습니다.`);
              }
              break;
              
            case 'error':
              console.error('❌ WebSocket 에러:', data.message);
              if (toast) {
                toast.showError(data.message);
              }
              break;
              
            default:
              console.log('🤔 알 수 없는 메시지:', data);
          }
        } catch (error) {
          console.error('메시지 파싱 오류:', error);
        }
      };
      
      socket.onclose = (event) => {
        console.log('🔌 WebSocket 연결 종료:', event.code, event.reason);
        setConnected(false);
        
        // 자동 재연결 시도
        if (connectionAttempts.current < maxReconnectAttempts) {
          connectionAttempts.current++;
          setIsReconnecting(true);
          
          const delay = Math.min(1000 * Math.pow(2, connectionAttempts.current), 10000);
          console.log(`🔄 ${delay}ms 후 재연결 시도 (${connectionAttempts.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectWebSocket();
          }, delay);
          
          if (toast) {
            toast.showWarning('연결이 끊어졌습니다. 재연결 중...');
          }
        } else {
          console.log('❌ 재연결 포기 (최대 시도 횟수 초과)');
          setIsReconnecting(false);
          if (toast) {
            toast.showError('서버와 연결할 수 없습니다. 페이지를 새로고침해주세요.');
          }
        }
      };
      
      socket.onerror = (error) => {
        console.error('❌ WebSocket 에러:', error);
        setConnected(false);
      };
      
      socketRef.current = socket;
      
    } catch (error) {
      console.error('❌ WebSocket 연결 생성 실패:', error);
      setConnected(false);
    }
  }, [roomId, isAuthenticated, user, toast]);

  // 📤 메시지 전송
  const sendMessage = useCallback((message) => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('❌ WebSocket 연결되지 않음');
      if (toast) {
        toast.showError('서버와 연결되어 있지 않습니다.');
      }
      return false;
    }
    
    try {
      const messageStr = JSON.stringify(message);
      console.log('📤 메시지 전송:', messageStr);
      socketRef.current.send(messageStr);
      return true;
    } catch (error) {
      console.error('❌ 메시지 전송 실패:', error);
      if (toast) {
        toast.showError('메시지 전송에 실패했습니다.');
      }
      return false;
    }
  }, [toast]);

  // 💬 채팅 메시지 전송
  const sendChatMessage = useCallback((content) => {
    return sendMessage({
      type: 'chat',
      message: content.trim(),
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  // ✅ 준비 상태 토글
  const toggleReady = useCallback(() => {
    return sendMessage({
      type: 'toggle_ready',
      timestamp: new Date().toISOString()
    });
  }, [sendMessage]);

  // 🔄 수동 재연결
  const manualReconnect = useCallback(() => {
    console.log('🔄 수동 재연결 시도');
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    connectionAttempts.current = 0;
    connectWebSocket();
  }, [connectWebSocket]);

  // 🔌 연결 해제
  const disconnect = useCallback(() => {
    console.log('🔌 WebSocket 연결 해제');
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }
    setConnected(false);
    setIsReconnecting(false);
  }, []);

  // 🎯 현재 사용자가 방장인지 확인
  const isOwner = useCallback(() => {
    if (!user || !participants.length) return false;
    const currentUser = participants.find(p => p.guest_id === user.guest_id);
    return currentUser?.is_creator === true;
  }, [user, participants]);

  // 📊 참가자 수
  const participantCount = participants.length;

  // 🔄 Effect: 연결 관리
  useEffect(() => {
    connectWebSocket();
    
    return () => {
      disconnect();
    };
  }, [connectWebSocket, disconnect]);

  // 🧹 정리
  useEffect(() => {
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, []);

  return {
    // 상태
    connected,
    participants,
    messages,
    isReconnecting,
    participantCount,
    
    // 액션
    sendChatMessage,
    toggleReady,
    manualReconnect,
    disconnect,
    
    // 계산된 값
    isOwner: isOwner(),
    
    // 연결 정보
    connectionAttempts: connectionAttempts.current,
    maxReconnectAttempts
  };
};

export default useSimpleGameRoom;