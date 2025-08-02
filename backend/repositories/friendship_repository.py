from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, func
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from models.friendship_model import Friendship, FriendshipStatus
from models.guest_model import Guest


class FriendshipRepository:
    """친구 관계 데이터 접근 계층"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_friend_request(self, requester_id: int, addressee_id: int, memo: Optional[str] = None) -> Friendship:
        """친구 요청을 생성합니다."""
        friendship = Friendship(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendshipStatus.PENDING,
            memo=memo
        )
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        return friendship

    def find_friendship(self, user1_id: int, user2_id: int) -> Optional[Friendship]:
        """두 사용자 간의 친구 관계를 조회합니다 (양방향)."""
        return self.db.query(Friendship).filter(
            or_(
                and_(Friendship.requester_id == user1_id, Friendship.addressee_id == user2_id),
                and_(Friendship.requester_id == user2_id, Friendship.addressee_id == user1_id)
            )
        ).first()

    def find_friendship_by_id(self, friendship_id: int) -> Optional[Friendship]:
        """친구 관계 ID로 조회합니다."""
        return self.db.query(Friendship).filter(
            Friendship.friendship_id == friendship_id
        ).first()

    def update_friendship_status(self, friendship_id: int, status: FriendshipStatus) -> Optional[Friendship]:
        """친구 관계 상태를 업데이트합니다."""
        friendship = self.find_friendship_by_id(friendship_id)
        if friendship:
            friendship.status = status
            friendship.updated_at = datetime.utcnow()
            
            # 친구 수락 시 accepted_at 설정
            if status == FriendshipStatus.ACCEPTED:
                friendship.accepted_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(friendship)
        return friendship

    def accept_friend_request(self, friendship_id: int, user_id: int) -> Optional[Friendship]:
        """친구 요청을 수락합니다. (요청 받은 사용자만 가능)"""
        friendship = self.db.query(Friendship).filter(
            Friendship.friendship_id == friendship_id,
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).first()
        
        if friendship:
            return self.update_friendship_status(friendship_id, FriendshipStatus.ACCEPTED)
        return None

    def reject_friend_request(self, friendship_id: int, user_id: int) -> Optional[Friendship]:
        """친구 요청을 거절합니다. (요청 받은 사용자만 가능)"""
        friendship = self.db.query(Friendship).filter(
            Friendship.friendship_id == friendship_id,
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).first()
        
        if friendship:
            return self.update_friendship_status(friendship_id, FriendshipStatus.REJECTED)
        return None

    def block_user(self, blocker_id: int, blocked_id: int) -> Friendship:
        """사용자를 차단합니다."""
        # 기존 관계가 있는지 확인
        existing = self.find_friendship(blocker_id, blocked_id)
        
        if existing:
            # 기존 관계를 차단으로 변경
            existing.status = FriendshipStatus.BLOCKED
            existing.requester_id = blocker_id  # 차단한 사람이 requester
            existing.addressee_id = blocked_id
            existing.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # 새로운 차단 관계 생성
            return self.create_friend_request(blocker_id, blocked_id)

    def unblock_user(self, blocker_id: int, blocked_id: int) -> bool:
        """사용자 차단을 해제합니다."""
        friendship = self.db.query(Friendship).filter(
            Friendship.requester_id == blocker_id,
            Friendship.addressee_id == blocked_id,
            Friendship.status == FriendshipStatus.BLOCKED
        ).first()
        
        if friendship:
            self.db.delete(friendship)
            self.db.commit()
            return True
        return False

    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """친구 관계를 삭제합니다."""
        friendship = self.find_friendship(user_id, friend_id)
        if friendship and friendship.status == FriendshipStatus.ACCEPTED:
            self.db.delete(friendship)
            self.db.commit()
            return True
        return False

    def get_friends_list(self, user_id: int, limit: int = 50, offset: int = 0) -> Tuple[List[Dict], int]:
        """사용자의 친구 목록을 조회합니다."""
        # 친구 관계 조회 (양방향)
        query = self.db.query(Friendship).filter(
            or_(
                and_(Friendship.requester_id == user_id, Friendship.status == FriendshipStatus.ACCEPTED),
                and_(Friendship.addressee_id == user_id, Friendship.status == FriendshipStatus.ACCEPTED)
            )
        ).options(
            joinedload(Friendship.requester),
            joinedload(Friendship.addressee)
        )
        
        total = query.count()
        friendships = query.order_by(desc(Friendship.accepted_at)).offset(offset).limit(limit).all()
        
        friends = []
        for friendship in friendships:
            # 상대방 정보 추출
            if friendship.requester_id == user_id:
                friend = friendship.addressee
            else:
                friend = friendship.requester
            
            friends.append({
                'guest_id': friend.guest_id,
                'nickname': friend.nickname,
                'friendship_date': friendship.accepted_at,
                'status': 'offline'  # TODO: 실시간 상태 구현 시 업데이트
            })
        
        return friends, total

    def get_received_requests(self, user_id: int, limit: int = 20) -> List[Friendship]:
        """받은 친구 요청 목록을 조회합니다."""
        return self.db.query(Friendship).filter(
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).options(
            joinedload(Friendship.requester)
        ).order_by(desc(Friendship.created_at)).limit(limit).all()

    def get_sent_requests(self, user_id: int, limit: int = 20) -> List[Friendship]:
        """보낸 친구 요청 목록을 조회합니다."""
        return self.db.query(Friendship).filter(
            Friendship.requester_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).options(
            joinedload(Friendship.addressee)
        ).order_by(desc(Friendship.created_at)).limit(limit).all()

    def search_users_by_nickname(self, search_term: str, current_user_id: int, limit: int = 10) -> List[Dict]:
        """닉네임으로 사용자를 검색합니다."""
        # 자기 자신을 제외하고 검색
        users = self.db.query(Guest).filter(
            Guest.nickname.ilike(f'%{search_term}%'),
            Guest.guest_id != current_user_id
        ).limit(limit).all()
        
        results = []
        for user in users:
            # 친구 관계 상태 확인
            friendship = self.find_friendship(current_user_id, user.guest_id)
            
            friendship_status = "none"
            can_send_request = True
            
            if friendship:
                if friendship.status == FriendshipStatus.ACCEPTED:
                    friendship_status = "friends"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.PENDING:
                    if friendship.requester_id == current_user_id:
                        friendship_status = "pending_sent"
                    else:
                        friendship_status = "pending_received"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.BLOCKED:
                    friendship_status = "blocked"
                    can_send_request = False
                elif friendship.status == FriendshipStatus.REJECTED:
                    # 거절된 경우 24시간 후 다시 요청 가능
                    if friendship.updated_at + timedelta(hours=24) > datetime.utcnow():
                        can_send_request = False
            
            results.append({
                'guest_id': user.guest_id,
                'nickname': user.nickname,
                'friendship_status': friendship_status,
                'can_send_request': can_send_request
            })
        
        return results

    def get_friendship_stats(self, user_id: int) -> Dict[str, int]:
        """사용자의 친구 관계 통계를 조회합니다."""
        # 총 친구 수
        friends_count = self.db.query(Friendship).filter(
            or_(
                and_(Friendship.requester_id == user_id, Friendship.status == FriendshipStatus.ACCEPTED),
                and_(Friendship.addressee_id == user_id, Friendship.status == FriendshipStatus.ACCEPTED)
            )
        ).count()
        
        # 받은 친구 요청 수
        received_requests = self.db.query(Friendship).filter(
            Friendship.addressee_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).count()
        
        # 보낸 친구 요청 수
        sent_requests = self.db.query(Friendship).filter(
            Friendship.requester_id == user_id,
            Friendship.status == FriendshipStatus.PENDING
        ).count()
        
        return {
            'total_friends': friends_count,
            'pending_received': received_requests,
            'pending_sent': sent_requests,
            'friends_online': 0,  # TODO: 실시간 상태 구현 시 업데이트
            'recently_active': 0  # TODO: 활동 로그 구현 시 업데이트
        }

    def is_blocked(self, blocker_id: int, blocked_id: int) -> bool:
        """한 사용자가 다른 사용자를 차단했는지 확인합니다."""
        return self.db.query(Friendship).filter(
            Friendship.requester_id == blocker_id,
            Friendship.addressee_id == blocked_id,
            Friendship.status == FriendshipStatus.BLOCKED
        ).first() is not None

    def can_send_friend_request(self, requester_id: int, addressee_id: int) -> Tuple[bool, str]:
        """친구 요청을 보낼 수 있는지 확인합니다."""
        if requester_id == addressee_id:
            return False, "자기 자신에게는 친구 요청을 보낼 수 없습니다"
        
        # 차단 관계 확인 (양방향)
        if self.is_blocked(addressee_id, requester_id):
            return False, "이 사용자에게는 친구 요청을 보낼 수 없습니다"
        
        if self.is_blocked(requester_id, addressee_id):
            return False, "차단한 사용자에게는 친구 요청을 보낼 수 없습니다"
        
        # 기존 관계 확인
        existing = self.find_friendship(requester_id, addressee_id)
        if existing:
            if existing.status == FriendshipStatus.ACCEPTED:
                return False, "이미 친구 관계입니다"
            elif existing.status == FriendshipStatus.PENDING:
                return False, "이미 친구 요청이 진행 중입니다"
            elif existing.status == FriendshipStatus.REJECTED:
                # 거절된 지 24시간이 지나지 않았으면 요청 불가
                if existing.updated_at + timedelta(hours=24) > datetime.utcnow():
                    return False, "거절된 후 24시간이 지나야 다시 요청할 수 있습니다"
        
        return True, "친구 요청을 보낼 수 있습니다"