"""
Tests for AuthService
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Response, Request
from fastapi.testclient import TestClient
import uuid

from services.auth_service import AuthService
from models.guest_model import Guest
from repositories.guest_repository import GuestRepository
from services.session_service import SessionStore


class TestAuthService:
    """Test cases for AuthService"""
    
    @pytest.fixture
    def mock_guest_repo(self):
        """Mock GuestRepository"""
        return Mock(spec=GuestRepository)
    
    @pytest.fixture
    def mock_session_store(self):
        """Mock SessionStore"""
        return Mock(spec=SessionStore)
    
    @pytest.fixture
    def auth_service(self, mock_guest_repo, mock_session_store):
        """Create AuthService instance with mocks"""
        with patch('services.auth_service.get_session_store', return_value=mock_session_store):
            return AuthService(mock_guest_repo)
    
    @pytest.fixture
    def sample_guest(self):
        """Create a sample guest for testing"""
        return Guest(
            guest_id=1,
            uuid=uuid.uuid4(),
            nickname="테스트사용자",
            device_info="test_device",
            created_at=None,
            last_login=None
        )
    
    def test_login_with_new_nickname(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test login with new nickname"""
        # Setup
        mock_guest_repo.find_by_nickname.return_value = None
        mock_guest_repo.create.return_value = sample_guest
        mock_session_store.create_session.return_value = "test_session_token"
        
        # Execute
        guest, session_token = auth_service.login("새사용자", "test_device")
        
        # Verify
        assert guest == sample_guest
        assert session_token == "test_session_token"
        mock_guest_repo.find_by_nickname.assert_called_once_with("새사용자")
        mock_guest_repo.create.assert_called_once()
        mock_session_store.create_session.assert_called_once_with(1, "테스트사용자")
    
    def test_login_with_existing_nickname(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test login with existing nickname"""
        # Setup
        mock_guest_repo.find_by_nickname.return_value = sample_guest
        mock_guest_repo.update_last_login.return_value = sample_guest
        mock_session_store.create_session.return_value = "test_session_token"
        
        # Execute
        guest, session_token = auth_service.login("테스트사용자", "test_device")
        
        # Verify
        assert guest == sample_guest
        assert session_token == "test_session_token"
        mock_guest_repo.find_by_nickname.assert_called_once_with("테스트사용자")
        mock_guest_repo.update_last_login.assert_called_once_with(sample_guest, "test_device")
        mock_session_store.create_session.assert_called_once_with(1, "테스트사용자")
    
    def test_login_anonymous(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test anonymous login"""
        # Setup
        mock_guest_repo.create.return_value = sample_guest
        mock_session_store.create_session.return_value = "test_session_token"
        
        # Execute
        guest, session_token = auth_service.login(None, "test_device")
        
        # Verify
        assert guest == sample_guest
        assert session_token == "test_session_token"
        mock_guest_repo.create.assert_called_once()
        mock_session_store.create_session.assert_called_once_with(1, "테스트사용자")
    
    def test_check_auth_status_authenticated(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test check_auth_status with valid session"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "valid_token"}
        mock_session_store.get_session.return_value = {"guest_id": 1}
        mock_guest_repo.find_by_id.return_value = sample_guest
        mock_guest_repo.check_active_game.return_value = (True, "room_123")
        
        # Execute
        result = auth_service.check_auth_status(mock_request)
        
        # Verify
        assert result["authenticated"] is True
        assert result["guest"]["guest_id"] == 1
        assert result["guest"]["nickname"] == "테스트사용자"
        assert result["room_id"] == "room_123"
        mock_session_store.get_session.assert_called_once_with("valid_token")
        mock_guest_repo.find_by_id.assert_called_once_with(1)
        mock_guest_repo.check_active_game.assert_called_once_with(1)
    
    def test_check_auth_status_no_session(self, auth_service):
        """Test check_auth_status without session"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}
        
        # Execute
        result = auth_service.check_auth_status(mock_request)
        
        # Verify
        assert result["authenticated"] is False
        assert result["guest"] is None
    
    def test_check_auth_status_invalid_session(self, auth_service, mock_session_store):
        """Test check_auth_status with invalid session"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "invalid_token"}
        mock_session_store.get_session.return_value = None
        
        # Execute
        result = auth_service.check_auth_status(mock_request)
        
        # Verify
        assert result["authenticated"] is False
        assert result["guest"] is None
        mock_session_store.get_session.assert_called_once_with("invalid_token")
    
    def test_logout(self, auth_service, mock_session_store):
        """Test logout"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "valid_token"}
        mock_response = Mock(spec=Response)
        
        # Execute
        result = auth_service.logout(mock_request, mock_response)
        
        # Verify
        assert result["message"] == "로그아웃되었습니다"
        mock_session_store.delete_session.assert_called_once_with("valid_token")
        mock_response.delete_cookie.assert_any_call("session_token")
        mock_response.delete_cookie.assert_any_call("csrf_token")
    
    def test_update_profile_success(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test successful profile update"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "valid_token"}
        mock_session_store.get_session.return_value = {"guest_id": 1}
        mock_guest_repo.find_by_id.return_value = sample_guest
        mock_guest_repo.find_by_nickname.return_value = None  # Nickname available
        mock_guest_repo.update_nickname.return_value = sample_guest
        
        # Execute
        result = auth_service.update_profile(mock_request, "새닉네임")
        
        # Verify
        assert result == sample_guest
        mock_session_store.get_session.assert_called_once_with("valid_token")
        mock_guest_repo.find_by_id.assert_called_once_with(1)
        mock_guest_repo.find_by_nickname.assert_called_once_with("새닉네임")
        mock_guest_repo.update_nickname.assert_called_once_with(sample_guest, "새닉네임")
        mock_session_store.update_session.assert_called_once_with("valid_token", nickname="새닉네임")
    
    def test_update_profile_no_session(self, auth_service):
        """Test profile update without session"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {}
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            auth_service.update_profile(mock_request, "새닉네임")
        
        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)
    
    def test_update_profile_invalid_session(self, auth_service, mock_session_store):
        """Test profile update with invalid session"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "invalid_token"}
        mock_session_store.get_session.return_value = None
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            auth_service.update_profile(mock_request, "새닉네임")
        
        assert exc_info.value.status_code == 401
        assert "Invalid session" in str(exc_info.value.detail)
    
    def test_update_profile_nickname_taken(self, auth_service, mock_guest_repo, mock_session_store, sample_guest):
        """Test profile update with taken nickname"""
        # Setup
        mock_request = Mock(spec=Request)
        mock_request.cookies = {"session_token": "valid_token"}
        mock_session_store.get_session.return_value = {"guest_id": 1}
        mock_guest_repo.find_by_id.return_value = sample_guest
        
        # Create another guest with the desired nickname
        other_guest = Guest(
            guest_id=2,
            uuid=uuid.uuid4(),
            nickname="새닉네임",
            device_info="other_device",
            created_at=None,
            last_login=None
        )
        mock_guest_repo.find_by_nickname.return_value = other_guest
        
        # Execute & Verify
        with pytest.raises(HTTPException) as exc_info:
            auth_service.update_profile(mock_request, "새닉네임")
        
        assert exc_info.value.status_code == 400
        assert "닉네임이 이미 사용 중입니다" in str(exc_info.value.detail)
    
    def test_set_auth_cookies(self, auth_service):
        """Test setting authentication cookies"""
        # Setup
        mock_response = Mock(spec=Response)
        
        with patch('services.auth_service.CSRFTokenManager.get_csrf_token_for_response', return_value="csrf_token"):
            # Execute
            csrf_token = auth_service.set_auth_cookies(mock_response, "session_token")
            
            # Verify
            assert csrf_token == "csrf_token"
            mock_response.set_cookie.assert_called_once()
    
    def test_get_session_stats(self, auth_service, mock_session_store):
        """Test getting session statistics"""
        # Setup
        mock_session_store.cleanup_expired_sessions.return_value = None
        mock_session_store.get_session_count.return_value = 5
        mock_session_store.sessions = {
            "token1": {"guest_id": 1},
            "token2": {"guest_id": 2},
            "token3": {"guest_id": 1}  # Same guest, multiple sessions
        }
        
        # Execute
        stats = auth_service.get_session_stats()
        
        # Verify
        assert stats["active_sessions"] == 5
        assert stats["total_guests"] == 2  # Unique guests
        mock_session_store.cleanup_expired_sessions.assert_called_once()