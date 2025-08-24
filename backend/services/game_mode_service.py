"""
게임 모드 서비스
다양한 게임 모드, 팀전, 관전 모드, 커스텀 규칙 관리
"""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from database import get_redis
from redis_models import GameState, GamePlayer, WordChainState

logger = logging.getLogger(__name__)


class GameModeType(str, Enum):
    """게임 모드 타입"""
    CLASSIC = "classic"                # 클래식 모드
    TEAM_BATTLE = "team_battle"        # 팀전 모드
    BLITZ = "blitz"                    # 번개 모드 (짧은 시간)
    MARATHON = "marathon"              # 마라톤 모드 (긴 게임)
    CHALLENGE = "challenge"            # 도전 모드 (특수 규칙)
    SURVIVAL = "survival"              # 서바이벌 모드
    TOURNAMENT = "tournament"          # 토너먼트 모드
    PRACTICE = "practice"              # 연습 모드


class TeamMode(str, Enum):
    """팀 모드"""
    NO_TEAMS = "no_teams"              # 개인전
    TEAMS_2V2 = "teams_2v2"            # 2대2 팀전
    TEAMS_3V3 = "teams_3v3"            # 3대3 팀전
    TEAMS_4V4 = "teams_4v4"            # 4대4 팀전
    RANDOM_TEAMS = "random_teams"      # 랜덤 팀 구성


class SpectatorMode(str, Enum):
    """관전 모드"""
    DISABLED = "disabled"              # 관전 불가
    ENABLED = "enabled"                # 관전 가능
    LIVE_STREAM = "live_stream"        # 실시간 스트리밍


@dataclass
class GameRules:
    """게임 규칙 설정"""
    turn_time_limit: int = 30          # 턴 제한 시간 (초)
    max_failed_attempts: int = 3       # 최대 실패 허용 횟수
    min_word_length: int = 2           # 최소 단어 길이
    max_word_length: int = 50          # 최대 단어 길이
    allow_items: bool = True           # 아이템 사용 허용
    combo_multiplier_limit: float = 3.0  # 최대 콤보 배수
    score_multiplier_limit: float = 5.0  # 최대 점수 배수
    word_repeat_penalty: bool = True   # 단어 반복 페널티
    difficulty_bonus: bool = True      # 난이도 보너스
    time_pressure_mode: bool = False   # 시간 압박 모드 (턴마다 시간 단축)
    target_score: Optional[int] = None # 목표 점수 (도달 시 게임 종료)
    max_rounds: Optional[int] = None   # 최대 라운드 수
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_time_limit": self.turn_time_limit,
            "max_failed_attempts": self.max_failed_attempts,
            "min_word_length": self.min_word_length,
            "max_word_length": self.max_word_length,
            "allow_items": self.allow_items,
            "combo_multiplier_limit": self.combo_multiplier_limit,
            "score_multiplier_limit": self.score_multiplier_limit,
            "word_repeat_penalty": self.word_repeat_penalty,
            "difficulty_bonus": self.difficulty_bonus,
            "time_pressure_mode": self.time_pressure_mode,
            "target_score": self.target_score,
            "max_rounds": self.max_rounds
        }


@dataclass
class TeamInfo:
    """팀 정보"""
    team_id: str
    team_name: str
    members: List[int] = field(default_factory=list)
    score: int = 0
    color: str = "#3B82F6"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_id": self.team_id,
            "team_name": self.team_name,
            "members": self.members,
            "score": self.score,
            "color": self.color
        }


