import axiosInstance from '../Api/axiosInstance';

async function userIsTrue() {
  try {
    // 새로운 인증 시스템의 상태 확인 API 사용
    const response = await axiosInstance.get('/auth/status');
    
    // 인증 상태 확인
    if (response.data && response.data.authenticated) {
      return true;
    }
  } catch (error) {
    console.warn('인증 상태 확인 중 오류 발생:', error);
  }

  return false;
}

export default userIsTrue;
