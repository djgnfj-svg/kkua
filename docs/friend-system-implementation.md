# 친구 시스템 및 플레이어 프로필 구현 가이드

## 개요

KKUA에 친구 시스템과 플레이어 프로필 기능을 추가하여 소셜 게임 경험을 강화합니다. 플레이어들이 서로 친구를 맺고, 프로필을 통해 게임 기록을 확인하며, 함께 게임을 즐길 수 있는 환경을 제공합니다.

## 주요 기능

### 1. 친구 시스템
- **친구 요청 및 수락/거절**
- **친구 목록 관리**
- **온라인 상태 표시**
- **친구 초대 기능**

### 2. 플레이어 프로필
- **게임 통계 표시**
- **업적 시스템**
- **아바타 및 프로필 커스터마이징**
- **게임 히스토리**

### 3. 소셜 기능
- **친구와 함께 방 생성**
- **친구 게임 관전**
- **소셜 알림 시스템**

---

## 데이터베이스 설계

### 친구 관계 모델

```python
# backend/models/friend_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.models.base import Base
from datetime import datetime
from enum import Enum

class FriendStatus(str, Enum):
    PENDING = "pending"      # 요청 대기
    ACCEPTED = "accepted"    # 수락됨
    DECLINED = "declined"    # 거절됨
    BLOCKED = "blocked"      # 차단됨

class Friendship(Base):
    __tablename__ = "friendships"
    
    friendship_id = Column(Integer, primary_key=True)
    requester_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    addressee_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    status = Column(String(20), default=FriendStatus.PENDING, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    responded_at = Column(DateTime)
    message = Column(Text)  # 친구 요청 메시지
    
    # 관계 설정
    requester = relationship("Guest", foreign_keys=[requester_id], back_populates="sent_requests")
    addressee = relationship("Guest", foreign_keys=[addressee_id], back_populates="received_requests")
    
    # 인덱스 설정
    __table_args__ = (
        Index("idx_friendship_requester", "requester_id"),
        Index("idx_friendship_addressee", "addressee_id"),
        Index("idx_friendship_status", "status"),
        Index("idx_friendship_composite", "requester_id", "addressee_id"),
    )
    
    def __repr__(self):
        return f"<Friendship {self.requester_id} -> {self.addressee_id} ({self.status})>"

class OnlineStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    IN_GAME = "in_game"
    AWAY = "away"

class PlayerSession(Base):
    __tablename__ = "player_sessions"
    
    session_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    status = Column(String(20), default=OnlineStatus.OFFLINE, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    current_room_id = Column(Integer, ForeignKey("gamerooms.room_id"))
    login_time = Column(DateTime, default=datetime.utcnow)
    logout_time = Column(DateTime)
    
    # 관계 설정
    guest = relationship("Guest", back_populates="current_session")
    current_room = relationship("Gameroom")
    
    __table_args__ = (
        Index("idx_player_session_guest", "guest_id"),
        Index("idx_player_session_status", "status"),
        Index("idx_player_session_activity", "last_activity"),
    )
```

### 플레이어 프로필 모델

```python
# backend/models/profile_model.py
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, BigInteger, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.base import Base
from datetime import datetime

class PlayerProfile(Base):
    __tablename__ = "player_profiles"
    
    profile_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), unique=True, nullable=False)
    
    # 기본 프로필 정보
    display_name = Column(String(50))
    bio = Column(Text)
    avatar_url = Column(String(255))
    banner_url = Column(String(255))
    favorite_quote = Column(String(200))
    
    # 게임 통계
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    total_score = Column(BigInteger, default=0)
    highest_score = Column(Integer, default=0)
    longest_word = Column(String(50))
    total_words_used = Column(Integer, default=0)
    total_play_time = Column(Integer, default=0)  # 초 단위
    
    # 고급 통계
    average_response_time = Column(Float, default=0.0)
    favorite_starting_letters = Column(JSON)  # 자주 사용하는 시작 글자들
    word_categories = Column(JSON)  # 사용한 단어 카테고리별 통계
    seasonal_stats = Column(JSON)  # 시즌별 통계
    
    # 업적 및 배지
    achievements = Column(JSON)  # 획득한 업적 목록
    badges = Column(JSON)       # 획득한 배지 목록
    titles = Column(JSON)       # 사용 가능한 타이틀들
    current_title = Column(String(50))
    
    # 개인 설정
    privacy_settings = Column(JSON)  # 프라이버시 설정
    notification_settings = Column(JSON)  # 알림 설정
    
    # 랭킹 정보
    current_rank = Column(Integer, default=0)
    peak_rank = Column(Integer, default=0)
    rank_points = Column(Integer, default=1000)  # ELO 점수 시스템
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    guest = relationship("Guest", back_populates="profile")
    
    def __repr__(self):
        return f"<PlayerProfile {self.guest_id}: {self.display_name}>"
    
    @property
    def win_rate(self) -> float:
        """승률 계산"""
        if self.total_games == 0:
            return 0.0
        return (self.wins / self.total_games) * 100
    
    @property
    def average_score_per_game(self) -> float:
        """게임당 평균 점수"""
        if self.total_games == 0:
            return 0.0
        return self.total_score / self.total_games
    
    @property
    def rank_tier(self) -> str:
        """랭크 티어 계산"""
        if self.rank_points >= 2000:
            return "마스터"
        elif self.rank_points >= 1800:
            return "다이아몬드"
        elif self.rank_points >= 1600:
            return "플래티넘"
        elif self.rank_points >= 1400:
            return "골드"
        elif self.rank_points >= 1200:
            return "실버"
        else:
            return "브론즈"

class Achievement(Base):
    __tablename__ = "achievements"
    
    achievement_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    icon_url = Column(String(255))
    category = Column(String(50))  # gameplay, social, special
    difficulty = Column(String(20))  # easy, medium, hard, legendary
    points = Column(Integer, default=0)  # 업적 점수
    hidden = Column(Boolean, default=False)  # 숨겨진 업적 여부
    
    # 달성 조건
    condition_type = Column(String(50))  # total_games, win_streak, score_threshold 등
    condition_value = Column(Integer)    # 조건 값
    condition_data = Column(JSON)        # 추가 조건 데이터
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Achievement {self.name}>"

class PlayerAchievement(Base):
    __tablename__ = "player_achievements"
    
    player_achievement_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.achievement_id"), nullable=False)
    achieved_at = Column(DateTime, default=datetime.utcnow)
    progress = Column(Integer, default=0)  # 진행도 (%)
    
    # 관계 설정
    guest = relationship("Guest")
    achievement = relationship("Achievement")
    
    __table_args__ = (
        Index("idx_player_achievement_guest", "guest_id"),
        Index("idx_player_achievement_combo", "guest_id", "achievement_id"),
    )
```

