import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { gameLobbyUrl } from '../../../Component/urls';
import { useAuth } from '../../../contexts/AuthContext';
import { getErrorMessage } from '../../../utils/errorMessages';

const useLobbyData = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
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
        console.error('API 응답 형식이 예상과 다릅니다:', res.data);
        setRoomsData([]);
      }
    } catch (error) {
      console.log('방 요청 실패 ' + error);
      setRoomsData([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // AuthContext가 이미 인증을 확인하므로 여기서는 단순히 방 목록만 가져옴
    if (isAuthenticated) {
      fetchRoom();
      
      // 실시간 업데이트를 위한 interval 설정 (10초마다)
      const interval = setInterval(() => {
        if (!isEntering) { // 입장 중이 아닐 때만 새로고침
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
        console.error('게스트 상태 확인 실패:', err);
      }
    };
    fetchGuestStatus();
  }, [isAuthenticated, user, navigate]);

  const handleEnterGame = async (room_id) => {
    // 중복 요청 방지
    if (isEntering || enteringRoomId === room_id) {
      return;
    }

    try {
      setIsEntering(true);
      setEnteringRoomId(room_id);
      
      const response = await axiosInstance.post(ROOM_API.JOIN_ROOMS(room_id));
      
      // 성공 시 즉시 이동
      navigate(gameLobbyUrl(room_id));
    } catch (err) {
      console.error('방 입장 실패:', err);
      
      const errorMessage = getErrorMessage(err);
      alert(errorMessage);
      
      // 에러 발생 시 방 목록 새로고침
      await fetchRoom();
    } finally {
      setIsEntering(false);
      setEnteringRoomId(null);
    }
  };

  const handleRandomEnter = async () => {
    // 이미 처리 중이면 중단
    if (isLoading || isEntering) {
      return;
    }

    try {
      setIsLoading(true);
      
      // 최신 방 목록 가져오기
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
      
      // setTimeout 제거하고 즉시 입장 처리
      await handleEnterGame(randomRoom.room_id);
    } catch (err) {
      console.error('랜덤 입장 실패:', err);
      
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
