"""
캐싱 서비스
Redis 기반 지능형 캐싱, 성능 최적화, 메모리 관리
"""

import json
import logging
import hashlib
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from database import get_redis
import asyncio

logger = logging.getLogger(__name__)


class CacheStrategy(str, Enum):
    """캐시 전략"""
    LRU = "lru"                        # Least Recently Used
    LFU = "lfu"                        # Least Frequently Used
    TTL = "ttl"                        # Time To Live
    WRITE_THROUGH = "write_through"    # 즉시 DB 반영
    WRITE_BEHIND = "write_behind"      # 지연 DB 반영
    READ_THROUGH = "read_through"      # Cache Miss 시 DB 조회


class CacheLevel(str, Enum):
    """캐시 레벨"""
    L1_MEMORY = "l1_memory"            # 메모리 캐시 (가장 빠름)
    L2_REDIS = "l2_redis"              # Redis 캐시
    L3_DATABASE = "l3_database"        # 데이터베이스


@dataclass
class CacheConfig:
    """캐시 설정"""
    ttl: int = 3600                    # TTL (초)
    max_size: int = 10000              # 최대 캐시 항목 수
    strategy: CacheStrategy = CacheStrategy.LRU
    compression: bool = False          # 압축 사용 여부
    serializer: str = "json"           # json, pickle, msgpack
    namespace: str = "default"         # 네임스페이스
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CacheStats:
    """캐시 통계"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    evictions: int = 0
    memory_usage: int = 0
    
    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total) if total > 0 else 0.0
    
    @property
    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate
        }


class CacheService:
    """지능형 캐싱 서비스"""
    
    def __init__(self):
        self.redis_client = get_redis()
        
        # 다단계 캐시
        self.l1_cache: Dict[str, Any] = {}  # 메모리 캐시
        self.l1_access_times: Dict[str, datetime] = {}
        self.l1_access_counts: Dict[str, int] = {}
        self.l1_max_size = 1000
        
        # 캐시 통계
        self.stats = CacheStats()
        
        # 캐시 키 접두사
        self.prefixes = {
            "word_validation": "word_val:",
            "game_state": "game_state:",
            "user_inventory": "user_inv:",
            "game_stats": "game_stats:",
            "leaderboard": "leaderboard:",
            "word_hints": "word_hints:",
            "session_data": "session:",
            "room_metadata": "room_meta:",
            "user_profile": "user_profile:",
            "daily_stats": "daily_stats:"
        }
        
        # 비동기 정리 작업
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """정리 작업 시작"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
    
    async def _periodic_cleanup(self):
        """주기적 캐시 정리"""
        while True:
            try:
                await asyncio.sleep(300)  # 5분마다 실행
                await self._cleanup_expired_l1()
                await self._enforce_l1_size_limit()
                logger.debug("캐시 정리 완료")
            except Exception as e:
                logger.error(f"캐시 정리 중 오류: {e}")
    
    def _make_key(self, category: str, key: str) -> str:
        """캐시 키 생성"""
        prefix = self.prefixes.get(category, f"{category}:")
        return f"{prefix}{key}"
    
    def _hash_key(self, data: Any) -> str:
        """복합 키를 해시로 변환"""
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode()).hexdigest()[:16]
    
    # === L1 캐시 (메모리) 관리 ===
    
    def _get_l1(self, key: str) -> Optional[Any]:
        """L1 캐시에서 조회"""
        if key in self.l1_cache:
            # 액세스 통계 업데이트
            self.l1_access_times[key] = datetime.now(timezone.utc)
            self.l1_access_counts[key] = self.l1_access_counts.get(key, 0) + 1
            self.stats.hits += 1
            return self.l1_cache[key]
        
        self.stats.misses += 1
        return None
    
    def _set_l1(self, key: str, value: Any, ttl: Optional[int] = None):
        """L1 캐시에 저장"""
        # 크기 제한 확인
        if len(self.l1_cache) >= self.l1_max_size:
            self._evict_l1_item()
        
        self.l1_cache[key] = {
            "data": value,
            "created_at": datetime.now(timezone.utc),
            "ttl": ttl,
            "expires_at": datetime.now(timezone.utc) + timedelta(seconds=ttl) if ttl else None
        }
        
        self.l1_access_times[key] = datetime.now(timezone.utc)
        self.l1_access_counts[key] = 1
        self.stats.sets += 1
    
    def _evict_l1_item(self):
        """L1 캐시 항목 퇴출 (LRU 전략)"""
        if not self.l1_cache:
            return
        
        # 가장 오래 전에 액세스된 항목 찾기
        oldest_key = min(self.l1_access_times.keys(), 
                        key=lambda k: self.l1_access_times[k])
        
        self._delete_l1(oldest_key)
        self.stats.evictions += 1
    
    def _delete_l1(self, key: str):
        """L1 캐시 항목 삭제"""
        self.l1_cache.pop(key, None)
        self.l1_access_times.pop(key, None)
        self.l1_access_counts.pop(key, None)
        self.stats.deletes += 1
    
    async def _cleanup_expired_l1(self):
        """만료된 L1 캐시 항목 정리"""
        now = datetime.now(timezone.utc)
        expired_keys = []
        
        for key, cached_item in self.l1_cache.items():
            if cached_item["expires_at"] and now >= cached_item["expires_at"]:
                expired_keys.append(key)
        
        for key in expired_keys:
            self._delete_l1(key)
    
    async def _enforce_l1_size_limit(self):
        """L1 캐시 크기 제한 적용"""
        while len(self.l1_cache) > self.l1_max_size:
            self._evict_l1_item()
    
    # === L2 캐시 (Redis) 관리 ===
    
    async def _get_l2(self, key: str) -> Optional[Any]:
        """L2 캐시에서 조회"""
        try:
            data = self.redis_client.get(key)
            if data:
                self.stats.hits += 1
                return json.loads(data)
            
            self.stats.misses += 1
            return None
            
        except Exception as e:
            logger.error(f"L2 캐시 조회 중 오류: {e}")
            self.stats.misses += 1
            return None
    
    async def _set_l2(self, key: str, value: Any, ttl: int):
        """L2 캐시에 저장"""
        try:
            data = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, data)
            self.stats.sets += 1
            
        except Exception as e:
            logger.error(f"L2 캐시 저장 중 오류: {e}")
    
    # === 공통 캐시 인터페이스 ===
    
    async def get(self, category: str, key: str, default: Any = None) -> Any:
        """캐시에서 값 조회 (다단계)"""
        cache_key = self._make_key(category, key)
        
        # L1 캐시 확인
        l1_result = self._get_l1(cache_key)
        if l1_result is not None:
            return l1_result["data"]
        
        # L2 캐시 확인
        l2_result = await self._get_l2(cache_key)
        if l2_result is not None:
            # L1에도 저장
            self._set_l1(cache_key, l2_result, ttl=300)  # L1은 5분 TTL
            return l2_result
        
        return default
    
    async def set(self, category: str, key: str, value: Any, ttl: int = 3600):
        """캐시에 값 저장 (다단계)"""
        cache_key = self._make_key(category, key)
        
        # L1 캐시 저장
        l1_ttl = min(ttl, 300)  # L1은 최대 5분
        self._set_l1(cache_key, value, l1_ttl)
        
        # L2 캐시 저장
        await self._set_l2(cache_key, value, ttl)
    
    async def delete(self, category: str, key: str):
        """캐시에서 삭제"""
        cache_key = self._make_key(category, key)
        
        # L1에서 삭제
        self._delete_l1(cache_key)
        
        # L2에서 삭제
        try:
            self.redis_client.delete(cache_key)
            self.stats.deletes += 1
        except Exception as e:
            logger.error(f"L2 캐시 삭제 중 오류: {e}")
    
    async def exists(self, category: str, key: str) -> bool:
        """캐시에 키가 존재하는지 확인"""
        cache_key = self._make_key(category, key)
        
        # L1 확인
        if cache_key in self.l1_cache:
            return True
        
        # L2 확인
        try:
            return bool(self.redis_client.exists(cache_key))
        except Exception as e:
            logger.error(f"캐시 존재 여부 확인 중 오류: {e}")
            return False
    
    async def invalidate_pattern(self, category: str, pattern: str = "*"):
        """패턴 기반 캐시 무효화"""
        cache_pattern = self._make_key(category, pattern)
        
        # L1 캐시에서 패턴 매칭 삭제
        import fnmatch
        keys_to_delete = []
        for key in self.l1_cache.keys():
            if fnmatch.fnmatch(key, cache_pattern):
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            self._delete_l1(key)
        
        # L2 캐시에서 패턴 매칭 삭제
        try:
            keys = self.redis_client.keys(cache_pattern)
            if keys:
                self.redis_client.delete(*keys)
                self.stats.deletes += len(keys)
        except Exception as e:
            logger.error(f"패턴 기반 캐시 삭제 중 오류: {e}")
    
    # === 특화 캐싱 기능 ===
    
    async def cache_word_validation(self, word: str, result: Dict[str, Any], ttl: int = 3600):
        """단어 검증 결과 캐싱"""
        await self.set("word_validation", word, result, ttl)
    
    async def get_cached_word_validation(self, word: str) -> Optional[Dict[str, Any]]:
        """캐싱된 단어 검증 결과 조회"""
        return await self.get("word_validation", word)
    
    async def cache_user_inventory(self, user_id: int, inventory: List[Dict[str, Any]], ttl: int = 1800):
        """사용자 인벤토리 캐싱"""
        await self.set("user_inventory", str(user_id), inventory, ttl)
    
    async def get_cached_user_inventory(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
        """캐싱된 사용자 인벤토리 조회"""
        return await self.get("user_inventory", str(user_id))
    
    async def cache_game_stats(self, room_id: str, stats: Dict[str, Any], ttl: int = 600):
        """게임 통계 캐싱"""
        await self.set("game_stats", room_id, stats, ttl)
    
    async def get_cached_game_stats(self, room_id: str) -> Optional[Dict[str, Any]]:
        """캐싱된 게임 통계 조회"""
        return await self.get("game_stats", room_id)
    
    async def cache_leaderboard(self, board_type: str, data: List[Dict[str, Any]], ttl: int = 300):
        """리더보드 캐싱"""
        await self.set("leaderboard", board_type, data, ttl)
    
    async def get_cached_leaderboard(self, board_type: str) -> Optional[List[Dict[str, Any]]]:
        """캐싱된 리더보드 조회"""
        return await self.get("leaderboard", board_type)
    
    async def cache_word_hints(self, last_char: str, hints: List[str], ttl: int = 1800):
        """단어 힌트 캐싱"""
        await self.set("word_hints", last_char, hints, ttl)
    
    async def get_cached_word_hints(self, last_char: str) -> Optional[List[str]]:
        """캐싱된 단어 힌트 조회"""
        return await self.get("word_hints", last_char)
    
    # === 메모이제이션 데코레이터 ===
    
    def memoize(self, category: str, ttl: int = 3600, key_func: Optional[Callable] = None):
        """메모이제이션 데코레이터"""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # 키 생성
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    key_parts = [str(arg) for arg in args]
                    key_parts.extend([f"{k}={v}" for k, v in kwargs.items()])
                    cache_key = self._hash_key("|".join(key_parts))
                
                # 캐시에서 조회
                cached_result = await self.get(category, cache_key)
                if cached_result is not None:
                    return cached_result
                
                # 함수 실행 및 결과 캐싱
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                await self.set(category, cache_key, result, ttl)
                
                return result
            
            return wrapper
        return decorator
    
    # === 캐시 워밍업 ===
    
    async def warmup_game_data(self):
        """게임 데이터 워밍업"""
        try:
            logger.info("캐시 워밍업 시작")
            
            # 자주 사용되는 단어들 사전 로드
            from services.word_validator import get_word_validator
            word_validator = get_word_validator()
            await word_validator.preload_common_words(1000)
            
            # 게임 모드 정보 캐싱
            from services.game_mode_service import get_game_mode_service
            game_mode_service = get_game_mode_service()
            modes = game_mode_service.get_available_modes()
            await self.set("game_modes", "all", modes, ttl=86400)  # 24시간
            
            logger.info("캐시 워밍업 완료")
            
        except Exception as e:
            logger.error(f"캐시 워밍업 중 오류: {e}")
    
    # === 성능 모니터링 ===
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """캐시 성능 지표"""
        l1_size = len(self.l1_cache)
        l1_memory = sum(len(str(item)) for item in self.l1_cache.values())
        
        try:
            # Redis 정보
            redis_info = self.redis_client.info('memory')
            redis_memory = redis_info.get('used_memory', 0)
        except Exception:
            redis_memory = 0
        
        return {
            "cache_stats": self.stats.to_dict(),
            "l1_cache": {
                "size": l1_size,
                "max_size": self.l1_max_size,
                "memory_usage": l1_memory,
                "utilization": l1_size / self.l1_max_size
            },
            "l2_cache": {
                "memory_usage": redis_memory
            },
            "performance": {
                "hit_rate": self.stats.hit_rate,
                "total_operations": self.stats.hits + self.stats.misses + self.stats.sets + self.stats.deletes
            }
        }
    
    async def reset_stats(self):
        """통계 초기화"""
        self.stats = CacheStats()
    
    async def clear_all_cache(self):
        """모든 캐시 클리어 (개발/테스트용)"""
        # L1 캐시 클리어
        self.l1_cache.clear()
        self.l1_access_times.clear()
        self.l1_access_counts.clear()
        
        # L2 캐시 클리어 (주의: 모든 Redis 키 삭제)
        logger.warning("전체 캐시를 클리어합니다")
        
    def __del__(self):
        """소멸자"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()


# 전역 캐시 서비스 인스턴스
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """캐시 서비스 의존성"""
    return cache_service