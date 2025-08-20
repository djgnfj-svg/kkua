import axios from 'axios';

// Get API URL from environment variables
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  withCredentials: true, // Include cookies for session management
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Log request in development
    if (import.meta.env.VITE_DEBUG) {
      console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    console.error('[API Request Error]', error);
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    // Log response in development
    if (import.meta.env.VITE_DEBUG) {
      console.log(`[API Response] ${response.status} ${response.config.url}`);
    }
    return response;
  },
  (error) => {
    console.error('[API Response Error]', error);
    
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login or clear session
      console.warn('Unauthorized access - clearing session');
      localStorage.removeItem('user');
    }
    
    return Promise.reject(error);
  }
);

// API endpoints
export const apiEndpoints = {
  // Health check
  health: () => api.get('/health'),
  
  // Auth endpoints
  auth: {
    loginGuest: (nickname: string) => api.post('/auth/login', { nickname }),
    logout: () => api.post('/auth/logout'),
    me: () => api.get('/auth/me'),
  },
  
  // Game room endpoints
  gameRooms: {
    list: () => api.get('/gamerooms'),
    create: (name: string, maxPlayers: number = 4) => 
      api.post('/gamerooms', { name, max_players: maxPlayers }),
    join: (roomId: string) => api.post(`/gamerooms/${roomId}/join`),
    leave: (roomId: string) => api.post(`/gamerooms/${roomId}/leave`),
    get: (roomId: string) => api.get(`/gamerooms/${roomId}`),
  },
  
  // Game endpoints
  game: {
    submitWord: (roomId: string, word: string) => 
      api.post(`/gamerooms/${roomId}/submit-word`, { word }),
  },
  
  // Item endpoints
  items: {
    inventory: (userId: number) => api.get(`/users/${userId}/inventory`),
    list: () => api.get('/items/list'),
  },
};

export default api;