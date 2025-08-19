"""
Redis-based session management service for persistent sessions
"""

import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from utils.security import SecurityUtils
from app_config import settings

logger = logging.getLogger(__name__)


class RedisSessionStore:
    """Redis-based session store for persistent session management"""

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize Redis session store"""
        if redis_client is None:
            # Redis 연결 설정
            redis_url = settings.redis_url
            if redis_url.startswith('redis://'):
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # 기본 연결 설정
                self.redis_client = redis.Redis(
                    host='redis', 
                    port=6379, 
                    db=1,  # 게임 데이터와 분리를 위해 다른 DB 사용
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True
                )
        else:
            self.redis_client = redis_client
            
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self.session_prefix = "session:"
        self.user_sessions_prefix = "user_sessions:"
        
        # Redis 연결 테스트
        try:
            self.redis_client.ping()
            logger.info("Redis 세션 스토어 초기화 완료")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            raise

    def create_session(self, guest_id: int, nickname: str = None) -> str:
        """Create a new session and return session token"""
        try:
            # 기존 사용자 세션 정리
            self._cleanup_user_sessions(guest_id)

            session_token = SecurityUtils.generate_secure_token(
                guest_id, nickname or ""
            )
            
            now = datetime.utcnow()
            session_data = {
                "guest_id": guest_id,
                "nickname": nickname,
                "created_at": now.isoformat(),
                "last_accessed": now.isoformat(),
                "expires_at": (now + timedelta(seconds=self.session_timeout)).isoformat(),
            }

            # Redis에 세션 저장 (자동 만료 설정)
            session_key = f"{self.session_prefix}{session_token}"
            self.redis_client.setex(
                session_key, 
                self.session_timeout,
                json.dumps(session_data, ensure_ascii=False)
            )
            
            # 사용자별 세션 목록 업데이트 (정리용)
            user_sessions_key = f"{self.user_sessions_prefix}{guest_id}"
            self.redis_client.sadd(user_sessions_key, session_token)
            self.redis_client.expire(user_sessions_key, self.session_timeout)

            logger.info(f"새 세션 생성: guest_id={guest_id}, token={session_token[:8]}...")
            return session_token
            
        except Exception as e:
            logger.error(f"세션 생성 실패: {e}")
            raise

    def _cleanup_user_sessions(self, guest_id: int):
        """동일 사용자의 기존 세션 정리"""
        try:
            user_sessions_key = f"{self.user_sessions_prefix}{guest_id}"
            existing_tokens = self.redis_client.smembers(user_sessions_key)
            
            if existing_tokens:
                # 기존 세션들 삭제
                pipeline = self.redis_client.pipeline()
                for token in existing_tokens:
                    session_key = f"{self.session_prefix}{token}"
                    pipeline.delete(session_key)
                pipeline.delete(user_sessions_key)
                pipeline.execute()
                
                logger.info(f"사용자 {guest_id}의 기존 세션 {len(existing_tokens)}개 정리 완료")
                
        except Exception as e:
            logger.warning(f"사용자 세션 정리 실패: {e}")

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        if not session_token:
            return None
            
        try:
            session_key = f"{self.session_prefix}{session_token}"
            session_data_str = self.redis_client.get(session_key)
            
            if not session_data_str:
                return None

            session_data = json.loads(session_data_str)
            
            # 만료 시간 확인
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                self.delete_session(session_token)
                return None

            # 마지막 접근 시간 업데이트
            session_data["last_accessed"] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                session_key, 
                self.session_timeout,
                json.dumps(session_data, ensure_ascii=False)
            )
            
            # guest_id를 정수로 변환 (JSON 직렬화 후 문자열이 됨)
            session_data["guest_id"] = int(session_data["guest_id"])
            
            return session_data
            
        except Exception as e:
            logger.error(f"세션 조회 실패 (token={session_token[:8]}...): {e}")
            return None

    def update_session(self, session_token: str, **kwargs) -> bool:
        """Update session data"""
        try:
            session_key = f"{self.session_prefix}{session_token}"
            session_data_str = self.redis_client.get(session_key)
            
            if not session_data_str:
                return False

            session_data = json.loads(session_data_str)
            
            # 만료 시간 확인
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            if datetime.utcnow() > expires_at:
                self.delete_session(session_token)
                return False

            # 허용된 필드만 업데이트
            for key, value in kwargs.items():
                if key in ["guest_id", "nickname"]:
                    session_data[key] = value

            session_data["last_accessed"] = datetime.utcnow().isoformat()
            
            # Redis에 업데이트된 데이터 저장
            self.redis_client.setex(
                session_key, 
                self.session_timeout,
                json.dumps(session_data, ensure_ascii=False)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"세션 업데이트 실패: {e}")
            return False

    def delete_session(self, session_token: str) -> bool:
        """Delete a session"""
        try:
            session_key = f"{self.session_prefix}{session_token}"
            
            # 세션 데이터 먼저 가져오기 (사용자 세션 목록에서 제거하기 위해)
            session_data_str = self.redis_client.get(session_key)
            if session_data_str:
                session_data = json.loads(session_data_str)
                guest_id = int(session_data["guest_id"])
                
                # 사용자 세션 목록에서 제거
                user_sessions_key = f"{self.user_sessions_prefix}{guest_id}"
                self.redis_client.srem(user_sessions_key, session_token)
            
            # 세션 삭제
            result = self.redis_client.delete(session_key)
            
            if result:
                logger.info(f"세션 삭제 완료: token={session_token[:8]}...")
            
            return result > 0
            
        except Exception as e:
            logger.error(f"세션 삭제 실패: {e}")
            return False

    def cleanup_expired_sessions(self) -> int:
        """정리할 만료된 세션 수 반환 (Redis TTL이 자동 관리하므로 참고용)"""
        try:
            # Redis TTL이 자동으로 만료된 키를 제거하므로
            # 여기서는 수동으로 정리할 필요 없음
            pattern = f"{self.session_prefix}*"
            active_sessions = len(list(self.redis_client.scan_iter(match=pattern)))
            logger.info(f"현재 활성 세션 수: {active_sessions}")
            return 0  # Redis가 자동 정리하므로 0 반환
            
        except Exception as e:
            logger.error(f"세션 정리 상태 확인 실패: {e}")
            return 0

    def get_session_count(self) -> int:
        """현재 활성 세션 수 반환"""
        try:
            pattern = f"{self.session_prefix}*"
            return len(list(self.redis_client.scan_iter(match=pattern)))
        except Exception as e:
            logger.error(f"세션 수 확인 실패: {e}")
            return 0

    def health_check(self) -> bool:
        """Redis 연결 상태 확인"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis 세션 스토어 상태 확인 실패: {e}")
            return False


# 전역 Redis 세션 스토어 인스턴스
_redis_session_store = None


def get_redis_session_store() -> RedisSessionStore:
    """Get Redis session store singleton"""
    global _redis_session_store
    if _redis_session_store is None:
        _redis_session_store = RedisSessionStore()
    return _redis_session_store


def reset_redis_session_store():
    """Reset session store instance (테스트용)"""
    global _redis_session_store
    _redis_session_store = None