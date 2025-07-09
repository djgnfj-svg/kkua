import axiosInstance from './axiosInstance';

export const authApi = {
  // 로그인 또는 새 게스트 생성
  login: async (nickname = null) => {
    const response = await axiosInstance.post('/auth/login', {
      nickname,
    });
    return response.data;
  },

  // 로그아웃
  logout: async () => {
    const response = await axiosInstance.post('/auth/logout');
    return response.data;
  },

  // 현재 사용자 정보 조회
  getProfile: async () => {
    const response = await axiosInstance.get('/auth/me');
    return response.data;
  },

  // 프로필 업데이트
  updateProfile: async (nickname) => {
    const response = await axiosInstance.put('/auth/me', { nickname });
    return response.data;
  },

  // 인증 상태 확인
  checkAuthStatus: async () => {
    const response = await axiosInstance.get('/auth/status');
    return response.data;
  },
};

export default authApi;
