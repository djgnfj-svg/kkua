import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { ROOM_API } from '../../../Api/roomApi';
import { USER_API } from '../../../Api/userApi';
import { gameLobbyUrl } from '../../../Component/urls';
import guestStore from '../../../store/guestStore';
import Cookies from 'js-cookie';

const useLobbyData = () => {
  const navigate = useNavigate();
  const [roomsData, setRoomsData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isEntering, setIsEntering] = useState(false);
  const { uuid, nickname } = guestStore.getState();

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
    const checkGuestInfo = async () => {
      const guestUuid = Cookies.get('kkua_guest_uuid');
      if (guestUuid) {
        try {
          await axiosInstance.post(USER_API.GET_GUEST, {
            guest_uuid: guestUuid,
            nickname: null,
            device_info: navigator.userAgent,
          });
        } catch (error) {
          console.error('게스트 로그인 실패:', error);
          alert('로그인에 실패했습니다. 메인 페이지로 이동합니다.');
          navigate('/');
        }
      } else {
        alert('로그인이 필요합니다. 메인 페이지로 이동합니다.');
        navigate('/');
      }
    };
    checkGuestInfo();
    fetchRoom();
  }, [navigate]);

  useEffect(() => {
    if (!uuid) return;

    const fetchGuestStatus = async () => {
      const guestUuid = Cookies.get('kkua_guest_uuid');
      if (guestUuid) {
        try {
          const res = await axiosInstance.get(USER_API.GET_GUEST_STATUS, {
            headers: {
              guest_uuid_str: guestUuid,
            },
          });
          const roomId = res?.data?.room_id;
          if (roomId) {
            alert('기존 방에 재입장합니다.');
            navigate(gameLobbyUrl(roomId));
          }
        } catch (err) {
          console.error('게스트 상태 확인 실패:', err);
        }
      }
    };
    fetchGuestStatus();
  }, [uuid, navigate]);

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
    nickname,
    fetchRoom,
    handleEnterGame,
    handleRandomEnter,
  };
};

export default useLobbyData;