---

## 백엔드 서비스 구현

### FriendService 구현

```python
# backend/services/friend_service.py
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.models.friend_model import Friendship, FriendStatus, PlayerSession, OnlineStatus
from backend.models.guest_model import Guest
from backend.repositories.friend_repository import FriendRepository
from backend.services.notification_service import NotificationService
from datetime import datetime, timedelta

class FriendService:
    """친구 시스템 관리 서비스"""
    
    def __init__(self, db: Session, notification_service: NotificationService):
        self.db = db
        self.notification_service = notification_service
        self.friend_repo = FriendRepository(db)
    
    async def send_friend_request(self, requester_id: int, addressee_id: int, 
                                message: Optional[str] = None) -> Dict[str, Any]:
        """친구 요청 보내기"""
        
        # 자기 자신에게 요청 방지
        if requester_id == addressee_id:
            return {
                "success": False,
                "message": "자기 자신에게는 친구 요청을 보낼 수 없습니다"
            }
        
        # 대상 사용자 존재 확인
        addressee = self.db.query(Guest).filter(Guest.guest_id == addressee_id).first()
        if not addressee:
            return {
                "success": False,
                "message": "존재하지 않는 사용자입니다"
            }
        
        # 기존 관계 확인
        existing_friendship = await self._get_friendship_between(requester_id, addressee_id)
        if existing_friendship:
            if existing_friendship.status == FriendStatus.PENDING:
                return {
                    "success": False,
                    "message": "이미 친구 요청이 진행 중입니다"
                }
            elif existing_friendship.status == FriendStatus.ACCEPTED:
                return {
                    "success": False,
                    "message": "이미 친구 관계입니다"
                }
            elif existing_friendship.status == FriendStatus.BLOCKED:
                return {
                    "success": False,
                    "message": "차단된 사용자입니다"
                }
        
        # 새 친구 요청 생성
        friendship = Friendship(
            requester_id=requester_id,
            addressee_id=addressee_id,
            status=FriendStatus.PENDING,
            message=message
        )
        
        self.db.add(friendship)
        self.db.commit()
        self.db.refresh(friendship)
        
        # 알림 전송
        await self.notification_service.send_friend_request_notification(
            requester_id, addressee_id, message
        )
        
        return {
            "success": True,
            "message": "친구 요청을 보냈습니다",
            "friendship_id": friendship.friendship_id
        }
    
    async def respond_to_friend_request(self, friendship_id: int, addressee_id: int, 
                                      accept: bool) -> Dict[str, Any]:
        """친구 요청 응답 (수락/거절)"""
        
        friendship = self.db.query(Friendship).filter(
            Friendship.friendship_id == friendship_id,
            Friendship.addressee_id == addressee_id,
            Friendship.status == FriendStatus.PENDING
        ).first()
        
        if not friendship:
            return {
                "success": False,
                "message": "유효하지 않은 친구 요청입니다"
            }
        
        # 응답 처리
        if accept:
            friendship.status = FriendStatus.ACCEPTED
            message = "친구 요청을 수락했습니다"
            
            # 양방향 친구 관계 생성 (선택적)
            # 현재 모델은 단방향이지만, 양방향으로 만들려면 역방향 관계도 생성
            reverse_friendship = Friendship(
                requester_id=addressee_id,
                addressee_id=friendship.requester_id,
                status=FriendStatus.ACCEPTED,
                requested_at=datetime.utcnow(),
                responded_at=datetime.utcnow()
            )
            self.db.add(reverse_friendship)
            
        else:
            friendship.status = FriendStatus.DECLINED
            message = "친구 요청을 거절했습니다"
        
        friendship.responded_at = datetime.utcnow()
        self.db.commit()
        
        # 알림 전송
        await self.notification_service.send_friend_response_notification(
            friendship.requester_id, addressee_id, accept
        )
        
        return {
            "success": True,
            "message": message,
            "accepted": accept
        }
    
    async def get_friends_list(self, user_id: int, include_online_status: bool = True) -> List[Dict[str, Any]]:
        """친구 목록 조회"""
        
        # 수락된 친구 관계만 조회
        friends_query = self.db.query(Friendship, Guest).join(
            Guest, 
            or_(
                and_(Friendship.requester_id == user_id, Guest.guest_id == Friendship.addressee_id),
                and_(Friendship.addressee_id == user_id, Guest.guest_id == Friendship.requester_id)
            )
        ).filter(
            Friendship.status == FriendStatus.ACCEPTED
        )
        
        friends_data = []
        for friendship, friend_guest in friends_query.all():
            friend_info = {
                "friend_id": friend_guest.guest_id,
                "nickname": friend_guest.nickname,
                "friendship_since": friendship.responded_at,
                "profile": None
            }
            
            # 프로필 정보 추가
            if hasattr(friend_guest, 'profile') and friend_guest.profile:
                friend_info["profile"] = {
                    "display_name": friend_guest.profile.display_name,
                    "avatar_url": friend_guest.profile.avatar_url,
                    "rank_tier": friend_guest.profile.rank_tier,
                    "total_games": friend_guest.profile.total_games,
                    "win_rate": friend_guest.profile.win_rate
                }
            
            # 온라인 상태 추가
            if include_online_status:
                online_status = await self._get_user_online_status(friend_guest.guest_id)
                friend_info["online_status"] = online_status
            
            friends_data.append(friend_info)
        
        # 온라인 상태별로 정렬 (온라인 > 게임중 > 자리비움 > 오프라인)
        status_priority = {
            OnlineStatus.ONLINE: 1,
            OnlineStatus.IN_GAME: 2,
            OnlineStatus.AWAY: 3,
            OnlineStatus.OFFLINE: 4
        }
        
        friends_data.sort(key=lambda f: (
            status_priority.get(f.get("online_status", {}).get("status"), 5),
            f["nickname"]
        ))
        
        return friends_data
    
    async def get_pending_requests(self, user_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """대기 중인 친구 요청 조회 (보낸 요청 + 받은 요청)"""
        
        # 보낸 요청들
        sent_requests = self.db.query(Friendship, Guest).join(
            Guest, Friendship.addressee_id == Guest.guest_id
        ).filter(
            Friendship.requester_id == user_id,
            Friendship.status == FriendStatus.PENDING
        ).all()
        
        # 받은 요청들
        received_requests = self.db.query(Friendship, Guest).join(
            Guest, Friendship.requester_id == Guest.guest_id
        ).filter(
            Friendship.addressee_id == user_id,
            Friendship.status == FriendStatus.PENDING
        ).all()
        
        return {
            "sent": [
                {
                    "friendship_id": friendship.friendship_id,
                    "addressee_id": guest.guest_id,
                    "addressee_nickname": guest.nickname,
                    "message": friendship.message,
                    "requested_at": friendship.requested_at
                }
                for friendship, guest in sent_requests
            ],
            "received": [
                {
                    "friendship_id": friendship.friendship_id,
                    "requester_id": guest.guest_id,
                    "requester_nickname": guest.nickname,
                    "message": friendship.message,
                    "requested_at": friendship.requested_at
                }
                for friendship, guest in received_requests
            ]
        }
    
    async def remove_friend(self, user_id: int, friend_id: int) -> Dict[str, Any]:
        """친구 관계 해제"""
        
        # 양방향 친구 관계 삭제
        friendships = self.db.query(Friendship).filter(
            or_(
                and_(Friendship.requester_id == user_id, Friendship.addressee_id == friend_id),
                and_(Friendship.requester_id == friend_id, Friendship.addressee_id == user_id)
            ),
            Friendship.status == FriendStatus.ACCEPTED
        ).all()
        
        if not friendships:
            return {
                "success": False,
                "message": "친구 관계가 아닙니다"
            }
        
        for friendship in friendships:
            self.db.delete(friendship)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": "친구 관계를 해제했습니다"
        }
    
    async def block_user(self, user_id: int, target_id: int) -> Dict[str, Any]:
        """사용자 차단"""
        
        # 기존 관계 확인 및 업데이트
        existing_friendship = await self._get_friendship_between(user_id, target_id)
        
        if existing_friendship:
            existing_friendship.status = FriendStatus.BLOCKED
            existing_friendship.responded_at = datetime.utcnow()
        else:
            # 새 차단 관계 생성
            friendship = Friendship(
                requester_id=user_id,
                addressee_id=target_id,
                status=FriendStatus.BLOCKED,
                responded_at=datetime.utcnow()
            )
            self.db.add(friendship)
        
        self.db.commit()
        
        return {
            "success": True,
            "message": "사용자를 차단했습니다"
        }
    
    async def update_online_status(self, user_id: int, status: OnlineStatus, 
                                 room_id: Optional[int] = None) -> Dict[str, Any]:
        """온라인 상태 업데이트"""
        
        session = self.db.query(PlayerSession).filter(
            PlayerSession.guest_id == user_id
        ).first()
        
        if not session:
            session = PlayerSession(guest_id=user_id)
            self.db.add(session)
        
        session.status = status
        session.last_activity = datetime.utcnow()
        session.current_room_id = room_id
        
        if status == OnlineStatus.OFFLINE:
            session.logout_time = datetime.utcnow()
        
        self.db.commit()
        
        # 친구들에게 상태 변경 알림
        await self._notify_friends_status_change(user_id, status)
        
        return {
            "success": True,
            "status": status.value,
            "last_activity": session.last_activity
        }
    
    async def _get_friendship_between(self, user1_id: int, user2_id: int) -> Optional[Friendship]:
        """두 사용자 간의 친구 관계 조회"""
        return self.db.query(Friendship).filter(
            or_(
                and_(Friendship.requester_id == user1_id, Friendship.addressee_id == user2_id),
                and_(Friendship.requester_id == user2_id, Friendship.addressee_id == user1_id)
            )
        ).first()
    
    async def _get_user_online_status(self, user_id: int) -> Dict[str, Any]:
        """사용자 온라인 상태 조회"""
        session = self.db.query(PlayerSession).filter(
            PlayerSession.guest_id == user_id
        ).first()
        
        if not session:
            return {
                "status": OnlineStatus.OFFLINE,
                "last_activity": None,
                "current_room_id": None
            }
        
        # 마지막 활동이 5분 이상 전이면 AWAY로 처리
        if session.last_activity < datetime.utcnow() - timedelta(minutes=5):
            if session.status != OnlineStatus.OFFLINE:
                session.status = OnlineStatus.AWAY
                self.db.commit()
        
        return {
            "status": session.status,
            "last_activity": session.last_activity,
            "current_room_id": session.current_room_id
        }
    
    async def _notify_friends_status_change(self, user_id: int, new_status: OnlineStatus):
        """친구들에게 상태 변경 알림"""
        friends = await self.get_friends_list(user_id, include_online_status=False)
        
        for friend in friends:
            await self.notification_service.send_status_change_notification(
                user_id, friend["friend_id"], new_status
            )
```

