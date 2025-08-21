"""
Redis 데이터 구조 및 모델 정의
실시간 게임 상태 관리를 위한 Redis 키-값 구조
"""

import json
import redis
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class GameStatus(Enum):
    """게임 상태"""
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    PAUSED = "paused"


class PlayerStatus(Enum):
    """플레이어 상태"""
    WAITING = "waiting"
    READY = "ready"
    PLAYING = "playing"
    DISCONNECTED = "disconnected"


@dataclass
class GamePlayer:
    """게임 플레이어 정보"""
    user_id: int
    nickname: str
    status: str = PlayerStatus.WAITING.value
    score: int = 0
    current_combo: int = 0
    max_combo: int = 0
    words_submitted: int = 0
    items_used: int = 0
    is_host: bool = False
    items: List[str] = None
    last_word_time: Optional[str] = None
    joined_at: str = None
    
    def __post_init__(self):
        if self.items is None:
            self.items = []
        if self.joined_at is None:
            self.joined_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GamePlayer':
        return cls(**data)
    


@dataclass
class GameTimer:
    """게임 타이머 정보"""
    expires_at: str
    current_player_id: int
    remaining_ms: int
    turn_duration_ms: int = 30000  # 기본 30초
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameTimer':
        return cls(**data)
    
    def is_expired(self) -> bool:
        """타이머 만료 확인"""
        now = datetime.now(timezone.utc)
        expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
        return now >= expires


@dataclass
class WordChainState:
    """끝말잇기 체인 상태"""
    words: List[str] = None
    used_words: set = None
    current_char: str = ""
    last_word: str = ""
    
    def __post_init__(self):
        if self.words is None:
            self.words = []
        if self.used_words is None:
            self.used_words = set()

    def add_word(self, word: str):
        """단어 추가"""
        self.words.append(word)
        self.used_words.add(word.lower())
        self.last_word = word
        self.current_char = word[-1] if word else ""

    def is_word_used(self, word: str) -> bool:
        """단어 중복 사용 확인"""
        return word.lower() in self.used_words
    
    def is_valid_chain(self, word: str) -> bool:
        """끝말잇기 규칙 확인"""
        if not self.current_char:
            return True
        return word[0] == self.current_char if word else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "words": self.words,
            "used_words": list(self.used_words),
            "current_char": self.current_char,
            "last_word": self.last_word
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WordChainState':
        instance = cls()
        instance.words = data.get("words", [])
        instance.used_words = set(data.get("used_words", []))
        instance.current_char = data.get("current_char", "")
        instance.last_word = data.get("last_word", "")
        return instance


