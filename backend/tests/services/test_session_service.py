"""
Tests for SessionService
"""

import pytest
import time
from datetime import datetime, timedelta
from unittest.mock import patch

from services.session_service import SessionStore, get_session_store


class TestSessionStore:
    """Test cases for SessionStore"""

    @pytest.fixture
    def session_store(self):
        """Create a fresh SessionStore instance"""
        return SessionStore()

    def test_create_session(self, session_store):
        """Test creating a session"""
        # Execute
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Verify
        assert token is not None
        assert len(token) > 0
        assert len(session_store.sessions) == 1

        # Check session data
        session_data = session_store.get_session(token)
        assert session_data is not None
        assert session_data["guest_id"] == 1
        assert session_data["nickname"] == "테스트사용자"
        assert "created_at" in session_data
        assert "last_accessed" in session_data
        assert "expires_at" in session_data

    def test_create_session_replaces_existing(self, session_store):
        """Test that creating a session for the same guest replaces existing session"""
        # Create first session
        token1 = session_store.create_session(guest_id=1, nickname="사용자1")

        # Create second session for same guest
        token2 = session_store.create_session(guest_id=1, nickname="사용자1")

        # Verify first session is removed
        assert session_store.get_session(token1) is None
        assert session_store.get_session(token2) is not None
        assert len(session_store.sessions) == 1

    def test_create_multiple_sessions_different_guests(self, session_store):
        """Test creating sessions for different guests"""
        # Create sessions for different guests
        token1 = session_store.create_session(guest_id=1, nickname="사용자1")
        token2 = session_store.create_session(guest_id=2, nickname="사용자2")

        # Verify both sessions exist
        assert session_store.get_session(token1) is not None
        assert session_store.get_session(token2) is not None
        assert len(session_store.sessions) == 2

    def test_get_session_valid(self, session_store):
        """Test getting a valid session"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Get session
        session_data = session_store.get_session(token)

        # Verify
        assert session_data is not None
        assert session_data["guest_id"] == 1
        assert session_data["nickname"] == "테스트사용자"

    def test_get_session_invalid_token(self, session_store):
        """Test getting session with invalid token"""
        # Try to get non-existent session
        session_data = session_store.get_session("invalid_token")

        # Verify
        assert session_data is None

    def test_get_session_expired(self, session_store):
        """Test getting expired session"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Manually expire the session
        session_store.sessions[token]["expires_at"] = datetime.utcnow() - timedelta(
            seconds=1
        )

        # Try to get expired session
        session_data = session_store.get_session(token)

        # Verify session is removed and None is returned
        assert session_data is None
        assert token not in session_store.sessions

    def test_get_session_updates_last_accessed(self, session_store):
        """Test that getting session updates last_accessed time"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Get initial last_accessed time
        initial_time = session_store.sessions[token]["last_accessed"]

        # Wait a bit and get session again
        time.sleep(0.1)
        session_data = session_store.get_session(token)

        # Verify last_accessed was updated
        assert session_data["last_accessed"] > initial_time

    def test_update_session(self, session_store):
        """Test updating session data"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="원래닉네임")

        # Update session
        success = session_store.update_session(token, nickname="새닉네임")

        # Verify
        assert success is True
        session_data = session_store.get_session(token)
        assert session_data["nickname"] == "새닉네임"

    def test_update_session_invalid_token(self, session_store):
        """Test updating session with invalid token"""
        # Try to update non-existent session
        success = session_store.update_session("invalid_token", nickname="새닉네임")

        # Verify
        assert success is False

    def test_update_session_expired(self, session_store):
        """Test updating expired session"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Manually expire the session
        session_store.sessions[token]["expires_at"] = datetime.utcnow() - timedelta(
            seconds=1
        )

        # Try to update expired session
        success = session_store.update_session(token, nickname="새닉네임")

        # Verify session is removed and update fails
        assert success is False
        assert token not in session_store.sessions

    def test_delete_session(self, session_store):
        """Test deleting a session"""
        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Delete session
        success = session_store.delete_session(token)

        # Verify
        assert success is True
        assert token not in session_store.sessions
        assert session_store.get_session(token) is None

    def test_delete_session_invalid_token(self, session_store):
        """Test deleting session with invalid token"""
        # Try to delete non-existent session
        success = session_store.delete_session("invalid_token")

        # Verify
        assert success is False

    def test_cleanup_expired_sessions(self, session_store):
        """Test cleaning up expired sessions"""
        # Create sessions
        token1 = session_store.create_session(guest_id=1, nickname="사용자1")
        token2 = session_store.create_session(guest_id=2, nickname="사용자2")

        # Expire one session
        session_store.sessions[token1]["expires_at"] = datetime.utcnow() - timedelta(
            seconds=1
        )

        # Clean up expired sessions
        session_store.cleanup_expired_sessions()

        # Verify only valid session remains
        assert token1 not in session_store.sessions
        assert token2 in session_store.sessions
        assert len(session_store.sessions) == 1

    def test_get_session_count(self, session_store):
        """Test getting session count"""
        # Initially no sessions
        assert session_store.get_session_count() == 0

        # Create sessions
        session_store.create_session(guest_id=1, nickname="사용자1")
        session_store.create_session(guest_id=2, nickname="사용자2")

        # Check count
        assert session_store.get_session_count() == 2

    def test_get_sessions_by_guest_id(self, session_store):
        """Test getting sessions by guest ID"""
        # Create sessions
        token1 = session_store.create_session(guest_id=1, nickname="사용자1")
        token2 = session_store.create_session(guest_id=2, nickname="사용자2")

        # Get sessions for guest 1
        sessions = session_store.get_sessions_by_guest_id(1)

        # Verify
        assert len(sessions) == 1
        assert sessions[0]["token"] == token1
        assert sessions[0]["data"]["guest_id"] == 1

    def test_get_session_stats(self, session_store):
        """Test getting session statistics"""
        # Create sessions
        session_store.create_session(guest_id=1, nickname="사용자1")
        session_store.create_session(guest_id=2, nickname="사용자2")

        # Get stats
        stats = session_store.get_session_stats()

        # Verify
        assert stats["total_sessions"] == 2
        assert stats["unique_users"] == 2
        assert "last_cleanup" in stats
        assert "cleanup_interval" in stats

    def test_thread_safety(self, session_store):
        """Test thread safety of session operations"""
        import threading
        import time

        results = []

        def create_sessions():
            for i in range(10):
                token = session_store.create_session(guest_id=i, nickname=f"사용자{i}")
                results.append(token)
                time.sleep(0.01)

        # Create multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=create_sessions)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all sessions were created
        assert len(results) == 30
        assert len(set(results)) == 30  # All tokens should be unique

    @patch("services.session_service.secrets.token_urlsafe")
    def test_create_session_with_secure_token(self, mock_token_urlsafe, session_store):
        """Test that create_session uses secure token generation"""
        # Mock the secure token generation
        mock_token_urlsafe.return_value = "mocked_secure_token"

        # Create session
        token = session_store.create_session(guest_id=1, nickname="테스트사용자")

        # Verify secure token was used
        assert "mocked_secure_token" in token
        mock_token_urlsafe.assert_called()


class TestGetSessionStore:
    """Test cases for get_session_store function"""

    def test_get_session_store_singleton(self):
        """Test that get_session_store returns the same instance"""
        store1 = get_session_store()
        store2 = get_session_store()

        assert store1 is store2

    def test_get_session_store_type(self):
        """Test that get_session_store returns SessionStore instance"""
        store = get_session_store()
        assert isinstance(store, SessionStore)
