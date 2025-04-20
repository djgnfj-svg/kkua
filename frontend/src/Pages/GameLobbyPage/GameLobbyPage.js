import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axiosInstance from '../../Api/axiosInstance';
import { gameLobbyUrl, gameUrl, lobbyUrl } from '../../Component/urls';
import userIsTrue from '../../Component/userIsTrue';
import { ROOM_API } from '../../Api/roomApi';
import guestStore from '../../store/guestStore';

function GameLobbyPage() {
  const { roomId } = useParams();
  const [roomsData, setRoomsData] = useState({
    title: "",
    game_mode: "",
    max_players: 0
  });
  const [userInfo , setUserInfo] = useState([]);
  const [isOwner, setIsOwner] = useState(false);
  const [redirectingToGame, setRedirectingToGame] = useState(false);
  const navigate = useNavigate();

  /* Guest Check */
  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (!result) {
        alert("올바르지않은 접근입니다.");
        navigate("/");
        return;
      }
    };
    checkGuest();
  }, []);

   /* ROOM INFO */
   useEffect(() => {
    axiosInstance.patch(`${ROOM_API.get_ROOMSID(roomId)}`)
    .then(res => {
      setRoomsData(res.data)
      const guestInfo = JSON.parse(localStorage.getItem('guest-storage'))?.state;
      if (guestInfo?.nickname === res.data.created_username) {
        setIsOwner(true);
      }
      console.log("GET 성공:", res.data);
    })
    .catch(err => {
      console.error("GET 실패:", err.response?.data || err.message);
    });
  },[])

  /* USER INFO */
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const res = await axiosInstance.get(ROOM_API.get_ROOMSUSER(roomId));
        console.log(res.data)
        setUserInfo(res.data);
        
        const guestInfo = JSON.parse(localStorage.getItem('guest-storage'))?.state;
        // const guestNicknames = res.data.map((item) => item.guest.nickname);
        const rawNickname = guestInfo?.nickname;
        const cleanedNickname = rawNickname?.replace(/^"|"$/g, '');
        console.log("guestInfo:", cleanedNickname);
        if (!cleanedNickname.includes(guestInfo?.nickname)) {
          alert("이 방에 참가된 유저가 아닙니다.");
          navigate(lobbyUrl);
        }
        
        const guestUUID = guestStore.getState().uuid;
        const currentGuest = res.data.find((item) => item.guest.uuid === guestUUID);
        if (currentGuest?.participant?.status === 'playing') {
          setRedirectingToGame(true);
          setTimeout(() => {
            setRedirectingToGame(false);
            navigate(gameUrl(roomId));
          }, 3000);
        }
      } catch (error) {
        console.log(error)
        if (error.response?.status === 404) {
          alert("이미 존재하지 않는 방입니다.");
          navigate(lobbyUrl);
        } else if (error.response?.status === 400 && error.response.data?.detail === "이 방에 참여하고 있지 않습니다.") {
          alert("이 방에 참여하고 있지 않습니다.");
          navigate(lobbyUrl);
        } else {
          console.log(error);
        }
      }
    };

    fetchUserInfo();
  }, []);

  /* LEAVE ROOM */
  const handleClickExit = async () => {
    if(isOwner){
      let res = window.confirm("방을 삭제 하시겟습니까?")
      if(res){
        try{
          const res = await axiosInstance.delete(ROOM_API.DELET_ROOMSID(roomId))
          navigate(lobbyUrl)
      }catch(error){
        console.log(error)
      }
    }
    } else {
      let res = window.confirm("로비로 나가시겠습니까?");
      if(res){
        try{
          await axiosInstance.post(ROOM_API.LEAVE_ROOMS(roomId))
          navigate(lobbyUrl);
        } catch(error){
          if (error.response?.status === 400 && error.response.data?.detail === "이 방에 참여하고 있지 않습니다.") {
            alert("이미 나간 방이거나 존재하지 않는 방입니다.");
            navigate(lobbyUrl);
          } else {
            console.log(error);
          }
        }
      }
    }
  }

  /* Start BTN */
  const handleClickStartBtn = async (id) => {
    try{
      const res = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId))
      alert("게임이 시작됩니다 !");
      navigate(gameUrl(roomId));
    }catch(error){
      alert("게임을 시작할 수 없습니다.")
      console.log(error)
    }
  }

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
          {roomsData?.game_mode} [{roomsData?.people} / {roomsData?.max_players}]
        </div>
      </div>

      {/* Players */}
      <div className="flex flex-col gap-5 mb-auto">
        {userInfo?.map((item,index) => (
          <div
            key={index}
            className="min-w-[100px] h-[160px] px-4 bg-gray-300 rounded-2xl shadow-md flex flex-col items-center justify-center"
          >
              <div className="flex flex-col items-center pt-2">
                <div className="w-[80px] h-[80px] bg-white rounded-2xl"></div>
                <div className="font-bold mt-2 mb-1 text-sm">
                  {item.guest.nickname.split('_')[0]}_
                </div>
                <div className="font-bold mt-2 mb-1 text-sm">
                  {item.guest.nickname.split('_')[1]}
                </div>
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
              className={`px-6 py-2 rounded-lg shadow transition-all font-bold ${
                userInfo.length >= 2
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
        {Array.from({ length: 5}).map((_, idx) => (
          <div
            key={idx}
            className="flex-1 py-4 text-center font-bold"
          >
            입티
          </div>
        ))}
      </div>
    </div>
  )
}

export default GameLobbyPage
