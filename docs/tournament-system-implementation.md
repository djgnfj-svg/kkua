# 토너먼트 시스템 및 순위 시스템 구현 가이드

## 개요

KKUA에 경쟁적인 토너먼트 시스템과 정교한 순위 시스템을 추가하여 플레이어들의 경쟁 욕구를 자극하고 장기적인 참여를 유도합니다. 다양한 토너먼트 형식과 공정한 ELO 기반 랭킹 시스템을 제공합니다.

## 주요 기능

### 1. 토너먼트 시스템
- **토너먼트 형식**: 단일 탈락제, 더블 탈락제, 라운드 로빈
- **토너먼트 생성**: 사용자 주최 토너먼트
- **자동 매칭**: 브래킷 자동 생성 및 대진표 관리
- **실시간 진행**: 실시간 토너먼트 진행 상황 추적

### 2. 순위 시스템
- **ELO 레이팅**: 공정한 실력 기반 순위
- **시즌 시스템**: 주기적 시즌과 리워드
- **티어 시스템**: 브론즈부터 마스터까지
- **리더보드**: 다양한 카테고리별 순위

### 3. 보상 시스템
- **토너먼트 상금**: 참가비 기반 상금 풀
- **시즌 보상**: 시즌 종료 시 티어별 보상
- **업적 연동**: 토너먼트 관련 특별 업적

---

## 데이터베이스 설계

### 토너먼트 관련 모델

```python
# backend/models/tournament_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.models.base import Base
from datetime import datetime
from enum import Enum

class TournamentFormat(str, Enum):
    SINGLE_ELIMINATION = "single_elimination"
    DOUBLE_ELIMINATION = "double_elimination"
    ROUND_ROBIN = "round_robin"
    SWISS = "swiss"

class TournamentStatus(str, Enum):
    REGISTRATION = "registration"
    WAITING = "waiting"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Tournament(Base):
    __tablename__ = "tournaments"
    
    tournament_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # 토너먼트 설정
    format = Column(SQLEnum(TournamentFormat), default=TournamentFormat.SINGLE_ELIMINATION)
    game_mode = Column(String(30), default="classic")
    max_participants = Column(Integer, nullable=False)
    min_participants = Column(Integer, default=4)
    
    # 참가비 및 상금
    entry_fee = Column(Integer, default=0)  # 가상 화폐
    prize_pool = Column(Integer, default=0)
    prize_distribution = Column(JSON)  # {"1st": 50, "2nd": 30, "3rd": 20}
    
    # 시간 설정
    registration_start = Column(DateTime, default=datetime.utcnow)
    registration_end = Column(DateTime, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    
    # 상태 관리
    status = Column(SQLEnum(TournamentStatus), default=TournamentStatus.REGISTRATION)
    current_round = Column(Integer, default=0)
    
    # 주최자 정보
    created_by = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    is_official = Column(Boolean, default=False)  # 공식 토너먼트 여부
    
    # 설정
    settings = Column(JSON)  # 추가 토너먼트 설정들
    
    # 타임스탬프
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    creator = relationship("Guest", back_populates="created_tournaments")
    participants = relationship("TournamentParticipant", back_populates="tournament")
    matches = relationship("TournamentMatch", back_populates="tournament")
    
    def __repr__(self):
        return f"<Tournament {self.name} ({self.status})>"

class TournamentParticipant(Base):
    __tablename__ = "tournament_participants"
    
    participant_id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.tournament_id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 토너먼트 내 정보
    seed = Column(Integer)  # 시드 번호 (1이 최고 시드)
    current_round = Column(Integer, default=1)
    is_eliminated = Column(Boolean, default=False)
    elimination_round = Column(Integer)
    final_rank = Column(Integer)
    
    # 성과 기록
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    total_score = Column(Integer, default=0)
    
    # 타임스탬프
    registered_at = Column(DateTime, default=datetime.utcnow)
    eliminated_at = Column(DateTime)
    
    # 관계 설정
    tournament = relationship("Tournament", back_populates="participants")
    guest = relationship("Guest")
    
    __table_args__ = (
        {"schema": None}  # 스키마 설정이 필요한 경우
    )

class MatchStatus(str, Enum):
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class TournamentMatch(Base):
    __tablename__ = "tournament_matches"
    
    match_id = Column(Integer, primary_key=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.tournament_id"), nullable=False)
    
    # 대진 정보
    round_number = Column(Integer, nullable=False)
    match_number = Column(Integer, nullable=False)  # 같은 라운드 내 매치 번호
    bracket_position = Column(String(50))  # "WB-1", "LB-2" 등 브래킷 위치
    
    # 참가자 정보
    player1_id = Column(Integer, ForeignKey("guests.guest_id"))
    player2_id = Column(Integer, ForeignKey("guests.guest_id"))
    winner_id = Column(Integer, ForeignKey("guests.guest_id"))
    loser_id = Column(Integer, ForeignKey("guests.guest_id"))
    
    # 게임 연결
    game_room_id = Column(Integer, ForeignKey("gamerooms.room_id"))
    game_log_id = Column(Integer, ForeignKey("game_logs.log_id"))
    
    # 상태 및 결과
    status = Column(SQLEnum(MatchStatus), default=MatchStatus.SCHEDULED)
    player1_score = Column(Integer, default=0)
    player2_score = Column(Integer, default=0)
    
    # 시간 관리
    scheduled_time = Column(DateTime)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # 추가 정보
    notes = Column(Text)  # 관리자 노트
    
    # 관계 설정
    tournament = relationship("Tournament", back_populates="matches")
    player1 = relationship("Guest", foreign_keys=[player1_id])
    player2 = relationship("Guest", foreign_keys=[player2_id])
    winner = relationship("Guest", foreign_keys=[winner_id])
    game_room = relationship("Gameroom")
    
    def __repr__(self):
        return f"<TournamentMatch {self.tournament_id}R{self.round_number}M{self.match_number}>"
```

### 순위 시스템 모델

