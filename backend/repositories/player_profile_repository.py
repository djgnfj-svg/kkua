from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta

from models.player_profile_model import PlayerProfile
from models.guest_model import Guest


class PlayerProfileRepository:
    """플레이어 프로필 데이터 접근 계층"""
    
    def __init__(self, db: Session):
        self.db = db

    def create_profile(self, guest_id: int, **kwargs) -> PlayerProfile:
        """새 플레이어 프로필을 생성합니다."""
        profile = PlayerProfile(guest_id=guest_id, **kwargs)
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def find_by_guest_id(self, guest_id: int) -> Optional[PlayerProfile]:
        """게스트 ID로 프로필을 조회합니다."""
        return self.db.query(PlayerProfile).options(
            joinedload(PlayerProfile.guest)
        ).filter(PlayerProfile.guest_id == guest_id).first()

    def find_by_id(self, profile_id: int) -> Optional[PlayerProfile]:
        """프로필 ID로 조회합니다."""
        return self.db.query(PlayerProfile).options(
            joinedload(PlayerProfile.guest)
        ).filter(PlayerProfile.profile_id == profile_id).first()

    def update_profile(self, guest_id: int, data: Dict[str, Any]) -> Optional[PlayerProfile]:
        """프로필 정보를 업데이트합니다."""
        profile = self.find_by_guest_id(guest_id)
        if profile:
            for key, value in data.items():
                if hasattr(profile, key) and value is not None:
                    setattr(profile, key, value)
            profile.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def get_or_create_profile(self, guest_id: int) -> PlayerProfile:
        """프로필을 조회하거나 없으면 생성합니다."""
        profile = self.find_by_guest_id(guest_id)
        if not profile:
            profile = self.create_profile(guest_id)
        return profile

    def get_leaderboard(
        self, 
        order_by: str = "rank_points", 
        limit: int = 50, 
        offset: int = 0,
        public_only: bool = True
    ) -> Tuple[List[PlayerProfile], int]:
        """리더보드를 조회합니다."""
        query = self.db.query(PlayerProfile).options(
            joinedload(PlayerProfile.guest)
        )
        
        if public_only:
            query = query.filter(PlayerProfile.is_public == True)
        
        # 정렬 기준 설정
        if order_by == "rank_points":
            query = query.order_by(desc(PlayerProfile.rank_points))
        elif order_by == "level":
            query = query.order_by(desc(PlayerProfile.level), desc(PlayerProfile.experience_points))
        elif order_by == "win_rate":
            # 최소 10게임 이상 플레이한 사용자만
            query = query.filter(PlayerProfile.total_games_played >= 10)
            query = query.order_by(
                desc(func.cast(PlayerProfile.total_games_won, func.Float) / PlayerProfile.total_games_played)
            )
        elif order_by == "total_games":
            query = query.order_by(desc(PlayerProfile.total_games_played))
        else:
            query = query.order_by(desc(PlayerProfile.rank_points))
        
        total = query.count()
        profiles = query.offset(offset).limit(limit).all()
        
        return profiles, total

    def search_profiles(
        self, 
        search_term: str, 
        limit: int = 10, 
        filter_by: str = "all"
    ) -> List[PlayerProfile]:
        """프로필을 검색합니다."""
        query = self.db.query(PlayerProfile).options(
            joinedload(PlayerProfile.guest)
        ).filter(PlayerProfile.is_public == True)
        
        # 닉네임 또는 표시명으로 검색
        search_filter = or_(
            PlayerProfile.guest.has(Guest.nickname.ilike(f'%{search_term}%')),
            PlayerProfile.display_name.ilike(f'%{search_term}%')
        )
        query = query.filter(search_filter)
        
        # 필터 적용
        if filter_by == "high_level":
            query = query.filter(PlayerProfile.level >= 10)
        elif filter_by == "active":
            # 최근 7일 내 활동
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(PlayerProfile.last_game_at >= week_ago)
        
        return query.order_by(desc(PlayerProfile.level)).limit(limit).all()

    def get_rank_by_guest_id(self, guest_id: int, order_by: str = "rank_points") -> Optional[int]:
        """특정 사용자의 순위를 조회합니다."""
        profile = self.find_by_guest_id(guest_id)
        if not profile:
            return None
        
        # 해당 사용자보다 높은 순위의 사용자 수를 계산
        query = self.db.query(PlayerProfile).filter(PlayerProfile.is_public == True)
        
        if order_by == "rank_points":
            rank = query.filter(PlayerProfile.rank_points > profile.rank_points).count() + 1
        elif order_by == "level":
            rank = query.filter(
                or_(
                    PlayerProfile.level > profile.level,
                    and_(
                        PlayerProfile.level == profile.level,
                        PlayerProfile.experience_points > profile.experience_points
                    )
                )
            ).count() + 1
        elif order_by == "win_rate":
            if profile.total_games_played < 10:
                return None
            profile_win_rate = profile.total_games_won / profile.total_games_played
            rank = query.filter(
                PlayerProfile.total_games_played >= 10,
                func.cast(PlayerProfile.total_games_won, func.Float) / PlayerProfile.total_games_played > profile_win_rate
            ).count() + 1
        else:
            rank = query.filter(PlayerProfile.rank_points > profile.rank_points).count() + 1
        
        return rank

    def update_global_ranks(self):
        """모든 사용자의 global_rank를 업데이트합니다."""
        # 랭크 포인트 순으로 순위 업데이트
        profiles = self.db.query(PlayerProfile).filter(
            PlayerProfile.is_public == True
        ).order_by(desc(PlayerProfile.rank_points)).all()
        
        for i, profile in enumerate(profiles, 1):
            profile.global_rank = i
            # 최고 순위 업데이트
            if profile.peak_rank is None or i < profile.peak_rank:
                profile.peak_rank = i
        
        self.db.commit()

    def get_statistics_summary(self) -> Dict[str, Any]:
        """전체 통계 요약을 조회합니다."""
        total_players = self.db.query(PlayerProfile).count()
        
        # 오늘 활동한 플레이어 수
        today = datetime.utcnow().date()
        active_today = self.db.query(PlayerProfile).filter(
            func.date(PlayerProfile.last_game_at) == today
        ).count()
        
        # 총 게임 수
        total_games = self.db.query(func.sum(PlayerProfile.total_games_played)).scalar() or 0
        
        # 평균 게임 시간 (추정)
        avg_play_time = self.db.query(func.avg(PlayerProfile.total_play_time)).scalar() or 0
        avg_games = self.db.query(func.avg(PlayerProfile.total_games_played)).scalar() or 1
        avg_game_duration = avg_play_time / avg_games if avg_games > 0 else 0
        
        return {
            "total_players": total_players,
            "active_players_today": active_today,
            "total_games_played": total_games,
            "average_game_duration": avg_game_duration,
            "most_popular_mode": "classic"  # TODO: 실제 통계로 계산
        }

    def get_recent_achievements(self, guest_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """최근 획득한 업적을 조회합니다."""
        profile = self.find_by_guest_id(guest_id)
        if not profile or not profile.achievements:
            return []
        
        # 업적을 날짜순으로 정렬하고 최근 것들을 반환
        achievements = sorted(
            profile.achievements,
            key=lambda x: datetime.fromisoformat(x.get("earned_at", "1970-01-01")),
            reverse=True
        )
        
        return achievements[:limit]

    def update_game_statistics(self, guest_id: int, game_result: Dict[str, Any]) -> PlayerProfile:
        """게임 결과로 플레이어 통계를 업데이트합니다."""
        profile = self.get_or_create_profile(guest_id)
        profile.update_game_statistics(game_result)
        
        # 플레이 시간 업데이트 (게임 시간 추가)
        game_duration = game_result.get("duration", 0)  # 초 단위
        profile.total_play_time += game_duration
        
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def get_top_players_by_mode(self, mode_name: str, limit: int = 10) -> List[PlayerProfile]:
        """특정 게임 모드에서 최고 성과를 낸 플레이어들을 조회합니다."""
        # JSON 컬럼에서 특정 모드 통계를 기준으로 정렬
        # PostgreSQL JSON 연산자 사용
        query = self.db.query(PlayerProfile).filter(
            PlayerProfile.is_public == True,
            PlayerProfile.mode_statistics.op('->')(mode_name).isnot(None)
        ).order_by(
            desc(PlayerProfile.mode_statistics.op('->>')(f'{mode_name}.best_score').cast(func.Integer))
        ).limit(limit)
        
        return query.all()

    def calculate_weekly_stats(self, guest_id: int) -> Dict[str, Any]:
        """주간 통계를 계산합니다."""
        # 이 기능은 게임 로그 테이블과 연동하여 구현해야 함
        # 현재는 기본값 반환
        return {
            "games_this_week": 0,
            "win_streak_this_week": 0,
            "weekly_rank_change": 0
        }

    def delete_profile(self, guest_id: int) -> bool:
        """프로필을 삭제합니다."""
        profile = self.find_by_guest_id(guest_id)
        if profile:
            self.db.delete(profile)
            self.db.commit()
            return True
        return False