import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import axiosInstance from '../../../Api/axiosInstance';
import { gameUrl } from '../../../Component/urls';
import userIsTrue from '../../../Component/userIsTrue';
import { ROOM_API } from '../../../Api/roomApi';
import guestStore from '../../../store/guestStore';
import useGameRoomSocket from '../../../hooks/useGameRoomSocket';

const useGameLobby = () => {
  const { roomId } = useParams();
  const [roomInfo, setRoomInfo] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isOwner, setIsOwner] = useState(false);
  const [redirectingToGame] = useState(false);
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
    connect,
    disconnect,
  } = useGameRoomSocket(roomId);

  /* Guest Check */
  useEffect(() => {
    const checkGuest = async () => {
      const { uuid, guest_id, nickname } = guestStore.getState();

      if (uuid && guest_id && nickname) {
        console.log('✅ 저장된 guestStore 정보 사용:', {
          uuid,
          guest_id,
          nickname,
        });
        return;
      }
      const cookies = document.cookie.split(';');
      const guestUuidCookie = cookies.find((cookie) =>
        cookie.trim().startsWith('kkua_guest_uuid=')
      );
      const guestUuid = guestUuidCookie
        ? guestUuidCookie.split('=')[1].trim()
        : null;

      console.log('쿠키에서 찾은 UUID:', guestUuid);
      console.log('스토어에 저장된 UUID:', uuid);

      if (guestUuid) {
        if (!uuid || uuid !== guestUuid) {
          console.log('UUID 불일치, 스토어 업데이트');
          const current = guestStore.getState();
          guestStore.getState().setGuestInfo({
            uuid: guestUuid,
            guest_id: current.guest_id,
            nickname: current.nickname,
            guest_uuid: current.guest_uuid,
          });
        }

        const result = await userIsTrue();
        if (!result) {
          alert('어멋 어딜들어오세요 Get Out !');
          navigate('/');
          return;
        }
      } else {
        try {
          const response = await axiosInstance.post('/guests/login');

          guestStore.getState().setGuestInfo({
            uuid: response.data.uuid,
            nickname: response.data.nickname,
            guest_id: response.data.guest_id,
          });
        } catch (error) {
          alert('서버 연결에 문제가 있습니다');
          navigate('/');
        }
      }
    };
    checkGuest();
  }, [navigate]);

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
        }
      }
    } catch (error) {
      console.error('방 정보 가져오기 실패:', error);
    } finally {
      setIsLoading(false);
    }
  }, [roomId]);

  /* 방장 확인 */
  const checkIfOwnerFromParticipants = useCallback(() => {
    const { guest_id } = guestStore.getState();
    const currentUser = guest_id
      ? participants.find((p) => String(p.guest_id) === String(guest_id))
      : null;
    return currentUser?.is_creator === true;
  }, [participants]);

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
          const { uuid } = guestStore.getState();
          axiosInstance
            .post(ROOM_API.LEAVE_ROOMS(roomId), {
              guest_uuid: uuid,
            })
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
    try {
      const response = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId));
      console.log('게임 시작 응답:', response.data);
      alert('게임이 시작됩니다!');
      navigate(gameUrl(roomId));
    } catch (error) {
      console.error('게임 시작 오류:', error);
      if (error.response && error.response.data && error.response.data.detail) {
        alert(`게임 시작 실패: ${error.response.data.detail}`);
      } else {
        alert(
          '게임을 시작할 수 없습니다. 모든 플레이어가 준비되었는지 확인하세요.'
        );
      }
    }
  };

  useEffect(() => {
    const checkUuidConsistency = async () => {
      const { uuid } = guestStore.getState();

      if (!uuid) {
        try {
          const response = await axiosInstance.post('/guests/login');
          guestStore.getState().setGuestInfo({
            uuid: response.data.uuid,
            nickname: response.data.nickname,
            guest_id: response.data.guest_id,
          });
        } catch (error) {
          console.error('로그인 실패:', error);
          alert('서버 연결에 문제가 있습니다');
          navigate('/');
        }
      }
    };
    checkUuidConsistency();
  }, [navigate]);

  useEffect(() => {
    console.log('웹소켓 연결 상태:', connected ? '연결됨' : '연결 안됨');
    if (!connected && connect) {
      console.log('웹소켓 연결 시도...');
      connect();
    }
    return () => {
      console.log('컴포넌트 언마운트: 웹소켓 연결 종료');
      if (disconnect) disconnect();
    };
  }, [connected, connect, disconnect]);

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

  useEffect(() => {
    const checkWebSocketConnection = () => {
      console.log(
        '웹소켓 연결 상태 주기적 확인:',
        connected ? '연결됨' : '연결 안됨'
      );
      if (!connected && connect) {
        console.log('웹소켓 연결 끊김 감지, 재연결 시도...');
        connect();
      }
    };
    const intervalId = setInterval(checkWebSocketConnection, 10000);
    return () => clearInterval(intervalId);
  }, [connected, connect]);

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
    sendMessage,
    toggleReady,
    handleClickExit,
    handleClickStartBtn,
  };
};

export default useGameLobby;
