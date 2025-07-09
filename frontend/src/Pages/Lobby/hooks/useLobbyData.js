import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { gameLobbyUrl } from '../../../Component/urls';
import { useAuth } from '../../../contexts/AuthContext';

const useLobbyData = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [roomsData, setRoomsData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEntering, setIsEntering] = useState(false);

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
    }
  }, [isAuthenticated]);

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
    try {
      setIsEntering(true);
      await new Promise((resolve) => setTimeout(resolve, 800));
      await axiosInstance.post(ROOM_API.JOIN_ROOMS(room_id));
      navigate(gameLobbyUrl(room_id));
    } catch (err) {
      console.log(err);
      alert(err.data);
    } finally {
      setIsEntering(false);
    }
  };

  const handleRandomEnter = async () => {
    try {
      setIsLoading(true);
      await fetchRoom();

      const availableRooms = roomsData.filter(
        (room) =>
          room.status === 'waiting' && room.participant_count < room.max_players
      );

      if (availableRooms.length === 0) {
        alert('입장 가능한 방이 없습니다.');
        return;
      }

      const randomRoom =
        availableRooms[Math.floor(Math.random() * availableRooms.length)];
      setIsEntering(true);
      setTimeout(() => {
        handleEnterGame(randomRoom.room_id);
      }, 700);
    } catch (err) {
      console.error('랜덤 입장 실패:', err);
      alert('랜덤 입장 중 문제가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    roomsData,
    isLoading,
    isEntering,
    nickname: user?.nickname || '',
    fetchRoom,
    handleEnterGame,
    handleRandomEnter,
  };
};

export default useLobbyData;
