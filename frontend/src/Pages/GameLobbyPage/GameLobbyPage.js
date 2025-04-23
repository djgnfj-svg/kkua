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
  const [hasShownAlert, setHasShownAlert] = useState(false);
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
          if (!hasShownAlert) {
            alert("서버 연결에 문제가 있습니다\n로비로 이동합니다...");
            setHasShownAlert(true);
            setRedirectingToGame(true);
            setTimeout(() => navigate(lobbyUrl), 1000);
          }
        }
      }
    };
    checkGuest();
  }, [navigate, hasShownAlert]);

  /* 참가자 정보 */
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
        }
      }
    } catch (error) {
      console.error("참가자 정보 가져오기 실패:", error)
      // 오류 발생 시 빈 배열로 설정하여 UI 에러 방지
      setUserInfo([]);
      setRedirectingToGame(true); // 로딩 UI 표시
      setTimeout(() => navigate(lobbyUrl), 3000); // 1초 뒤 이동
    }
  };

  /* 방장 확인 */
  const checkIfOwner = async () => {
    try {
      const response = await axiosInstance.get(`/gamerooms/${roomId}/is-owner`);
      console.log("방장 확인 응답:", response.data);

      if (response.data.is_owner) {
        console.log("✅ 방장 확인: 현재 사용자는 방장입니다!");
        setIsOwner(true);
      } else {
        console.log("❌ 방장 확인: 현재 사용자는 방장이 아닙니다.");
        setIsOwner(false);
      }
    } catch (error) {
      console.error("방장 여부 확인 실패:", error);
      setIsOwner(false);
    }
  };

  useEffect(() => {
    fetchParticipants();
    checkIfOwner(); // 방장 여부 확인 추가
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
      // 여기서 백엔드의 게임 시작 엔드포인트 호출
      const response = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId));

      // 응답 로깅하여 디버깅 지원
      console.log("게임 시작 응답:", response.data);

      alert("게임이 시작됩니다!");
      navigate(gameUrl(roomId));
    } catch (error) {
      console.error("게임 시작 오류:", error);

      // 오류 메시지 상세하게 표시
      if (error.response && error.response.data && error.response.data.detail) {
        alert(`게임 시작 실패: ${error.response.data.detail}`);
      } else {
        alert("게임을 시작할 수 없습니다. 모든 플레이어가 준비되었는지 확인하세요.");
      }
    }
  }

  /* 웹소켓 연결 사용 */
  const {
    connected,
    messages,
    participants,
    gameStatus,
    isReady,
    sendMessage,
    toggleReady,
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

  // 준비 상태 핸들러: 서버에 상태 전달 후 약간의 지연을 두고 참가자 정보 갱신
  const handleReady = () => {
    toggleReady(); // 서버에 상태 전달

    // 상태 갱신을 위해 참여자 정보를 수동으로 최신화
    setTimeout(() => {
      fetchParticipants();
      setRoomUpdated(true);
    }, 300); // 약간의 지연을 줘서 서버 처리 반영 기다림
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

  // 웹소켓 관련 useEffect 수정/추가
  useEffect(() => {
    // participants나 connected 상태가 변경될 때 API 다시 호출
    if (connected) {
      console.log("웹소켓 연결 상태 변경 또는 참가자 목록 업데이트. 참가자 정보 새로고침");
      fetchParticipants();
    }
  }, [connected, participants]);
  useEffect(() => {
    const handleParticipantUpdate = () => fetchParticipants();
    window.addEventListener("participantStatusUpdated", handleParticipantUpdate);
    return () => window.removeEventListener("participantStatusUpdated", handleParticipantUpdate);
  }, []);

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
          잘못된 정보입니다. <br />페이지를 이동합니다.
        </div>
      </div>
    );
  }

  // 상단 정보 바 추가
  // (이 바는 main return 바로 위에 위치해야 함)
  // 아래의 return문 바로 위에 삽입

  return (
    <>
      {/* 상단 정보 바 */}
      <div className="w-full bg-gray-100 py-2 px-4 flex justify-around items-center border-b border-gray-300 mb-4">
        <div className="text-sm font-semibold text-gray-700">
          게임 모드: 아케이드
        </div>
        <div className="text-sm font-semibold text-gray-700">
          방 제목: {roomsData?.title || '---'}
        </div>
        <div className="text-sm font-semibold text-gray-700">
          인원: {userInfo.length} / {roomsData?.max_players || '-'}
        </div>
      </div>
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

        {/* Players */}
        <div className="flex flex-row flex-wrap justify-center gap-4 w-full px-4">
          {participants.map((item, index) => (
            <div
              key={index}
              className={`w-[140px] h-[180px] rounded-2xl shadow-lg flex flex-col items-center justify-start pt-4 gap-1 border participant-card ${(item.is_owner || item.is_creator || (item.guest && item.guest.guest_id === roomsData.created_by))
                  ? 'bg-white'
                  : (item.status === 'READY' || item.status === 'ready' || item.is_ready === true)
                    ? 'bg-[rgb(115,200,255)]'
                    : 'bg-[rgb(203,203,203)]'
                }`}
            >
              {/* 프로필 원 */}
              <div className="w-[60px] h-[60px] bg-[#fde2e4] rounded-full flex items-center justify-center text-xl font-bold text-gray-700 shadow">
                {item.nickname?.charAt(0)?.toUpperCase() || 'G'}
              </div>

              {/* 닉네임 */}
              <div className="mt-1 font-bold text-sm text-gray-800">
                {item.nickname || (item.guest?.nickname) || `Guest_${item.guest_id || index}`}
              </div>

              {/* 상태 뱃지 */}
              {!(item.is_owner || item.is_creator || (item.guest && item.guest.guest_id === roomsData.created_by)) && (
                <div
                  className="text-xs mt-0.5 px-2 py-0.5 rounded-full font-semibold text-white"
                  style={{
                    backgroundColor:
                      (item.status === 'READY' || item.status === 'ready' || item.is_ready === true) ? '#e9b306' : // green
                        (item.status === 'PLAYING' || item.status === 'playing') ? '#3b82f6' : // blue
                          '#d1d5db' // gray
                  }}
                >
                  {(item.status === 'READY' || item.status === 'ready' || item.is_ready === true)
                    ? '준비완료'
                    : (item.status === 'PLAYING' || item.status === 'playing')
                      ? '게임중'
                      : '대기중'}
                </div>
              )}

              {/* 방장 뱃지 */}
              {(item.is_owner || item.is_creator || (item.guest && item.guest.guest_id === roomsData.created_by)) && (
                <div className="text-xs mt-1 px-2 py-0.5 bg-red-500 text-white rounded-full font-semibold">
                  방장
                </div>
              )}
            </div>
          ))}
        </div>
        {/* 준비 버튼 - 상태에 따라 텍스트와 색상 변경 (참가자 카드 아래로 이동) */}
        {!isOwner && (
          <button
            onClick={handleReady}
            className={`mt-4 px-6 py-2 ${isReady
              ? 'bg-green-500 hover:bg-green-600'
              : 'bg-yellow-500 hover:bg-yellow-600'
              } text-white rounded-lg shadow transition-all`}
          >
            {isReady ? '준비취소' : '준비하기'}
          </button>
        )}

        {/* Owner button */}
        {isOwner && (
          <div className="w-full text-center mt-4">
            <div className="relative inline-block group">
              <button
                onClick={() => {
                  // 디버깅을 위한 콘솔 로그 추가
                  console.log("참가자 전체 목록:", participants);

                  // 각 참가자별 준비 상태 확인 로그
                  participants.forEach((player, index) => {
                    console.log(`참가자 ${index} 정보:`, {
                      닉네임: player.nickname || (player.guest?.nickname) || `게스트_${player.guest_id || index}`,
                      방장여부: player.is_owner ? "방장" : "일반 참가자",
                      준비상태: player.is_owner ? "방장(준비체크 제외)" :
                        (player.status === 'READY' || player.status === 'ready' || player.is_ready === true ?
                          "준비완료" : "미준비")
                    });
                  });

                  // 모든 플레이어가 준비되었는지 확인 (방장 제외)
                  const allNonOwnerPlayersReady = participants.every(player =>
                    player.is_owner || // 방장은 준비 상태 확인에서 제외
                    player.status === 'READY' ||
                    player.status === 'ready' ||
                    player.is_ready === true
                  );

                  console.log("모든 비방장 참가자 준비 완료?", allNonOwnerPlayersReady);
                  console.log("참가자 수:", participants.length);

                  if (participants.length >= 2 && allNonOwnerPlayersReady) {
                    console.log("✅ 게임 시작 조건 충족: 게임을 시작합니다");
                    handleClickStartBtn();
                  } else if (participants.length < 2) {
                    console.log("❌ 게임 시작 실패: 참가자 수 부족");
                    alert('게임 시작을 위해 최소 2명의 플레이어가 필요합니다.');
                  } else {
                    console.log("❌ 게임 시작 실패: 모든 플레이어가 준비되지 않음");
                    alert('모든 플레이어가 준비 상태여야 합니다.');
                  }
                }}
                className={`px-6 py-2 rounded-lg shadow transition-all font-bold ${participants.length >= 2
                  ? 'bg-blue-600 text-white hover:bg-blue-700'
                  : 'bg-gray-400 text-white cursor-not-allowed'
                  }`}
              >
                게임 시작
              </button>
              {participants.length < 2 && (
                <div className="absolute -top-10 left-1/2 transform -translate-x-1/2 bg-black text-white text-sm px-4 py-2 rounded-lg whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-10 shadow-md">
                  2인 이상일 때 게임을 시작할 수 있습니다
                </div>
              )}
            </div>
          </div>
        )}


        {/* 접속 상태 표시 */}
        <div className={`absolute top-5 left-5 w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>

        {/* 채팅 섹션 (리뉴얼) */}
        <div className="w-full mt-4 border border-gray-300 rounded-lg bg-white flex flex-col h-[300px] overflow-hidden shadow-md">
          {/* 채팅 상단 바 */}
          <div className="bg-slate-900 text-white text-center py-2 font-bold">
            채팅
          </div>

          {/* 채팅 메시지 목록 */}
          <div className="flex-1 overflow-y-auto px-4 py-2 bg-gray-50 text-sm" ref={chatContainerRef}>
            {messages.length > 0 ? (
              messages.map((msg, i) => {
                const isSystem = msg.type === 'system';
                // guest_id 판별 로직 보강 및 디버깅 로그 추가
                const myGuestId = String(guestStore.getState().guest_id);
                const messageGuestId = String(msg.guest_id || (msg.guest && msg.guest.guest_id) || '');

                console.log('내 guest_id:', myGuestId);
                console.log('메시지 guest_id:', messageGuestId);
                console.log('같은 사람인가?', messageGuestId === myGuestId);

                const isSelf = messageGuestId === myGuestId;

                // Listen for participantStatusUpdated event and refresh participants

                return (
                  <div key={i} className={`mb-2 ${isSystem ? 'text-center text-gray-600' : ''}`}>
                    {isSystem ? (
                      <div>
                        <span className="text-blue-500 font-semibold">시스템</span>{' '}
                        <span className="text-xs text-gray-400 ml-1">{new Date(msg.timestamp).toLocaleTimeString()}</span>
                        <div>{msg.message}</div>
                      </div>
                    ) : (
                      <div className={`w-full flex mb-2 ${isSelf ? 'justify-end' : 'justify-start'}`}>
                        <div className={`flex flex-col items-start max-w-[80%] text-sm ${isSelf ? 'items-end text-right' : 'items-start text-left'}`}>
                          <span className={`font-bold mb-1 ${isSelf ? 'text-orange-500' : 'text-blue-600'}`}>
                            {msg.nickname || `게스트_${msg.guest_id}`}
                          </span>
                          <div className="bg-white border rounded px-2 py-1 shadow text-black break-words">
                            {msg.message || ''}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-center text-gray-400">아직 메시지가 없습니다</div>
            )}
          </div>

          {/* 채팅 입력창 */}
          <div className="flex border-t border-gray-300 p-2 bg-white">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="채팅 메시지를 입력하세요..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none"
            />
            <button
              onClick={handleSendMessage}
              className="bg-blue-500 text-white px-4 py-2 rounded-r-md hover:bg-blue-600"
            >
              전송
            </button>
          </div>
        </div>

      </div>
    </>
  )
}

export default GameLobbyPage
