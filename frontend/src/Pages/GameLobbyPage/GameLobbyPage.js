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
  const [roomInfo, setRoomInfo] = useState(null);
  const [participants, setParticipants] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
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
  const fetchRoomData = async () => {
    try {
      setIsLoading(true);
      const response = await axiosInstance.get(`/gamerooms/${roomId}`);
      console.log("방 정보 API 응답:", response.data);

      // API 응답 구조 처리
      if (response.data) {
        // room 객체 저장
        if (response.data.room) {
          setRoomInfo(response.data.room);
        } else {
          // 직접 객체가 room 정보인 경우 (이전 API 호환)
          setRoomInfo(response.data);
        }

        // participants 배열 저장
        if (response.data.participants && Array.isArray(response.data.participants)) {
          setParticipants(response.data.participants);
        }
      }
    } catch (error) {
      console.error("방 정보 가져오기 실패:", error);
    } finally {
      setIsLoading(false);
    }
  };

  /* 방장 확인 */
  const checkIfOwnerFromParticipants = () => {
    // 현재 사용자의 guest_id 가져오기
    const { guest_id } = guestStore.getState();

    // 참가자 목록에서 현재 사용자가 방장인지 확인
    const currentUser = participants.find(p => p.guest_id === guest_id);
    return currentUser?.is_creator === true;
  };

  useEffect(() => {
    fetchRoomData();

    // 주기적으로 방 정보 갱신 (옵션)
    const interval = setInterval(fetchRoomData, 30000);
    return () => clearInterval(interval);
  }, [roomId]);

  // 방장 여부 확인 useEffect - fetchRoomData에서 가져온 데이터 사용
  useEffect(() => {
    // 참가자 정보로 방장 여부 확인
    const isOwnerFromParticipants = checkIfOwnerFromParticipants();
    if (isOwnerFromParticipants !== undefined) {
      setIsOwner(isOwnerFromParticipants);
      return;
    }

    // 기존 API 호출 방식으로 확인 (백업)
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

    checkIfOwner();
  }, [roomId, participants]);

  /* Exit from Room BTN */
  const handleClickExit = () => {
    const lobbyUrl = "/lobby";
    
    if (isOwner) {
      let confirmDelete = window.confirm("정말로 방을 삭제하시겠습니까?");
      if (confirmDelete) {
        try {
          // 방 삭제 API 직접 호출
          axiosInstance.delete(ROOM_API.DELET_ROOMSID(roomId))
            .then(() => {
              alert("방이 삭제되었습니다.");
              navigate(lobbyUrl);
            })
            .catch((error) => {
              alert("당신은 나갈수 없어요. 끄아지옥 ON....");
              console.log(error);
            });
        } catch (error) {
          alert("당신은 나갈수 없어요. 끄아지옥 ON.... Create User");
          console.log(error);
        }
      }
    } else {
      let confirmLeave = window.confirm("로비로 나가시겠습니까?");
      if (confirmLeave) {
        try {
          // uuid 가져오기
          const { uuid } = guestStore.getState();

          // 요청 본문에 게스트 UUID 추가
          axiosInstance.post(ROOM_API.LEAVE_ROOMS(roomId), {
            guest_uuid: uuid
          })
          .then(() => {
            alert("방에서 나갑니다!");
            navigate(lobbyUrl);
          })
          .catch((error) => {
            console.error("방 나가기 실패:", error);
            alert("당신은 나갈수 없어요. 끄아지옥 ON....");
          });
        } catch (error) {
          console.error("방 나가기 실패:", error);
          alert("당신은 나갈수 없어요. 끄아지옥 ON....");
        }
      }
    }
  };

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

  /* 웹소켓 연결 사용 부분 개선 */
  const {
    connected,
    messages,
    participants: socketParticipants,
    gameStatus,
    isReady,
    sendMessage,
    toggleReady,
    updateStatus,
    roomUpdated,
    setRoomUpdated,
    connect, // 연결 메서드 추가
    disconnect // 연결 종료 메서드 추가
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

  /* 준비 상태 업데이트 핸들러 수정 */
  const handleReady = () => {
    toggleReady(); // 새로운 toggleReady 함수 사용
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

  // 웹소켓 연결 상태 모니터링 및 재연결 로직 추가
  useEffect(() => {
    console.log("웹소켓 연결 상태:", connected ? "연결됨" : "연결 안됨");

    // 연결이 안 되어 있으면 명시적으로 연결 시도
    if (!connected && connect) {
      console.log("웹소켓 연결 시도...");
      connect();
    }

    // 컴포넌트 언마운트 시 연결 종료
    return () => {
      console.log("컴포넌트 언마운트: 웹소켓 연결 종료");
      if (disconnect) disconnect();
    };
  }, [connected, connect, disconnect]);

  // 웹소켓 참가자 정보와 API 참가자 정보 동기화
  useEffect(() => {
    if (connected && socketParticipants && socketParticipants.length > 0) {
      console.log("소켓에서 받은 참가자 정보:", socketParticipants);
      setParticipants(socketParticipants);
    }
  }, [connected, socketParticipants]);

  // 게임 상태 변경 시 처리 (playing으로 변경되면 게임 페이지로 이동)
  useEffect(() => {
    console.log("현재 게임 상태:", gameStatus);
    if (gameStatus === 'playing') {
      console.log("게임 상태가 'playing'으로 변경됨 -> 게임 페이지로 이동");
      navigate(gameUrl(roomId));
    }
  }, [gameStatus, roomId, navigate]);

  // roomUpdated 이벤트 처리 수정
  useEffect(() => {
    // roomUpdated가 true이면 방 정보를 다시 가져옴
    if (roomUpdated) {
      console.log('방 업데이트 트리거 감지, 방 정보 새로고침');
      fetchRoomData();
      // 정보를 가져온 후 상태 초기화
      setRoomUpdated(false);
    }
  }, [roomUpdated]);

  // 추가: 주기적으로 웹소켓 연결 상태 확인
  useEffect(() => {
    const checkWebSocketConnection = () => {
      console.log("웹소켓 연결 상태 주기적 확인:", connected ? "연결됨" : "연결 안됨");

      // 연결이 끊어진 경우 재연결 시도
      if (!connected && connect) {
        console.log("웹소켓 연결 끊김 감지, 재연결 시도...");
        connect();
      }
    };

    // 10초마다 연결 상태 확인
    const intervalId = setInterval(checkWebSocketConnection, 10000);

    return () => clearInterval(intervalId);
  }, [connected, connect]);

  if (redirectingToGame) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-white">
        <div className="text-center text-2xl font-extrabold text-red-600 animate-pulse leading-relaxed">
          게임을 이미 시작하셨습니다.<br />게임페이지로 이동 중입니다...
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="w-full h-screen flex items-center justify-center bg-white">
        <div className="text-center text-2xl font-bold animate-pulse">
          로딩 중...
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
        <div className="font-bold text-lg">
          {roomInfo?.title || "로딩 중..."}
        </div>
        <div className="font-bold text-base">
          {roomInfo?.game_mode || "표준"} [{participants.length} / {roomInfo?.max_players || 8}]
        </div>
      </div>

      {/* Players */}
      <div className="flex flex-col gap-5 mb-auto">
        {participants.map((player, index) => (
          <div
            key={player.guest_id || index}
            className="min-w-[100px] h-[160px] px-4 bg-gray-300 rounded-2xl shadow-md flex flex-col items-center justify-center"
          >
            <div className="flex flex-col items-center pt-2">
              <div className="w-[80px] h-[80px] bg-white rounded-2xl"></div>

              {/* 참가자 닉네임 표시 */}
              <div className="font-bold mt-2 mb-1 text-sm">
                {player.nickname || `게스트_${player.guest_id}`}
              </div>

              {/* 참가자 상태 표시 */}
              <div className="text-xs">
                {player.status === 'READY' || player.status === 'ready' ? (
                  <span className="text-green-600">준비완료</span>
                ) : player.status === 'PLAYING' || player.status === 'playing' ? (
                  <span className="text-blue-600">게임중</span>
                ) : (
                  <span className="text-gray-600">대기중</span>
                )}
              </div>

              {/* 방장 표시 */}
              {player.is_creator && (
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
              onClick={() => {
                // 디버깅을 위한 콘솔 로그 추가
                console.log("참가자 전체 목록:", socketParticipants);

                // 각 참가자별 준비 상태 확인 로그
                socketParticipants.forEach((player, index) => {
                  console.log(`참가자 ${index} 정보:`, {
                    닉네임: player.nickname || `게스트_${player.guest_id}`,
                    방장여부: player.is_creator ? "방장" : "일반 참가자",
                    준비상태: player.is_creator ? "방장(준비체크 제외)" :
                      (player.status === 'READY' || player.status === 'ready' ?
                        "준비완료" : "미준비")
                  });
                });

                // 모든 플레이어가 준비되었는지 확인 (방장 제외)
                const allNonOwnerPlayersReady = socketParticipants.every(player =>
                  player.is_creator || // 방장은 준비 상태 확인에서 제외
                  player.status === 'READY' ||
                  player.status === 'ready'
                );

                console.log("모든 비방장 참가자 준비 완료?", allNonOwnerPlayersReady);
                console.log("참가자 수:", socketParticipants.length);

                if (socketParticipants.length >= 2 && allNonOwnerPlayersReady) {
                  console.log("✅ 게임 시작 조건 충족: 게임을 시작합니다");
                  handleClickStartBtn();
                } else if (socketParticipants.length < 2) {
                  console.log("❌ 게임 시작 실패: 참가자 수 부족");
                  alert('게임 시작을 위해 최소 2명의 플레이어가 필요합니다.');
                } else {
                  console.log("❌ 게임 시작 실패: 모든 플레이어가 준비되지 않음");
                  alert('모든 플레이어가 준비 상태여야 합니다.');
                }
              }}
              className={`px-6 py-2 rounded-lg shadow transition-all font-bold ${socketParticipants.length >= 2
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-400 text-white cursor-not-allowed'
                }`}
            >
              게임 시작
            </button>
            {socketParticipants.length < 2 && (
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

      {/* 준비 버튼 - 상태에 따라 텍스트와 색상 변경 */}
      {!isOwner && (
        <button
          onClick={handleReady}
          className={`mt-4 px-6 py-2 ${isReady
            ? 'bg-green-500 hover:bg-green-600'
            : 'bg-yellow-500 hover:bg-yellow-600'
            } text-white rounded-lg shadow transition-all`}
        >
          {isReady ? '준비완료' : '준비하기'}
        </button>
      )}
    </div>
  )
}

export default GameLobbyPage