@dataclass 
class GameModeConfig:
    """게임 모드 설정"""
    mode_type: GameModeType
    mode_name: str
    description: str
    min_players: int = 2
    max_players: int = 8
    team_mode: TeamMode = TeamMode.NO_TEAMS
    spectator_mode: SpectatorMode = SpectatorMode.ENABLED
    rules: GameRules = field(default_factory=GameRules)
    teams: List[TeamInfo] = field(default_factory=list)
    is_ranked: bool = True
    difficulty_level: int = 1          # 1~5 난이도
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode_type": self.mode_type,
            "mode_name": self.mode_name,
            "description": self.description,
            "min_players": self.min_players,
            "max_players": self.max_players,
            "team_mode": self.team_mode,
            "spectator_mode": self.spectator_mode,
            "rules": self.rules.to_dict(),
            "teams": [team.to_dict() for team in self.teams],
            "is_ranked": self.is_ranked,
            "difficulty_level": self.difficulty_level
        }


@dataclass
class SpectatorInfo:
    """관전자 정보"""
    user_id: int
    nickname: str
    joined_at: datetime
    is_streaming: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "nickname": self.nickname,
            "joined_at": self.joined_at.isoformat(),
            "is_streaming": self.is_streaming
        }


class GameModeService:
    """게임 모드 서비스"""
    
    def __init__(self):
        self.redis_client = get_redis()
        self.mode_configs = self._initialize_game_modes()
        self.spectators_prefix = "spectators:"
        self.team_assignments_prefix = "teams:"
    
    def _initialize_game_modes(self) -> Dict[str, GameModeConfig]:
        """기본 게임 모드들 초기화"""
        modes = {}
        
        # 클래식 모드
        modes["classic"] = GameModeConfig(
            mode_type=GameModeType.CLASSIC,
            mode_name="클래식",
            description="기본 끝말잇기 게임",
            min_players=2,
            max_players=8,
            rules=GameRules()
        )
        
        # 번개 모드
        modes["blitz"] = GameModeConfig(
            mode_type=GameModeType.BLITZ,
            mode_name="번개전",
            description="빠른 속도의 짧은 게임",
            min_players=2,
            max_players=6,
            rules=GameRules(
                turn_time_limit=15,
                max_rounds=3,
                time_pressure_mode=True
            ),
            difficulty_level=2
        )
        
        # 마라톤 모드
        modes["marathon"] = GameModeConfig(
            mode_type=GameModeType.MARATHON,
            mode_name="마라톤",
            description="장시간 지구력 게임",
            min_players=3,
            max_players=8,
            rules=GameRules(
                turn_time_limit=45,
                target_score=2000,
                combo_multiplier_limit=5.0
            ),
            difficulty_level=3
        )
        
        # 팀전 모드
        modes["team_battle"] = GameModeConfig(
            mode_type=GameModeType.TEAM_BATTLE,
            mode_name="팀전",
            description="2대2 또는 3대3 팀 대전",
            min_players=4,
            max_players=8,
            team_mode=TeamMode.TEAMS_2V2,
            rules=GameRules(
                target_score=1000,
                allow_items=True
            ),
            difficulty_level=3
        )
        
        # 서바이벌 모드
        modes["survival"] = GameModeConfig(
            mode_type=GameModeType.SURVIVAL,
            mode_name="서바이벌",
            description="제한 시간 내 최고 점수 경쟁",
            min_players=4,
            max_players=10,
            rules=GameRules(
                max_failed_attempts=1,
                turn_time_limit=20
            ),
            difficulty_level=4
        )
        
        # 도전 모드
        modes["challenge"] = GameModeConfig(
            mode_type=GameModeType.CHALLENGE,
            mode_name="도전",
            description="특수 규칙이 적용된 고난도 게임",
            min_players=2,
            max_players=6,
            rules=GameRules(
                min_word_length=3,
                turn_time_limit=25,
                time_pressure_mode=True,
                word_repeat_penalty=True
            ),
            difficulty_level=5
        )
        
        # 연습 모드
        modes["practice"] = GameModeConfig(
            mode_type=GameModeType.PRACTICE,
            mode_name="연습",
            description="AI와 함께하는 연습 게임",
            min_players=1,
            max_players=4,
            is_ranked=False,
            rules=GameRules(
                turn_time_limit=60,
                allow_items=False
            ),
            difficulty_level=1
        )
        
        return modes
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """사용 가능한 게임 모드 목록"""
        return [config.to_dict() for config in self.mode_configs.values()]
    
    def get_mode_config(self, mode_type: str) -> Optional[GameModeConfig]:
        """특정 게임 모드 설정 조회"""
        return self.mode_configs.get(mode_type)
    
    def validate_mode_settings(self, mode_type: str, player_count: int, 
                             custom_rules: Optional[Dict[str, Any]] = None) -> Tuple[bool, str]:
        """게임 모드 설정 검증"""
        config = self.get_mode_config(mode_type)
        if not config:
            return False, f"존재하지 않는 게임 모드: {mode_type}"
        
        # 플레이어 수 검증
        if player_count < config.min_players:
            return False, f"최소 {config.min_players}명의 플레이어가 필요합니다"
        
        if player_count > config.max_players:
            return False, f"최대 {config.max_players}명까지 참여 가능합니다"
        
        # 팀 모드 플레이어 수 검증
        if config.team_mode != TeamMode.NO_TEAMS:
            if config.team_mode == TeamMode.TEAMS_2V2 and player_count != 4:
                return False, "2대2 팀전은 정확히 4명이 필요합니다"
            elif config.team_mode == TeamMode.TEAMS_3V3 and player_count != 6:
                return False, "3대3 팀전은 정확히 6명이 필요합니다"
        
        return True, "검증 통과"
    
    async def setup_teams(self, room_id: str, players: List[GamePlayer], 
                         team_mode: TeamMode) -> List[TeamInfo]:
        """팀 구성"""
        if team_mode == TeamMode.NO_TEAMS:
            return []
        
        teams = []
        player_list = list(players)
        
        if team_mode == TeamMode.TEAMS_2V2:
            # 2대2 팀 구성
            random.shuffle(player_list)
            teams.append(TeamInfo(
                team_id="team_a",
                team_name="팀 A",
                members=[player_list[0].user_id, player_list[1].user_id],
                color="#3B82F6"  # 파란색
            ))
            teams.append(TeamInfo(
                team_id="team_b", 
                team_name="팀 B",
                members=[player_list[2].user_id, player_list[3].user_id],
                color="#EF4444"  # 빨간색
            ))
        
        elif team_mode == TeamMode.TEAMS_3V3:
            # 3대3 팀 구성
            random.shuffle(player_list)
            teams.append(TeamInfo(
                team_id="team_a",
                team_name="팀 A",
                members=[p.user_id for p in player_list[:3]],
                color="#3B82F6"
            ))
            teams.append(TeamInfo(
                team_id="team_b",
                team_name="팀 B", 
                members=[p.user_id for p in player_list[3:]],
                color="#EF4444"
            ))
        
        elif team_mode == TeamMode.RANDOM_TEAMS:
            # 랜덤 팀 구성 (플레이어 수에 따라 자동 분배)
            random.shuffle(player_list)
            team_size = len(player_list) // 2
            
            teams.append(TeamInfo(
                team_id="team_a",
                team_name="팀 A",
                members=[p.user_id for p in player_list[:team_size]],
                color="#3B82F6"
            ))
            teams.append(TeamInfo(
                team_id="team_b",
                team_name="팀 B",
                members=[p.user_id for p in player_list[team_size:]],
                color="#EF4444"
            ))
        
        # Redis에 팀 정보 저장
        await self._save_teams_to_redis(room_id, teams)
        
        logger.info(f"팀 구성 완료: room_id={room_id}, mode={team_mode}, teams={len(teams)}")
        return teams
    
    async def _save_teams_to_redis(self, room_id: str, teams: List[TeamInfo]):
        """팀 정보를 Redis에 저장"""
        key = f"{self.team_assignments_prefix}{room_id}"
        teams_data = [team.to_dict() for team in teams]
        
        import json
        self.redis_client.setex(
            key,
            3600,  # 1시간 TTL
            json.dumps(teams_data, ensure_ascii=False)
        )
    
    async def get_teams(self, room_id: str) -> List[TeamInfo]:
        """팀 정보 조회"""
        key = f"{self.team_assignments_prefix}{room_id}"
        teams_data = self.redis_client.get(key)
        
        if not teams_data:
            return []
        
        try:
            import json
            teams_list = json.loads(teams_data)
            teams = []
            
            for team_data in teams_list:
                team = TeamInfo(
                    team_id=team_data["team_id"],
                    team_name=team_data["team_name"],
                    members=team_data["members"],
                    score=team_data.get("score", 0),
                    color=team_data.get("color", "#3B82F6")
                )
                teams.append(team)
            
            return teams
            
        except Exception as e:
            logger.error(f"팀 정보 조회 중 오류: {e}")
            return []
    
    def get_team_for_player(self, teams: List[TeamInfo], user_id: int) -> Optional[TeamInfo]:
        """플레이어가 속한 팀 조회"""
        for team in teams:
            if user_id in team.members:
                return team
        return None
    
    async def update_team_score(self, room_id: str, team_id: str, score: int):
        """팀 점수 업데이트"""
        teams = await self.get_teams(room_id)
        
        for team in teams:
            if team.team_id == team_id:
                team.score += score
                break
        
        await self._save_teams_to_redis(room_id, teams)
    
    # === 관전자 관리 ===
    
    async def add_spectator(self, room_id: str, user_id: int, nickname: str, 
                          is_streaming: bool = False) -> bool:
        """관전자 추가"""
        try:
            spectator = SpectatorInfo(
                user_id=user_id,
                nickname=nickname,
                joined_at=datetime.now(timezone.utc),
                is_streaming=is_streaming
            )
            
            key = f"{self.spectators_prefix}{room_id}"
            
            # 기존 관전자 목록 조회
            spectators_data = self.redis_client.get(key)
            spectators = []
            
            if spectators_data:
                import json
                spectators_list = json.loads(spectators_data)
                spectators = [
                    SpectatorInfo(**spec_data) 
                    for spec_data in spectators_list 
                    if spec_data["user_id"] != user_id  # 중복 제거
                ]
            
            # 새 관전자 추가
            spectators.append(spectator)
            
            # Redis 저장
            import json
            spectators_json = [spec.to_dict() for spec in spectators]
            self.redis_client.setex(
                key,
                3600,  # 1시간 TTL
                json.dumps(spectators_json, ensure_ascii=False)
            )
            
            logger.info(f"관전자 추가: room_id={room_id}, user_id={user_id}, streaming={is_streaming}")
            return True
            
        except Exception as e:
            logger.error(f"관전자 추가 중 오류: {e}")
            return False
    
    async def remove_spectator(self, room_id: str, user_id: int) -> bool:
        """관전자 제거"""
        try:
            key = f"{self.spectators_prefix}{room_id}"
            spectators_data = self.redis_client.get(key)
            
            if not spectators_data:
                return True
            
            import json
            spectators_list = json.loads(spectators_data)
            
            # 해당 사용자 제거
            filtered_spectators = [
                spec for spec in spectators_list 
                if spec["user_id"] != user_id
            ]
            
            # Redis 업데이트
            if filtered_spectators:
                self.redis_client.setex(
                    key,
                    3600,
                    json.dumps(filtered_spectators, ensure_ascii=False)
                )
            else:
                self.redis_client.delete(key)
            
            logger.info(f"관전자 제거: room_id={room_id}, user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"관전자 제거 중 오류: {e}")
            return False
    
    async def get_spectators(self, room_id: str) -> List[SpectatorInfo]:
        """관전자 목록 조회"""
        try:
            key = f"{self.spectators_prefix}{room_id}"
            spectators_data = self.redis_client.get(key)
            
            if not spectators_data:
                return []
            
            import json
            spectators_list = json.loads(spectators_data)
            
            spectators = []
            for spec_data in spectators_list:
                spectator = SpectatorInfo(
                    user_id=spec_data["user_id"],
                    nickname=spec_data["nickname"],
                    joined_at=datetime.fromisoformat(spec_data["joined_at"]),
                    is_streaming=spec_data.get("is_streaming", False)
                )
                spectators.append(spectator)
            
            return spectators
            
        except Exception as e:
            logger.error(f"관전자 목록 조회 중 오류: {e}")
            return []
    
    def can_spectate(self, mode_config: GameModeConfig) -> bool:
        """관전 가능 여부 확인"""
        return mode_config.spectator_mode != SpectatorMode.DISABLED
    
    def can_live_stream(self, mode_config: GameModeConfig) -> bool:
        """라이브 스트리밍 가능 여부 확인"""
        return mode_config.spectator_mode == SpectatorMode.LIVE_STREAM
    
    # === 게임 종료 조건 체크 ===
    
    def check_win_condition(self, game_state: GameState, mode_config: GameModeConfig) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """게임 승리 조건 확인"""
        rules = mode_config.rules
        
        # 목표 점수 달성 확인
        if rules.target_score:
            for player in game_state.players.values():
                if player.score >= rules.target_score:
                    return True, "목표 점수 달성", {"winner": player.user_id, "score": player.score}
        
        # 최대 라운드 수 달성 확인
        if rules.max_rounds and game_state.word_chain:
            if game_state.word_chain.total_words >= rules.max_rounds:
                # 최고 점수 플레이어 승리
                winner = max(game_state.players.values(), key=lambda p: p.score)
                return True, "라운드 완료", {"winner": winner.user_id, "score": winner.score}
        
        # 서바이벌 모드는 점수 기반 승부로 운영
        
        return False, "", None
    
    def check_team_win_condition(self, game_state: GameState, teams: List[TeamInfo], 
                               mode_config: GameModeConfig) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """팀전 승리 조건 확인"""
        rules = mode_config.rules
        
        # 팀 점수 계산
        team_scores = {}
        for team in teams:
            team_score = 0
            for member_id in team.members:
                player = game_state.players.get(str(member_id))
                if player:
                    team_score += player.score
            team_scores[team.team_id] = team_score
        
        # 목표 점수 달성 팀 확인
        if rules.target_score:
            for team_id, score in team_scores.items():
                if score >= rules.target_score:
                    winning_team = next(t for t in teams if t.team_id == team_id)
                    return True, "팀 목표 점수 달성", {
                        "winning_team": winning_team.to_dict(),
                        "team_scores": team_scores
                    }
        
        return False, "", None
    
    async def cleanup_room_data(self, room_id: str):
        """룸 관련 데이터 정리"""
        # 관전자 데이터 삭제
        spectator_key = f"{self.spectators_prefix}{room_id}"
        self.redis_client.delete(spectator_key)
        
        # 팀 데이터 삭제
        team_key = f"{self.team_assignments_prefix}{room_id}"
        self.redis_client.delete(team_key)
        
        logger.info(f"룸 데이터 정리 완료: room_id={room_id}")
    
    def get_mode_statistics(self) -> Dict[str, Any]:
        """게임 모드 통계"""
        return {
            "available_modes": len(self.mode_configs),
            "team_modes": len([m for m in self.mode_configs.values() if m.team_mode != TeamMode.NO_TEAMS]),
            "ranked_modes": len([m for m in self.mode_configs.values() if m.is_ranked]),
            "spectator_enabled_modes": len([m for m in self.mode_configs.values() if m.spectator_mode != SpectatorMode.DISABLED]),
            "difficulty_distribution": {
                f"level_{i}": len([m for m in self.mode_configs.values() if m.difficulty_level == i])
                for i in range(1, 6)
            }
        }


# 전역 게임 모드 서비스 인스턴스
game_mode_service = GameModeService()


def get_game_mode_service() -> GameModeService:
    """게임 모드 서비스 의존성"""
    return game_mode_service