"""
Session management service - Redis-based persistent sessions
"""

from services.redis_session_service import RedisSessionStore, get_redis_session_store

# 하위 호환성을 위한 래퍼 클래스
class SessionStore:
    """Wrapper for Redis-based session store to maintain backward compatibility"""
    
    def __init__(self):
        self._redis_store = get_redis_session_store()
    
    def create_session(self, guest_id: int, nickname: str = None) -> str:
        return self._redis_store.create_session(guest_id, nickname)
    
    def get_session(self, session_token: str):
        return self._redis_store.get_session(session_token)
    
    def update_session(self, session_token: str, **kwargs) -> bool:
        return self._redis_store.update_session(session_token, **kwargs)
    
    def delete_session(self, session_token: str) -> bool:
        return self._redis_store.delete_session(session_token)
    
    def cleanup_expired_sessions(self) -> int:
        return self._redis_store.cleanup_expired_sessions()
    
    def get_session_count(self) -> int:
        return self._redis_store.get_session_count()

# Global session store instance - now Redis-based
_session_store = None

def get_session_store() -> SessionStore:
    """Get Redis-based session store singleton"""
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store

def reset_session_store():
    """Reset session store instance (for testing)"""
    global _session_store
    _session_store = None