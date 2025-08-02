"""
친구 관계 모델 테스트
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models.friendship_model import Friendship, FriendshipStatus
from models.guest_model import Guest


@pytest.fixture
def sample_guests(db_session):
    """테스트용 게스트 사용자들"""
    guest1 = Guest(
        uuid="test-uuid-1",
        nickname="테스트유저1",
        session_token="token1"
    )
    guest2 = Guest(
        uuid="test-uuid-2", 
        nickname="테스트유저2",
        session_token="token2"
    )
    guest3 = Guest(
        uuid="test-uuid-3",
        nickname="테스트유저3",
        session_token="token3"
    )
    
    db_session.add_all([guest1, guest2, guest3])
    db_session.commit()
    db_session.refresh(guest1)
    db_session.refresh(guest2)
    db_session.refresh(guest3)
    
    return guest1, guest2, guest3


class TestFriendshipModel:
    """친구 관계 모델 테스트"""
    
    def test_create_friendship_request(self, db_session, sample_guests):
        """친구 요청 생성 테스트"""
        guest1, guest2, _ = sample_guests
        
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id
        )
        
        db_session.add(friendship)
        db_session.commit()
        db_session.refresh(friendship)
        
        assert friendship.friendship_id is not None
        assert friendship.requester_id == guest1.guest_id
        assert friendship.addressee_id == guest2.guest_id
        assert friendship.status == FriendshipStatus.PENDING
        assert friendship.created_at is not None
        assert friendship.accepted_at is None
    
    def test_friendship_status_enum(self, db_session, sample_guests):
        """친구 관계 상태 Enum 테스트"""
        guest1, guest2, _ = sample_guests
        
        # PENDING 상태
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.PENDING
        )
        db_session.add(friendship)
        db_session.commit()
        
        assert friendship.status == FriendshipStatus.PENDING
        
        # ACCEPTED 상태로 변경
        friendship.status = FriendshipStatus.ACCEPTED
        friendship.accepted_at = datetime.utcnow()
        db_session.commit()
        
        assert friendship.status == FriendshipStatus.ACCEPTED
        assert friendship.accepted_at is not None
    
    def test_duplicate_friendship_prevention(self, db_session, sample_guests):
        """중복 친구 요청 방지 테스트"""
        guest1, guest2, _ = sample_guests
        
        # 첫 번째 친구 요청
        friendship1 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id
        )
        db_session.add(friendship1)
        db_session.commit()
        
        # 동일한 방향의 중복 요청 시도
        friendship2 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id
        )
        db_session.add(friendship2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_get_friendship_bidirectional(self, db_session, sample_guests):
        """양방향 친구 관계 조회 테스트"""
        guest1, guest2, _ = sample_guests
        
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.ACCEPTED
        )
        db_session.add(friendship)
        db_session.commit()
        
        # 양방향 조회 테스트
        found1 = Friendship.get_friendship(db_session, guest1.guest_id, guest2.guest_id)
        found2 = Friendship.get_friendship(db_session, guest2.guest_id, guest1.guest_id)
        
        assert found1 is not None
        assert found2 is not None
        assert found1.friendship_id == found2.friendship_id
    
    def test_are_friends(self, db_session, sample_guests):
        """친구 관계 확인 테스트"""
        guest1, guest2, guest3 = sample_guests
        
        # 아직 친구가 아님
        assert not Friendship.are_friends(db_session, guest1.guest_id, guest2.guest_id)
        
        # 친구 관계 생성
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.ACCEPTED
        )
        db_session.add(friendship)
        db_session.commit()
        
        # 친구 관계 확인
        assert Friendship.are_friends(db_session, guest1.guest_id, guest2.guest_id)
        assert Friendship.are_friends(db_session, guest2.guest_id, guest1.guest_id)
        
        # 친구가 아닌 사용자
        assert not Friendship.are_friends(db_session, guest1.guest_id, guest3.guest_id)
    
    def test_is_blocked(self, db_session, sample_guests):
        """차단 관계 확인 테스트"""
        guest1, guest2, guest3 = sample_guests
        
        # 차단 관계 생성
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.BLOCKED
        )
        db_session.add(friendship)
        db_session.commit()
        
        # 차단 확인
        assert Friendship.is_blocked(db_session, guest1.guest_id, guest2.guest_id)
        assert not Friendship.is_blocked(db_session, guest2.guest_id, guest1.guest_id)
        assert not Friendship.is_blocked(db_session, guest1.guest_id, guest3.guest_id)
    
    def test_get_friends_list(self, db_session, sample_guests):
        """친구 목록 조회 테스트"""
        guest1, guest2, guest3 = sample_guests
        
        # guest1과 guest2가 친구
        friendship1 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.ACCEPTED
        )
        
        # guest3가 guest1에게 친구 요청하고 수락됨
        friendship2 = Friendship(
            requester_id=guest3.guest_id,
            addressee_id=guest1.guest_id,
            status=FriendshipStatus.ACCEPTED
        )
        
        db_session.add_all([friendship1, friendship2])
        db_session.commit()
        
        # guest1의 친구 목록 조회
        friends_list = Friendship.get_friends_list(db_session, guest1.guest_id)
        assert len(friends_list) == 2
        
        friend_ids = []
        for friendship in friends_list:
            if friendship.requester_id == guest1.guest_id:
                friend_ids.append(friendship.addressee_id)
            else:
                friend_ids.append(friendship.requester_id)
        
        assert guest2.guest_id in friend_ids
        assert guest3.guest_id in friend_ids
    
    def test_get_pending_requests(self, db_session, sample_guests):
        """대기 중인 친구 요청 조회 테스트"""
        guest1, guest2, guest3 = sample_guests
        
        # guest1이 guest2에게 친구 요청
        friendship1 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        # guest3가 guest2에게 친구 요청
        friendship2 = Friendship(
            requester_id=guest3.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        db_session.add_all([friendship1, friendship2])
        db_session.commit()
        
        # guest2가 받은 대기 중인 요청들
        pending_requests = Friendship.get_pending_requests(db_session, guest2.guest_id)
        assert len(pending_requests) == 2
        
        requester_ids = [req.requester_id for req in pending_requests]
        assert guest1.guest_id in requester_ids
        assert guest3.guest_id in requester_ids
    
    def test_get_sent_requests(self, db_session, sample_guests):
        """보낸 친구 요청 조회 테스트"""
        guest1, guest2, guest3 = sample_guests
        
        # guest1이 guest2, guest3에게 친구 요청
        friendship1 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        friendship2 = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest3.guest_id,
            status=FriendshipStatus.PENDING
        )
        
        db_session.add_all([friendship1, friendship2])
        db_session.commit()
        
        # guest1이 보낸 요청들
        sent_requests = Friendship.get_sent_requests(db_session, guest1.guest_id)
        assert len(sent_requests) == 2
        
        addressee_ids = [req.addressee_id for req in sent_requests]
        assert guest2.guest_id in addressee_ids
        assert guest3.guest_id in addressee_ids
    
    def test_friendship_with_memo(self, db_session, sample_guests):
        """메모가 있는 친구 관계 테스트"""
        guest1, guest2, _ = sample_guests
        
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            memo="같은 회사 동료"
        )
        
        db_session.add(friendship)
        db_session.commit()
        db_session.refresh(friendship)
        
        assert friendship.memo == "같은 회사 동료"
    
    def test_friendship_repr(self, db_session, sample_guests):
        """Friendship __repr__ 테스트"""
        guest1, guest2, _ = sample_guests
        
        friendship = Friendship(
            requester_id=guest1.guest_id,
            addressee_id=guest2.guest_id,
            status=FriendshipStatus.ACCEPTED
        )
        
        db_session.add(friendship)
        db_session.commit()
        db_session.refresh(friendship)
        
        repr_str = repr(friendship)
        assert str(friendship.friendship_id) in repr_str
        assert str(guest1.guest_id) in repr_str
        assert str(guest2.guest_id) in repr_str
        assert "ACCEPTED" in repr_str