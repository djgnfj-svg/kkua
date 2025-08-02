import axiosInstance from './axiosInstance';

const ITEM_API_BASE = '/items';

/**
 * 아이템 관련 API 함수들
 */
export const itemApi = {
  /**
   * 모든 아이템 목록 조회
   */
  getAllItems: async () => {
    try {
      const response = await axiosInstance.get(`${ITEM_API_BASE}/`);
      return response.data;
    } catch (error) {
      console.error('아이템 목록 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 특정 아이템 정보 조회
   */
  getItemById: async (itemId) => {
    try {
      const response = await axiosInstance.get(`${ITEM_API_BASE}/${itemId}`);
      return response.data;
    } catch (error) {
      console.error('아이템 정보 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 내 아이템 인벤토리 조회
   */
  getMyInventory: async () => {
    try {
      const response = await axiosInstance.get(`${ITEM_API_BASE}/inventory/my`);
      return response.data;
    } catch (error) {
      console.error('인벤토리 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 아이템 구매
   */
  purchaseItem: async (itemId, quantity = 1) => {
    try {
      const response = await axiosInstance.post(`${ITEM_API_BASE}/purchase`, {
        item_id: itemId,
        quantity: quantity
      });
      return response.data;
    } catch (error) {
      console.error('아이템 구매 실패:', error);
      throw error;
    }
  },

  /**
   * 게임 중 아이템 사용
   */
  useItemInGame: async (roomId, itemId, targetGuestId = null) => {
    try {
      const response = await axiosInstance.post(`${ITEM_API_BASE}/use/${roomId}`, {
        item_id: itemId,
        target_guest_id: targetGuestId
      });
      return response.data;
    } catch (error) {
      console.error('아이템 사용 실패:', error);
      throw error;
    }
  },

  /**
   * 게임 중 아이템 상태 조회
   */
  getGameItemState: async (roomId) => {
    try {
      const response = await axiosInstance.get(`${ITEM_API_BASE}/game-state/${roomId}`);
      return response.data;
    } catch (error) {
      console.error('게임 아이템 상태 조회 실패:', error);
      throw error;
    }
  },

  /**
   * 기본 아이템 초기화 (관리자용)
   */
  initializeItems: async () => {
    try {
      const response = await axiosInstance.post(`${ITEM_API_BASE}/initialize`);
      return response.data;
    } catch (error) {
      console.error('아이템 초기화 실패:', error);
      throw error;
    }
  }
};

export default itemApi;