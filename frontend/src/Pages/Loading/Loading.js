import React, { useEffect, useState } from 'react'
import './Loading.css';
import { useNavigate } from 'react-router-dom';
import LoadingButton from './LoadingButton';
import TutoModal from './Modal/TutoModal';
import guestStore from '../../store/guestStore'
import axiosInstance from '../../Api/axiosInstance';
import { lobbyUrl } from '../../Component/urls';
import { USER_API } from '../../Api/userApi';
import Cookies from 'js-cookie';
import userIsTrue from '../../Component/userIsTrue';

function Loading() {

  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (result) {
        alert("어허 로그인하셧으면 시작페이지 오지마세요 !");
        navigate(lobbyUrl)
      }
    };
    checkGuest();
  }, []);

  const startButtonOn = async () => {
    try {
      const response = await axiosInstance.post(USER_API.GET_GUEST());
      const data = response.data;

      const current = guestStore.getState();
      if (!current.uuid) {
        guestStore.getState().setGuestInfo({
          uuid: data.uuid,
          nickname: data.nickname,
          guest_id: data.guest_id,
        });

        // 쿠키에 uuid 저장 (이미 없을 경우만)
        if (!Cookies.get('kkua_guest_uuid')) {
          Cookies.set('kkua_guest_uuid', data.uuid, { expires: 1 });
        }
      }

      alert(`게스트 가입을 환영합니다 "${data.nickname}" 님!`);
      setShowModal(true)
    } catch (error) {
      console.error("게스트 생성 실패:", error)
      alert("게스트 로그인에 실패했습니다.")
    }
  }; 

  const backButtonOn = () => {
    window.close(); 
  };

  const guideSections = [
    {
      image: <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>,
      text: (
        <>
          첫 번째 아이템<br />
          재미있는 효과<br />
          플레이를 도와줘요!
        </>
      ),
    },
    {
      image: <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>,
    },
    {
      image: <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>,
      text: (
        <>
          두 번째 아이템<br />
          상대를 방해하거나<br />
          유리하게 만들 수 있어요!
        </>
      ),
    },
    {
      image: <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>,
    },
    {
      image: <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>,
      text: (
        <>
          세 번째 아이템<br />
          위기를 기회로!<br />
          전략적 활용 가능!
        </>
      ),
    },
    {
      image: <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>,
    },
    {
      image: <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>,
      text: (
        <>
          네 번째 아이템<br />
          마지막 한 방!<br />
          반전의 기회를 노려보세요!
        </>
      ),
    },
    {
      image: <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>,
    },
  ];


  return (
    <div className='min-h-screen flex justify-center items-center'>
       <div>
         <div className='text-[25px]'>        
          <a className='text-[33px] text-[#CD0000]' >끄</a>
          <a className='text-[#CD0000]' >ㅌ</a>
          <a className='text-[#DC8000]'>잇기</a>
          <a className='text-[33px] text-[#00B106]' >아</a>
          <a className='text-[#00B106]' >케</a>
          <a className='text-[#0088CC]'>이드</a>
        </div> 
    
        
        <img src='/imgs/logo/kkeua_logoA.png' className="mx-auto mt-5 w-[40%]"></img>
          <LoadingButton onClick={startButtonOn} id="Loading__button--startbutton" text="시작하기"></LoadingButton><br></br>
          <LoadingButton onClick={backButtonOn} id="Loading__button--backbutton" text="뒤로가기"></LoadingButton> 
      </div> 

      <TutoModal showModal={showModal} setShowModal={setShowModal} guideSections={guideSections} />
    </div>
  )
}

export default Loading