### ProfileService 구현

```python
# backend/services/profile_service.py
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.models.profile_model import PlayerProfile, Achievement, PlayerAchievement
from backend.models.guest_model import Guest
from backend.models.game_log_model import GameLog
from backend.repositories.profile_repository import ProfileRepository
from datetime import datetime, timedelta

class ProfileService:
    """플레이어 프로필 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.profile_repo = ProfileRepository(db)
    
    async def get_or_create_profile(self, guest_id: int) -> PlayerProfile:
        """프로필 조회 또는 생성"""
        profile = self.db.query(PlayerProfile).filter(
            PlayerProfile.guest_id == guest_id
        ).first()
        
        if not profile:
            guest = self.db.query(Guest).filter(Guest.guest_id == guest_id).first()
            if not guest:
                raise ValueError("존재하지 않는 사용자입니다")
            
            profile = PlayerProfile(
                guest_id=guest_id,
                display_name=guest.nickname,
                privacy_settings={
                    "show_stats": True,
                    "show_game_history": True,
                    "allow_friend_requests": True
                },
                notification_settings={
                    "friend_requests": True,
                    "game_invites": True,
                    "achievements": True
                }
            )
            
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        
        return profile
    
    async def update_profile(self, guest_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """프로필 정보 업데이트"""
        profile = await self.get_or_create_profile(guest_id)
        
        # 업데이트 가능한 필드들
        updatable_fields = [
            'display_name', 'bio', 'avatar_url', 'banner_url', 
            'favorite_quote', 'current_title', 'privacy_settings', 
            'notification_settings'
        ]
        
        updated_fields = []
        for field in updatable_fields:
            if field in update_data:
                setattr(profile, field, update_data[field])
                updated_fields.append(field)
        
        profile.updated_at = datetime.utcnow()
        self.db.commit()
        
        return {
            "success": True,
            "updated_fields": updated_fields,
            "message": "프로필이 업데이트되었습니다"
        }
    
    async def get_profile_stats(self, guest_id: int) -> Dict[str, Any]:
        """프로필 통계 조회"""
        profile = await self.get_or_create_profile(guest_id)
        
        # 최근 게임 기록 조회
        recent_games = self.db.query(GameLog).filter(
            GameLog.winner_id == guest_id
        ).order_by(GameLog.created_at.desc()).limit(10).all()
        
        # 이번 주 통계
        week_ago = datetime.utcnow() - timedelta(days=7)
        weekly_games = self.db.query(GameLog).filter(
            GameLog.created_at >= week_ago
        ).count()
        
        return {
            "basic_stats": {
                "total_games": profile.total_games,
                "wins": profile.wins,
                "losses": profile.losses,
                "draws": profile.draws,
                "win_rate": profile.win_rate,
                "total_score": profile.total_score,
                "average_score": profile.average_score_per_game,
                "highest_score": profile.highest_score,
                "longest_word": profile.longest_word,
                "total_words_used": profile.total_words_used
            },
            "ranking_info": {
                "current_rank": profile.current_rank,
                "peak_rank": profile.peak_rank,
                "rank_points": profile.rank_points,
                "tier": profile.rank_tier
            },
            "time_stats": {
                "total_play_time": profile.total_play_time,
                "average_response_time": profile.average_response_time,
                "last_active": profile.last_active
            },
            "weekly_stats": {
                "games_this_week": weekly_games
            },
            "achievements": await self._get_player_achievements(guest_id),
            "recent_games": [
                {
                    "game_id": game.log_id,
                    "created_at": game.created_at,
                    "duration": game.duration_seconds,
                    "participants_count": len(game.participant_data) if game.participant_data else 0
                }
                for game in recent_games
            ]
        }
    
    async def update_game_stats(self, guest_id: int, game_result: Dict[str, Any]) -> Dict[str, Any]:
        """게임 결과를 바탕으로 프로필 통계 업데이트"""
        profile = await self.get_or_create_profile(guest_id)
        
        # 기본 통계 업데이트
        profile.total_games += 1
        
        if game_result.get("won"):
            profile.wins += 1
        elif game_result.get("lost"):
            profile.losses += 1
        else:
            profile.draws += 1
        
        # 점수 관련 통계
        game_score = game_result.get("score", 0)
        profile.total_score += game_score
        if game_score > profile.highest_score:
            profile.highest_score = game_score
        
        # 단어 관련 통계
        words_used = game_result.get("words_used", [])
        profile.total_words_used += len(words_used)
        
        # 가장 긴 단어 업데이트
        if words_used:
            longest_in_game = max(words_used, key=len)
            if not profile.longest_word or len(longest_in_game) > len(profile.longest_word):
                profile.longest_word = longest_in_game
        
        # 플레이 시간 업데이트
        game_duration = game_result.get("duration_seconds", 0)
        profile.total_play_time += game_duration
        
        # 응답 시간 통계 (이동 평균)
        avg_response_time = game_result.get("average_response_time", 0)
        if avg_response_time > 0:
            if profile.average_response_time == 0:
                profile.average_response_time = avg_response_time
            else:
                profile.average_response_time = (
                    profile.average_response_time * 0.8 + avg_response_time * 0.2
                )
        
        profile.last_active = datetime.utcnow()
        profile.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        # 업적 확인
        await self._check_achievements(guest_id, game_result)
        
        return {
            "success": True,
            "new_stats": {
                "total_games": profile.total_games,
                "win_rate": profile.win_rate,
                "total_score": profile.total_score
            }
        }
    
    async def _get_player_achievements(self, guest_id: int) -> List[Dict[str, Any]]:
        """플레이어 업적 조회"""
        player_achievements = self.db.query(PlayerAchievement, Achievement).join(
            Achievement, PlayerAchievement.achievement_id == Achievement.achievement_id
        ).filter(
            PlayerAchievement.guest_id == guest_id
        ).all()
        
        return [
            {
                "achievement_id": achievement.achievement_id,
                "name": achievement.name,
                "description": achievement.description,
                "icon_url": achievement.icon_url,
                "category": achievement.category,
                "difficulty": achievement.difficulty,
                "points": achievement.points,
                "achieved_at": player_achievement.achieved_at,
                "progress": player_achievement.progress
            }
            for player_achievement, achievement in player_achievements
        ]
    
    async def _check_achievements(self, guest_id: int, game_result: Dict[str, Any]):
        """게임 결과 기반 업적 확인 및 부여"""
        profile = await self.get_or_create_profile(guest_id)
        
        # 이미 획득한 업적들
        obtained_achievements = {
            pa.achievement_id for pa in 
            self.db.query(PlayerAchievement).filter(
                PlayerAchievement.guest_id == guest_id
            ).all()
        }
        
        # 모든 업적 조회
        all_achievements = self.db.query(Achievement).all()
        
        new_achievements = []
        
        for achievement in all_achievements:
            if achievement.achievement_id in obtained_achievements:
                continue
            
            if await self._check_achievement_condition(guest_id, achievement, game_result, profile):
                # 업적 부여
                player_achievement = PlayerAchievement(
                    guest_id=guest_id,
                    achievement_id=achievement.achievement_id,
                    progress=100
                )
                
                self.db.add(player_achievement)
                new_achievements.append(achievement)
        
        if new_achievements:
            self.db.commit()
            
            # 업적 획득 알림 (비동기로 처리)
            for achievement in new_achievements:
                await self._notify_achievement_unlocked(guest_id, achievement)
    
    async def _check_achievement_condition(self, guest_id: int, achievement: Achievement, 
                                         game_result: Dict[str, Any], profile: PlayerProfile) -> bool:
        """업적 달성 조건 확인"""
        condition_type = achievement.condition_type
        condition_value = achievement.condition_value
        
        if condition_type == "total_games":
            return profile.total_games >= condition_value
        
        elif condition_type == "total_wins":
            return profile.wins >= condition_value
        
        elif condition_type == "win_streak":
            # 연승 확인 (별도 구현 필요)
            return await self._get_current_win_streak(guest_id) >= condition_value
        
        elif condition_type == "high_score":
            return game_result.get("score", 0) >= condition_value
        
        elif condition_type == "long_word":
            words_used = game_result.get("words_used", [])
            return any(len(word) >= condition_value for word in words_used)
        
        elif condition_type == "fast_response":
            avg_response = game_result.get("average_response_time", float('inf'))
            return avg_response <= condition_value
        
        elif condition_type == "total_score":
            return profile.total_score >= condition_value
        
        return False
    
    async def get_leaderboard(self, category: str = "rank_points", limit: int = 100) -> List[Dict[str, Any]]:
        """리더보드 조회"""
        
        valid_categories = {
            "rank_points": PlayerProfile.rank_points,
            "total_score": PlayerProfile.total_score,
            "total_games": PlayerProfile.total_games,
            "win_rate": PlayerProfile.wins,  # 승률은 계산 필요
            "highest_score": PlayerProfile.highest_score
        }
        
        if category not in valid_categories:
            category = "rank_points"
        
        order_column = valid_categories[category]
        
        # 승률의 경우 특별 처리
        if category == "win_rate":
            # 최소 10게임 이상 플레이한 플레이어만
            query = self.db.query(PlayerProfile, Guest).join(
                Guest, PlayerProfile.guest_id == Guest.guest_id
            ).filter(
                PlayerProfile.total_games >= 10
            ).order_by(
                (PlayerProfile.wins * 100 / PlayerProfile.total_games).desc()
            )
        else:
            query = self.db.query(PlayerProfile, Guest).join(
                Guest, PlayerProfile.guest_id == Guest.guest_id
            ).order_by(order_column.desc())
        
        results = query.limit(limit).all()
        
        leaderboard = []
        for rank, (profile, guest) in enumerate(results, 1):
            entry = {
                "rank": rank,
                "guest_id": profile.guest_id,
                "display_name": profile.display_name or guest.nickname,
                "avatar_url": profile.avatar_url,
                "tier": profile.rank_tier,
                "value": getattr(profile, category) if category != "win_rate" else profile.win_rate
            }
            
            # 카테고리별 추가 정보
            if category == "rank_points":
                entry["rank_points"] = profile.rank_points
            elif category == "total_score":
                entry["total_score"] = profile.total_score
                entry["total_games"] = profile.total_games
            
            leaderboard.append(entry)
        
        return leaderboard
```