```python
# backend/models/ranking_model.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.models.base import Base
from datetime import datetime
from enum import Enum

class RankTier(str, Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"
    MASTER = "master"
    GRANDMASTER = "grandmaster"

class Season(Base):
    __tablename__ = "seasons"
    
    season_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # "2024 Spring"
    season_number = Column(Integer, nullable=False)
    
    # 시간 설정
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=False)
    
    # 시즌 설정
    initial_rating = Column(Integer, default=1000)
    rating_decay_rate = Column(Float, default=0.0)  # 주당 감소율
    placement_matches = Column(Integer, default=10)  # 배치고사 경기 수
    
    # 보상 설정
    rewards = Column(JSON)  # 티어별 보상 정보
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Season {self.name}>"

class PlayerRating(Base):
    __tablename__ = "player_ratings"
    
    rating_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.season_id"), nullable=False)
    
    # 현재 레이팅
    current_rating = Column(Integer, default=1000)
    peak_rating = Column(Integer, default=1000)
    
    # 경기 기록
    total_matches = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    
    # 배치고사
    placement_matches_left = Column(Integer, default=10)
    is_placement_completed = Column(Boolean, default=False)
    
    # 연속 기록
    current_win_streak = Column(Integer, default=0)
    current_loss_streak = Column(Integer, default=0)
    best_win_streak = Column(Integer, default=0)
    
    # 통계
    average_score = Column(Float, default=0.0)
    total_score = Column(Integer, default=0)
    
    # 업데이트 시간
    last_match_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    guest = relationship("Guest")
    season = relationship("Season")
    
    # 인덱스
    __table_args__ = (
        Index("idx_player_rating_season", "season_id"),
        Index("idx_player_rating_guest", "guest_id"),
        Index("idx_player_rating_rating", "current_rating"),
        Index("idx_player_rating_combo", "guest_id", "season_id"),
    )
    
    @property
    def tier(self) -> RankTier:
        """현재 레이팅을 기반으로 티어 계산"""
        if self.current_rating >= 2400:
            return RankTier.GRANDMASTER
        elif self.current_rating >= 2000:
            return RankTier.MASTER
        elif self.current_rating >= 1800:
            return RankTier.DIAMOND
        elif self.current_rating >= 1600:
            return RankTier.PLATINUM
        elif self.current_rating >= 1400:
            return RankTier.GOLD
        elif self.current_rating >= 1200:
            return RankTier.SILVER
        else:
            return RankTier.BRONZE
    
    @property
    def win_rate(self) -> float:
        """승률 계산"""
        if self.total_matches == 0:
            return 0.0
        return (self.wins / self.total_matches) * 100

class RatingHistory(Base):
    __tablename__ = "rating_history"
    
    history_id = Column(Integer, primary_key=True)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    season_id = Column(Integer, ForeignKey("seasons.season_id"), nullable=False)
    
    # 레이팅 변화
    rating_before = Column(Integer, nullable=False)
    rating_after = Column(Integer, nullable=False)
    rating_change = Column(Integer, nullable=False)
    
    # 경기 정보
    match_result = Column(String(10))  # "win", "loss", "draw"
    opponent_id = Column(Integer, ForeignKey("guests.guest_id"))
    opponent_rating = Column(Integer)
    
    # 추가 정보
    game_log_id = Column(Integer, ForeignKey("game_logs.log_id"))
    tournament_match_id = Column(Integer, ForeignKey("tournament_matches.match_id"))
    match_type = Column(String(20))  # "ranked", "tournament", "placement"
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    guest = relationship("Guest", foreign_keys=[guest_id])
    opponent = relationship("Guest", foreign_keys=[opponent_id])
    season = relationship("Season")
    
    __table_args__ = (
        Index("idx_rating_history_guest", "guest_id"),
        Index("idx_rating_history_season", "season_id"),
        Index("idx_rating_history_date", "created_at"),
    )

class Leaderboard(Base):
    __tablename__ = "leaderboards"
    
    leaderboard_id = Column(Integer, primary_key=True)
    season_id = Column(Integer, ForeignKey("seasons.season_id"), nullable=False)
    guest_id = Column(Integer, ForeignKey("guests.guest_id"), nullable=False)
    
    # 순위 정보
    rank = Column(Integer, nullable=False)
    tier = Column(SQLEnum(RankTier), nullable=False)
    rating = Column(Integer, nullable=False)
    
    # 통계
    matches_played = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    win_streak = Column(Integer, default=0)
    
    # 스냅샷 시간 (매일 업데이트)
    snapshot_date = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    season = relationship("Season")
    guest = relationship("Guest")
    
    __table_args__ = (
        Index("idx_leaderboard_season_rank", "season_id", "rank"),
        Index("idx_leaderboard_season_tier", "season_id", "tier"),
        Index("idx_leaderboard_date", "snapshot_date"),
    )
```

---

## 백엔드 서비스 구현

### TournamentService 구현

