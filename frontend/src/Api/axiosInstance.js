import axios from 'axios';

const axiosInstance = axios.create({
  baseURL:
    window.location.hostname === 'localhost'
      ? 'http://localhost:8000'
      : 'https://your-production-api.com', // replace with actual production API if needed
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 5000,
  withCredentials: true,
});

export default axiosInstance;
