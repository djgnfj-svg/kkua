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

  // 브라우저 뒤로가기 처리 - DB 상태 동기화
  useEffect(() => {
    const handlePopState = async (event) => {
      // 뒤로가기 시 무조건 방 나가기 API 호출 (DB 동기화)
      try {
        if (isOwner) {
          // 방장인 경우 방 삭제 여부 확인
          if (window.confirm('방장이 나가면 방이 삭제됩니다. 정말 나가시겠습니까?')) {
            await axiosInstance.delete(ROOM_API.DELET_ROOMSID(roomId));
            navigate('/lobby', { replace: true });
          } else {
            // 취소하면 현재 페이지 유지
            window.history.pushState(null, '', window.location.href);
          }
        } else {
          // 일반 참가자인 경우 방 나가기
          await axiosInstance.post(ROOM_API.LEAVE_ROOMS(roomId));
          navigate('/lobby', { replace: true });
        }
      } catch (error) {
        console.error('방 나가기 실패:', error);
        // API 실패해도 프론트엔드에서는 로비로 이동 (UI 일관성)
        navigate('/lobby', { replace: true });
      }
    };

    // beforeunload 이벤트로 새로고침/창 닫기도 처리
    const handleBeforeUnload = () => {
      // 페이지를 떠날 때 방 나가기 (fetch 사용으로 변경)
      if (roomId) {
        try {
          fetch(ROOM_API.LEAVE_ROOMS(roomId), {
            method: 'POST',
            credentials: 'include',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({})
          }).catch(() => {
            // 에러 무시 (페이지 종료 시점이므로)
          });
        } catch (error) {
          // 에러 무시 (페이지 종료 시점이므로)
        }
      }
    };

    window.addEventListener('popstate', handlePopState);
    window.addEventListener('beforeunload', handleBeforeUnload);

    return () => {
      window.removeEventListener('popstate', handlePopState);
      window.removeEventListener('beforeunload', handleBeforeUnload);
    };
  }, [roomId, isOwner, navigate]);

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
    console.log('🚀 handleClickStartBtn 함수 시작');
    console.log('현재 isStartingGame:', isStartingGame);
    
    if (isStartingGame) {
      console.log('❌ 이미 시작 중이므로 리턴');
      return;
    }
    
    try {
      console.log('🎯 게임 시작 API 호출 시작');
      setIsStartingGame(true);
      
      const apiUrl = ROOM_API.PLAY_ROOMS(roomId);
      console.log('API URL:', apiUrl);
      
      const response = await axiosInstance.post(apiUrl);
      console.log('✅ 게임 시작 API 응답:', response.data);
      
      // 게임 시작 성공 시 상태 리셋 (WebSocket으로 navigate 처리)
      // setIsStartingGame(false); // WebSocket에서 페이지 이동하므로 리셋하지 않음
      
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
