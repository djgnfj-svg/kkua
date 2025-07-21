# 다양한 게임 모드 구현 가이드

## 개요

KKUA에 다양한 게임 모드를 추가하여 플레이어의 게임 경험을 풍부하게 만들고 재미 요소를 극대화합니다. 각 모드는 고유한 규칙과 전략적 요소를 제공합니다.

## 게임 모드 종류

### 1. Classic Mode (기본 모드)
- **현재 구현된 기본 모드**
- 30초 턴 제한, 10라운드, 최대 6명

### 2. Blitz Mode (블리츠 모드)
- **빠른 게임**: 15초 턴 제한
- **짧은 게임**: 8라운드
- **아이템 활성화**: 전략적 아이템 사용 가능

### 3. Marathon Mode (마라톤 모드)
- **긴 게임**: 45초 턴 제한, 20라운드
- **대규모**: 최대 8명 참여
- **지구력 테스트**: 장기전 전략 필요

### 4. Survival Mode (서바이벌 모드)
- **생명 시스템**: 각 플레이어 3번의 기회
- **탈락제**: 실패 시 생명 차감, 0개 시 탈락
- **최후의 1인**: 마지막까지 살아남은 플레이어 승리

### 5. Team Battle Mode (팀 배틀 모드)
- **팀 대전**: 3vs3 형태
- **팀 점수**: 팀원들의 점수 합산
- **협력 전략**: 팀원 간 협력 필요

### 6. Challenge Mode (챌린지 모드)
- **일일 챌린지**: 매일 새로운 특별 규칙
- **특별 보상**: 완료 시 특별 아이템 획득

---

## 데이터베이스 설계

### GameMode 모델 확장

```python
# backend/models/gameroom_model.py
from enum import Enum
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime

class GameMode(str, Enum):
    CLASSIC = "classic"
    BLITZ = "blitz"
    MARATHON = "marathon"
    SURVIVAL = "survival"
    TEAM_BATTLE = "team_battle"
    CHALLENGE = "challenge"

class GameModeConfig(Base):
    __tablename__ = "game_mode_configs"
    
    config_id = Column(Integer, primary_key=True)
    mode = Column(String(30), nullable=False, unique=True)
    display_name = Column(String(50), nullable=False)
    description = Column(Text)
    turn_time_limit = Column(Integer, default=30)  # 초
    max_rounds = Column(Integer, default=10)
    max_players = Column(Integer, default=6)
    min_players = Column(Integer, default=2)
    items_enabled = Column(Boolean, default=False)
    lives_per_player = Column(Integer, default=0)  # 0 = 무제한
    team_mode = Column(Boolean, default=False)
    teams_count = Column(Integer, default=0)
    special_rules = Column(JSON)  # 특별 규칙 저장
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# Gameroom 모델에 game_mode 필드 추가
class Gameroom(Base):
    # ... 기존 필드들 ...
    game_mode = Column(String(30), default=GameMode.CLASSIC)
    mode_config = Column(JSON)  # 모드별 추가 설정
```

### Team 관련 모델

```python
# backend/models/team_model.py
class GameTeam(Base):
    __tablename__ = "game_teams"
    
    team_id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"))
    team_number = Column(Integer, nullable=False)  # 1, 2, 3...
    team_name = Column(String(50))
    team_color = Column(String(7))  # HEX 색상 코드
    total_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class TeamMember(Base):
    __tablename__ = "team_members"
    
    member_id = Column(Integer, primary_key=True)
    team_id = Column(Integer, ForeignKey("game_teams.team_id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    role = Column(String(20), default="member")  # leader, member
    joined_at = Column(DateTime, default=datetime.utcnow)
```

### Survival 모드 전용 모델