---

## API 엔드포인트 구현

### Friend API Router

```python
# backend/routers/friend_router.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from backend.services.friend_service import FriendService
from backend.services.notification_service import NotificationService
from backend.dependencies import get_db, require_authentication
from backend.models.guest_model import Guest
from backend.schemas.friend_schema import (
    FriendRequestSchema, FriendResponseSchema, FriendListResponse
)

router = APIRouter(prefix="/friends", tags=["friends"])

def get_friend_service(db: Session = Depends(get_db)):
    notification_service = NotificationService()
    return FriendService(db, notification_service)

@router.post("/request")
async def send_friend_request(
    request: FriendRequestSchema,
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """친구 요청 보내기"""
    result = await friend_service.send_friend_request(
        requester_id=current_user.guest_id,
        addressee_id=request.addressee_id,
        message=request.message
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "data": result}

@router.post("/{friendship_id}/respond")
async def respond_to_friend_request(
    friendship_id: int,
    response: FriendResponseSchema,
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """친구 요청 응답 (수락/거절)"""
    result = await friend_service.respond_to_friend_request(
        friendship_id=friendship_id,
        addressee_id=current_user.guest_id,
        accept=response.accept
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "data": result}

@router.get("/")
async def get_friends_list(
    include_online_status: bool = Query(True),
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """친구 목록 조회"""
    friends = await friend_service.get_friends_list(
        user_id=current_user.guest_id,
        include_online_status=include_online_status
    )
    
    return {"status": "success", "data": {"friends": friends}}

@router.get("/requests")
async def get_pending_requests(
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """대기 중인 친구 요청 조회"""
    requests = await friend_service.get_pending_requests(current_user.guest_id)
    
    return {"status": "success", "data": requests}

@router.delete("/{friend_id}")
async def remove_friend(
    friend_id: int,
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """친구 관계 해제"""
    result = await friend_service.remove_friend(
        user_id=current_user.guest_id,
        friend_id=friend_id
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    
    return {"status": "success", "data": result}

@router.post("/{user_id}/block")
async def block_user(
    user_id: int,
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """사용자 차단"""
    result = await friend_service.block_user(
        user_id=current_user.guest_id,
        target_id=user_id
    )
    
    return {"status": "success", "data": result}

@router.post("/status")
async def update_online_status(
    status: str,
    room_id: int = None,
    current_user: Guest = Depends(require_authentication),
    friend_service: FriendService = Depends(get_friend_service)
):
    """온라인 상태 업데이트"""
    try:
        from backend.models.friend_model import OnlineStatus
        status_enum = OnlineStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="유효하지 않은 상태입니다")
    
    result = await friend_service.update_online_status(
        user_id=current_user.guest_id,
        status=status_enum,
        room_id=room_id
    )
    
    return {"status": "success", "data": result}
```

