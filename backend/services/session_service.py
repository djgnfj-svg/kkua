"""
Session management service for handling user sessions
"""

import threading
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from utils.security import SecurityUtils


class SessionStore:
    """Thread-safe in-memory session store for managing user sessions"""

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
        self._lock = threading.RLock()
        self._cleanup_executor = ThreadPoolExecutor(max_workers=1)
        self._last_cleanup = datetime.utcnow()
        self._cleanup_interval = 300

    def create_session(self, guest_id: int, nickname: str = None) -> str:
        """Create a new session and return session token"""
        with self._lock:
            self._cleanup_user_sessions(guest_id)

            session_token = SecurityUtils.generate_secure_token(
                guest_id, nickname or ""
            )
            session_data = {
                "guest_id": guest_id,
                "nickname": nickname,
                "created_at": datetime.utcnow(),
                "last_accessed": datetime.utcnow(),
                "expires_at": datetime.utcnow()
                + timedelta(seconds=self.session_timeout),
            }

            self.sessions[session_token] = session_data
            self._trigger_cleanup_if_needed()
            return session_token

    def _cleanup_user_sessions(self, guest_id: int):
        """동일 사용자의 기존 세션 정리"""
        tokens_to_remove = []
        for token, session_data in self.sessions.items():
            if session_data["guest_id"] == guest_id:
                tokens_to_remove.append(token)

        for token in tokens_to_remove:
            del self.sessions[token]

    def _trigger_cleanup_if_needed(self):
        """필요시 자동 정리 트리거"""
        now = datetime.utcnow()
        if (now - self._last_cleanup).seconds > self._cleanup_interval:
            self._last_cleanup = now
            self._cleanup_executor.submit(self._cleanup_expired_sessions_async)

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        with self._lock:
            if not session_token or session_token not in self.sessions:
                return None

            session_data = self.sessions[session_token]

            if datetime.utcnow() > session_data["expires_at"]:
                del self.sessions[session_token]
                return None

            session_data["last_accessed"] = datetime.utcnow()
            return session_data.copy()

    def update_session(self, session_token: str, **kwargs) -> bool:
        """Update session data"""
        with self._lock:
            if session_token not in self.sessions:
                return False

            session_data = self.sessions[session_token]

            if datetime.utcnow() > session_data["expires_at"]:
                del self.sessions[session_token]
                return False

            for key, value in kwargs.items():
                if key in ["guest_id", "nickname"]:
                    session_data[key] = value

            session_data["last_accessed"] = datetime.utcnow()
            return True

    def delete_session(self, session_token: str) -> bool:
        """Delete a session"""
        with self._lock:
            if session_token in self.sessions:
                del self.sessions[session_token]
                return True
            return False

    def cleanup_expired_sessions(self):
        """Remove expired sessions (public method)"""
        with self._lock:
            self._cleanup_expired_sessions_sync()

    def _cleanup_expired_sessions_sync(self):
        """Remove expired sessions (synchronized)"""
        current_time = datetime.utcnow()
        expired_tokens = []

        for token, session_data in self.sessions.items():
            if current_time > session_data["expires_at"]:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.sessions[token]

    def _cleanup_expired_sessions_async(self):
        """비동기 세션 정리"""
        with self._lock:
            self._cleanup_expired_sessions_sync()

    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        with self._lock:
            self._cleanup_expired_sessions_sync()
            return len(self.sessions)

    def get_sessions_by_guest_id(self, guest_id: int) -> list:
        """Get all sessions for a specific guest"""
        with self._lock:
            self._cleanup_expired_sessions_sync()
            sessions = []

            for token, session_data in self.sessions.items():
                if session_data["guest_id"] == guest_id:
                    sessions.append({"token": token, "data": session_data.copy()})

            return sessions

    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 정보 반환"""
        with self._lock:
            self._cleanup_expired_sessions_sync()
            return {
                "total_sessions": len(self.sessions),
                "unique_users": len(set(s["guest_id"] for s in self.sessions.values())),
                "last_cleanup": self._last_cleanup.isoformat(),
                "cleanup_interval": self._cleanup_interval,
            }


session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get the global session store instance"""
    return session_store