```python
# backend/services/tournament_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from backend.models.tournament_model import (
    Tournament, TournamentParticipant, TournamentMatch, 
    TournamentFormat, TournamentStatus, MatchStatus
)
from backend.models.guest_model import Guest
from backend.services.notification_service import NotificationService
from backend.services.bracket_generator import BracketGenerator
from datetime import datetime, timedelta
import math
import random

class TournamentService:
    """토너먼트 시스템 관리 서비스"""
    
    def __init__(self, db: Session, notification_service: NotificationService):
        self.db = db
        self.notification_service = notification_service
        self.bracket_generator = BracketGenerator()
    
    async def create_tournament(self, creator_id: int, tournament_data: Dict[str, Any]) -> Dict[str, Any]:
        """새 토너먼트 생성"""
        
        # 데이터 검증
        validation_result = self._validate_tournament_data(tournament_data)
        if not validation_result["valid"]:
            return {
                "success": False,
                "message": validation_result["message"],
                "errors": validation_result["errors"]
            }
        
        # 토너먼트 생성
        tournament = Tournament(
            name=tournament_data["name"],
            description=tournament_data.get("description", ""),
            format=TournamentFormat(tournament_data["format"]),
            game_mode=tournament_data.get("game_mode", "classic"),
            max_participants=tournament_data["max_participants"],
            min_participants=tournament_data.get("min_participants", 4),
            entry_fee=tournament_data.get("entry_fee", 0),
            registration_end=tournament_data["registration_end"],
            start_time=tournament_data["start_time"],
            created_by=creator_id,
            settings=tournament_data.get("settings", {})
        )
        
        # 상금 풀 계산
        if tournament.entry_fee > 0:
            tournament.prize_pool = tournament.entry_fee * tournament.max_participants
            tournament.prize_distribution = self._calculate_prize_distribution(
                tournament.format, tournament.max_participants
            )
        
        self.db.add(tournament)
        self.db.commit()
        self.db.refresh(tournament)
        
        # 주최자를 첫 번째 참가자로 자동 등록 (선택사항)
        if tournament_data.get("auto_register_creator", True):
            await self.register_participant(tournament.tournament_id, creator_id)
        
        return {
            "success": True,
            "tournament_id": tournament.tournament_id,
            "message": "토너먼트가 성공적으로 생성되었습니다"
        }
    
    async def register_participant(self, tournament_id: int, guest_id: int) -> Dict[str, Any]:
        """토너먼트 참가 등록"""
        
        tournament = self.db.query(Tournament).filter(
            Tournament.tournament_id == tournament_id
        ).first()
        
        if not tournament:
            return {"success": False, "message": "존재하지 않는 토너먼트입니다"}
        
        # 등록 조건 확인
        validation_result = await self._validate_registration(tournament, guest_id)
        if not validation_result["valid"]:
            return {"success": False, "message": validation_result["message"]}
        
        # 현재 참가자 수 확인
        current_participants = self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id
        ).count()
        
        if current_participants >= tournament.max_participants:
            return {"success": False, "message": "참가자 정원이 가득 찼습니다"}
        
        # 참가자 등록
        participant = TournamentParticipant(
            tournament_id=tournament_id,
            guest_id=guest_id
        )
        
        self.db.add(participant)
        self.db.commit()
        
        # 참가비 차감 (가상 화폐 시스템이 있다면)
        if tournament.entry_fee > 0:
            await self._deduct_entry_fee(guest_id, tournament.entry_fee)
        
        # 정원이 가득 찬 경우 토너먼트 시작 스케줄링
        if current_participants + 1 >= tournament.max_participants:
            await self._schedule_tournament_start(tournament)
        
        return {
            "success": True,
            "message": "토너먼트에 성공적으로 등록되었습니다",
            "participants_count": current_participants + 1,
            "max_participants": tournament.max_participants
        }
    
    async def start_tournament(self, tournament_id: int) -> Dict[str, Any]:
        """토너먼트 시작"""
        
        tournament = self.db.query(Tournament).filter(
            Tournament.tournament_id == tournament_id,
            Tournament.status == TournamentStatus.REGISTRATION
        ).first()
        
        if not tournament:
            return {"success": False, "message": "시작할 수 없는 토너먼트입니다"}
        
        # 최소 참가자 수 확인
        participants = self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament_id
        ).all()
        
        if len(participants) < tournament.min_participants:
            return {
                "success": False,
                "message": f"최소 {tournament.min_participants}명의 참가자가 필요합니다"
            }
        
        # 시드 배정 (레이팅 기반)
        await self._assign_seeds(tournament_id, participants)
        
        # 브래킷 생성
        bracket_result = await self._generate_bracket(tournament, participants)
        if not bracket_result["success"]:
            return bracket_result
        
        # 토너먼트 상태 업데이트
        tournament.status = TournamentStatus.ONGOING
        tournament.current_round = 1
        self.db.commit()
        
        # 첫 라운드 매치 생성
        first_round_matches = await self._create_first_round_matches(tournament, participants)
        
        # 참가자들에게 알림
        await self._notify_tournament_start(tournament_id, participants)
        
        return {
            "success": True,
            "message": "토너먼트가 시작되었습니다",
            "first_round_matches": len(first_round_matches),
            "bracket": bracket_result["bracket"]
        }
    
    async def report_match_result(self, match_id: int, winner_id: int, 
                                game_log_id: Optional[int] = None) -> Dict[str, Any]:
        """매치 결과 보고"""
        
        match = self.db.query(TournamentMatch).filter(
            TournamentMatch.match_id == match_id,
            TournamentMatch.status == MatchStatus.ONGOING
        ).first()
        
        if not match:
            return {"success": False, "message": "유효하지 않은 매치입니다"}
        
        # 승자 검증
        if winner_id not in [match.player1_id, match.player2_id]:
            return {"success": False, "message": "유효하지 않은 승자입니다"}
        
        # 결과 기록
        match.winner_id = winner_id
        match.loser_id = match.player2_id if winner_id == match.player1_id else match.player1_id
        match.status = MatchStatus.COMPLETED
        match.completed_at = datetime.utcnow()
        match.game_log_id = game_log_id
        
        # 참가자 정보 업데이트
        await self._update_participant_stats(match)
        
        # 다음 라운드 진출 처리
        tournament = self.db.query(Tournament).filter(
            Tournament.tournament_id == match.tournament_id
        ).first()
        
        advancement_result = await self._handle_match_advancement(tournament, match)
        
        self.db.commit()
        
        # 토너먼트 완료 확인
        if await self._check_tournament_completion(tournament.tournament_id):
            await self._complete_tournament(tournament.tournament_id)
        
        return {
            "success": True,
            "message": "매치 결과가 기록되었습니다",
            "winner_id": winner_id,
            "advancement": advancement_result
        }
    
    async def get_tournament_bracket(self, tournament_id: int) -> Dict[str, Any]:
        """토너먼트 대진표 조회"""
        
        tournament = self.db.query(Tournament).filter(
            Tournament.tournament_id == tournament_id
        ).first()
        
        if not tournament:
            return {"success": False, "message": "존재하지 않는 토너먼트입니다"}
        
        # 모든 매치 조회
        matches = self.db.query(TournamentMatch).filter(
            TournamentMatch.tournament_id == tournament_id
        ).order_by(TournamentMatch.round_number, TournamentMatch.match_number).all()
        
        # 참가자 정보 조회
        participants = self.db.query(TournamentParticipant, Guest).join(
            Guest, TournamentParticipant.guest_id == Guest.guest_id
        ).filter(
            TournamentParticipant.tournament_id == tournament_id
        ).all()
        
        # 브래킷 구조 생성
        bracket = self._build_bracket_structure(tournament, matches, participants)
        
        return {
            "success": True,
            "tournament": {
                "tournament_id": tournament.tournament_id,
                "name": tournament.name,
                "format": tournament.format,
                "status": tournament.status,
                "current_round": tournament.current_round,
                "total_rounds": self._calculate_total_rounds(tournament.format, len(participants))
            },
            "bracket": bracket,
            "participants": [
                {
                    "participant_id": participant.participant_id,
                    "guest_id": participant.guest_id,
                    "nickname": guest.nickname,
                    "seed": participant.seed,
                    "current_round": participant.current_round,
                    "is_eliminated": participant.is_eliminated,
                    "wins": participant.wins,
                    "losses": participant.losses
                }
                for participant, guest in participants
            ]
        }
    
    async def get_upcoming_matches(self, tournament_id: int) -> List[Dict[str, Any]]:
        """다가오는 매치 목록 조회"""
        
        matches = self.db.query(TournamentMatch, Guest, Guest).join(
            Guest, TournamentMatch.player1_id == Guest.guest_id, isouter=True
        ).join(
            Guest, TournamentMatch.player2_id == Guest.guest_id, isouter=True
        ).filter(
            TournamentMatch.tournament_id == tournament_id,
            TournamentMatch.status.in_([MatchStatus.SCHEDULED, MatchStatus.ONGOING])
        ).order_by(TournamentMatch.scheduled_time).all()
        
        upcoming_matches = []
        for match, player1, player2 in matches:
            match_info = {
                "match_id": match.match_id,
                "round_number": match.round_number,
                "match_number": match.match_number,
                "bracket_position": match.bracket_position,
                "status": match.status,
                "scheduled_time": match.scheduled_time,
                "player1": {
                    "guest_id": player1.guest_id if player1 else None,
                    "nickname": player1.nickname if player1 else "TBD"
                },
                "player2": {
                    "guest_id": player2.guest_id if player2 else None,
                    "nickname": player2.nickname if player2 else "TBD"
                }
            }
            upcoming_matches.append(match_info)
        
        return upcoming_matches
    
    def _validate_tournament_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """토너먼트 데이터 유효성 검사"""
        errors = []
        
        # 필수 필드 확인
        required_fields = ["name", "format", "max_participants", "registration_end", "start_time"]
        for field in required_fields:
            if field not in data:
                errors.append(f"{field}는 필수 필드입니다")
        
        # 참가자 수 검증
        max_participants = data.get("max_participants", 0)
        if max_participants < 4 or max_participants > 64:
            errors.append("참가자 수는 4명 이상 64명 이하여야 합니다")
        
        # 토너먼트 형식별 참가자 수 검증
        format_type = data.get("format")
        if format_type == TournamentFormat.SINGLE_ELIMINATION:
            # 단일 탈락제는 2의 거듭제곱이어야 함
            if max_participants & (max_participants - 1) != 0:
                errors.append("단일 탈락제는 2의 거듭제곱 참가자 수가 필요합니다 (4, 8, 16, 32, 64)")
        
        # 시간 검증
        registration_end = data.get("registration_end")
        start_time = data.get("start_time")
        if registration_end and start_time:
            if registration_end >= start_time:
                errors.append("등록 마감 시간은 시작 시간보다 빨라야 합니다")
            
            if registration_end <= datetime.utcnow():
                errors.append("등록 마감 시간은 현재 시간보다 늦어야 합니다")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "message": errors[0] if errors else "유효한 토너먼트 데이터입니다"
        }
    
    async def _validate_registration(self, tournament: Tournament, guest_id: int) -> Dict[str, Any]:
        """참가 등록 유효성 검사"""
        
        # 등록 기간 확인
        if tournament.status != TournamentStatus.REGISTRATION:
            return {"valid": False, "message": "등록 기간이 아닙니다"}
        
        if datetime.utcnow() > tournament.registration_end:
            return {"valid": False, "message": "등록 기간이 종료되었습니다"}
        
        # 중복 참가 확인
        existing_participant = self.db.query(TournamentParticipant).filter(
            TournamentParticipant.tournament_id == tournament.tournament_id,
            TournamentParticipant.guest_id == guest_id
        ).first()
        
        if existing_participant:
            return {"valid": False, "message": "이미 등록된 토너먼트입니다"}
        
        # 참가비 확인 (가상 화폐 시스템이 있다면)
        if tournament.entry_fee > 0:
            if not await self._check_balance(guest_id, tournament.entry_fee):
                return {"valid": False, "message": "참가비가 부족합니다"}
        
        return {"valid": True, "message": "등록 가능합니다"}
    
    def _calculate_prize_distribution(self, format_type: TournamentFormat, 
                                   max_participants: int) -> Dict[str, int]:
        """상금 분배 계산"""
        
        if format_type == TournamentFormat.SINGLE_ELIMINATION:
            return {
                "1st": 50,  # 1위 50%
                "2nd": 30,  # 2위 30%
                "3rd": 20   # 3위 20%
            }
        elif format_type == TournamentFormat.DOUBLE_ELIMINATION:
            return {
                "1st": 45,  # 1위 45%
                "2nd": 25,  # 2위 25%
                "3rd": 15,  # 3위 15%
                "4th": 15   # 4위 15%
            }
        else:  # ROUND_ROBIN
            # 참가자 수에 따라 상위 순위에게 분배
            top_positions = min(max_participants // 2, 8)
            percentage_per_position = 100 // top_positions
            
            distribution = {}
            for i in range(1, top_positions + 1):
                distribution[f"{i}{'st' if i == 1 else 'nd' if i == 2 else 'rd' if i == 3 else 'th'}"] = percentage_per_position
            
            return distribution
    
    async def _assign_seeds(self, tournament_id: int, participants: List[TournamentParticipant]):
        """시드 배정 (레이팅 기반)"""
        
        # 각 참가자의 현재 레이팅 조회
        participant_ratings = []
        for participant in participants:
            rating = await self._get_player_current_rating(participant.guest_id)
            participant_ratings.append((participant, rating))
        
        # 레이팅 순으로 정렬 (높은 순)
        participant_ratings.sort(key=lambda x: x[1], reverse=True)
        
        # 시드 배정
        for seed, (participant, rating) in enumerate(participant_ratings, 1):
            participant.seed = seed
        
        self.db.commit()
    
    async def _generate_bracket(self, tournament: Tournament, 
                              participants: List[TournamentParticipant]) -> Dict[str, Any]:
        """브래킷 생성"""
        
        try:
            if tournament.format == TournamentFormat.SINGLE_ELIMINATION:
                bracket = self.bracket_generator.generate_single_elimination(participants)
            elif tournament.format == TournamentFormat.DOUBLE_ELIMINATION:
                bracket = self.bracket_generator.generate_double_elimination(participants)
            elif tournament.format == TournamentFormat.ROUND_ROBIN:
                bracket = self.bracket_generator.generate_round_robin(participants)
            else:
                return {"success": False, "message": "지원하지 않는 토너먼트 형식입니다"}
            
            return {"success": True, "bracket": bracket}
            
        except Exception as e:
            return {"success": False, "message": f"브래킷 생성 실패: {str(e)}"}
    
    def _calculate_total_rounds(self, format_type: TournamentFormat, participant_count: int) -> int:
        """총 라운드 수 계산"""
        
        if format_type == TournamentFormat.SINGLE_ELIMINATION:
            return math.ceil(math.log2(participant_count))
        elif format_type == TournamentFormat.DOUBLE_ELIMINATION:
            # 더블 엘리미네이션은 복잡하지만 대략 2 * log2(n) - 1
            return 2 * math.ceil(math.log2(participant_count)) - 1
        elif format_type == TournamentFormat.ROUND_ROBIN:
            # 라운드 로빈은 (n-1) 라운드
            return participant_count - 1
        
        return 1
```

