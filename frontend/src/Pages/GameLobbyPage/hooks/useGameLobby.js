import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { gameUrl } from '../../../utils/urls';
import { ROOM_API } from '../../../Api/roomApi';
import useGameRoomSocket from '../../../hooks/useGameRoomSocket';
import { useAuth } from '../../../contexts/AuthContext';

const useGameLobby = () => {
  const { roomId } = useParams();
  const { user, isAuthenticated } = useAuth();
  const [roomInfo, setRoomInfo] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOwner, setIsOwner] = useState(false);
  const [redirectingToGame] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);
  const navigate = useNavigate();

  const {
    connected,
    messages,
    participants: socketParticipants,
    isReady,
    sendMessage,
    toggleReady,
    roomUpdated,
    setRoomUpdated,
  } = useGameRoomSocket(roomId);

  useEffect(() => {
    if (!isAuthenticated || !user) {
      navigate('/');
      return;
    }
  }, [isAuthenticated, user, navigate]);
  const fetchRoomData = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axiosInstance.get(`/gamerooms/${roomId}`);

      if (response.data) {
        if (response.data.room) {
          setRoomInfo(response.data.room);
        } else {
          setRoomInfo(response.data);
        }

        if (
          response.data.participants &&
          Array.isArray(response.data.participants)
        ) {
          setParticipants(response.data.participants);
          
          const isParticipant = response.data.participants.some(
            (p) => String(p.guest_id) === String(user?.guest_id)
          );
          
          if (!isParticipant) {
            alert('이 방에 참가하지 않은 사용자입니다. 로비로 이동합니다.');
            navigate('/lobby');
            return;
          }
        }
      }
    } catch (error) {
      console.error('방 정보 가져오기 실패:', error);
      if (error.response?.status === 404) {
        alert('존재하지 않는 방입니다. 로비로 이동합니다.');
        navigate('/lobby');
      } else if (error.response?.status === 403) {
        alert('접근 권한이 없습니다. 로비로 이동합니다.');
        navigate('/lobby');
      }
    } finally {
      setIsLoading(false);
    }
  }, [roomId, user, navigate]);
  const checkIfOwnerFromParticipants = useCallback(() => {
    if (!user?.guest_id) return false;
    const currentUser = participants.find(
      (p) => String(p.guest_id) === String(user.guest_id)
    );
    return currentUser?.is_creator === true;
  }, [participants, user]);

  useEffect(() => {
    fetchRoomData();
    const interval = setInterval(fetchRoomData, 30000);
    return () => clearInterval(interval);
  }, [fetchRoomData]);

  useEffect(() => {
    const isOwnerFromParticipants = checkIfOwnerFromParticipants();
    if (isOwnerFromParticipants !== undefined) {
      setIsOwner(isOwnerFromParticipants);
      return;
    }

    const checkIfOwner = async () => {
      try {
        const response = await axiosInstance.get(
          `/gamerooms/${roomId}/is-owner`
        );
        if (response.data.is_owner) {
          setIsOwner(true);
        } else {
          setIsOwner(false);
        }
      } catch (error) {
        console.error('방장 여부 확인 실패:', error);
        setIsOwner(false);
      }
    };
    checkIfOwner();
  }, [roomId, checkIfOwnerFromParticipants]);

  const handleClickExit = () => {
    const lobbyUrl = '/lobby';

    if (isOwner) {
      let confirmDelete = window.confirm('정말로 방을 삭제하시겠습니까?');
      if (confirmDelete) {
        try {
          axiosInstance
            .delete(ROOM_API.DELET_ROOMSID(roomId))
            .then(() => {
              alert('방이 삭제되었습니다.');
              navigate(lobbyUrl);
            })
            .catch((error) => {
              alert('당신은 나갈수 없어요. 끄아지옥 ON....');
              console.error('방 삭제 실패:', error);
            });
        } catch (error) {
          alert('당신은 나갈수 없어요. 끄아지옥 ON.... Create User');
          console.error('방 삭제 오류:', error);
        }
      }
    } else {
      let confirmLeave = window.confirm('로비로 나가시겠습니까?');
      if (confirmLeave) {
        try {
          axiosInstance
            .post(ROOM_API.LEAVE_ROOMS(roomId))
            .then(() => {
              alert('방에서 나갑니다!');
              navigate(lobbyUrl);
            })
            .catch((error) => {
              console.error('방 나가기 실패:', error);
              alert('당신은 나갈수 없어요. 끄아지옥 ON....');
            });
        } catch (error) {
          console.error('방 나가기 실패:', error);
          alert('당신은 나갈수 없어요. 끄아지옥 ON....');
        }
      }
    }
  };

  const handleClickStartBtn = async () => {
    if (isStartingGame) return;
    
    try {
      setIsStartingGame(true);
      
      const response = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId));
      
    } catch (error) {
      console.error('게임 시작 오류:', error);
      setIsStartingGame(false);
      
      let errorMessage = '게임을 시작할 수 없습니다.';
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.response?.status === 400) {
        errorMessage = '모든 플레이어가 준비되었는지 확인하세요.';
      } else if (error.response?.status === 403) {
        errorMessage = '방장만 게임을 시작할 수 있습니다.';
      } else if (error.code === 'ERR_NETWORK') {
        errorMessage = '네트워크 연결을 확인해주세요.';
      }
      
      alert(`게임 시작 실패: ${errorMessage}`);
    }
  };

  useEffect(() => {
    if (connected && socketParticipants && socketParticipants.length > 0) {
      setParticipants(socketParticipants);
    }
  }, [connected, socketParticipants]);

  useEffect(() => {
    if (roomUpdated) {
      fetchRoomData();
      setRoomUpdated(false);
    }
  }, [roomUpdated, fetchRoomData, setRoomUpdated]);

  useEffect(() => {
    if (connected) {
      fetchRoomData();
    }
  }, [connected, fetchRoomData]);

  return {
    roomId,
    roomInfo,
    participants,
    isLoading,
    isOwner,
    redirectingToGame,
    connected,
    messages,
    isReady,
    isStartingGame,
    sendMessage,
    toggleReady,
    handleClickExit,
    handleClickStartBtn,
  };
};

export default useGameLobby;
