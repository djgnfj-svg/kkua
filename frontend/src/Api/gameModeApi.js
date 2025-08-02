import axiosInstance from './axiosInstance';

const GAME_MODE_API_BASE = '/game-modes';

/**
 * 게임 모드 관련 API 함수들
 */
export const gameModeApi = {
  /**
   * 모든 게임 모드 조회
   */
  getAllModes: async (activeOnly = true) => {
    try {
      const response = await axiosInstance.get(`${GAME_MODE_API_BASE}/`, {
        params: { active_only: activeOnly }
      });
      return response.data;
    } catch (error) {
      console.error('게임 모드 목록 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 기본 게임 모드 조회
   */
  getDefaultMode: async () => {
    try {
      const response = await axiosInstance.get(`${GAME_MODE_API_BASE}/default`);
      return response.data;
    } catch (error) {
      console.error('기본 게임 모드 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 이름으로 게임 모드 조회
   */
  getModeByName: async (modeName) => {
    try {
      const response = await axiosInstance.get(`${GAME_MODE_API_BASE}/${modeName}`);
      return response.data;
    } catch (error) {
      console.error('게임 모드 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 게임 모드 설정 검증
   */
  validateModeForRoom: async (modeName, customSettings = {}) => {
    try {
      const response = await axiosInstance.post(`${GAME_MODE_API_BASE}/validate`, {
        mode_name: modeName,
        custom_settings: customSettings
      });
      return response.data;
    } catch (error) {
      console.error('게임 모드 검증 실패:', error);
      throw error;
    }
  },

  /**
   * 게임 모드 통계 조회
   */
  getModeStatistics: async () => {
    try {
      const response = await axiosInstance.get(`${GAME_MODE_API_BASE}/statistics/overview`);
      return response.data;
    } catch (error) {
      console.error('게임 모드 통계 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 기본 게임 모드 초기화 (관리자용)
   */
  initializeModes: async () => {
    try {
      const response = await axiosInstance.post(`${GAME_MODE_API_BASE}/initialize`);
      return response.data;
    } catch (error) {
      console.error('게임 모드 초기화 실패:', error);
      throw error;
    }
  }
};

export default gameModeApi;