```python
# backend/models/survival_model.py
class SurvivalPlayer(Base):
    __tablename__ = "survival_players"
    
    survival_id = Column(Integer, primary_key=True)
    room_id = Column(Integer, ForeignKey("gamerooms.room_id"))
    guest_id = Column(Integer, ForeignKey("guests.guest_id"))
    lives_remaining = Column(Integer, default=3)
    elimination_round = Column(Integer)  # 탈락한 라운드
    is_eliminated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 게임 모드 설정 시스템

### GameModeManager 서비스

```python
# backend/services/game_mode_service.py
from typing import Dict, Any, List
from backend.models.gameroom_model import GameMode, GameModeConfig

class GameModeManager:
    """게임 모드 관리 및 설정을 담당하는 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.mode_configs = self._load_mode_configs()
    
    def _load_mode_configs(self) -> Dict[str, Dict[str, Any]]:
        """데이터베이스에서 게임 모드 설정 로드"""
        configs = {}
        db_configs = self.db.query(GameModeConfig).filter(
            GameModeConfig.is_active == True
        ).all()
        
        for config in db_configs:
            configs[config.mode] = {
                "display_name": config.display_name,
                "description": config.description,
                "turn_time_limit": config.turn_time_limit,
                "max_rounds": config.max_rounds,
                "max_players": config.max_players,
                "min_players": config.min_players,
                "items_enabled": config.items_enabled,
                "lives_per_player": config.lives_per_player,
                "team_mode": config.team_mode,
                "teams_count": config.teams_count,
                "special_rules": config.special_rules or {}
            }
        
        # 기본 설정이 없으면 하드코딩된 설정 사용
        if not configs:
            configs = self._get_default_configs()
        
        return configs
    
    def _get_default_configs(self) -> Dict[str, Dict[str, Any]]:
        """기본 게임 모드 설정"""
        return {
            GameMode.CLASSIC: {
                "display_name": "클래식",
                "description": "기본 끝말잇기 게임",
                "turn_time_limit": 30,
                "max_rounds": 10,
                "max_players": 6,
                "min_players": 2,
                "items_enabled": False,
                "lives_per_player": 0,
                "team_mode": False,
                "teams_count": 0,
                "special_rules": {}
            },
            GameMode.BLITZ: {
                "display_name": "블리츠",
                "description": "빠른 속도의 짧은 게임",
                "turn_time_limit": 15,
                "max_rounds": 8,
                "max_players": 4,
                "min_players": 2,
                "items_enabled": True,
                "lives_per_player": 0,
                "team_mode": False,
                "teams_count": 0,
                "special_rules": {
                    "quick_start": True,
                    "bonus_speed_multiplier": 1.5
                }
            },
            GameMode.MARATHON: {
                "display_name": "마라톤",
                "description": "긴 시간의 대규모 게임",
                "turn_time_limit": 45,
                "max_rounds": 20,
                "max_players": 8,
                "min_players": 3,
                "items_enabled": True,
                "lives_per_player": 0,
                "team_mode": False,
                "teams_count": 0,
                "special_rules": {
                    "endurance_bonus": True,
                    "progressive_difficulty": True
                }
            },
            GameMode.SURVIVAL: {
                "display_name": "서바이벌",
                "description": "생명을 가진 탈락제 게임",
                "turn_time_limit": 20,
                "max_rounds": 0,  # 무제한
                "max_players": 6,
                "min_players": 3,
                "items_enabled": True,
                "lives_per_player": 3,
                "team_mode": False,
                "teams_count": 0,
                "special_rules": {
                    "elimination_mode": True,
                    "life_recovery_items": True
                }
            },
            GameMode.TEAM_BATTLE: {
                "display_name": "팀 배틀",
                "description": "팀 대항전 (3vs3)",
                "turn_time_limit": 25,
                "max_rounds": 12,
                "max_players": 6,
                "min_players": 4,
                "items_enabled": True,
                "lives_per_player": 0,
                "team_mode": True,
                "teams_count": 2,
                "special_rules": {
                    "team_scoring": True,
                    "team_items": True,
                    "cooperative_bonus": True
                }
            },
            GameMode.CHALLENGE: {
                "display_name": "챌린지",
                "description": "일일 특별 챌린지",
                "turn_time_limit": 30,
                "max_rounds": 15,
                "max_players": 4,
                "min_players": 2,
                "items_enabled": True,
                "lives_per_player": 0,
                "team_mode": False,
                "teams_count": 0,
                "special_rules": {
                    "daily_challenge": True,
                    "special_rewards": True,
                    "unique_constraints": True
                }
            }
        }
    
    def get_mode_config(self, mode: str) -> Dict[str, Any]:
        """특정 게임 모드의 설정 반환"""
        return self.mode_configs.get(mode, self.mode_configs[GameMode.CLASSIC])
    
    def get_available_modes(self) -> List[Dict[str, Any]]:
        """사용 가능한 게임 모드 목록 반환"""
        modes = []
        for mode_key, config in self.mode_configs.items():
            modes.append({
                "mode": mode_key,
                "display_name": config["display_name"],
                "description": config["description"],
                "max_players": config["max_players"],
                "min_players": config["min_players"],
                "estimated_duration": self._estimate_duration(config),
                "difficulty": self._get_difficulty_level(mode_key)
            })
        return modes
    
    def _estimate_duration(self, config: Dict[str, Any]) -> int:
        """게임 예상 소요 시간 계산 (분)"""
        rounds = config["max_rounds"] or 15  # 무제한이면 평균 15라운드로 가정
        turn_time = config["turn_time_limit"]
        players = config["max_players"]
        
        total_seconds = rounds * turn_time * players
        return int(total_seconds / 60)
    
    def _get_difficulty_level(self, mode: str) -> str:
        """게임 모드별 난이도 레벨"""
        difficulty_map = {
            GameMode.CLASSIC: "초급",
            GameMode.BLITZ: "중급",
            GameMode.MARATHON: "고급",
            GameMode.SURVIVAL: "중급",
            GameMode.TEAM_BATTLE: "고급",
            GameMode.CHALLENGE: "다양함"
        }
        return difficulty_map.get(mode, "초급")
```

---

## 모드별 게임 로직 구현

### 1. Blitz Mode 구현

```python
# backend/services/blitz_game_service.py
class BlitzGameService:
    """블리츠 모드 전용 게임 로직"""
    
    def __init__(self, redis_client, websocket_manager):
        self.redis = redis_client
        self.ws_manager = websocket_manager
        self.speed_multiplier = 1.5
    
    async def handle_word_submission(self, room_id: int, player_id: int, 
                                   word: str, response_time: float) -> Dict[str, Any]:
        """블리츠 모드 단어 제출 처리"""
        
        # 기본 검증
        base_result = await self._validate_word_basic(room_id, player_id, word)
        if not base_result["valid"]:
            return base_result
        
        # 블리츠 모드 보너스 계산
        speed_bonus = self._calculate_blitz_bonus(response_time)
        base_score = len(word) * 10
        total_score = int((base_score + speed_bonus) * self.speed_multiplier)
        
        # 연속 성공 보너스 (블리츠 전용)
        combo_count = await self._get_player_combo(room_id, player_id)
        if combo_count >= 3:
            total_score += combo_count * 5
        
        # 게임 상태 업데이트
        await self._update_game_state(room_id, player_id, word, total_score)
        
        # 빠른 턴 전환 (블리츠 특성)
        await self._quick_turn_transition(room_id)
        
        return {
            "valid": True,
            "word": word,
            "base_score": base_score,
            "speed_bonus": speed_bonus,
            "combo_bonus": combo_count * 5 if combo_count >= 3 else 0,
            "total_score": total_score,
            "multiplier": self.speed_multiplier,
            "message": f"블리츠 보너스! {word} (+{total_score}점)"
        }
    
    def _calculate_blitz_bonus(self, response_time: float) -> int:
        """블리츠 모드 속도 보너스 계산"""
        if response_time <= 5:
            return 20  # 초고속
        elif response_time <= 8:
            return 15  # 고속
        elif response_time <= 12:
            return 10  # 빠름
        else:
            return 0   # 보너스 없음
    
    async def _quick_turn_transition(self, room_id: int):
        """빠른 턴 전환 (블리츠 모드 특성)"""
        # 일반 모드보다 2초 빠른 턴 전환
        await asyncio.sleep(1)
        await self._notify_next_player(room_id)
```

### 2. Survival Mode 구현

```python
# backend/services/survival_game_service.py
class SurvivalGameService:
    """서바이벌 모드 전용 게임 로직"""
    
    def __init__(self, db: Session, redis_client, websocket_manager):
        self.db = db
        self.redis = redis_client
        self.ws_manager = websocket_manager
        self.default_lives = 3
    
    async def initialize_survival_game(self, room_id: int, players: List[int]):
        """서바이벌 게임 초기화"""
        
        # 각 플레이어의 생명 설정
        for player_id in players:
            survival_player = SurvivalPlayer(
                room_id=room_id,
                guest_id=player_id,
                lives_remaining=self.default_lives
            )
            self.db.add(survival_player)
        
        self.db.commit()
        
        # Redis에 생존 정보 저장
        survival_data = {
            player_id: {
                "lives": self.default_lives,
                "eliminated": False,
                "elimination_round": None
            }
            for player_id in players
        }
        
        await self.redis.hset(
            f"survival:{room_id}",
            mapping={str(k): json.dumps(v) for k, v in survival_data.items()}
        )
    
    async def handle_player_failure(self, room_id: int, player_id: int, 
                                  failure_type: str) -> Dict[str, Any]:
        """플레이어 실패 처리 (시간 초과, 잘못된 단어 등)"""
        
        # 현재 생명 상태 조회
        survival_data = await self._get_survival_data(room_id, player_id)
        
        # 생명 차감
        survival_data["lives"] -= 1
        
        # 생명이 0이 되면 탈락
        if survival_data["lives"] <= 0:
            survival_data["eliminated"] = True
            current_round = await self._get_current_round(room_id)
            survival_data["elimination_round"] = current_round
            
            # 탈락 처리
            await self._eliminate_player(room_id, player_id, current_round)
            
            # 남은 플레이어 확인
            remaining_players = await self._count_remaining_players(room_id)
            
            if remaining_players <= 1:
                # 게임 종료
                await self._end_survival_game(room_id)
                return {
                    "eliminated": True,
                    "game_ended": True,
                    "message": f"플레이어 {player_id}님이 탈락했습니다. 게임이 종료되었습니다!"
                }
            
            return {
                "eliminated": True,
                "lives_remaining": 0,
                "remaining_players": remaining_players,
                "message": f"플레이어 {player_id}님이 탈락했습니다! (생명 0개)"
            }
        
        # 생명이 남아있으면 계속 진행
        await self._update_survival_data(room_id, player_id, survival_data)
        
        return {
            "eliminated": False,
            "lives_remaining": survival_data["lives"],
            "failure_type": failure_type,
            "message": f"실패! 남은 생명: {survival_data['lives']}개"
        }
    
    async def _eliminate_player(self, room_id: int, player_id: int, round_number: int):
        """플레이어 탈락 처리"""
        
        # 데이터베이스 업데이트
        survival_player = self.db.query(SurvivalPlayer).filter(
            SurvivalPlayer.room_id == room_id,
            SurvivalPlayer.guest_id == player_id
        ).first()
        
        if survival_player:
            survival_player.is_eliminated = True
            survival_player.elimination_round = round_number
            self.db.commit()
        
        # 게임에서 플레이어 제거
        await self._remove_player_from_turn_order(room_id, player_id)
        
        # 탈락 알림
        await self.ws_manager.broadcast_to_room(room_id, {
            "type": "player_eliminated",
            "player_id": player_id,
            "round": round_number,
            "message": f"플레이어 {player_id}님이 탈락했습니다"
        })
    
    async def get_survival_status(self, room_id: int) -> Dict[str, Any]:
        """서바이벌 게임 현재 상태 조회"""
        
        # 모든 플레이어의 생존 상태
        survival_status = {}
        survival_keys = await self.redis.hgetall(f"survival:{room_id}")
        
        for player_id_str, data_json in survival_keys.items():
            player_id = int(player_id_str)
            data = json.loads(data_json)
            survival_status[player_id] = {
                "lives_remaining": data["lives"],
                "is_eliminated": data["eliminated"],
                "elimination_round": data.get("elimination_round")
            }
        
        # 생존자 수 계산
        survivors = sum(1 for status in survival_status.values() 
                       if not status["is_eliminated"])
        
        return {
            "players_status": survival_status,
            "survivors_count": survivors,
            "elimination_order": self._get_elimination_order(survival_status)
        }
```

### 3. Team Battle Mode 구현

```python
# backend/services/team_battle_service.py
class TeamBattleService:
    """팀 배틀 모드 전용 게임 로직"""
    
    def __init__(self, db: Session, redis_client, websocket_manager):
        self.db = db
        self.redis = redis_client
        self.ws_manager = websocket_manager
    
    async def setup_teams(self, room_id: int, players: List[int]) -> Dict[str, Any]:
        """팀 구성 설정"""
        
        if len(players) % 2 != 0:
            raise ValueError("팀 배틀은 짝수 인원이 필요합니다")
        
        team_size = len(players) // 2
        
        # 팀 무작위 배정
        shuffled_players = players.copy()
        random.shuffle(shuffled_players)
        
        team1_players = shuffled_players[:team_size]
        team2_players = shuffled_players[team_size:]
        
        # 팀 생성
        team1 = GameTeam(
            room_id=room_id,
            team_number=1,
            team_name="팀 A",
            team_color="#FF6B6B"
        )
        team2 = GameTeam(
            room_id=room_id,
            team_number=2,
            team_name="팀 B",
            team_color="#4ECDC4"
        )
        
        self.db.add_all([team1, team2])
        self.db.flush()
        
        # 팀 멤버 배정
        for player_id in team1_players:
            member = TeamMember(team_id=team1.team_id, guest_id=player_id)
            self.db.add(member)
        
        for player_id in team2_players:
            member = TeamMember(team_id=team2.team_id, guest_id=player_id)
            self.db.add(member)
        
        self.db.commit()
        
        # Redis에 팀 정보 저장
        team_data = {
            "team1": {
                "id": team1.team_id,
                "name": team1.team_name,
                "color": team1.team_color,
                "players": team1_players,
                "score": 0
            },
            "team2": {
                "id": team2.team_id,
                "name": team2.team_name,
                "color": team2.team_color,
                "players": team2_players,
                "score": 0
            }
        }
        
        await self.redis.set(
            f"teams:{room_id}",
            json.dumps(team_data),
            ex=86400  # 24시간
        )
        
        return team_data
    
    async def handle_team_word_submission(self, room_id: int, player_id: int, 
                                        word: str) -> Dict[str, Any]:
        """팀 배틀 단어 제출 처리"""
        
        # 기본 검증
        base_result = await self._validate_word_basic(room_id, player_id, word)
        if not base_result["valid"]:
            return base_result
        
        # 플레이어가 속한 팀 찾기
        team_data = await self._get_team_data(room_id)
        player_team = None
        
        for team_key, team_info in team_data.items():
            if player_id in team_info["players"]:
                player_team = team_key
                break
        
        if not player_team:
            return {"valid": False, "message": "팀 정보를 찾을 수 없습니다"}
        
        # 점수 계산 (팀 보너스 포함)
        base_score = len(word) * 10
        team_bonus = self._calculate_team_bonus(team_data[player_team])
        cooperation_bonus = await self._calculate_cooperation_bonus(
            room_id, player_team, word
        )
        
        total_score = base_score + team_bonus + cooperation_bonus
        
        # 팀 점수 업데이트
        team_data[player_team]["score"] += total_score
        await self._update_team_data(room_id, team_data)
        
        # 팀원들에게 점수 업데이트 알림
        await self._notify_team_score_update(room_id, player_team, total_score)
        
        return {
            "valid": True,
            "word": word,
            "base_score": base_score,
            "team_bonus": team_bonus,
            "cooperation_bonus": cooperation_bonus,
            "total_score": total_score,
            "team_total_score": team_data[player_team]["score"],
            "message": f"팀 득점! {word} (+{total_score}점)"
        }
    
    def _calculate_team_bonus(self, team_info: Dict[str, Any]) -> int:
        """팀 보너스 계산"""
        # 팀 점수가 높을수록 추가 보너스
        current_score = team_info["score"]
        if current_score >= 200:
            return 15
        elif current_score >= 100:
            return 10
        elif current_score >= 50:
            return 5
        else:
            return 0
    
    async def _calculate_cooperation_bonus(self, room_id: int, team: str, 
                                         word: str) -> int:
        """협력 보너스 계산 (팀원이 연속으로 성공할 때)"""
        
        # 최근 5턴의 성공 기록 확인
        recent_turns = await self._get_recent_turns(room_id, 5)
        team_data = await self._get_team_data(room_id)
        team_players = team_data[team]["players"]
        
        consecutive_team_success = 0
        for turn in reversed(recent_turns):
            if turn["player_id"] in team_players and turn["success"]:
                consecutive_team_success += 1
            else:
                break
        
        # 연속 성공에 따른 보너스
        if consecutive_team_success >= 3:
            return consecutive_team_success * 8
        elif consecutive_team_success >= 2:
            return consecutive_team_success * 5
        else:
            return 0
    
    async def get_team_battle_status(self, room_id: int) -> Dict[str, Any]:
        """팀 배틀 현재 상태 조회"""
        
        team_data = await self._get_team_data(room_id)
        
        # 각 팀의 상세 통계
        team_stats = {}
        for team_key, team_info in team_data.items():
            stats = await self._calculate_team_stats(room_id, team_info["players"])
            team_stats[team_key] = {
                **team_info,
                "stats": stats,
                "average_score_per_player": team_info["score"] / len(team_info["players"]),
                "leading": team_info["score"] == max(t["score"] for t in team_data.values())
            }
        
        return {
            "teams": team_stats,
            "score_difference": abs(team_data["team1"]["score"] - team_data["team2"]["score"]),
            "leading_team": "team1" if team_data["team1"]["score"] > team_data["team2"]["score"] else "team2"
        }
```

---

## API 엔드포인트 확장

### 게임 모드 관련 API

```python
# backend/routers/game_mode_router.py
from fastapi import APIRouter, Depends, HTTPException
from backend.services.game_mode_service import GameModeManager

router = APIRouter(prefix="/game-modes", tags=["game-modes"])

@router.get("/")
async def get_available_game_modes(
    mode_manager: GameModeManager = Depends(get_game_mode_manager)
):
    """사용 가능한 게임 모드 목록 조회"""
    modes = mode_manager.get_available_modes()
    return {"status": "success", "data": {"modes": modes}}

@router.get("/{mode}")
async def get_game_mode_details(
    mode: str,
    mode_manager: GameModeManager = Depends(get_game_mode_manager)
):
    """특정 게임 모드의 상세 정보 조회"""
    try:
        config = mode_manager.get_mode_config(mode)
        return {"status": "success", "data": {"config": config}}
    except KeyError:
        raise HTTPException(status_code=404, detail="게임 모드를 찾을 수 없습니다")

@router.post("/validate-room-settings")
async def validate_room_settings(
    settings: dict,
    mode_manager: GameModeManager = Depends(get_game_mode_manager)
):
    """방 설정이 게임 모드에 적합한지 검증"""
    mode = settings.get("game_mode", "classic")
    config = mode_manager.get_mode_config(mode)
    
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    # 플레이어 수 검증
    player_count = settings.get("max_players", 6)
    if player_count < config["min_players"]:
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"최소 {config['min_players']}명이 필요합니다"
        )
    
    if player_count > config["max_players"]:
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"최대 {config['max_players']}명까지 가능합니다"
        )
    
    # 팀 모드 검증
    if config["team_mode"] and player_count % config["teams_count"] != 0:
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"팀 모드는 {config['teams_count']}의 배수 인원이 필요합니다"
        )
    
    return {"status": "success", "data": validation_result}
```

---

## 프론트엔드 구현

### GameModeSelector 컴포넌트

```javascript
// frontend/src/Pages/Lobby/components/GameModeSelector.js
import React, { useState, useEffect } from 'react';
import { getGameModes, validateRoomSettings } from '../../../Api/gameModeApi';

const GameModeSelector = ({ selectedMode, onModeChange, maxPlayers, onValidationChange }) => {
    const [gameModes, setGameModes] = useState([]);
    const [validationResult, setValidationResult] = useState({ valid: true, errors: [] });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchGameModes();
    }, []);

    useEffect(() => {
        if (selectedMode) {
            validateSettings();
        }
    }, [selectedMode, maxPlayers]);

    const fetchGameModes = async () => {
        try {
            const response = await getGameModes();
            setGameModes(response.data.modes);
        } catch (error) {
            console.error('게임 모드 로드 실패:', error);
        } finally {
            setLoading(false);
        }
    };

    const validateSettings = async () => {
        try {
            const settings = {
                game_mode: selectedMode,
                max_players: maxPlayers
            };
            
            const response = await validateRoomSettings(settings);
            setValidationResult(response.data);
            onValidationChange?.(response.data);
        } catch (error) {
            console.error('설정 검증 실패:', error);
        }
    };

    const getDifficultyColor = (difficulty) => {
        const colors = {
            '초급': 'text-green-600',
            '중급': 'text-yellow-600',
            '고급': 'text-red-600',
            '다양함': 'text-purple-600'
        };
        return colors[difficulty] || 'text-gray-600';
    };

    const getEstimatedDurationText = (minutes) => {
        if (minutes < 60) {
            return `약 ${minutes}분`;
        } else {
            const hours = Math.floor(minutes / 60);
            const remainingMinutes = minutes % 60;
            return `약 ${hours}시간 ${remainingMinutes}분`;
        }
    };

    if (loading) {
        return (
            <div className="p-4 bg-gray-100 rounded-lg">
                <div className="animate-pulse">게임 모드 로딩 중...</div>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">게임 모드 선택</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {gameModes.map((mode) => (
                    <div
                        key={mode.mode}
                        className={`
                            relative p-4 border-2 rounded-lg cursor-pointer transition-all duration-200
                            hover:shadow-md
                            ${selectedMode === mode.mode 
                                ? 'border-blue-500 bg-blue-50' 
                                : 'border-gray-200 bg-white'
                            }
                        `}
                        onClick={() => onModeChange(mode.mode)}
                    >
                        {/* 모드 아이콘 */}
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="font-bold text-gray-800">{mode.display_name}</h4>
                            <span className={`text-sm font-medium ${getDifficultyColor(mode.difficulty)}`}>
                                {mode.difficulty}
                            </span>
                        </div>
                        
                        {/* 모드 설명 */}
                        <p className="text-sm text-gray-600 mb-3">{mode.description}</p>
                        
                        {/* 모드 정보 */}
                        <div className="space-y-1 text-xs text-gray-500">
                            <div className="flex justify-between">
                                <span>인원:</span>
                                <span>{mode.min_players}-{mode.max_players}명</span>
                            </div>
                            <div className="flex justify-between">
                                <span>예상 시간:</span>
                                <span>{getEstimatedDurationText(mode.estimated_duration)}</span>
                            </div>
                        </div>
                        
                        {/* 선택 표시 */}
                        {selectedMode === mode.mode && (
                            <div className="absolute top-2 right-2 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                </svg>
                            </div>
                        )}
                    </div>
                ))}
            </div>
            
            {/* 검증 결과 표시 */}
            {!validationResult.valid && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <h4 className="font-medium text-red-800 mb-2">설정 오류</h4>
                    <ul className="list-disc list-inside text-sm text-red-700">
                        {validationResult.errors.map((error, index) => (
                            <li key={index}>{error}</li>
                        ))}
                    </ul>
                </div>
            )}
            
            {validationResult.warnings && validationResult.warnings.length > 0 && (
                <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                    <h4 className="font-medium text-yellow-800 mb-2">주의사항</h4>
                    <ul className="list-disc list-inside text-sm text-yellow-700">
                        {validationResult.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default GameModeSelector;
```

### TeamDisplay 컴포넌트 (팀 배틀용)

```javascript
// frontend/src/Pages/InGame/components/TeamDisplay.js
import React from 'react';

const TeamDisplay = ({ teams, currentPlayer, myPlayerId }) => {
    const getTeamByPlayer = (playerId) => {
        return Object.values(teams).find(team => 
            team.players.includes(playerId)
        );
    };

    const myTeam = getTeamByPlayer(myPlayerId);
    const currentPlayerTeam = getTeamByPlayer(currentPlayer);

    return (
        <div className="grid grid-cols-2 gap-4 mb-6">
            {Object.values(teams).map((team) => (
                <div
                    key={team.id}
                    className={`
                        p-4 rounded-lg border-2 transition-all duration-300
                        ${team.id === myTeam?.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-gray-50'}
                        ${team.id === currentPlayerTeam?.id ? 'ring-2 ring-yellow-400' : ''}
                    `}
                    style={{ borderColor: team.color }}
                >
                    {/* 팀 헤더 */}
                    <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                            <div 
                                className="w-4 h-4 rounded-full" 
                                style={{ backgroundColor: team.color }}
                            ></div>
                            <h3 className="font-bold text-gray-800">{team.name}</h3>
                            {team.id === myTeam?.id && (
                                <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                    내 팀
                                </span>
                            )}
                        </div>
                        <div className="text-right">
                            <div className="text-2xl font-bold" style={{ color: team.color }}>
                                {team.score}
                            </div>
                            <div className="text-xs text-gray-500">점수</div>
                        </div>
                    </div>
                    
                    {/* 팀원 목록 */}
                    <div className="space-y-1">
                        {team.players.map((playerId) => (
                            <div
                                key={playerId}
                                className={`
                                    flex items-center justify-between p-2 rounded text-sm
                                    ${playerId === currentPlayer ? 'bg-yellow-100 border border-yellow-300' : 'bg-white'}
                                    ${playerId === myPlayerId ? 'font-bold' : ''}
                                `}
                            >
                                <span>플레이어 {playerId}</span>
                                {playerId === currentPlayer && (
                                    <span className="text-yellow-600 text-xs">차례</span>
                                )}
                            </div>
                        ))}
                    </div>
                    
                    {/* 팀 통계 */}
                    {team.stats && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                            <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
                                <div>평균 점수: {team.average_score_per_player.toFixed(1)}</div>
                                <div>성공률: {team.stats.success_rate}%</div>
                            </div>
                        </div>
                    )}
                </div>
            ))}
        </div>
    );
};

export default TeamDisplay;
```

---

## 구현 우선순위

### Phase 1 (1주차): 기본 모드 구현
1. **GameModeManager 서비스** - 모드 설정 관리
2. **Blitz Mode** - 가장 단순한 변형 모드
3. **모드 선택 UI** - 프론트엔드 컴포넌트

### Phase 2 (2주차): 고급 모드 구현
1. **Survival Mode** - 생명 시스템
2. **Team Battle Mode** - 팀 시스템
3. **Marathon Mode** - 확장된 게임 시간

### Phase 3 (3주차): 특별 모드 및 완성
1. **Challenge Mode** - 일일 챌린지
2. **모든 모드 통합 테스트**
3. **성능 최적화**

이 가이드를 통해 KKUA에 다양하고 흥미진진한 게임 모드를 추가하여 플레이어의 게임 경험을 크게 향상시킬 수 있습니다.