@dataclass
class GameState:
    """게임 전체 상태"""
    room_id: str
    status: str = GameStatus.WAITING.value
    players: List[GamePlayer] = None
    current_round: int = 1
    current_turn: int = 0
    max_rounds: int = 5
    turn_time_limit_ms: int = 30000  # 현재 턴의 시간 제한
    initial_turn_time_ms: int = 30000  # 첫 턴 초기 시간
    turn_time_reduction_ms: int = 5000  # 매 턴마다 감소하는 시간
    min_turn_time_ms: int = 100  # 최소 턴 시간 (0.1초) - 원래대로
    total_turns: int = 0  # 전체 진행된 턴 수
    word_chain: WordChainState = None
    timer: Optional[GameTimer] = None
    game_settings: Dict[str, Any] = None
    created_at: str = None
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    
    def __post_init__(self):
        if self.players is None:
            self.players = []
        if self.word_chain is None:
            self.word_chain = WordChainState()
        if self.game_settings is None:
            self.game_settings = {}
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def get_current_player(self) -> Optional[GamePlayer]:
        """현재 턴 플레이어 반환"""
        if not self.players or self.current_turn >= len(self.players):
            return None
        return self.players[self.current_turn]

    def get_host_player(self) -> Optional[GamePlayer]:
        """방장 플레이어 반환"""
        for player in self.players:
            if player.is_host:
                return player
        return None

    def is_player_host(self, user_id: int) -> bool:
        """플레이어가 방장인지 확인"""
        host = self.get_host_player()
        return host is not None and host.user_id == user_id

    def next_turn(self):
        """다음 턴으로 이동"""
        if self.players:
            # 턴 수 증가
            self.total_turns += 1
            
            # 다음 턴으로 이동
            self.current_turn = (self.current_turn + 1) % len(self.players)
            
            # 라운드 관리는 게임 핸들러에서 별도로 처리
            # (자동 라운드 증가 제거)
            
            # 턴 시간 업데이트 (5초씩 감소)
            self.update_turn_time()
    
    def get_current_turn_time_ms(self) -> int:
        """현재 턴의 시간 제한 반환 (밀리초)"""
        return self.turn_time_limit_ms
    
    def get_current_turn_time_seconds(self) -> float:
        """현재 턴의 시간 제한 반환 (초)"""
        return self.turn_time_limit_ms / 1000.0
    
    def update_turn_time(self):
        """턴 시간 업데이트 (5초씩 감소, 최소 0.1초)"""
        old_time = self.turn_time_limit_ms / 1000.0
        new_time = self.initial_turn_time_ms - (self.total_turns * self.turn_time_reduction_ms)
        self.turn_time_limit_ms = max(self.min_turn_time_ms, new_time)
        new_time_sec = self.turn_time_limit_ms / 1000.0
        
        logger.debug(f"턴 시간 업데이트: R{self.current_round}T{self.total_turns} {old_time}초 → {new_time_sec}초")
    
    def is_time_up(self) -> bool:
        """시간이 최소값에 도달했는지 확인"""
        return self.turn_time_limit_ms <= self.min_turn_time_ms
    
    def complete_round(self):
        """라운드 완료 처리"""
        # 이전 라운드 정보 로그
        prev_round = self.current_round
        prev_time = self.turn_time_limit_ms / 1000.0
        
        # 다음 라운드로 이동
        self.current_round += 1
        self.current_turn = 0
        self.total_turns = 0
        
        # 턴 시간 초기화 (새 라운드는 다시 30초부터 시작)
        self.turn_time_limit_ms = self.initial_turn_time_ms
        
        # 단어 체인 초기화
        self.word_chain = WordChainState()
        
        logger.info(f"라운드 완료: R{prev_round}({prev_time}초) → R{self.current_round}({self.turn_time_limit_ms/1000.0}초)")
    
    def is_final_game_finished(self) -> bool:
        """모든 라운드가 완료되었는지 확인"""
        return self.current_round >= self.max_rounds
    
    def reset_players_for_next_game(self):
        """게임 완료 후 플레이어들을 준비 해제 상태로 만들기"""
        for player in self.players:
            player.status = PlayerStatus.WAITING.value
            # 점수와 게임 통계 모두 초기화
            player.score = 0
            player.words_submitted = 0
            player.current_combo = 0
            player.max_combo = 0
            player.items_used = 0
            player.timeouts = 0
            player.failed_attempts = 0
    
    def reset_game_state_for_new_game(self):
        """새 게임을 위한 완전한 게임 상태 초기화"""
        # 게임 진행 상태 초기화
        self.current_round = 1
        self.current_turn = 0
        self.total_turns = 0
        
        # 시간 시스템 초기화
        self.turn_time_limit_ms = self.initial_turn_time_ms
        
        # 단어 체인 초기화
        self.word_chain = WordChainState()
        
        # 타이머 초기화
        self.timer = None
        
        # 게임 상태 초기화
        self.status = GameStatus.WAITING.value
        self.started_at = None
        self.ended_at = None
        self.phase = "waiting"
        
        # 플레이어들 초기화
        self.reset_players_for_next_game()
    
    def get_final_rankings(self) -> List[Dict[str, Any]]:
        """최종 순위 반환"""
        sorted_players = sorted(self.players, key=lambda p: p.score, reverse=True)
        rankings = []
        for i, player in enumerate(sorted_players):
            rankings.append({
                "rank": i + 1,
                "user_id": player.user_id,
                "nickname": player.nickname,
                "score": player.score,
                "words_submitted": player.words_submitted,
                "max_combo": player.max_combo,
                "items_used": player.items_used
            })
        return rankings

    def add_player(self, player: GamePlayer) -> bool:
        """플레이어 추가"""
        # 중복 확인
        for existing_player in self.players:
            if existing_player.user_id == player.user_id:
                return False
        
        # 최대 인원 확인 (기본 8명)
        max_players = self.game_settings.get("max_players", 8)
        if len(self.players) >= max_players:
            return False
            
        self.players.append(player)
        return True

    def remove_player(self, user_id: int) -> bool:
        """플레이어 제거"""
        for i, player in enumerate(self.players):
            if player.user_id == user_id:
                del self.players[i]
                # 현재 턴 조정
                if i < self.current_turn:
                    self.current_turn -= 1
                elif i == self.current_turn and self.current_turn >= len(self.players):
                    self.current_turn = 0
                return True
        return False

    def is_game_finished(self) -> bool:
        """게임 종료 조건 확인 (점수제)"""
        return (self.current_round > self.max_rounds or
                self.status == GameStatus.FINISHED.value)

    def get_winner(self) -> Optional[GamePlayer]:
        """승자 반환"""
        if not self.players:
            return None
        return max(self.players, key=lambda p: p.score)

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "room_id": self.room_id,
            "status": self.status,
            "players": [p.to_dict() for p in self.players],
            "current_round": self.current_round,
            "current_turn": self.current_turn,
            "max_rounds": self.max_rounds,
            "turn_time_limit_ms": self.turn_time_limit_ms,
            "initial_turn_time_ms": self.initial_turn_time_ms,
            "turn_time_reduction_ms": self.turn_time_reduction_ms,
            "min_turn_time_ms": self.min_turn_time_ms,
            "total_turns": self.total_turns,
            "word_chain": self.word_chain.to_dict(),
            "timer": self.timer.to_dict() if self.timer else None,
            "game_settings": self.game_settings,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GameState':
        """딕셔너리에서 생성"""
        players = [GamePlayer.from_dict(p) for p in data.get("players", [])]
        word_chain = WordChainState.from_dict(data.get("word_chain", {}))
        timer_data = data.get("timer")
        timer = GameTimer.from_dict(timer_data) if timer_data else None
        
        return cls(
            room_id=data["room_id"],
            status=data.get("status", GameStatus.WAITING.value),
            players=players,
            current_round=data.get("current_round", 1),
            current_turn=data.get("current_turn", 0),
            max_rounds=data.get("max_rounds", 5),
            turn_time_limit_ms=data.get("turn_time_limit_ms", 30000),
            initial_turn_time_ms=data.get("initial_turn_time_ms", 30000),
            turn_time_reduction_ms=data.get("turn_time_reduction_ms", 5000),
            min_turn_time_ms=data.get("min_turn_time_ms", 100),
            total_turns=data.get("total_turns", 0),
            word_chain=word_chain,
            timer=timer,
            game_settings=data.get("game_settings", {}),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            ended_at=data.get("ended_at")
        )


