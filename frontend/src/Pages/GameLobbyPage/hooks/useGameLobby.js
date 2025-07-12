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

  /* 인증 상태 확인 */
  useEffect(() => {
    if (!isAuthenticated || !user) {
      console.log('인증되지 않은 사용자 - 메인 페이지로 리다이렉트');
      navigate('/');
      return;
    }
    
    console.log('✅ 인증된 사용자:', {
      guest_id: user.guest_id,
      nickname: user.nickname,
    });
  }, [isAuthenticated, user, navigate]);

  /* USER INFO */
  const fetchRoomData = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await axiosInstance.get(`/gamerooms/${roomId}`);
      console.log('방 정보 API 응답:', response.data);

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
          
          // 현재 사용자가 방 참가자인지 확인
          const isParticipant = response.data.participants.some(
            (p) => String(p.guest_id) === String(user?.guest_id)
          );
          
          if (!isParticipant) {
            console.log('방 참가자가 아님 - 접근 거부');
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

  /* 방장 확인 */
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

  /* Exit from Room BTN */
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
              console.log(error);
            });
        } catch (error) {
          alert('당신은 나갈수 없어요. 끄아지옥 ON.... Create User');
          console.log(error);
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

  /* Start BTN */
  const handleClickStartBtn = async () => {
    if (isStartingGame) return; // 중복 클릭 방지
    
    try {
      setIsStartingGame(true);
      console.log('🎮 게임 시작 요청 중...');
      
      const response = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId));
      console.log('게임 시작 응답:', response.data);
      
      // WebSocket을 통해 game_started 이벤트가 오면 자동으로 페이지 이동됨
      // 따라서 여기서는 성공 메시지만 표시
      console.log('✅ 게임 시작 성공! WebSocket 이벤트 대기 중...');
      
    } catch (error) {
      console.error('❌ 게임 시작 오류:', error);
      setIsStartingGame(false); // 에러 시 로딩 상태 해제
      
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

  /* 인증 상태 재확인 (세션 기반) */
  useEffect(() => {
    if (!isAuthenticated || !user) {
      console.log('인증 상태 확인 실패 - 메인 페이지로 리다이렉트');
      navigate('/');
    }
  }, [isAuthenticated, user, navigate]);

  useEffect(() => {
    console.log('웹소켓 연결 상태:', connected ? '연결됨' : '연결 안됨');
  }, [connected]);

  useEffect(() => {
    if (connected && socketParticipants && socketParticipants.length > 0) {
      console.log('소켓에서 받은 참가자 정보:', socketParticipants);
      setParticipants(socketParticipants);
    }
  }, [connected, socketParticipants]);

  // useEffect(() => {
  //   console.log('현재 게임 상태:', gameStatus);
  //   if (gameStatus === 'playing') {
  //     console.log("게임 상태가 'playing'으로 변경됨 -> 게임 페이지로 이동");
  //     navigate(gameUrl(roomId));
  //   }
  // }, [gameStatus, roomId, navigate]);

  useEffect(() => {
    if (roomUpdated) {
      console.log('방 업데이트 트리거 감지, 방 정보 새로고침');
      fetchRoomData();
      setRoomUpdated(false);
    }
  }, [roomUpdated, fetchRoomData, setRoomUpdated]);

  // 웹소켓 연결 상태 모니터링 및 방 정보 동기화
  useEffect(() => {
    if (!connected) {
      console.log('웹소켓 연결이 끊어졌습니다.');
    } else {
      console.log('웹소켓 연결 성공! 방 정보를 동기화합니다.');
      // 웹소켓 연결 성공 시 방 정보 새로고침
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
