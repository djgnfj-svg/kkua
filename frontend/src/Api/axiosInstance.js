import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'http://127.0.0.1:8000/', // 본인 백엔드 주소로 수정
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000, // 요청 제한 시간 (원하는 대로 조절)
});

export default axiosInstance;