class RedisGameManager:
    """Redis 게임 상태 관리자"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.GAME_KEY_PREFIX = "game:room:"
        self.TIMER_KEY_PREFIX = "timer:"
        self.SESSION_KEY_PREFIX = "session:"
        self.WORD_CACHE_PREFIX = "word:cache:"
        self.DEFAULT_TTL = 24 * 60 * 60  # 24시간

    def _get_game_key(self, room_id: str) -> str:
        """게임 상태 키 생성"""
        return f"{self.GAME_KEY_PREFIX}{room_id}"

    def _get_timer_key(self, room_id: str) -> str:
        """타이머 키 생성"""
        return f"{self.TIMER_KEY_PREFIX}{room_id}"

    def _get_session_key(self, user_id: int) -> str:
        """세션 키 생성"""
        return f"{self.SESSION_KEY_PREFIX}{user_id}"

    def _get_word_cache_key(self, word: str) -> str:
        """단어 캐시 키 생성"""
        return f"{self.WORD_CACHE_PREFIX}{word.lower()}"

    async def save_game_state(self, game_state: GameState) -> bool:
        """게임 상태 저장"""
        try:
            key = self._get_game_key(game_state.room_id)
            data = json.dumps(game_state.to_dict(), ensure_ascii=False)
            await self.redis.setex(key, self.DEFAULT_TTL, data)
            return True
        except Exception as e:
            logger.error(f"게임 상태 저장 실패: {e}")
            return False

    async def get_game_state(self, room_id: str) -> Optional[GameState]:
        """게임 상태 조회"""
        try:
            key = self._get_game_key(room_id)
            data = await self.redis.get(key)
            if data:
                return GameState.from_dict(json.loads(data))
            return None
        except Exception as e:
            logger.error(f"게임 상태 조회 실패: {e}")
            return None

    async def delete_game_state(self, room_id: str) -> bool:
        """게임 상태 삭제"""
        try:
            key = self._get_game_key(room_id)
            timer_key = self._get_timer_key(room_id)
            
            # 게임 상태와 타이머 모두 삭제
            result = await self.redis.delete(key, timer_key)
            
            logger = logging.getLogger(__name__)
            logger.info(f"방 삭제 완료: room_id={room_id}, 삭제된 키: {result}개")
            return True
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"게임 상태 삭제 실패: {e}")
            return False

    async def save_timer(self, room_id: str, timer: GameTimer) -> bool:
        """타이머 저장"""
        try:
            key = self._get_timer_key(room_id)
            data = json.dumps(timer.to_dict(), ensure_ascii=False)
            # 타이머는 만료 시간보다 약간 더 길게 TTL 설정
            ttl = max(timer.remaining_ms // 1000 + 10, 60)
            await self.redis.setex(key, ttl, data)
            logger.info(f"타이머 Redis 저장: room_id={room_id}, ttl={ttl}초, expires_at={timer.expires_at}")
            return True
        except Exception as e:
            logger.error(f"타이머 저장 실패: {e}")
            return False

    async def get_timer(self, room_id: str) -> Optional[GameTimer]:
        """타이머 조회"""
        try:
            key = self._get_timer_key(room_id)
            data = await self.redis.get(key)
            if data:
                timer = GameTimer.from_dict(json.loads(data))
                logger.info(f"타이머 Redis 조회 성공: room_id={room_id}, expires_at={timer.expires_at}")
                return timer
            else:
                logger.info(f"타이머 Redis 조회 실패: room_id={room_id}, 데이터 없음")
                return None
        except Exception as e:
            logger.error(f"타이머 조회 실패: {e}")
            return None

    async def cache_word_validation(self, word: str, is_valid: bool, word_info: Dict[str, Any] = None):
        """단어 검증 결과 캐시"""
        try:
            key = self._get_word_cache_key(word)
            data = {
                "is_valid": is_valid,
                "word_info": word_info or {},
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            # 1시간 캐시
            await self.redis.setex(key, 3600, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"단어 캐시 저장 실패: {e}")

    async def get_cached_word_validation(self, word: str) -> Optional[Dict[str, Any]]:
        """캐시된 단어 검증 결과 조회"""
        try:
            key = self._get_word_cache_key(word)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"단어 캐시 조회 실패: {e}")
            return None

    async def save_user_session(self, user_id: int, session_data: Dict[str, Any]) -> bool:
        """사용자 세션 저장"""
        try:
            key = self._get_session_key(user_id)
            data = json.dumps(session_data, ensure_ascii=False)
            await self.redis.setex(key, self.DEFAULT_TTL, data)
            return True
        except Exception as e:
            logger.error(f"세션 저장 실패: {e}")
            return False

    async def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 세션 조회"""
        try:
            key = self._get_session_key(user_id)
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"세션 조회 실패: {e}")
            return None

    async def get_all_active_games(self) -> List[str]:
        """모든 활성 게임 룸 ID 조회"""
        try:
            keys = await self.redis.keys(f"{self.GAME_KEY_PREFIX}*")
            return [key.replace(self.GAME_KEY_PREFIX, "") for key in keys]
        except Exception as e:
            logger.error(f"활성 게임 조회 실패: {e}")
            return []
    
    async def add_player_to_game(self, room_id: str, user_id: int, nickname: str) -> bool:
        """게임에 플레이어 추가"""
        try:
            # 게임 상태 가져오기 또는 생성
            game_state = await self.get_game_state(room_id)
            if not game_state:
                # 새 게임 상태 생성
                game_state = GameState(
                    room_id=room_id,
                    status=GameStatus.WAITING.value,
                    players=[],
                    word_chain=WordChainState(),
                    game_settings={"max_players": 8},  # GameConfig.MAX_PLAYERS와 일치
                    created_at=datetime.now(timezone.utc).isoformat()
                )
            
            # 플레이어 추가 (첫 번째 플레이어는 방장)
            is_host = len(game_state.players) == 0  # 첫 번째 플레이어가 방장
            logger.debug(f"플레이어 추가 - user_id={user_id}, nickname={nickname}, 현재 플레이어 수={len(game_state.players)}, is_host={is_host}")
            
            new_player = GamePlayer(
                user_id=user_id,
                nickname=nickname,
                score=0,
                status=PlayerStatus.WAITING.value,
                is_host=is_host,
                items=[]
            )
            
            if game_state.add_player(new_player):
                return await self.save_game_state(game_state)
            return False
            
        except Exception as e:
            logger.error(f"플레이어 게임 추가 실패: {e}")
            return False
    
    async def remove_player_from_game(self, room_id: str, user_id: int) -> bool:
        """게임에서 플레이어 제거"""
        try:
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return False
            
            if game_state.remove_player(user_id):
                # 플레이어가 모두 없으면 게임 삭제
                if not game_state.players:
                    return await self.delete_game_state(room_id)
                else:
                    return await self.save_game_state(game_state)
            return False
            
        except Exception as e:
            logger.error(f"플레이어 게임 제거 실패: {e}")
            return False
    
    async def update_game_state(self, game_state: GameState) -> bool:
        """게임 상태 업데이트 (save_game_state의 별칭)"""
        return await self.save_game_state(game_state)