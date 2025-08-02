from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FriendshipStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    REJECTED = "rejected"


# 친구 요청 생성
class FriendRequestCreate(BaseModel):
    target_user_id: int
    memo: Optional[str] = None

    @validator('memo')
    def validate_memo(cls, v):
        if v is not None and len(v.strip()) > 200:
            raise ValueError('메모는 200자를 초과할 수 없습니다')
        return v.strip() if v else None


# 친구 요청 응답 (수락/거절)
class FriendRequestResponse(BaseModel):
    action: str  # "accept" or "reject"

    @validator('action')
    def validate_action(cls, v):
        if v not in ['accept', 'reject']:
            raise ValueError('action은 "accept" 또는 "reject"만 가능합니다')
        return v


# 친구 정보
class FriendInfo(BaseModel):
    guest_id: int
    nickname: str
    status: Optional[str] = None  # 게임 상태 (lobby, in_game, offline 등)
    last_seen: Optional[datetime] = None
    friendship_date: Optional[datetime] = None  # 친구가 된 날짜

    class Config:
        orm_mode = True
        from_attributes = True


# 친구 요청 정보
class FriendRequestInfo(BaseModel):
    friendship_id: int
    requester_id: int
    requester_nickname: str
    addressee_id: int
    addressee_nickname: str
    status: FriendshipStatus
    created_at: datetime
    updated_at: datetime
    memo: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


# 친구 목록 응답
class FriendsListResponse(BaseModel):
    friends: List[FriendInfo]
    total_count: int
    online_count: int = 0

    class Config:
        orm_mode = True


# 친구 요청 목록 응답
class FriendRequestsResponse(BaseModel):
    received_requests: List[FriendRequestInfo]
    sent_requests: List[FriendRequestInfo]
    received_count: int
    sent_count: int

    class Config:
        orm_mode = True


# 친구 검색
class FriendSearchRequest(BaseModel):
    nickname: str
    limit: int = 10

    @validator('nickname')
    def validate_nickname(cls, v):
        if not v or len(v.strip()) < 2:
            raise ValueError('닉네임은 2자 이상이어야 합니다')
        if len(v.strip()) > 20:
            raise ValueError('닉네임은 20자를 초과할 수 없습니다')
        return v.strip()

    @validator('limit')
    def validate_limit(cls, v):
        if v < 1 or v > 50:
            raise ValueError('검색 결과는 1-50개 사이여야 합니다')
        return v


# 사용자 검색 결과
class UserSearchResult(BaseModel):
    guest_id: int
    nickname: str
    friendship_status: Optional[str] = None  # "friends", "pending_sent", "pending_received", "blocked", "none"
    can_send_request: bool = True

    class Config:
        orm_mode = True
        from_attributes = True


# 친구 검색 응답
class UserSearchResponse(BaseModel):
    users: List[UserSearchResult]
    total_count: int
    query: str

    class Config:
        orm_mode = True


# 친구 관계 상태 확인
class FriendshipStatusResponse(BaseModel):
    user1_id: int
    user2_id: int
    are_friends: bool
    status: Optional[str] = None
    can_send_request: bool
    is_blocked: bool

    class Config:
        orm_mode = True


# 친구 통계
class FriendshipStats(BaseModel):
    total_friends: int
    pending_received: int
    pending_sent: int
    friends_online: int = 0
    recently_active: int = 0  # 최근 활동한 친구 수

    class Config:
        orm_mode = True


# 친구 활동 로그 (향후 확장용)
class FriendActivity(BaseModel):
    friend_id: int
    friend_nickname: str
    activity_type: str  # "joined_game", "won_game", "online", "offline"
    activity_data: Optional[dict] = None
    timestamp: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# 친구 활동 피드 응답
class FriendActivityResponse(BaseModel):
    activities: List[FriendActivity]
    total_count: int
    last_updated: datetime

    class Config:
        orm_mode = True