---

## 프론트엔드 구현

### FriendsList 컴포넌트

```javascript
// frontend/src/Pages/Friends/FriendsList.js
import React, { useState, useEffect } from 'react';
import { getFriendsList, getPendingRequests, respondToFriendRequest } from '../../Api/friendApi';
import { useToast } from '../../contexts/ToastContext';
import OnlineStatusIndicator from '../../components/OnlineStatusIndicator';
import UserAvatar from '../../components/UserAvatar';

const FriendsList = () => {
    const [friends, setFriends] = useState([]);
    const [pendingRequests, setPendingRequests] = useState({ sent: [], received: [] });
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('friends');
    const { showSuccess, showError } = useToast();

    useEffect(() => {
        loadFriendsData();
    }, []);

    const loadFriendsData = async () => {
        try {
            const [friendsResponse, requestsResponse] = await Promise.all([
                getFriendsList({ include_online_status: true }),
                getPendingRequests()
            ]);

            setFriends(friendsResponse.data.friends);
            setPendingRequests(requestsResponse.data);
        } catch (error) {
            console.error('친구 데이터 로드 실패:', error);
            showError('친구 목록을 불러오는데 실패했습니다');
        } finally {
            setLoading(false);
        }
    };

    const handleFriendRequestResponse = async (friendshipId, accept) => {
        try {
            await respondToFriendRequest(friendshipId, { accept });
            
            showSuccess(accept ? '친구 요청을 수락했습니다' : '친구 요청을 거절했습니다');
            
            // 데이터 다시 로드
            await loadFriendsData();
        } catch (error) {
            console.error('친구 요청 응답 실패:', error);
            showError('요청 처리에 실패했습니다');
        }
    };

    const getOnlineStatusText = (status) => {
        const statusMap = {
            'online': '온라인',
            'in_game': '게임 중',
            'away': '자리 비움',
            'offline': '오프라인'
        };
        return statusMap[status] || '알 수 없음';
    };

    const getOnlineStatusColor = (status) => {
        const colorMap = {
            'online': 'text-green-600',
            'in_game': 'text-blue-600',
            'away': 'text-yellow-600',
            'offline': 'text-gray-400'
        };
        return colorMap[status] || 'text-gray-400';
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto p-6">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">친구</h1>
            
            {/* 탭 네비게이션 */}
            <div className="flex space-x-1 mb-6">
                <button
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        activeTab === 'friends'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    onClick={() => setActiveTab('friends')}
                >
                    친구 목록 ({friends.length})
                </button>
                <button
                    className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                        activeTab === 'requests'
                            ? 'bg-blue-500 text-white'
                            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    onClick={() => setActiveTab('requests')}
                >
                    요청 ({pendingRequests.received.length})
                </button>
            </div>

            {/* 친구 목록 탭 */}
            {activeTab === 'friends' && (
                <div className="space-y-4">
                    {friends.length === 0 ? (
                        <div className="text-center py-12">
                            <p className="text-gray-500 text-lg">아직 친구가 없습니다</p>
                            <p className="text-gray-400 text-sm mt-2">
                                다른 플레이어들과 친구가 되어보세요!
                            </p>
                        </div>
                    ) : (
                        friends.map((friend) => (
                            <div
                                key={friend.friend_id}
                                className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        <UserAvatar
                                            src={friend.profile?.avatar_url}
                                            name={friend.profile?.display_name || friend.nickname}
                                            size="md"
                                        />
                                        
                                        <div>
                                            <h3 className="font-semibold text-gray-800">
                                                {friend.profile?.display_name || friend.nickname}
                                            </h3>
                                            <div className="flex items-center space-x-2 text-sm">
                                                <OnlineStatusIndicator status={friend.online_status?.status} />
                                                <span className={getOnlineStatusColor(friend.online_status?.status)}>
                                                    {getOnlineStatusText(friend.online_status?.status)}
                                                </span>
                                            </div>
                                            {friend.profile && (
                                                <div className="text-xs text-gray-500 mt-1">
                                                    {friend.profile.rank_tier} • 
                                                    {friend.profile.total_games}게임 • 
                                                    승률 {friend.profile.win_rate.toFixed(1)}%
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    
                                    <div className="flex space-x-2">
                                        {friend.online_status?.status === 'online' && (
                                            <button className="px-3 py-1 bg-green-100 text-green-700 rounded-md text-sm hover:bg-green-200 transition-colors">
                                                게임 초대
                                            </button>
                                        )}
                                        <button className="px-3 py-1 bg-gray-100 text-gray-600 rounded-md text-sm hover:bg-gray-200 transition-colors">
                                            프로필 보기
                                        </button>
                                        <button className="px-3 py-1 bg-red-100 text-red-600 rounded-md text-sm hover:bg-red-200 transition-colors">
                                            친구 삭제
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            )}

            {/* 친구 요청 탭 */}
            {activeTab === 'requests' && (
                <div className="space-y-6">
                    {/* 받은 요청 */}
                    <div>
                        <h2 className="text-lg font-semibold text-gray-800 mb-4">
                            받은 요청 ({pendingRequests.received.length})
                        </h2>
                        <div className="space-y-3">
                            {pendingRequests.received.length === 0 ? (
                                <p className="text-gray-500 text-center py-8">받은 친구 요청이 없습니다</p>
                            ) : (
                                pendingRequests.received.map((request) => (
                                    <div
                                        key={request.friendship_id}
                                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-4">
                                                <UserAvatar
                                                    name={request.requester_nickname}
                                                    size="sm"
                                                />
                                                <div>
                                                    <h4 className="font-medium text-gray-800">
                                                        {request.requester_nickname}
                                                    </h4>
                                                    {request.message && (
                                                        <p className="text-sm text-gray-600 mt-1">
                                                            "{request.message}"
                                                        </p>
                                                    )}
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {new Date(request.requested_at).toLocaleDateString('ko-KR')}
                                                    </p>
                                                </div>
                                            </div>
                                            
                                            <div className="flex space-x-2">
                                                <button
                                                    className="px-4 py-2 bg-green-500 text-white rounded-md text-sm hover:bg-green-600 transition-colors"
                                                    onClick={() => handleFriendRequestResponse(request.friendship_id, true)}
                                                >
                                                    수락
                                                </button>
                                                <button
                                                    className="px-4 py-2 bg-red-500 text-white rounded-md text-sm hover:bg-red-600 transition-colors"
                                                    onClick={() => handleFriendRequestResponse(request.friendship_id, false)}
                                                >
                                                    거절
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* 보낸 요청 */}
                    <div>
                        <h2 className="text-lg font-semibold text-gray-800 mb-4">
                            보낸 요청 ({pendingRequests.sent.length})
                        </h2>
                        <div className="space-y-3">
                            {pendingRequests.sent.length === 0 ? (
                                <p className="text-gray-500 text-center py-8">보낸 친구 요청이 없습니다</p>
                            ) : (
                                pendingRequests.sent.map((request) => (
                                    <div
                                        key={request.friendship_id}
                                        className="bg-white rounded-lg shadow-sm border border-gray-200 p-4"
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-4">
                                                <UserAvatar
                                                    name={request.addressee_nickname}
                                                    size="sm"
                                                />
                                                <div>
                                                    <h4 className="font-medium text-gray-800">
                                                        {request.addressee_nickname}
                                                    </h4>
                                                    {request.message && (
                                                        <p className="text-sm text-gray-600 mt-1">
                                                            "{request.message}"
                                                        </p>
                                                    )}
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        {new Date(request.requested_at).toLocaleDateString('ko-KR')} • 응답 대기 중
                                                    </p>
                                                </div>
                                            </div>
                                            
                                            <button className="px-4 py-2 bg-gray-100 text-gray-600 rounded-md text-sm hover:bg-gray-200 transition-colors">
                                                요청 취소
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default FriendsList;
```

---

## 구현 우선순위

### Phase 1 (1주차): 기본 친구 시스템
1. **데이터베이스 모델** - Friendship, PlayerSession 테이블
2. **FriendService** - 친구 요청/수락/거절 기능
3. **Friend API** - REST API 엔드포인트
4. **기본 UI** - 친구 목록, 요청 관리

### Phase 2 (2주차): 프로필 시스템
1. **프로필 모델** - PlayerProfile, Achievement 테이블
2. **ProfileService** - 통계 관리, 업적 시스템
3. **프로필 UI** - 프로필 페이지, 통계 표시

### Phase 3 (3주차): 고급 기능
1. **온라인 상태** - 실시간 상태 업데이트
2. **게임 초대** - 친구 초대 기능
3. **알림 시스템** - 친구 관련 알림

이 가이드를 통해 KKUA에 완전한 소셜 기능을 추가하여 플레이어들의 커뮤니티 경험을 크게 향상시킬 수 있습니다.