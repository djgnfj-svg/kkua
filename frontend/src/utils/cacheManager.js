// 캐시 관리 유틸리티

class CacheManager {
  constructor() {
    this.cache = new Map();
    this.timestamps = new Map();
    this.defaultTTL = 5 * 60 * 1000; // 5분 기본 TTL
  }

  // 캐시 설정
  set(key, data, ttl = this.defaultTTL) {
    this.cache.set(key, data);
    this.timestamps.set(key, Date.now() + ttl);
  }

  // 캐시 조회
  get(key) {
    const timestamp = this.timestamps.get(key);
    
    if (!timestamp || Date.now() > timestamp) {
      // TTL 만료된 경우 삭제
      this.delete(key);
      return null;
    }
    
    return this.cache.get(key);
  }

  // 캐시 삭제
  delete(key) {
    this.cache.delete(key);
    this.timestamps.delete(key);
  }

  // 패턴으로 캐시 삭제 (예: room_* 로 시작하는 모든 캐시)
  deletePattern(pattern) {
    const regex = new RegExp(pattern);
    
    for (const key of this.cache.keys()) {
      if (regex.test(key)) {
        this.delete(key);
      }
    }
  }

  // 전체 캐시 클리어
  clear() {
    this.cache.clear();
    this.timestamps.clear();
  }

  // 캐시 크기 제한 (메모리 관리)
  cleanup(maxSize = 100) {
    if (this.cache.size <= maxSize) return;

    // 가장 오래된 항목부터 삭제
    const entries = Array.from(this.timestamps.entries())
      .sort((a, b) => a[1] - b[1])
      .slice(0, this.cache.size - maxSize);

    entries.forEach(([key]) => this.delete(key));
  }
}

// 싱글톤 인스턴스
const cacheManager = new CacheManager();

// 게임 관련 캐시 키 상수
export const CACHE_KEYS = {
  ROOM_LIST: 'rooms_list',
  ROOM_INFO: (roomId) => `room_${roomId}`,
  ROOM_PARTICIPANTS: (roomId) => `room_${roomId}_participants`,
  USER_PROFILE: 'user_profile',
  GAME_RESULT: (roomId) => `game_result_${roomId}`,
};

// 캐시 무효화 전략
export const invalidateCache = {
  // 방 관련 캐시 무효화
  room: (roomId) => {
    cacheManager.delete(CACHE_KEYS.ROOM_LIST);
    cacheManager.delete(CACHE_KEYS.ROOM_INFO(roomId));
    cacheManager.delete(CACHE_KEYS.ROOM_PARTICIPANTS(roomId));
  },

  // 사용자 관련 캐시 무효화
  user: () => {
    cacheManager.delete(CACHE_KEYS.USER_PROFILE);
    cacheManager.deletePattern('^room_.*'); // 모든 방 관련 캐시
  },

  // 전체 무효화 (로그아웃 시)
  all: () => {
    cacheManager.clear();
    // localStorage도 정리
    try {
      localStorage.removeItem('auth_state');
      localStorage.removeItem('guest-storage');
    } catch (error) {
      console.warn('localStorage 정리 실패:', error);
    }
  }
};

export default cacheManager;