### RankingService 구현

```python
# backend/services/ranking_service.py
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from backend.models.ranking_model import (
    Season, PlayerRating, RatingHistory, Leaderboard, RankTier
)
from backend.models.guest_model import Guest
from datetime import datetime, timedelta
import math

class RankingService:
    """순위 시스템 관리 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.k_factor = 32  # ELO K-factor
        self.initial_rating = 1000
        self.rating_floor = 100  # 최소 레이팅
    
    async def get_or_create_current_season(self) -> Season:
        """현재 시즌 조회 또는 생성"""
        current_season = self.db.query(Season).filter(
            Season.is_active == True
        ).first()
        
        if not current_season:
            # 새 시즌 생성
            current_season = Season(
                name=f"Season {datetime.now().year}",
                season_number=1,
                start_date=datetime.now().replace(day=1),
                end_date=datetime.now().replace(month=12, day=31),
                is_active=True
            )
            self.db.add(current_season)
            self.db.commit()
            self.db.refresh(current_season)
        
        return current_season
    
    async def get_player_rating(self, guest_id: int, season_id: Optional[int] = None) -> PlayerRating:
        """플레이어 레이팅 조회 또는 생성"""
        
        if not season_id:
            current_season = await self.get_or_create_current_season()
            season_id = current_season.season_id
        
        rating = self.db.query(PlayerRating).filter(
            PlayerRating.guest_id == guest_id,
            PlayerRating.season_id == season_id
        ).first()
        
        if not rating:
            rating = PlayerRating(
                guest_id=guest_id,
                season_id=season_id,
                current_rating=self.initial_rating,
                peak_rating=self.initial_rating
            )
            self.db.add(rating)
            self.db.commit()
            self.db.refresh(rating)
        
        return rating
    
    async def calculate_rating_change(self, winner_id: int, loser_id: int, 
                                    winner_score: int, loser_score: int) -> Dict[str, Any]:
        """ELO 레이팅 변화 계산"""
        
        winner_rating = await self.get_player_rating(winner_id)
        loser_rating = await self.get_player_rating(loser_id)
        
        # 기본 ELO 계산
        expected_winner = self._calculate_expected_score(
            winner_rating.current_rating, loser_rating.current_rating
        )
        expected_loser = 1 - expected_winner
        
        # 실제 결과 (승부의 경우 1-0, 점수차가 클 경우 가중치 적용)
        actual_winner = 1.0
        actual_loser = 0.0
        
        # 점수차에 따른 가중치 (선택적)
        score_multiplier = self._calculate_score_multiplier(winner_score, loser_score)
        
        # K-factor 조정 (경기 수, 레이팅에 따라)
        winner_k = self._calculate_k_factor(winner_rating)
        loser_k = self._calculate_k_factor(loser_rating)
        
        # 레이팅 변화 계산
        winner_change = int(winner_k * score_multiplier * (actual_winner - expected_winner))
        loser_change = int(loser_k * score_multiplier * (actual_loser - expected_loser))
        
        # 최소 레이팅 보장
        new_loser_rating = max(
            self.rating_floor, 
            loser_rating.current_rating + loser_change
        )
        
        # 실제 패자 변화량 재조정 (최소 레이팅에 걸린 경우)
        if new_loser_rating == self.rating_floor:
            loser_change = self.rating_floor - loser_rating.current_rating
        
        return {
            "winner": {
                "player_id": winner_id,
                "rating_before": winner_rating.current_rating,
                "rating_change": winner_change,
                "rating_after": winner_rating.current_rating + winner_change
            },
            "loser": {
                "player_id": loser_id,
                "rating_before": loser_rating.current_rating,
                "rating_change": loser_change,
                "rating_after": new_loser_rating
            },
            "expected_scores": {
                "winner": expected_winner,
                "loser": expected_loser
            }
        }
    
    async def update_ratings_after_match(self, winner_id: int, loser_id: int, 
                                       winner_score: int, loser_score: int,
                                       match_type: str = "ranked",
                                       game_log_id: Optional[int] = None) -> Dict[str, Any]:
        """경기 후 레이팅 업데이트"""
        
        # 레이팅 변화 계산
        rating_changes = await self.calculate_rating_change(
            winner_id, loser_id, winner_score, loser_score
        )
        
        current_season = await self.get_or_create_current_season()
        
        # 승자 레이팅 업데이트
        winner_rating = await self.get_player_rating(winner_id, current_season.season_id)
        winner_new_rating = rating_changes["winner"]["rating_after"]
        
        winner_rating.current_rating = winner_new_rating
        if winner_new_rating > winner_rating.peak_rating:
            winner_rating.peak_rating = winner_new_rating
        
        winner_rating.total_matches += 1
        winner_rating.wins += 1
        winner_rating.current_win_streak += 1
        winner_rating.current_loss_streak = 0
        
        if winner_rating.current_win_streak > winner_rating.best_win_streak:
            winner_rating.best_win_streak = winner_rating.current_win_streak
        
        # 배치고사 처리
        if winner_rating.placement_matches_left > 0:
            winner_rating.placement_matches_left -= 1
            if winner_rating.placement_matches_left == 0:
                winner_rating.is_placement_completed = True
        
        winner_rating.last_match_at = datetime.utcnow()
        
        # 패자 레이팅 업데이트
        loser_rating = await self.get_player_rating(loser_id, current_season.season_id)
        loser_new_rating = rating_changes["loser"]["rating_after"]
        
        loser_rating.current_rating = loser_new_rating
        loser_rating.total_matches += 1
        loser_rating.losses += 1
        loser_rating.current_loss_streak += 1
        loser_rating.current_win_streak = 0
        
        # 배치고사 처리
        if loser_rating.placement_matches_left > 0:
            loser_rating.placement_matches_left -= 1
            if loser_rating.placement_matches_left == 0:
                loser_rating.is_placement_completed = True
        
        loser_rating.last_match_at = datetime.utcnow()
        
        # 히스토리 기록
        winner_history = RatingHistory(
            guest_id=winner_id,
            season_id=current_season.season_id,
            rating_before=rating_changes["winner"]["rating_before"],
            rating_after=winner_new_rating,
            rating_change=rating_changes["winner"]["rating_change"],
            match_result="win",
            opponent_id=loser_id,
            opponent_rating=rating_changes["loser"]["rating_before"],
            game_log_id=game_log_id,
            match_type=match_type
        )
        
        loser_history = RatingHistory(
            guest_id=loser_id,
            season_id=current_season.season_id,
            rating_before=rating_changes["loser"]["rating_before"],
            rating_after=loser_new_rating,
            rating_change=rating_changes["loser"]["rating_change"],
            match_result="loss",
            opponent_id=winner_id,
            opponent_rating=rating_changes["winner"]["rating_before"],
            game_log_id=game_log_id,
            match_type=match_type
        )
        
        self.db.add_all([winner_history, loser_history])
        self.db.commit()
        
        return {
            "success": True,
            "rating_changes": rating_changes,
            "winner_tier_change": self._check_tier_change(
                rating_changes["winner"]["rating_before"],
                winner_new_rating
            ),
            "loser_tier_change": self._check_tier_change(
                rating_changes["loser"]["rating_before"],
                loser_new_rating
            )
        }
    
    async def get_leaderboard(self, season_id: Optional[int] = None, 
                            tier: Optional[RankTier] = None,
                            limit: int = 100) -> List[Dict[str, Any]]:
        """리더보드 조회"""
        
        if not season_id:
            current_season = await self.get_or_create_current_season()
            season_id = current_season.season_id
        
        query = self.db.query(PlayerRating, Guest).join(
            Guest, PlayerRating.guest_id == Guest.guest_id
        ).filter(
            PlayerRating.season_id == season_id,
            PlayerRating.is_placement_completed == True  # 배치고사 완료자만
        )
        
        if tier:
            tier_ranges = self._get_tier_rating_ranges()
            min_rating, max_rating = tier_ranges[tier]
            query = query.filter(
                PlayerRating.current_rating >= min_rating,
                PlayerRating.current_rating <= max_rating
            )
        
        results = query.order_by(
            desc(PlayerRating.current_rating)
        ).limit(limit).all()
        
        leaderboard = []
        for rank, (rating, guest) in enumerate(results, 1):
            entry = {
                "rank": rank,
                "guest_id": guest.guest_id,
                "nickname": guest.nickname,
                "rating": rating.current_rating,
                "tier": rating.tier.value,
                "peak_rating": rating.peak_rating,
                "total_matches": rating.total_matches,
                "wins": rating.wins,
                "losses": rating.losses,
                "win_rate": rating.win_rate,
                "win_streak": rating.current_win_streak,
                "last_match": rating.last_match_at
            }
            leaderboard.append(entry)
        
        return leaderboard
    
    async def get_player_rank(self, guest_id: int, season_id: Optional[int] = None) -> Dict[str, Any]:
        """플레이어 순위 조회"""
        
        if not season_id:
            current_season = await self.get_or_create_current_season()
            season_id = current_season.season_id
        
        player_rating = await self.get_player_rating(guest_id, season_id)
        
        # 더 높은 레이팅을 가진 플레이어 수 + 1 = 순위
        higher_rated_count = self.db.query(PlayerRating).filter(
            PlayerRating.season_id == season_id,
            PlayerRating.current_rating > player_rating.current_rating,
            PlayerRating.is_placement_completed == True
        ).count()
        
        rank = higher_rated_count + 1
        
        # 같은 티어 내 순위
        tier_rank = self.db.query(PlayerRating).filter(
            PlayerRating.season_id == season_id,
            PlayerRating.current_rating > player_rating.current_rating,
            PlayerRating.is_placement_completed == True,
            PlayerRating.current_rating >= self._get_tier_min_rating(player_rating.tier),
            PlayerRating.current_rating <= self._get_tier_max_rating(player_rating.tier)
        ).count() + 1
        
        return {
            "guest_id": guest_id,
            "overall_rank": rank,
            "tier_rank": tier_rank,
            "tier": player_rating.tier.value,
            "rating": player_rating.current_rating,
            "peak_rating": player_rating.peak_rating,
            "total_matches": player_rating.total_matches,
            "win_rate": player_rating.win_rate,
            "placement_completed": player_rating.is_placement_completed,
            "placement_matches_left": player_rating.placement_matches_left
        }
    
    def _calculate_expected_score(self, rating_a: int, rating_b: int) -> float:
        """ELO 기대 점수 계산"""
        return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    
    def _calculate_k_factor(self, player_rating: PlayerRating) -> int:
        """K-factor 계산 (경기 수와 레이팅에 따라 조정)"""
        
        base_k = self.k_factor
        
        # 신규 플레이어는 더 큰 K-factor
        if player_rating.total_matches < 10:
            return base_k * 2
        elif player_rating.total_matches < 30:
            return int(base_k * 1.5)
        
        # 고레이팅 플레이어는 더 작은 K-factor
        if player_rating.current_rating >= 2000:
            return int(base_k * 0.8)
        elif player_rating.current_rating >= 1800:
            return int(base_k * 0.9)
        
        return base_k
    
    def _calculate_score_multiplier(self, winner_score: int, loser_score: int) -> float:
        """점수차에 따른 가중치 계산"""
        
        if loser_score == 0:
            return 1.2  # 완승 시 추가 보너스
        
        score_ratio = winner_score / (winner_score + loser_score)
        
        if score_ratio >= 0.8:
            return 1.1  # 압도적 승리
        elif score_ratio >= 0.6:
            return 1.0  # 일반적 승리
        else:
            return 0.9  # 근소한 승리
    
    def _check_tier_change(self, old_rating: int, new_rating: int) -> Optional[Dict[str, str]]:
        """티어 변화 확인"""
        
        old_tier = self._rating_to_tier(old_rating)
        new_tier = self._rating_to_tier(new_rating)
        
        if old_tier != new_tier:
            return {
                "from": old_tier.value,
                "to": new_tier.value,
                "type": "promotion" if new_rating > old_rating else "demotion"
            }
        
        return None
    
    def _rating_to_tier(self, rating: int) -> RankTier:
        """레이팅을 티어로 변환"""
        if rating >= 2400:
            return RankTier.GRANDMASTER
        elif rating >= 2000:
            return RankTier.MASTER
        elif rating >= 1800:
            return RankTier.DIAMOND
        elif rating >= 1600:
            return RankTier.PLATINUM
        elif rating >= 1400:
            return RankTier.GOLD
        elif rating >= 1200:
            return RankTier.SILVER
        else:
            return RankTier.BRONZE
```

