from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Index, Enum as SQLEnum
from sqlalchemy.orm import relationship
from db.postgres import Base
import enum
from datetime import datetime


class FriendshipStatus(str, enum.Enum):
    PENDING = "pending"      # 친구 요청 대기 중
    ACCEPTED = "accepted"    # 친구 관계 성립
    BLOCKED = "blocked"      # 차단됨
    REJECTED = "rejected"    # 친구 요청 거절됨


class Friendship(Base):
    """
    친구 관계를 나타내는 모델
    
    양방향 친구 관계를 단방향 레코드로 관리하며,
    상태 변화를 통해 친구 요청, 수락, 거절, 차단 등을 처리합니다.
    """
    __tablename__ = "friendships"

    friendship_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 친구 요청을 보낸 사용자
    requester_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 친구 요청을 받은 사용자
    addressee_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 친구 관계 상태
    status = Column(
        SQLEnum(FriendshipStatus), 
        nullable=False, 
        default=FriendshipStatus.PENDING
    )
    
    # 요청 생성 시간
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # 상태 변경 시간 (수락/거절/차단 시간)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 친구가 된 시간 (status가 ACCEPTED가 된 시간)
    accepted_at = Column(DateTime, nullable=True)
    
    # 메모 (선택사항)
    memo = Column(String(200), nullable=True)

    # 관계 설정
    requester = relationship("Guest", foreign_keys=[requester_id], backref="sent_friend_requests")
    addressee = relationship("Guest", foreign_keys=[addressee_id], backref="received_friend_requests")

    # 인덱스 정의
    __table_args__ = (
        # 중복 친구 요청 방지 (같은 방향)
        Index('idx_friendship_unique', 'requester_id', 'addressee_id', unique=True),
        
        # 상태별 조회 최적화
        Index('idx_friendship_status', 'status'),
        
        # 사용자별 친구 목록 조회 최적화
        Index('idx_friendship_requester_status', 'requester_id', 'status'),
        Index('idx_friendship_addressee_status', 'addressee_id', 'status'),
        
        # 시간순 정렬 최적화
        Index('idx_friendship_created_at', 'created_at'),
        Index('idx_friendship_updated_at', 'updated_at'),
    )

    @classmethod
    def get_friendship(cls, db, user1_id: int, user2_id: int):
        """
        두 사용자 간의 친구 관계를 조회합니다.
        양방향으로 검색하여 어느 쪽에서 요청했든 관계를 찾습니다.
        """
        return db.query(cls).filter(
            ((cls.requester_id == user1_id) & (cls.addressee_id == user2_id)) |
            ((cls.requester_id == user2_id) & (cls.addressee_id == user1_id))
        ).first()

    @classmethod
    def are_friends(cls, db, user1_id: int, user2_id: int) -> bool:
        """두 사용자가 친구 관계인지 확인합니다."""
        friendship = cls.get_friendship(db, user1_id, user2_id)
        return friendship is not None and friendship.status == FriendshipStatus.ACCEPTED

    @classmethod
    def is_blocked(cls, db, blocker_id: int, blocked_id: int) -> bool:
        """한 사용자가 다른 사용자를 차단했는지 확인합니다."""
        friendship = db.query(cls).filter(
            cls.requester_id == blocker_id,
            cls.addressee_id == blocked_id,
            cls.status == FriendshipStatus.BLOCKED
        ).first()
        return friendship is not None

    @classmethod
    def get_friends_list(cls, db, user_id: int):
        """사용자의 친구 목록을 반환합니다."""
        # 본인이 요청한 친구들
        friends_as_requester = db.query(cls).filter(
            cls.requester_id == user_id,
            cls.status == FriendshipStatus.ACCEPTED
        ).all()
        
        # 본인이 수락한 친구들
        friends_as_addressee = db.query(cls).filter(
            cls.addressee_id == user_id,
            cls.status == FriendshipStatus.ACCEPTED
        ).all()
        
        return friends_as_requester + friends_as_addressee

    @classmethod
    def get_pending_requests(cls, db, user_id: int):
        """사용자가 받은 친구 요청 목록을 반환합니다."""
        return db.query(cls).filter(
            cls.addressee_id == user_id,
            cls.status == FriendshipStatus.PENDING
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_sent_requests(cls, db, user_id: int):
        """사용자가 보낸 친구 요청 목록을 반환합니다."""
        return db.query(cls).filter(
            cls.requester_id == user_id,
            cls.status == FriendshipStatus.PENDING
        ).order_by(cls.created_at.desc()).all()

    def __repr__(self):
        return f"<Friendship(id={self.friendship_id}, {self.requester_id}->{self.addressee_id}, status={self.status})>"