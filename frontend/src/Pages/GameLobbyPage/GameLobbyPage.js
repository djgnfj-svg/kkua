import React, { useEffect, useState, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axiosInstance from '../../Api/axiosInstance';
import { gameLobbyUrl, gameUrl, lobbyUrl } from '../../Component/urls';
import userIsTrue from '../../Component/userIsTrue';
import { ROOM_API } from '../../Api/roomApi';
import guestStore from '../../store/guestStore';
import useGameRoomSocket from '../../hooks/useGameRoomSocket';

function GameLobbyPage() {
  const { roomId } = useParams();
  const [roomsData, setRoomsData] = useState({
    title: "",
    game_mode: "",
    max_players: 0
  });
  const [userInfo, setUserInfo] = useState([]);
  const [isOwner, setIsOwner] = useState(false);
  const [redirectingToGame, setRedirectingToGame] = useState(false);
  const navigate = useNavigate();

  /* Guest Check */
  useEffect(() => {
    const checkGuest = async () => {
      // 쿠키 확인 (직접 document.cookie 사용)
      const cookies = document.cookie.split(';');
      const guestUuidCookie = cookies.find(cookie => cookie.trim().startsWith('kkua_guest_uuid='));
      const guestUuid = guestUuidCookie ? guestUuidCookie.split('=')[1].trim() : null;

      console.log("쿠키에서 찾은 UUID:", guestUuid);

      // 스토어 상태 확인
      const { uuid } = guestStore.getState();
      console.log("스토어에 저장된 UUID:", uuid);

      if (guestUuid) {
        // 스토어 상태 업데이트
        if (!uuid || uuid !== guestUuid) {
          console.log("UUID 불일치, 스토어 업데이트");
          guestStore.getState().setGuestInfo({
            ...guestStore.getState(),
            uuid: guestUuid
          });
        }

        // userIsTrue 호출
        const result = await userIsTrue();
        if (!result) {
          alert("어멋 어딜들어오세요 Get Out !");
          navigate("/");
          return;
        }
      } else {
        // 쿠키가 없으면 로그인 시도
        try {
          const response = await axiosInstance.post('/guests/login');

          guestStore.getState().setGuestInfo({
            uuid: response.data.uuid,
            nickname: response.data.nickname,
            guest_id: response.data.guest_id
          });
        } catch (error) {
          alert("서버 연결에 문제가 있습니다");
          navigate("/");
        }
      }
    };
    checkGuest();
  }, [navigate]);

  /* USER INFO */
  const fetchParticipants = async () => {
    try {
      const response = await axiosInstance.get(ROOM_API.get_ROOMSUSER(roomId));

      // 응답 형식 로깅
      console.log("참가자 API 응답:", response.data);

      // 새로운 응답 구조 처리
      if (response.data) {
        // 참가자 정보 설정 (participants 배열)
        if (response.data.participants && Array.isArray(response.data.participants)) {
          setUserInfo(response.data.participants);
        } else {
          console.error("참가자 정보가 올바른 형식이 아닙니다:", response.data);
          setUserInfo([]);
        }

        // 방 정보 설정 (room_info 객체)
        if (response.data.room_info) {
          setRoomsData(response.data.room_info);

          // 방장 여부 확인
          const guestInfo = JSON.parse(localStorage.getItem('guest-storage'))?.state;
          if (guestInfo?.nickname === response.data.room_info.created_username) {
            setIsOwner(true);
          }
        }
      }
    } catch (error) {
      console.error("참가자 정보 가져오기 실패:", error);
      // 오류 발생 시 빈 배열로 설정하여 UI 에러 방지
      setUserInfo([]);
    }
  };

  useEffect(() => {
    fetchParticipants();
    // 30초마다 참가자 정보 갱신
    const interval = setInterval(fetchParticipants, 30000);
    return () => clearInterval(interval);
  }, [roomId]);

  /* LEAVE ROOM */
  const handleClickExit = async () => {
    if (isOwner) {
      let confirmDelete = window.confirm("방을 삭제 하시겟습니까?")
      if (confirmDelete) {
        try {
          await axiosInstance.delete(ROOM_API.DELET_ROOMSID(roomId))
          navigate(lobbyUrl)
        } catch (error) {
          alert("당신은 나갈수 없어요. 끄아지옥 ON.... Create User");
          console.log(error)
        }
      }
    } else {
      let confirmLeave = window.confirm("로비로 나가시겠습니까?");
      if (confirmLeave) {
        try {
          // uuid 가져오기
          const { uuid } = guestStore.getState();

          // 요청 본문에 게스트 UUID 추가
          await axiosInstance.post(ROOM_API.LEAVE_ROOMS(roomId), {
            guest_uuid: uuid
          });

          alert("방에서 나갑니다!");
          navigate(lobbyUrl);
        } catch (error) {
          console.error("방 나가기 실패:", error);
          alert("당신은 나갈수 없어요. 끄아지옥 ON....");
        }
      }
    }
  }

  /* Start BTN */
  const handleClickStartBtn = async (id) => {
    try {
      const res = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId))
      alert("게임이 시작됩니다 !");
      navigate(gameUrl(roomId));
    } catch (error) {
      console.log(error)
      alert("버그행동 금지")
    }
  }

  /* 웹소켓 연결 사용 */
  const {
    connected,
    messages,
    participants,
    gameStatus,
    sendMessage,
    updateStatus,
    roomUpdated,
    setRoomUpdated
  } = useGameRoomSocket(roomId);

  /* 채팅 메시지 상태 및 핸들러 추가 */
  const [chatMessage, setChatMessage] = useState('');

  const chatContainerRef = useRef(null);

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = () => {
    if (chatMessage.trim() === '') return;

    if (sendMessage) {
      sendMessage(chatMessage);
      setChatMessage('');
    }
  };

  /* 준비 상태 업데이트 핸들러 */
  const handleReady = () => {
    updateStatus('READY');
  };

  /* 게임 시작 후 자동 이동 */
  useEffect(() => {
    if (gameStatus === 'playing') {
      navigate(gameUrl(roomId));
    }
  }, [gameStatus, roomId]);

  useEffect(() => {
    if (messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      console.log('마지막 메시지 전체:', lastMsg);
      console.log('마지막 메시지 닉네임:', lastMsg.nickname);
      console.log('마지막 메시지 내용:', lastMsg.message);
    }
  }, [messages]);

  useEffect(() => {
    // 메시지 배열이 업데이트될 때마다 로그 출력
    console.log("현재 메시지 배열:", messages);

    // 메시지가 있을 경우 각 메시지의 닉네임을 확인
    if (messages.length > 0) {
      messages.forEach((msg, idx) => {
        console.log(`메시지 ${idx} 닉네임:`, msg.nickname);
      });
    }
  }, [messages]);

  useEffect(() => {
    // UUID 확인 로직 추가
    const checkUuidConsistency = async () => {
      const { uuid } = guestStore.getState();

      if (!uuid) {
        // UUID가 없는 경우 로그인 API 호출
        try {
          const response = await axiosInstance.post('/guests/login');
          console.log("로그인 응답:", response.data);

          // 응답 데이터로 게스트 정보 업데이트
          guestStore.getState().setGuestInfo({
            uuid: response.data.uuid,
            nickname: response.data.nickname,
            guest_id: response.data.guest_id
          });

          console.log("게스트 스토어 업데이트 완료:", guestStore.getState());
        } catch (error) {
          console.error("로그인 실패:", error);
          alert("서버 연결에 문제가 있습니다");
          navigate("/");
        }
      }
    };

    checkUuidConsistency();
  }, [navigate]);

  // 웹소켓 관련 useEffect 수정/추가
  useEffect(() => {
    // participants나 connected 상태가 변경될 때 API 다시 호출
    if (connected) {
      console.log("웹소켓 연결 상태 변경 또는 참가자 목록 업데이트. 참가자 정보 새로고침");
      fetchParticipants();
    }
  }, [connected, participants]);

  // 더 확실한 방법으로, 방 상태 업데이트 웹소켓 메시지를 추가로 처리하기 위해
  // useGameRoomSocket 훅 수정 후, 해당 훅에서 다음 효과를 추가
  useEffect(() => {
    // roomUpdated가 true이면 참가자 정보를 다시 가져옴
    if (roomUpdated) {
      console.log('방 업데이트 트리거 감지, 참가자 정보 새로고침');
      fetchParticipants();
      // 정보를 가져온 후 상태 초기화
      setRoomUpdated(false);
    }
  }, [roomUpdated]);
  if (redirectingToGame) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-white">
        <div className="text-center text-2xl font-extrabold text-red-600 animate-pulse leading-relaxed">
          게임을 이미 시작하셨습니다.<br />게임페이지로 이동 중입니다...
        </div>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen bg-white flex flex-col items-center pt-5 relative overflow-y-auto">
      {/* Close button */}
      {isOwner ? (
        <button
          onClick={handleClickExit}
          className="absolute top-5 right-5 px-4 py-2 bg-red-600 text-white rounded-lg shadow hover:bg-red-700 transition-all"
        >
          방 삭제
        </button>
      ) : (
        <button
          onClick={handleClickExit}
          className="absolute top-5 right-5 px-4 py-2 bg-red-500 text-white rounded-lg shadow hover:bg-red-600 transition-all"
        >
          나가기
        </button>
      )}

      {/* Title */}
      <div className="text-center mb-5">
        <div className="font-bold text-lg">{roomsData.title}</div>
        <div className="font-bold text-base">
          {roomsData?.game_mode} [{roomsData?.participant_count} / {roomsData?.max_players}]
        </div>
      </div>

      {/* Players */}
      <div className="flex flex-col gap-5 mb-auto">
        {(participants.length > 0 ? participants : userInfo)?.map((item, index) => (
          <div
            key={index}
            className="min-w-[100px] h-[160px] px-4 bg-gray-300 rounded-2xl shadow-md flex flex-col items-center justify-center"
          >
            <div className="flex flex-col items-center pt-2">
              <div className="w-[80px] h-[80px] bg-white rounded-2xl"></div>

              {/* 참가자 닉네임 표시 - 다양한 데이터 구조 처리 */}
              <div className="font-bold mt-2 mb-1 text-sm">
                {item.nickname || (item.guest?.nickname) || `게스트_${item.guest_id || index}`}
              </div>

              {/* 참가자 상태 표시 */}
              <div className="text-xs">
                {item.status === 'READY' || item.participant?.status === 'ready' ? (
                  <span className="text-green-600">준비완료</span>
                ) : item.status === 'PLAYING' || item.participant?.status === 'playing' ? (
                  <span className="text-blue-600">게임중</span>
                ) : (
                  <span className="text-gray-600">대기중</span>
                )}
              </div>

              {/* 방장 표시 */}
              {item.is_owner && (
                <div className="text-xs text-red-500 font-bold mt-1">방장</div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Owner button */}
      {isOwner && (
        <div className="w-full text-center mt-4">
          <div className="relative inline-block group">
            <button
              onClick={userInfo.length >= 2 ? handleClickStartBtn : null}
              disabled={userInfo.length < 2}
              className={`px-6 py-2 rounded-lg shadow transition-all font-bold ${userInfo.length >= 2
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-400 text-white cursor-not-allowed'
                }`}
            >
              게임 시작
            </button>
            {userInfo.length < 2 && (
              <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-black text-white text-sm px-4 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 shadow-md">
                2인 이상일 때 게임을 시작할 수 있습니다
              </div>
            )}
          </div>
        </div>
      )}

      {/* Bottom button list */}
      <div className="flex justify-between w-full bg-gray-200 pb-4 mt-auto">
        {Array.from({ length: 5 }).map((_, idx) => (
          <div
            key={idx}
            className="flex-1 py-4 text-center font-bold"
          >
            입티
          </div>
        ))}
      </div>

      {/* 접속 상태 표시 */}
      <div className={`absolute top-5 left-5 w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>

      {/* 채팅 섹션 수정 */}
      <div className="w-full max-w-md mt-4 border border-gray-300 rounded-lg">
        <div className="h-40 overflow-y-auto p-3 bg-gray-100" ref={chatContainerRef}>
          {messages.length > 0 ? (
            messages.map((msg, i) => {
              // 디버깅용 콘솔 로그
              console.log(`메시지 ${i} 상세:`, JSON.stringify(msg));

              return (
                <div key={i} className="mb-2">
                  <span className="font-bold text-blue-600">
                    {msg.nickname || (msg.guest_id ? `게스트_${msg.guest_id}` : `게스트_${i}`)}
                  </span>: <span>{msg.message || ''}</span>
                </div>
              );
            })
          ) : (
            <div className="text-center text-gray-500 py-2">아직 메시지가 없습니다</div>
          )}
        </div>
        <div className="flex border-t p-2">
          <input
            type="text"
            value={chatMessage}
            onChange={(e) => setChatMessage(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="메시지 입력..."
            className="flex-1 px-2 py-1 border rounded-l-md focus:outline-none"
          />
          <button
            onClick={handleSendMessage}
            className="bg-blue-500 text-white px-3 py-1 rounded-r-md"
          >
            전송
          </button>
        </div>
      </div>

      {/* 준비 버튼 */}
      {!isOwner && (
        <button
          onClick={handleReady}
          className="mt-4 px-6 py-2 bg-yellow-500 text-white rounded-lg shadow hover:bg-yellow-600 transition-all"
        >
          준비하기
        </button>
      )}
    </div>
  )
}

export default GameLobbyPage
