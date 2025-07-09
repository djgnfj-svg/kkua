import React from 'react';
import LoadingButton from '../LoadingButton';

const WelcomeSection = ({ startButtonOn, backButtonOn }) => {
  return (
    <div>
      <div className="text-[25px]">
        <span className="text-[33px] text-[#CD0000]">끄</span>
        <span className="text-[#CD0000]">ㅌ</span>
        <span className="text-[#DC8000]">잇기</span>
        <span className="text-[33px] text-[#00B106]">아</span>
        <span className="text-[#00B106]">케</span>
        <span className="text-[#0088CC]">이드</span>
      </div>

      <img
        src="/imgs/logo/kkeua_logo.png"
        alt="끄아 로고"
        className="mx-auto mt-5 w-[40%]"
      />
      <LoadingButton
        onClick={startButtonOn}
        id="Loading__button--startbutton"
        text="시작하기"
      />
      <br />
      <LoadingButton
        onClick={backButtonOn}
        id="Loading__button--backbutton"
        text="뒤로가기"
      />
    </div>
  );
};

export default WelcomeSection;
