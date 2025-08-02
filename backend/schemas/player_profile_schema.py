from pydantic import BaseModel, validator, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# 프로필 업데이트 요청
class ProfileUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    banner_url: Optional[str] = Field(None, max_length=500)
    preferred_game_mode: Optional[str] = Field(None, max_length=50)
    is_public: Optional[bool] = None
    allow_friend_requests: Optional[bool] = None

    @validator('display_name')
    def validate_display_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) < 2:
                raise ValueError('표시명은 2자 이상이어야 합니다')
            if len(v) > 50:
                raise ValueError('표시명은 50자를 초과할 수 없습니다')
        return v

    @validator('bio')
    def validate_bio(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 500:
                raise ValueError('자기소개는 500자를 초과할 수 없습니다')
        return v


# 업적 정보
class Achievement(BaseModel):
    id: str
    name: str
    earned_at: datetime

    class Config:
        orm_mode = True


# 배지 정보
class Badge(BaseModel):
    id: str
    name: str
    type: str = "general"
    earned_at: datetime

    class Config:
        orm_mode = True


# 게임 모드별 통계
class ModeStatistics(BaseModel):
    mode_name: str
    games_played: int = 0
    games_won: int = 0
    win_rate: float = 0.0
    average_score: float = 0.0
    best_score: int = 0

    class Config:
        orm_mode = True


# 기본 프로필 정보 (공개용)
class BasicProfileInfo(BaseModel):
    guest_id: int
    nickname: str
    display_name: Optional[str] = None
    level: int
    rank_tier: str
    total_games_played: int
    win_rate: float
    is_public: bool

    class Config:
        orm_mode = True
        from_attributes = True


# 상세 프로필 정보
class DetailedProfileInfo(BaseModel):
    guest_id: int
    nickname: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    banner_url: Optional[str] = None
    
    # 레벨 및 경험치
    level: int
    experience_points: int
    experience_to_next_level: int
    
    # 랭킹 정보
    rank_tier: str
    rank_points: int
    global_rank: Optional[int] = None
    peak_rank: Optional[int] = None
    
    # 게임 통계
    total_games_played: int
    total_games_won: int
    total_games_lost: int
    win_rate: float
    total_words_submitted: int
    total_score: int
    average_score: float
    
    # 상세 통계
    longest_word: Optional[str] = None
    longest_word_length: int
    fastest_response_time: Optional[float] = None
    average_response_time: Optional[float] = None
    best_streak: int
    current_streak: int
    
    # 모드별 통계
    mode_statistics: Dict[str, Any] = {}
    
    # 업적 및 배지
    achievements: List[Achievement] = []
    badges: List[Badge] = []
    
    # 설정
    preferred_game_mode: str
    favorite_words: List[str] = []
    
    # 활동 정보
    first_game_at: Optional[datetime] = None
    last_game_at: Optional[datetime] = None
    total_play_time: int = 0  # 초 단위
    
    # 소셜 설정
    is_public: bool
    allow_friend_requests: bool
    
    # 메타 정보
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


# 프로필 생성 요청 (내부용)
class ProfileCreateRequest(BaseModel):
    guest_id: int
    display_name: Optional[str] = None
    bio: Optional[str] = None


# 리더보드 엔트리
class LeaderboardEntry(BaseModel):
    rank: int
    guest_id: int
    nickname: str
    display_name: Optional[str] = None
    level: int
    rank_points: int
    rank_tier: str
    win_rate: float
    total_games_played: int
    avatar_url: Optional[str] = None

    class Config:
        orm_mode = True
        from_attributes = True


# 리더보드 응답
class LeaderboardResponse(BaseModel):
    entries: List[LeaderboardEntry]
    total_players: int
    current_user_rank: Optional[int] = None
    leaderboard_type: str  # "rank_points", "win_rate", "level" 등

    class Config:
        orm_mode = True


# 통계 요약
class StatisticsSummary(BaseModel):
    total_players: int
    active_players_today: int
    total_games_played: int
    average_game_duration: float
    most_popular_mode: str
    top_words: List[Dict[str, Any]]  # 인기 단어들

    class Config:
        orm_mode = True


# 개인 통계 상세
class PersonalStatistics(BaseModel):
    # 기본 통계
    games_this_week: int
    games_this_month: int
    win_streak_this_week: int
    
    # 성과 통계
    recent_achievements: List[Achievement]
    weekly_rank_change: int
    
    # 게임 패턴
    favorite_play_times: List[int]  # 선호하는 플레이 시간대
    most_used_words: List[Dict[str, Any]]
    opponent_win_rates: Dict[str, float]  # 상대별 승률
    
    # 진행률
    achievements_progress: Dict[str, Dict[str, Any]]  # 업적 진행률
    next_level_progress: float  # 다음 레벨까지 진행률

    class Config:
        orm_mode = True


# 프로필 검색 요청
class ProfileSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=50)
    limit: int = Field(default=10, ge=1, le=50)
    filter_by: str = Field(default="all")  # "all", "friends", "high_level" 등

    @validator('query')
    def validate_query(cls, v):
        return v.strip()


# 프로필 검색 결과
class ProfileSearchResult(BaseModel):
    profiles: List[BasicProfileInfo]
    total_count: int
    query: str

    class Config:
        orm_mode = True


# 업적 진행률 정보
class AchievementProgress(BaseModel):
    achievement_id: str
    achievement_name: str
    description: str
    current_progress: int
    required_progress: int
    progress_percentage: float
    is_completed: bool
    category: str

    class Config:
        orm_mode = True


# 업적 목록 응답
class AchievementsResponse(BaseModel):
    completed_achievements: List[Achievement]
    in_progress: List[AchievementProgress]
    total_achievements: int
    completion_rate: float

    class Config:
        orm_mode = True