"""
친구 관계 서비스 테스트
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.friendship_service import FriendshipService
from models.friendship_model import Friendship, FriendshipStatus
from models.guest_model import Guest
from schemas.friendship_schema import FriendRequestCreate


@pytest.fixture
def mock_db():
    """Mock 데이터베이스 세션"""
    return Mock(spec=Session)


@pytest.fixture
def sample_users():
    """테스트용 사용자들"""
    user1 = Guest(
        guest_id=1,
        uuid="test-uuid-1",
        nickname="사용자1",
        session_token="token1"
    )
    user2 = Guest(
        guest_id=2,
        uuid="test-uuid-2",
        nickname="사용자2",
        session_token="token2"
    )
    user3 = Guest(
        guest_id=3,
        uuid="test-uuid-3",
        nickname="사용자3",
        session_token="token3"
    )
    return user1, user2, user3


@pytest.fixture
def friendship_service(mock_db):
    """친구 관계 서비스 인스턴스"""
    return FriendshipService(mock_db)


class TestFriendshipService:
    """친구 관계 서비스 테스트"""
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_send_friend_request_success(self, mock_guest_repo_class, mock_friendship_repo_class, 
                                       friendship_service, sample_users):
        """친구 요청 성공 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        # 서비스 인스턴스 재생성 (mocked repositories 사용)
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        mock_guest_repo.find_by_id.return_value = user2
        mock_friendship_repo.can_send_friend_request.return_value = (True, None)
        mock_friendship_repo.create_friend_request.return_value = Friendship(
            friendship_id=1,
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        # 테스트 실행
        request_data = FriendRequestCreate(target_user_id=user2.guest_id)
        result = service.send_friend_request(user1, request_data)
        
        # 검증
        assert result["success"] is True
        assert result["message"] == "친구 요청을 보냈습니다"
        mock_guest_repo.find_by_id.assert_called_once_with(user2.guest_id)
        mock_friendship_repo.can_send_friend_request.assert_called_once_with(
            user1.guest_id, user2.guest_id
        )
        mock_friendship_repo.create_friend_request.assert_called_once()
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_send_friend_request_user_not_found(self, mock_guest_repo_class, mock_friendship_repo_class,
                                               friendship_service, sample_users):
        """존재하지 않는 사용자에게 친구 요청 테스트"""
        user1, _, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정 - 사용자 없음
        mock_guest_repo.find_by_id.return_value = None
        
        # 테스트 실행 및 검증
        request_data = FriendRequestCreate(target_user_id=999)
        with pytest.raises(HTTPException) as exc_info:
            service.send_friend_request(user1, request_data)
        
        assert exc_info.value.status_code == 404
        assert "대상 사용자를 찾을 수 없습니다" in str(exc_info.value.detail)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_send_friend_request_cannot_send(self, mock_guest_repo_class, mock_friendship_repo_class,
                                           friendship_service, sample_users):
        """친구 요청을 보낼 수 없는 경우 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        mock_guest_repo.find_by_id.return_value = user2
        mock_friendship_repo.can_send_friend_request.return_value = (False, "이미 친구 요청을 보냈습니다")
        
        # 테스트 실행 및 검증
        request_data = FriendRequestCreate(target_user_id=user2.guest_id)
        with pytest.raises(HTTPException) as exc_info:
            service.send_friend_request(user1, request_data)
        
        assert exc_info.value.status_code == 400
        assert "이미 친구 요청을 보냈습니다" in str(exc_info.value.detail)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_accept_friend_request_success(self, mock_guest_repo_class, mock_friendship_repo_class,
                                         friendship_service, sample_users):
        """친구 요청 수락 성공 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 친구 요청
        friendship = Friendship(
            friendship_id=1,
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        # Mock 설정
        mock_friendship_repo.find_by_id.return_value = friendship
        mock_friendship_repo.accept_friend_request.return_value = True
        
        # 테스트 실행
        result = service.accept_friend_request(user2, 1)
        
        # 검증
        assert result["success"] is True
        assert result["message"] == "친구 요청을 수락했습니다"
        mock_friendship_repo.find_by_id.assert_called_once_with(1)
        mock_friendship_repo.accept_friend_request.assert_called_once_with(friendship)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_get_friends_list(self, mock_guest_repo_class, mock_friendship_repo_class,
                             friendship_service, sample_users):
        """친구 목록 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 친구 관계들
        friendships = [
            Friendship(
                friendship_id=1,
                requester_id=user1.guest_id,
                addressee_id=user2.guest_id,
                status=FriendshipStatus.ACCEPTED
            ),
            Friendship(
                friendship_id=2,
                requester_id=user3.guest_id,
                addressee_id=user1.guest_id,
                status=FriendshipStatus.ACCEPTED
            )
        ]
        
        # Mock 설정
        mock_friendship_repo.get_accepted_friendships.return_value = friendships
        mock_guest_repo.find_by_id.side_effect = lambda guest_id: {
            user2.guest_id: user2,
            user3.guest_id: user3
        }.get(guest_id)
        
        # 테스트 실행
        result = service.get_friends_list(user1)
        
        # 검증
        assert len(result["friends"]) == 2
        assert result["total_count"] == 2
        mock_friendship_repo.get_accepted_friendships.assert_called_once_with(user1.guest_id)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_get_pending_requests(self, mock_guest_repo_class, mock_friendship_repo_class,
                                 friendship_service, sample_users):
        """대기 중인 친구 요청 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 대기 중인 요청들
        pending_requests = [
            Friendship(
                friendship_id=1,
                requester_id=user2.guest_id,
                addressee_id=user1.guest_id,
                status=FriendshipStatus.PENDING
            ),
            Friendship(
                friendship_id=2,
                requester_id=user3.guest_id,
                addressee_id=user1.guest_id,
                status=FriendshipStatus.PENDING
            )
        ]
        
        # Mock 설정
        mock_friendship_repo.get_pending_requests.return_value = pending_requests
        mock_guest_repo.find_by_id.side_effect = lambda guest_id: {
            user2.guest_id: user2,
            user3.guest_id: user3
        }.get(guest_id)
        
        # 테스트 실행
        result = service.get_pending_requests(user1)
        
        # 검증
        assert len(result["requests"]) == 2
        assert result["total_count"] == 2
        mock_friendship_repo.get_pending_requests.assert_called_once_with(user1.guest_id)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_reject_friend_request(self, mock_guest_repo_class, mock_friendship_repo_class,
                                  friendship_service, sample_users):
        """친구 요청 거절 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 친구 요청
        friendship = Friendship(
            friendship_id=1,
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        # Mock 설정
        mock_friendship_repo.find_by_id.return_value = friendship
        mock_friendship_repo.reject_friend_request.return_value = True
        
        # 테스트 실행
        result = service.reject_friend_request(user2, 1)
        
        # 검증
        assert result["success"] is True
        assert result["message"] == "친구 요청을 거절했습니다"
        mock_friendship_repo.reject_friend_request.assert_called_once_with(friendship)
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_remove_friend(self, mock_guest_repo_class, mock_friendship_repo_class,
                          friendship_service, sample_users):
        """친구 삭제 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        mock_friendship_repo.remove_friendship.return_value = True
        
        # 테스트 실행
        result = service.remove_friend(user1, user2.guest_id)
        
        # 검증
        assert result["success"] is True
        assert result["message"] == "친구를 삭제했습니다"
        mock_friendship_repo.remove_friendship.assert_called_once_with(
            user1.guest_id, user2.guest_id
        )
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_block_user(self, mock_guest_repo_class, mock_friendship_repo_class,
                       friendship_service, sample_users):
        """사용자 차단 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        mock_guest_repo.find_by_id.return_value = user2
        mock_friendship_repo.block_user.return_value = True
        
        # 테스트 실행
        result = service.block_user(user1, user2.guest_id)
        
        # 검증
        assert result["success"] is True
        assert result["message"] == "사용자를 차단했습니다"
        mock_friendship_repo.block_user.assert_called_once_with(
            user1.guest_id, user2.guest_id
        )
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_check_friendship_status(self, mock_guest_repo_class, mock_friendship_repo_class,
                                   friendship_service, sample_users):
        """친구 관계 상태 확인 테스트"""
        user1, user2, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        mock_friendship_repo.get_friendship_status.return_value = "friends"
        
        # 테스트 실행
        result = service.check_friendship_status(user1, user2.guest_id)
        
        # 검증
        assert result["status"] == "friends"
        mock_friendship_repo.get_friendship_status.assert_called_once_with(
            user1.guest_id, user2.guest_id
        )
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_search_users_for_friends(self, mock_guest_repo_class, mock_friendship_repo_class,
                                     friendship_service, sample_users):
        """친구 추가용 사용자 검색 테스트"""
        user1, user2, user3 = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        search_results = [user2, user3]
        mock_guest_repo.search_users.return_value = search_results
        mock_friendship_repo.get_friendship_status.return_value = "none"
        
        # 테스트 실행
        result = service.search_users_for_friends(user1, "테스트")
        
        # 검증
        assert len(result["users"]) == 2
        assert result["total_count"] == 2
        mock_guest_repo.search_users.assert_called_once()
    
    @patch('services.friendship_service.FriendshipRepository')
    @patch('services.friendship_service.GuestRepository')
    def test_get_friendship_statistics(self, mock_guest_repo_class, mock_friendship_repo_class,
                                     friendship_service, sample_users):
        """친구 관계 통계 조회 테스트"""
        user1, _, _ = sample_users
        
        # Repository mocks 설정
        mock_friendship_repo = Mock()
        mock_guest_repo = Mock()
        mock_friendship_repo_class.return_value = mock_friendship_repo
        mock_guest_repo_class.return_value = mock_guest_repo
        
        service = FriendshipService(friendship_service.db)
        
        # Mock 설정
        stats = {
            "total_friends": 5,
            "pending_requests_received": 2,
            "pending_requests_sent": 1,
            "blocked_users": 0
        }
        mock_friendship_repo.get_friendship_statistics.return_value = stats
        
        # 테스트 실행
        result = service.get_friendship_statistics(user1)
        
        # 검증
        assert result["total_friends"] == 5
        assert result["pending_requests_received"] == 2
        assert result["pending_requests_sent"] == 1
        assert result["blocked_users"] == 0
        mock_friendship_repo.get_friendship_statistics.assert_called_once_with(user1.guest_id)