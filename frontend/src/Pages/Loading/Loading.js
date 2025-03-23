import React from 'react'
import './Loading.css';
import { useNavigate } from 'react-router-dom';
import LoadingButton from './LoadingButton';

function Loading() {

  const navigate = useNavigate();

  const startButtonOn = () => {
    navigate('/lobby'); 
  }; 

  const backButtonOn = () => {
    window.close(); 
  };

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
        
        <img src='/imgs/logo/kkeua_logo.png' className="mx-auto mt-5 w-[40%]"></img>
          <LoadingButton onClick={startButtonOn} id="Loading__button--startbutton" text="시작하기"></LoadingButton><br></br>
          <LoadingButton onClick={backButtonOn} id="Loading__button--backbutton" text="뒤로가기"></LoadingButton> 
      </div> 
    </div>
  )
}

export default Loading
