import React, { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import axiosInstance from '../../Api/axiosInstance';
import { gameLobbyUrl, gameUrl, lobbyUrl } from '../../Component/urls';
import userIsTrue from '../../Component/userIsTrue';
import { ROOM_API } from '../../Api/roomApi';

function GameLobbyPage() {
  const { roomId } = useParams();
  const [roomsData, setRoomsData] = useState({
    title: "",
    game_mode: "",
    max_players: 0
  });
  const [userInfo , setUserInfo] = useState([]);
  const [isOwner, setIsOwner] = useState(false);
  const navigate = useNavigate();

  /* Guest Check */
  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (!result) {
        alert("어멋 어딜들어오세요 Get Out !");
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
      } catch (error) {
        console.log(error);
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
        alert("당신은 나갈수 없어요. 끄아지옥 ON.... Create User");
        console.log(error)
      }
    }
    }else{
    let res = window.confirm("로비로 나가시겠습니까?");
    if(res){
      try{
        await axiosInstance.post(ROOM_API.LEAVE_ROOMS(roomId))
        navigate(lobbyUrl);
      }catch(error){
        alert("당신은 나갈수 없어요. 끄아지옥 ON....");
        console.log(error)
      }
    }
  }}

  /* Start BTN */
  const handleClickStartBtn = async (id) => {
    try{
      const res = await axiosInstance.post(ROOM_API.PLAY_ROOMS(roomId))
      alert("게임이 시작됩니다 !");
      navigate(gameUrl(roomId));
    }catch(error){
      alert("버그행동 금지")
      console.log(error)
    }
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
          <button onClick={handleClickStartBtn} className="px-6 py-2 bg-blue-600 text-white rounded-lg shadow hover:bg-blue-700 transition-all"  >
            게임 시작
          </button>
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
