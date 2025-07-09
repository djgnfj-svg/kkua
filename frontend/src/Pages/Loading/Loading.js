import React, { useEffect, useState } from 'react';
import './Loading.css';
import { useNavigate } from 'react-router-dom';
import TutoModal from './Modal/TutoModal';
import axiosInstance from '../../Api/axiosInstance';
import { lobbyUrl } from '../../Component/urls';
import { USER_API } from '../../Api/userApi';
import userIsTrue from '../../Component/userIsTrue';
import guestStore from '../../store/guestStore';
import WelcomeSection from './components/WelcomeSection';

function Loading() {
  console.log('Loading 컴포넌트 렌더링');

  const [showModal, setShowModal] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const checkGuest = async () => {
      const result = await userIsTrue();
      if (result) {
        alert('어허 로그인하셧으면 시작페이지 오지마세요 !');
        navigate(lobbyUrl);
      }
    };
    checkGuest();
  }, [navigate]);

  const startButtonOn = async () => {
    try {
      const response = await axiosInstance.post(USER_API.GET_GUEST, {
        nickname: null,
        device_info: navigator.userAgent,
      });

      const data = response.data;

      guestStore.getState().setGuestInfo(data);

      alert(`게스트 ${data.nickname}님으로 로그인되었습니다!`);

      setTimeout(() => {
        setShowModal(true);
      }, 100);
    } catch (error) {
      console.error('게스트 로그인 실패:', error);
      alert('게스트 로그인에 실패했습니다.');
    }
  };

  const backButtonOn = () => {
    window.close();
  };

  const guideSections = [
    {
      image: (
        <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>
      ),
      text: (
        <>
          첫 번째 아이템
          <br />
          재미있는 효과
          <br />
          플레이를 도와줘요!
        </>
      ),
    },
    {
      image: (
        <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>
      ),
    },
    {
      image: (
        <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>
      ),
      text: (
        <>
          두 번째 아이템
          <br />
          상대를 방해하거나
          <br />
          유리하게 만들 수 있어요!
        </>
      ),
    },
    {
      image: (
        <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>
      ),
    },
    {
      image: (
        <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>
      ),
      text: (
        <>
          세 번째 아이템
          <br />
          위기를 기회로!
          <br />
          전략적 활용 가능!
        </>
      ),
    },
    {
      image: (
        <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>
      ),
    },
    {
      image: (
        <div className="w-[60px] h-[60px] border border-red-300 mr-2"></div>
      ),
      text: (
        <>
          네 번째 아이템
          <br />
          마지막 한 방!
          <br />
          반전의 기회를 노려보세요!
        </>
      ),
    },
    {
      image: (
        <div className="w-full h-[120px] bg-gray-200 border border-red-300"></div>
      ),
    },
  ];

  return (
    <div className="min-h-screen flex justify-center items-center">
      <WelcomeSection
        startButtonOn={startButtonOn}
        backButtonOn={backButtonOn}
      />

      <TutoModal
        showModal={showModal}
        setShowModal={(show) => {
          console.log('모달 상태 변경:', show);
          setShowModal(show);
          if (!show) {
            console.log('모달 닫힘 - 로비로 이동 시도');
            navigate(lobbyUrl);
          }
        }}
        guideSections={guideSections}
      />
    </div>
  );
}

export default Loading;
