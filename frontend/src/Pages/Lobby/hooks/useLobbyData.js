import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { gameLobbyUrl } from '../../../utils/urls';
import { useAuth } from '../../../contexts/AuthContext';
import { useToast } from '../../../contexts/ToastContext';
import { getErrorMessage, ERROR_MESSAGES } from '../../../utils/errorMessages';

const useLobbyData = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const toast = useToast();
  const [roomsData, setRoomsData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const [enteringRoomId, setEnteringRoomId] = useState(null);

  const fetchRoom = async () => {
    try {
      setIsLoading(true);
      const res = await axiosInstance.get(ROOM_API.get_ROOMS);
      if (res.data && Array.isArray(res.data.rooms)) {
        setRoomsData(
          res.data.rooms.filter((room) => room.status !== 'finished')
        );
      } else {
        // API 응답 형식이 다른 경우 빈 배열로 설정
        setRoomsData([]);
        if (process.env.NODE_ENV === 'development') {
          console.warn('예상과 다른 API 응답 형식:', res.data);
        }
      }
    } catch (error) {
      setRoomsData([]);
      // 방 목록 로딩 실패는 사용자에게 알리지 않음 (자동 재시도됨)
      if (process.env.NODE_ENV === 'development') {
        console.warn('방 목록 로딩 실패:', error);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchRoom();
      
      const interval = setInterval(() => {
        if (!isEntering) {
          fetchRoom();
        }
      }, 10000);
      
      return () => clearInterval(interval);
    }
  }, [isAuthenticated, isEntering]);

  useEffect(() => {
    if (!isAuthenticated || !user) return;

    const fetchGuestStatus = async () => {
      try {
        const res = await axiosInstance.get('/auth/status');
        const roomId = res?.data?.room_id;
        if (roomId) {
          alert('기존 방에 재입장합니다.');
          navigate(gameLobbyUrl(roomId));
        }
      } catch (err) {
        // 게스트 상태 확인 실패는 무시 (필수적이지 않은 기능)
        if (process.env.NODE_ENV === 'development') {
          console.warn('게스트 상태 확인 실패:', err);
        }
      }
    };
    fetchGuestStatus();
  }, [isAuthenticated, user, navigate]);

  const handleEnterGame = async (room_id) => {
    if (isEntering || enteringRoomId === room_id) {
      return;
    }

    try {
      setIsEntering(true);
      setEnteringRoomId(room_id);
      
      const response = await axiosInstance.post(ROOM_API.JOIN_ROOMS(room_id));
      
      navigate(gameLobbyUrl(room_id));
    } catch (err) {
      // 방 입장 실패 시 사용자에게 알림
      const errorMessage = getErrorMessage(err) || ERROR_MESSAGES.ROOM_JOIN_FAILED;
      toast.showError(errorMessage);
      
      await fetchRoom();
    } finally {
      setIsEntering(false);
      setEnteringRoomId(null);
    }
  };

  const handleRandomEnter = async () => {
    if (isLoading || isEntering) {
      return;
    }

    try {
      setIsLoading(true);
      
      const res = await axiosInstance.get(ROOM_API.get_ROOMS);
      let currentRooms = [];
      
      if (res.data && Array.isArray(res.data.rooms)) {
        currentRooms = res.data.rooms.filter((room) => room.status !== 'finished');
        setRoomsData(currentRooms);
      }

      const availableRooms = currentRooms.filter(
        (room) =>
          room.status === 'waiting' && room.participant_count < room.max_players
      );

      if (availableRooms.length === 0) {
        alert('현재 입장 가능한 방이 없습니다.');
        return;
      }

      const randomRoom = availableRooms[Math.floor(Math.random() * availableRooms.length)];
      
      await handleEnterGame(randomRoom.room_id);
    } catch (err) {
      // 랜덤 입장 실패 시 사용자에게 알림
      const errorMessage = getErrorMessage(err);
      toast.showError(errorMessage || '랜덤 입장에 실패했습니다. 다시 시도해주세요.');
      
      const errorMessage = getErrorMessage(err);
      alert(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return {
    roomsData,
    isLoading,
    isEntering,
    enteringRoomId,
    nickname: user?.nickname || '',
    fetchRoom,
    handleEnterGame,
    handleRandomEnter,
  };
};

export default useLobbyData;
