"""
Redis 클라이언트 관리 및 연결 처리
"""

import redis.asyncio as redis
from redis.exceptions import (
    RedisError, ConnectionError, TimeoutError, 
    ResponseError, BusyLoadingError
)
from app_config import settings
import logging

logger = logging.getLogger(__name__)


class GameRedisClient:
    """게임용 Redis 클라이언트 관리"""
    
    def __init__(self):
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://redis:6379/0')
        self.redis_client = None
        
    async def connect(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Redis 연결 (재시도 로직 포함)"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    max_connections=20
                )
                
                # 연결 테스트
                await self.redis_client.ping()
                logger.info(f"Redis 연결 성공 (시도 {attempt + 1}/{max_retries})")
                return True
                
            except (ConnectionError, TimeoutError) as e:
                last_exception = e
                logger.warning(f"Redis 연결 실패 (시도 {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
            except Exception as e:
                last_exception = e
                logger.error(f"예상치 못한 Redis 연결 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                
        logger.error(f"Redis 연결 실패 - 모든 재시도 소진: {last_exception}")
        raise last_exception or ConnectionError("Redis 연결에 실패했습니다")
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            try:
                await self.redis_client.close()
                logger.info("Redis 연결 해제 완료")
            except Exception as e:
                logger.error(f"Redis 연결 해제 중 오류: {e}")
    
    async def is_connected(self) -> bool:
        """Redis 연결 상태 확인"""
        if not self.redis_client:
            return False
        try:
            await self.redis_client.ping()
            return True
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection check failed: {e}")
            return False
        except (ResponseError, BusyLoadingError) as e:
            logger.warning(f"Redis server error during ping: {e}")
            return False
        except RedisError as e:
            logger.error(f"Redis error during connection check: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error in Redis connection check: {e}", exc_info=True)
            return False
    
    async def ensure_connection(self):
        """연결 상태 확인 후 필요시 재연결"""
        if not await self.is_connected():
            logger.info("Redis 연결이 끊어져 재연결 시도...")
            await self.connect()