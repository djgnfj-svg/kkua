from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, Index, ForeignKey
from sqlalchemy.orm import relationship
from db.postgres import Base
from datetime import datetime


class PlayerProfile(Base):
    """
    플레이어 프로필 및 통계 정보를 저장하는 모델
    
    게임 통계, 개인 설정, 배지, 업적 등을 관리합니다.
    """
    __tablename__ = "player_profiles"

    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False, unique=True)
    
    # 기본 프로필 정보
    display_name = Column(String(50), nullable=True)  # 표시명 (닉네임과 별도)
    bio = Column(Text, nullable=True)  # 자기소개
    avatar_url = Column(String(500), nullable=True)  # 아바타 이미지 URL
    banner_url = Column(String(500), nullable=True)  # 배너 이미지 URL
    
    # 게임 통계
    total_games_played = Column(Integer, default=0, nullable=False)
    total_games_won = Column(Integer, default=0, nullable=False)
    total_games_lost = Column(Integer, default=0, nullable=False)
    total_words_submitted = Column(Integer, default=0, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    
    # 상세 통계
    longest_word = Column(String(50), nullable=True)  # 가장 긴 단어
    longest_word_length = Column(Integer, default=0, nullable=False)
    fastest_response_time = Column(Float, nullable=True)  # 가장 빠른 응답 시간 (초)
    average_response_time = Column(Float, nullable=True)  # 평균 응답 시간 (초)
    best_streak = Column(Integer, default=0, nullable=False)  # 최고 연승
    current_streak = Column(Integer, default=0, nullable=False)  # 현재 연승
    
    # 게임 모드별 통계 (JSON)
    mode_statistics = Column(JSON, default=lambda: {}, nullable=False)
    
    # 레벨 시스템
    level = Column(Integer, default=1, nullable=False)
    experience_points = Column(Integer, default=0, nullable=False)
    experience_to_next_level = Column(Integer, default=100, nullable=False)
    
    # 랭킹 정보
    global_rank = Column(Integer, nullable=True)  # 전체 순위
    rank_points = Column(Integer, default=1000, nullable=False)  # 랭킹 포인트 (레이팅)
    peak_rank = Column(Integer, nullable=True)  # 최고 순위
    
    # 업적 및 배지 (JSON 배열)
    achievements = Column(JSON, default=lambda: [], nullable=False)
    badges = Column(JSON, default=lambda: [], nullable=False)
    
    # 개인 설정
    preferred_game_mode = Column(String(50), default="classic", nullable=False)
    favorite_words = Column(JSON, default=lambda: [], nullable=False)  # 즐겨 사용하는 단어들
    
    # 활동 정보
    first_game_at = Column(DateTime, nullable=True)  # 첫 게임 시간
    last_game_at = Column(DateTime, nullable=True)  # 마지막 게임 시간
    total_play_time = Column(Integer, default=0, nullable=False)  # 총 플레이 시간 (초)
    
    # 소셜 정보
    is_public = Column(Boolean, default=True, nullable=False)  # 프로필 공개 여부
    allow_friend_requests = Column(Boolean, default=True, nullable=False)  # 친구 요청 허용
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # 관계 설정
    guest = relationship("Guest", backref="profile")

    # 인덱스 정의
    __table_args__ = (
        Index('idx_player_profile_guest_id', 'guest_id'),
        Index('idx_player_profile_rank_points', 'rank_points'),
        Index('idx_player_profile_global_rank', 'global_rank'),
        Index('idx_player_profile_level', 'level'),
        Index('idx_player_profile_total_games', 'total_games_played'),
        Index('idx_player_profile_updated_at', 'updated_at'),
        Index('idx_player_profile_public', 'is_public'),
    )

    @property
    def win_rate(self) -> float:
        """승률 계산"""
        if self.total_games_played == 0:
            return 0.0
        return (self.total_games_won / self.total_games_played) * 100

    @property
    def average_score(self) -> float:
        """평균 점수 계산"""
        if self.total_games_played == 0:
            return 0.0
        return self.total_score / self.total_games_played

    @property
    def rank_tier(self) -> str:
        """랭킹 티어 반환"""
        if self.rank_points >= 2000:
            return "diamond"
        elif self.rank_points >= 1600:
            return "platinum"
        elif self.rank_points >= 1200:
            return "gold"
        elif self.rank_points >= 800:
            return "silver"
        else:
            return "bronze"

    def add_achievement(self, achievement_id: str, achievement_name: str, earned_at: datetime = None):
        """업적 추가"""
        if earned_at is None:
            earned_at = datetime.utcnow()
        
        achievement = {
            "id": achievement_id,
            "name": achievement_name,
            "earned_at": earned_at.isoformat()
        }
        
        # 중복 확인
        existing_ids = [ach.get("id") for ach in self.achievements]
        if achievement_id not in existing_ids:
            self.achievements.append(achievement)

    def add_badge(self, badge_id: str, badge_name: str, badge_type: str = "general", earned_at: datetime = None):
        """배지 추가"""
        if earned_at is None:
            earned_at = datetime.utcnow()
        
        badge = {
            "id": badge_id,
            "name": badge_name,
            "type": badge_type,
            "earned_at": earned_at.isoformat()
        }
        
        # 중복 확인
        existing_ids = [badge.get("id") for badge in self.badges]
        if badge_id not in existing_ids:
            self.badges.append(badge)

    def update_game_statistics(self, game_result: dict):
        """게임 결과로 통계 업데이트"""
        self.total_games_played += 1
        
        if game_result.get("won", False):
            self.total_games_won += 1
            self.current_streak += 1
            self.best_streak = max(self.best_streak, self.current_streak)
        else:
            self.total_games_lost += 1
            self.current_streak = 0
        
        # 단어 및 점수 통계
        words_count = game_result.get("words_submitted", 0)
        score = game_result.get("score", 0)
        response_time = game_result.get("avg_response_time")
        longest_word = game_result.get("longest_word")
        
        self.total_words_submitted += words_count
        self.total_score += score
        
        # 응답 시간 업데이트
        if response_time:
            if self.fastest_response_time is None or response_time < self.fastest_response_time:
                self.fastest_response_time = response_time
            
            # 평균 응답 시간 계산
            if self.average_response_time is None:
                self.average_response_time = response_time
            else:
                total_time = self.average_response_time * (self.total_games_played - 1) + response_time
                self.average_response_time = total_time / self.total_games_played
        
        # 가장 긴 단어 업데이트
        if longest_word and len(longest_word) > self.longest_word_length:
            self.longest_word = longest_word
            self.longest_word_length = len(longest_word)
        
        # 경험치 및 레벨 업데이트
        exp_gained = self._calculate_experience(game_result)
        self.add_experience(exp_gained)
        
        # 마지막 게임 시간 업데이트
        self.last_game_at = datetime.utcnow()
        if self.first_game_at is None:
            self.first_game_at = self.last_game_at

    def add_experience(self, exp: int):
        """경험치 추가 및 레벨업 처리"""
        self.experience_points += exp
        
        while self.experience_points >= self.experience_to_next_level:
            self.experience_points -= self.experience_to_next_level
            self.level += 1
            self.experience_to_next_level = self._calculate_next_level_exp()

    def _calculate_experience(self, game_result: dict) -> int:
        """게임 결과에 따른 경험치 계산"""
        base_exp = 10  # 기본 경험치
        
        if game_result.get("won", False):
            base_exp += 20  # 승리 보너스
        
        # 점수에 따른 추가 경험치
        score = game_result.get("score", 0)
        score_exp = min(score // 10, 50)  # 점수 10점당 1exp, 최대 50exp
        
        return base_exp + score_exp

    def _calculate_next_level_exp(self) -> int:
        """다음 레벨까지 필요한 경험치 계산"""
        return 100 + (self.level - 1) * 50  # 레벨업마다 50씩 증가

    def __repr__(self):
        return f"<PlayerProfile(guest_id={self.guest_id}, level={self.level}, rank_points={self.rank_points})>"