---

## 프론트엔드 구현

### TournamentBracket 컴포넌트

```javascript
// frontend/src/Pages/Tournament/components/TournamentBracket.js
import React, { useState, useEffect } from 'react';
import { getTournamentBracket } from '../../../Api/tournamentApi';

const TournamentBracket = ({ tournamentId }) => {
    const [bracket, setBracket] = useState(null);
    const [tournament, setTournament] = useState(null);
    const [loading, setLoading] = useState(true);
    const [selectedMatch, setSelectedMatch] = useState(null);

    useEffect(() => {
        loadBracket();
    }, [tournamentId]);

    const loadBracket = async () => {
        try {
            const response = await getTournamentBracket(tournamentId);
            setBracket(response.data.bracket);
            setTournament(response.data.tournament);
        } catch (error) {
            console.error('브래킷 로드 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    const getMatchStatusColor = (status) => {
        const colors = {
            'scheduled': 'border-gray-300 bg-gray-50',
            'ongoing': 'border-blue-500 bg-blue-50',
            'completed': 'border-green-500 bg-green-50',
            'cancelled': 'border-red-500 bg-red-50'
        };
        return colors[status] || 'border-gray-300 bg-white';
    };

    const renderMatch = (match, roundIndex, matchIndex) => {
        const isCompleted = match.status === 'completed';
        const isOngoing = match.status === 'ongoing';
        
        return (
            <div
                key={`${roundIndex}-${matchIndex}`}
                className={`
                    border-2 rounded-lg p-3 mb-4 cursor-pointer transition-all duration-200
                    hover:shadow-md ${getMatchStatusColor(match.status)}
                    ${selectedMatch?.match_id === match.match_id ? 'ring-2 ring-blue-400' : ''}
                `}
                onClick={() => setSelectedMatch(match)}
            >
                {/* 매치 헤더 */}
                <div className="flex justify-between items-center mb-2">
                    <span className="text-xs font-medium text-gray-600">
                        R{match.round_number}M{match.match_number}
                    </span>
                    <span className={`
                        text-xs px-2 py-1 rounded
                        ${isCompleted ? 'bg-green-100 text-green-800' : 
                          isOngoing ? 'bg-blue-100 text-blue-800' : 
                          'bg-gray-100 text-gray-600'}
                    `}>
                        {match.status === 'completed' ? '완료' :
                         match.status === 'ongoing' ? '진행중' :
                         match.status === 'scheduled' ? '예정' : '취소'}
                    </span>
                </div>

                {/* 플레이어들 */}
                <div className="space-y-2">
                    <div className={`
                        flex justify-between items-center p-2 rounded
                        ${isCompleted && match.winner_id === match.player1?.guest_id ? 
                          'bg-yellow-100 border border-yellow-300' : 'bg-white'}
                    `}>
                        <span className="font-medium">
                            {match.player1?.nickname || 'TBD'}
                        </span>
                        {isCompleted && (
                            <span className="text-sm font-bold">
                                {match.player1_score || 0}
                            </span>
                        )}
                    </div>
                    
                    <div className="text-center text-xs text-gray-400">vs</div>
                    
                    <div className={`
                        flex justify-between items-center p-2 rounded
                        ${isCompleted && match.winner_id === match.player2?.guest_id ? 
                          'bg-yellow-100 border border-yellow-300' : 'bg-white'}
                    `}>
                        <span className="font-medium">
                            {match.player2?.nickname || 'TBD'}
                        </span>
                        {isCompleted && (
                            <span className="text-sm font-bold">
                                {match.player2_score || 0}
                            </span>
                        )}
                    </div>
                </div>

                {/* 예정 시간 */}
                {match.scheduled_time && !isCompleted && (
                    <div className="mt-2 text-xs text-gray-500 text-center">
                        {new Date(match.scheduled_time).toLocaleString('ko-KR')}
                    </div>
                )}
            </div>
        );
    };

    const renderRound = (rounds, roundIndex) => {
        const roundMatches = rounds[roundIndex] || [];
        
        return (
            <div key={roundIndex} className="flex-shrink-0 mx-4">
                <h3 className="text-center font-bold text-gray-700 mb-4">
                    {tournament?.format === 'single_elimination' ? (
                        roundIndex === rounds.length - 1 ? '결승' :
                        roundIndex === rounds.length - 2 ? '준결승' :
                        roundIndex === rounds.length - 3 ? '8강' :
                        `${Math.pow(2, rounds.length - roundIndex)}강`
                    ) : (
                        `라운드 ${roundIndex + 1}`
                    )}
                </h3>
                
                <div className="min-w-64">
                    {roundMatches.map((match, matchIndex) => 
                        renderMatch(match, roundIndex, matchIndex)
                    )}
                </div>
            </div>
        );
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            </div>
        );
    }

    if (!bracket || !tournament) {
        return (
            <div className="text-center text-gray-500 py-12">
                브래킷 정보를 불러올 수 없습니다.
            </div>
        );
    }

    return (
        <div className="tournament-bracket">
            {/* 토너먼트 정보 헤더 */}
            <div className="mb-6 p-4 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg">
                <h1 className="text-2xl font-bold">{tournament.name}</h1>
                <div className="mt-2 flex items-center space-x-4 text-sm">
                    <span>형식: {tournament.format}</span>
                    <span>현재 라운드: {tournament.current_round}</span>
                    <span>상태: {tournament.status}</span>
                </div>
            </div>

            {/* 브래킷 뷰 */}
            <div className="bracket-container overflow-x-auto">
                <div className="flex items-start min-w-max py-4">
                    {bracket.rounds?.map((round, index) => renderRound(bracket.rounds, index))}
                </div>
            </div>

            {/* 매치 상세 정보 모달 */}
            {selectedMatch && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-bold">
                                매치 상세 정보
                            </h3>
                            <button
                                onClick={() => setSelectedMatch(null)}
                                className="text-gray-500 hover:text-gray-700"
                            >
                                ✕
                            </button>
                        </div>
                        
                        <div className="space-y-4">
                            <div>
                                <span className="text-sm text-gray-600">라운드: </span>
                                <span className="font-medium">{selectedMatch.round_number}</span>
                            </div>
                            
                            <div>
                                <span className="text-sm text-gray-600">상태: </span>
                                <span className="font-medium">{selectedMatch.status}</span>
                            </div>
                            
                            {selectedMatch.scheduled_time && (
                                <div>
                                    <span className="text-sm text-gray-600">예정 시간: </span>
                                    <span className="font-medium">
                                        {new Date(selectedMatch.scheduled_time).toLocaleString('ko-KR')}
                                    </span>
                                </div>
                            )}
                            
                            <div className="pt-4 border-t">
                                <div className="flex justify-between items-center mb-2">
                                    <span>{selectedMatch.player1?.nickname || 'TBD'}</span>
                                    {selectedMatch.status === 'completed' && (
                                        <span className="font-bold">{selectedMatch.player1_score}</span>
                                    )}
                                </div>
                                
                                <div className="flex justify-between items-center">
                                    <span>{selectedMatch.player2?.nickname || 'TBD'}</span>
                                    {selectedMatch.status === 'completed' && (
                                        <span className="font-bold">{selectedMatch.player2_score}</span>
                                    )}
                                </div>
                            </div>
                            
                            {selectedMatch.status === 'completed' && selectedMatch.winner_id && (
                                <div className="text-center p-3 bg-yellow-100 rounded-lg">
                                    <span className="text-yellow-800 font-bold">
                                        승자: {selectedMatch.winner_id === selectedMatch.player1?.guest_id ? 
                                               selectedMatch.player1?.nickname : 
                                               selectedMatch.player2?.nickname}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TournamentBracket;
```

---

## 구현 우선순위

### Phase 1 (2주차): 기본 토너먼트 시스템
1. **데이터베이스 모델** - Tournament, TournamentParticipant, TournamentMatch
2. **토너먼트 생성/등록** - 기본 CRUD 기능
3. **단일 탈락제 브래킷** - 가장 기본적인 형식
4. **매치 진행** - 결과 입력 및 다음 라운드 진출

### Phase 2 (1주차): 순위 시스템
1. **ELO 레이팅 시스템** - 기본 레이팅 계산
2. **시즌 시스템** - 시즌 관리 및 리더보드
3. **티어 시스템** - 티어 분류 및 표시

### Phase 3 (1주차): 고급 기능
1. **더블 탈락제/라운드 로빈** - 추가 토너먼트 형식
2. **자동 매칭** - 레이팅 기반 자동 대진 생성
3. **보상 시스템** - 상금 분배 및 시즌 보상

이 가이드를 통해 KKUA에 완전한 경쟁 시스템을 구축하여 플레이어들의 장기적인 참여와 경쟁 의식을 높일 수 있습니다.