"""
친구 관계 리포지토리 테스트
"""

import pytest
from datetime import datetime, timedelta
from repositories.friendship_repository import FriendshipRepository
from models.friendship_model import Friendship, FriendshipStatus
from models.guest_model import Guest


@pytest.fixture
def friendship_repository(db_session):
    """친구 관계 리포지토리 인스턴스"""
    return FriendshipRepository(db_session)


@pytest.fixture
def sample_users(db_session):
    """테스트용 사용자들"""
    users = []
    for i in range(3):
        user = Guest(
            uuid=f"test-uuid-{i+1}",
            nickname=f"테스트유저{i+1}",
            session_token=f"token{i+1}"
        )
        db_session.add(user)
        users.append(user)
    
    db_session.commit()
    
    for user in users:
        db_session.refresh(user)
    
    return users


class TestFriendshipRepository:
    """친구 관계 리포지토리 테스트"""
    
    def test_create_friend_request(self, friendship_repository, sample_users):
        """친구 요청 생성 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id,
            memo="안녕하세요!"
        )
        
        # 검증
        assert friendship.friendship_id is not None
        assert friendship.requester_id == user1.guest_id
        assert friendship.addressee_id == user2.guest_id
        assert friendship.status == FriendshipStatus.PENDING
        assert friendship.memo == "안녕하세요!"
        assert friendship.created_at is not None
    
    def test_create_friend_request_without_memo(self, friendship_repository, sample_users):
        """메모 없이 친구 요청 생성 테스트"""
        user1, user2, _ = sample_users
        
        friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id
        )
        
        assert friendship.memo is None
        assert friendship.status == FriendshipStatus.PENDING
    
    def test_find_friendship_bidirectional(self, friendship_repository, sample_users):
        """양방향 친구 관계 조회 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        created_friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id
        )
        
        # 양방향 조회 테스트
        found1 = friendship_repository.find_friendship(user1.guest_id, user2.guest_id)
        found2 = friendship_repository.find_friendship(user2.guest_id, user1.guest_id)
        
        assert found1 is not None
        assert found2 is not None
        assert found1.friendship_id == found2.friendship_id == created_friendship.friendship_id
    
    def test_find_friendship_not_exists(self, friendship_repository, sample_users):
        """존재하지 않는 친구 관계 조회 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 관계가 없는 경우
        friendship = friendship_repository.find_friendship(user1.guest_id, user2.guest_id)
        
        assert friendship is None
    
    def test_find_friendship_by_id(self, friendship_repository, sample_users):
        """ID로 친구 관계 조회 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        created_friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id
        )
        
        # ID로 조회
        found_friendship = friendship_repository.find_friendship_by_id(created_friendship.friendship_id)
        
        assert found_friendship is not None
        assert found_friendship.friendship_id == created_friendship.friendship_id
    
    def test_find_friendship_by_id_not_exists(self, friendship_repository):
        """존재하지 않는 ID로 친구 관계 조회 테스트"""
        friendship = friendship_repository.find_friendship_by_id(999)
        assert friendship is None
    
    def test_update_friendship_status(self, friendship_repository, sample_users):
        """친구 관계 상태 업데이트 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id
        )
        
        original_updated_at = friendship.updated_at
        
        # 상태 업데이트
        updated_friendship = friendship_repository.update_friendship_status(
            friendship.friendship_id,
            FriendshipStatus.ACCEPTED
        )
        
        # 검증
        assert updated_friendship is not None
        assert updated_friendship.status == FriendshipStatus.ACCEPTED
        assert updated_friendship.updated_at > original_updated_at
    
    def test_update_friendship_status_with_accepted_time(self, friendship_repository, sample_users):
        """수락 시간과 함께 상태 업데이트 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        friendship = friendship_repository.create_friend_request(
            requester_id=user1.guest_id,
            addressee_id=user2.guest_id
        )
        
        # ACCEPTED 상태로 업데이트
        updated_friendship = friendship_repository.update_friendship_status(
            friendship.friendship_id,
            FriendshipStatus.ACCEPTED
        )
        
        # accepted_at이 설정되었는지 확인
        assert updated_friendship.accepted_at is not None
        assert updated_friendship.status == FriendshipStatus.ACCEPTED
    
    def test_get_accepted_friendships(self, friendship_repository, sample_users):
        """수락된 친구 관계 목록 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # 여러 친구 관계 생성
        friendship1 = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship2 = friendship_repository.create_friend_request(user3.guest_id, user1.guest_id)
        friendship3 = friendship_repository.create_friend_request(user1.guest_id, user3.guest_id)
        
        # 일부만 수락
        friendship_repository.update_friendship_status(friendship1.friendship_id, FriendshipStatus.ACCEPTED)
        friendship_repository.update_friendship_status(friendship2.friendship_id, FriendshipStatus.ACCEPTED)
        # friendship3는 PENDING 상태로 유지
        
        # user1의 수락된 친구 관계 조회
        accepted_friendships = friendship_repository.get_accepted_friendships(user1.guest_id)
        
        # 검증
        assert len(accepted_friendships) == 2
        friendship_ids = [f.friendship_id for f in accepted_friendships]
        assert friendship1.friendship_id in friendship_ids
        assert friendship2.friendship_id in friendship_ids
    
    def test_get_pending_requests_received(self, friendship_repository, sample_users):
        """받은 대기 중인 친구 요청 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # user2와 user3가 user1에게 친구 요청
        friendship1 = friendship_repository.create_friend_request(user2.guest_id, user1.guest_id)
        friendship2 = friendship_repository.create_friend_request(user3.guest_id, user1.guest_id)
        
        # user1이 받은 대기 중인 요청들
        pending_requests = friendship_repository.get_pending_requests(user1.guest_id)
        
        # 검증
        assert len(pending_requests) == 2
        requester_ids = [f.requester_id for f in pending_requests]
        assert user2.guest_id in requester_ids
        assert user3.guest_id in requester_ids
    
    def test_get_sent_requests(self, friendship_repository, sample_users):
        """보낸 친구 요청 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # user1이 user2, user3에게 친구 요청
        friendship1 = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship2 = friendship_repository.create_friend_request(user1.guest_id, user3.guest_id)
        
        # user1이 보낸 요청들
        sent_requests = friendship_repository.get_sent_requests(user1.guest_id)
        
        # 검증
        assert len(sent_requests) == 2
        addressee_ids = [f.addressee_id for f in sent_requests]
        assert user2.guest_id in addressee_ids
        assert user3.guest_id in addressee_ids
    
    def test_can_send_friend_request_success(self, friendship_repository, sample_users):
        """친구 요청 가능 여부 확인 - 성공 케이스"""
        user1, user2, _ = sample_users
        
        # 친구 관계가 없는 경우
        can_send, reason = friendship_repository.can_send_friend_request(user1.guest_id, user2.guest_id)
        
        assert can_send is True
        assert reason is None
    
    def test_can_send_friend_request_self(self, friendship_repository, sample_users):
        """자기 자신에게 친구 요청 시도 테스트"""
        user1, _, _ = sample_users
        
        can_send, reason = friendship_repository.can_send_friend_request(user1.guest_id, user1.guest_id)
        
        assert can_send is False
        assert "자기 자신" in reason
    
    def test_can_send_friend_request_already_pending(self, friendship_repository, sample_users):
        """이미 대기 중인 친구 요청이 있는 경우 테스트"""
        user1, user2, _ = sample_users
        
        # 첫 번째 친구 요청
        friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        
        # 두 번째 친구 요청 시도
        can_send, reason = friendship_repository.can_send_friend_request(user1.guest_id, user2.guest_id)
        
        assert can_send is False
        assert "이미" in reason
    
    def test_can_send_friend_request_already_friends(self, friendship_repository, sample_users):
        """이미 친구인 경우 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 관계 생성 및 수락
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship_repository.update_friendship_status(friendship.friendship_id, FriendshipStatus.ACCEPTED)
        
        # 추가 친구 요청 시도
        can_send, reason = friendship_repository.can_send_friend_request(user1.guest_id, user2.guest_id)
        
        assert can_send is False
        assert "이미 친구" in reason
    
    def test_can_send_friend_request_blocked(self, friendship_repository, sample_users):
        """차단된 사용자에게 친구 요청 시도 테스트"""
        user1, user2, _ = sample_users
        
        # 차단 관계 생성
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship_repository.update_friendship_status(friendship.friendship_id, FriendshipStatus.BLOCKED)
        
        # 친구 요청 시도
        can_send, reason = friendship_repository.can_send_friend_request(user1.guest_id, user2.guest_id)
        
        assert can_send is False
        assert "차단" in reason
    
    def test_accept_friend_request(self, friendship_repository, sample_users):
        """친구 요청 수락 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        
        # 요청 수락
        result = friendship_repository.accept_friend_request(friendship)
        
        # 검증
        assert result is True
        assert friendship.status == FriendshipStatus.ACCEPTED
        assert friendship.accepted_at is not None
    
    def test_reject_friend_request(self, friendship_repository, sample_users):
        """친구 요청 거절 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 요청 생성
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        
        # 요청 거절
        result = friendship_repository.reject_friend_request(friendship)
        
        # 검증
        assert result is True
        assert friendship.status == FriendshipStatus.REJECTED
    
    def test_block_user(self, friendship_repository, sample_users):
        """사용자 차단 테스트"""
        user1, user2, _ = sample_users
        
        # 사용자 차단
        result = friendship_repository.block_user(user1.guest_id, user2.guest_id)
        
        # 검증
        assert result is True
        
        # 차단 관계 확인
        friendship = friendship_repository.find_friendship(user1.guest_id, user2.guest_id)
        assert friendship is not None
        assert friendship.status == FriendshipStatus.BLOCKED
    
    def test_remove_friendship(self, friendship_repository, sample_users):
        """친구 관계 제거 테스트"""
        user1, user2, _ = sample_users
        
        # 친구 관계 생성 및 수락
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship_repository.update_friendship_status(friendship.friendship_id, FriendshipStatus.ACCEPTED)
        
        # 친구 관계 제거
        result = friendship_repository.remove_friendship(user1.guest_id, user2.guest_id)
        
        # 검증
        assert result is True
        
        # 관계가 삭제되었는지 확인
        remaining_friendship = friendship_repository.find_friendship(user1.guest_id, user2.guest_id)
        assert remaining_friendship is None
    
    def test_get_friendship_status(self, friendship_repository, sample_users):
        """친구 관계 상태 확인 테스트"""
        user1, user2, user3 = sample_users
        
        # 관계 없음
        status1 = friendship_repository.get_friendship_status(user1.guest_id, user3.guest_id)
        assert status1 == "none"
        
        # 대기 중인 요청
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        status2 = friendship_repository.get_friendship_status(user1.guest_id, user2.guest_id)
        assert status2 == "pending"
        
        # 친구 관계
        friendship_repository.update_friendship_status(friendship.friendship_id, FriendshipStatus.ACCEPTED)
        status3 = friendship_repository.get_friendship_status(user1.guest_id, user2.guest_id)
        assert status3 == "friends"
    
    def test_get_friendship_statistics(self, friendship_repository, sample_users):
        """친구 관계 통계 조회 테스트"""
        user1, user2, user3 = sample_users
        
        # 다양한 친구 관계 생성
        friendship1 = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship2 = friendship_repository.create_friend_request(user3.guest_id, user1.guest_id)
        friendship3 = friendship_repository.create_friend_request(user1.guest_id, user3.guest_id)
        
        # 일부 수락, 일부 대기, 일부 차단
        friendship_repository.update_friendship_status(friendship1.friendship_id, FriendshipStatus.ACCEPTED)
        friendship_repository.update_friendship_status(friendship3.friendship_id, FriendshipStatus.BLOCKED)
        # friendship2는 PENDING 상태로 유지
        
        # 통계 조회
        stats = friendship_repository.get_friendship_statistics(user1.guest_id)
        
        # 검증
        assert stats["total_friends"] == 1  # 수락된 친구 1명
        assert stats["pending_requests_received"] == 1  # 받은 대기 요청 1개
        assert stats["pending_requests_sent"] == 0  # 보낸 대기 요청 0개 (하나는 차단됨)
        assert stats["blocked_users"] == 1  # 차단한 사용자 1명
    
    def test_search_potential_friends(self, friendship_repository, sample_users, db_session):
        """친구 추가 가능한 사용자 검색 테스트"""
        user1, user2, user3 = sample_users
        
        # 추가 사용자 생성
        user4 = Guest(
            uuid="test-uuid-4",
            nickname="검색테스트",
            session_token="token4"
        )
        db_session.add(user4)
        db_session.commit()
        db_session.refresh(user4)
        
        # user1과 user2는 이미 친구
        friendship = friendship_repository.create_friend_request(user1.guest_id, user2.guest_id)
        friendship_repository.update_friendship_status(friendship.friendship_id, FriendshipStatus.ACCEPTED)
        
        # 친구 추가 가능한 사용자 검색
        potential_friends = friendship_repository.search_potential_friends(
            user1.guest_id, 
            search_query="테스트"
        )
        
        # 검증: user2는 이미 친구이므로 제외, user3와 user4만 포함
        found_ids = [user.guest_id for user in potential_friends]
        assert user2.guest_id not in found_ids  # 이미 친구
        assert user1.guest_id not in found_ids  # 자기 자신
        assert user3.guest_id in found_ids      # 친구 추가 가능
        assert user4.guest_id in found_ids      # 친구 추가 가능