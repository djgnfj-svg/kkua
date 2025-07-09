"""
Session management service for handling user sessions
"""

import secrets
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta


class SessionStore:
    """In-memory session store for managing user sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = 24 * 60 * 60  # 24 hours in seconds
    
    def create_session(self, guest_id: int, nickname: str = None) -> str:
        """Create a new session and return session token"""
        session_token = secrets.token_urlsafe(32)
        session_data = {
            'guest_id': guest_id,
            'nickname': nickname,
            'created_at': datetime.utcnow(),
            'last_accessed': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=self.session_timeout)
        }
        
        self.sessions[session_token] = session_data
        return session_token
    
    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data by token"""
        if not session_token or session_token not in self.sessions:
            return None
            
        session_data = self.sessions[session_token]
        
        # Check if session has expired
        if datetime.utcnow() > session_data['expires_at']:
            self.delete_session(session_token)
            return None
        
        # Update last accessed time
        session_data['last_accessed'] = datetime.utcnow()
        return session_data
    
    def update_session(self, session_token: str, **kwargs) -> bool:
        """Update session data"""
        if session_token not in self.sessions:
            return False
            
        session_data = self.sessions[session_token]
        
        # Check if session has expired
        if datetime.utcnow() > session_data['expires_at']:
            self.delete_session(session_token)
            return False
        
        # Update session data
        for key, value in kwargs.items():
            if key in ['guest_id', 'nickname']:
                session_data[key] = value
        
        session_data['last_accessed'] = datetime.utcnow()
        return True
    
    def delete_session(self, session_token: str) -> bool:
        """Delete a session"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            return True
        return False
    
    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = datetime.utcnow()
        expired_tokens = []
        
        for token, session_data in self.sessions.items():
            if current_time > session_data['expires_at']:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.sessions[token]
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        self.cleanup_expired_sessions()
        return len(self.sessions)
    
    def get_sessions_by_guest_id(self, guest_id: int) -> list:
        """Get all sessions for a specific guest"""
        self.cleanup_expired_sessions()
        sessions = []
        
        for token, session_data in self.sessions.items():
            if session_data['guest_id'] == guest_id:
                sessions.append({
                    'token': token,
                    'data': session_data
                })
        
        return sessions


# Global session store instance
session_store = SessionStore()


def get_session_store() -> SessionStore:
    """Get the global session store instance"""
    return session_store