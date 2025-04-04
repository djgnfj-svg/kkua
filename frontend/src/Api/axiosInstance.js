import axios from 'axios';


const axiosInstance = axios.create({
  baseURL: process.env.REACT_APP_API_URL, // localhost 배포시 변경
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000, // 요청 제한 시간 (원하는 대로 조절)
});

export default axiosInstance;