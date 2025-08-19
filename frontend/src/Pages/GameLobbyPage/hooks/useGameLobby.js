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
  const [isLoading, setIsLoading] = useState(false);
  const [isOwner, setIsOwner] = useState(false);
  const [redirectingToGame] = useState(false);
  const [isStartingGame, setIsStartingGame] = useState(false);
  const navigate = useNavigate();

  const {
    connected,
    isReconnecting,
    connectionAttempts,
    maxReconnectAttempts,
    messages,
    participants: socketParticipants,
    isReady,
    sendMessage,
    toggleReady,
    manualReconnect,
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
          if (
            window.confirm(
              '방장이 나가면 방이 삭제됩니다. 정말 나가시겠습니까?'
            )
          ) {
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
            body: JSON.stringify({}),
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

  // WebSocket 메시지를 통한 게임 시작 감지
  useEffect(() => {
    const hasGameStartedMessage = messages.some(
      (msg) =>
        msg.type === 'system' &&
        (msg.message.includes('게임이 시작') ||
          msg.message.includes('게임 페이지로 이동'))
    );

    if (hasGameStartedMessage && isStartingGame) {
      setIsStartingGame(false);
    }
  }, [messages, isStartingGame]);
  const fetchRoomData = useCallback(async () => {
    console.log('fetchRoomData 호출됨:', { roomId, user: !!user });
    try {
      setIsLoading(true);
      console.log('API 요청 시작:', `/gamerooms/${roomId}`);
      const response = await axiosInstance.get(`/gamerooms/${roomId}`);
      console.log('API 응답 받음:', response.data);

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
            setIsLoading(false);
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
    console.log('방장 체크:', { user: user?.guest_id, participants, participantsLength: participants.length });
    if (!user?.guest_id || !Array.isArray(participants) || participants.length === 0) return false;
    const currentUser = participants.find(
      (p) => p && p.guest_id && String(p.guest_id) === String(user.guest_id)
    );
    console.log('찾은 사용자:', currentUser, '방장 여부:', currentUser?.is_creator);
    return currentUser?.is_creator === true;
  }, [participants, user]);

  useEffect(() => {
    // 초기 데이터 로드만 수행
    console.log('초기 데이터 로드 useEffect:', { roomInfo: !!roomInfo, roomId, user: !!user, isLoading });
    if (!roomInfo && roomId && user) {
      console.log('fetchRoomData 호출 예정');
      fetchRoomData();
    }
  }, [roomId, user, fetchRoomData]); // 초기 로드만, 인터벌 제거로 성능 개선

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
  }, [roomId, participants, user]); // 실제 dependencies로 변경

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
              alert('방 삭제에 실패했습니다. 다시 시도해주세요.');
              console.error('방 삭제 실패:', error);
            });
        } catch (error) {
          alert('방 삭제 중 오류가 발생했습니다.');
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
              alert('방 나가기에 실패했습니다. 다시 시도해주세요.');
            });
        } catch (error) {
          console.error('방 나가기 실패:', error);
          alert('방 나가기 중 오류가 발생했습니다.');
        }
      }
    }
  };

  const handleClickStartBtn = async () => {
    if (isStartingGame) {
      return;
    }

    try {
      setIsStartingGame(true);

      const apiUrl = ROOM_API.PLAY_ROOMS(roomId);
      const response = await axiosInstance.post(apiUrl);

      // 백업 로직: WebSocket 메시지가 3초 내에 오지 않으면 수동 이동
      setTimeout(() => {
        if (isStartingGame) {
          navigate(gameUrl(roomId));
        }
      }, 3000);
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

  const handleKickPlayer = useCallback((targetGuestId, reason = '') => {
    // 안전성 검사
    if (!user?.guest_id) {
      alert('사용자 정보를 확인할 수 없습니다.');
      return;
    }

    if (!isOwner) {
      alert('방장만 플레이어를 강퇴할 수 있습니다.');
      return;
    }

    if (!targetGuestId) {
      alert('강퇴할 플레이어를 선택해주세요.');
      return;
    }

    if (targetGuestId === user.guest_id) {
      alert('자기 자신을 강퇴할 수 없습니다.');
      return;
    }

    if (!connected) {
      alert('서버와의 연결이 끊어졌습니다. 다시 시도해주세요.');
      return;
    }

    try {
      const success = sendMessage({
        type: 'kick_player',
        target_guest_id: targetGuestId,
        reason: reason || null
      });

      if (!success) {
        alert('강퇴 요청 전송에 실패했습니다. 연결 상태를 확인해주세요.');
      }
    } catch (error) {
      console.error('강퇴 요청 실패:', error);
      alert('강퇴 요청에 실패했습니다.');
    }
  }, [isOwner, user?.guest_id, sendMessage, connected]);

  // WebSocket에서 직접 참가자 목록 업데이트 (가장 간단한 방법)
  useEffect(() => {
    if (connected && socketParticipants && socketParticipants.length >= 0) {
      console.log('🔥 WebSocket 참가자 직접 업데이트:', socketParticipants);
      setParticipants(socketParticipants);
    }
  }, [connected, socketParticipants]);

  // roomUpdated 플래그 처리 (단순화)
  useEffect(() => {
    if (roomUpdated && !connected) {
      // WebSocket 미연결 시에만 REST API 사용
      console.log('🔄 WebSocket 미연결 - REST API 호출');
      fetchRoomData();
      setRoomUpdated(false);
    } else if (roomUpdated) {
      // WebSocket 연결 상태면 이미 socketParticipants로 업데이트됨
      console.log('🔄 WebSocket 연결됨 - roomUpdated 플래그만 리셋');
      setRoomUpdated(false);
    }
  }, [roomUpdated, connected, fetchRoomData, setRoomUpdated]);

  useEffect(() => {
    console.log('WebSocket 연결 useEffect:', { connected, roomInfo: !!roomInfo, isLoading });
    if (connected && !roomInfo) {
      // WebSocket 연결 시 방 정보가 없는 경우에만 로드
      console.log('WebSocket 연결 후 fetchRoomData 호출 예정');
      fetchRoomData();
    }
  }, [connected, roomInfo, fetchRoomData]);

  return {
    roomId,
    roomInfo,
    participants,
    isLoading,
    isOwner,
    redirectingToGame,
    connected,
    isReconnecting,
    connectionAttempts,
    maxReconnectAttempts,
    messages,
    isReady,
    isStartingGame,
    sendMessage,
    toggleReady,
    manualReconnect,
    handleClickExit,
    handleClickStartBtn,
    handleKickPlayer,
  };
};

export default useGameLobby;
