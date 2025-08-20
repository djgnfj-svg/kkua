"""
게임 엔진 서비스
게임 시작/종료, 턴 관리, 라운드 진행, 승리 조건 검사
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
from redis_models import RedisGameManager, GameState, GamePlayer, WordChainState
from database import get_redis, get_db
from models.game_models import GameRoom, GameSession
from models.user_models import User
from sqlalchemy import select

logger = logging.getLogger(__name__)


class GamePhase(str, Enum):
    """게임 단계"""
    LOBBY = "lobby"           # 로비 대기
    WAITING = "waiting"       # 플레이어 대기
    READY = "ready"          # 준비 완료
    STARTING = "starting"    # 게임 시작 중
    PLAYING = "playing"      # 게임 진행 중
    PAUSED = "paused"        # 일시 정지
    ENDING = "ending"        # 게임 종료 중
    FINISHED = "finished"    # 게임 완료


class GameEndReason(str, Enum):
    """게임 종료 사유"""
    COMPLETED = "completed"           # 정상 완료
    PLAYER_LEFT = "player_left"       # 플레이어 이탈
    TIME_LIMIT = "time_limit"         # 제한 시간 초과
    ADMIN_END = "admin_end"           # 관리자 종료
    ERROR = "error"                   # 오류 발생


@dataclass
class GameConfig:
    """게임 설정"""
    min_players: int = 2
    max_players: int = 4
    max_rounds: int = 10
    turn_timeout_seconds: int = 30
    min_word_length: int = 2
    max_word_length: int = 10
    auto_start_delay: int = 5  # 모든 플레이어 준비 완료 후 자동 시작 딜레이


class GameEngine:
    """게임 엔진 클래스"""
    
    def __init__(self):
        self.redis_manager = RedisGameManager(get_redis())
        self.config = GameConfig()
        
        # 활성 게임 추적
        self.active_games: Dict[str, GameState] = {}
        self.game_timers: Dict[str, asyncio.Task] = {}
        
        # 게임 모드 서비스 지연 로딩 (순환 import 방지)
        self._game_mode_service = None
    
    @property
    def game_mode_service(self):
        """게임 모드 서비스 지연 로딩"""
        if self._game_mode_service is None:
            from services.game_mode_service import get_game_mode_service
            self._game_mode_service = get_game_mode_service()
        return self._game_mode_service
    
    async def create_game(self, room_id: str, creator_id: int, game_settings: Optional[Dict[str, Any]] = None) -> bool:
        """게임 생성 (게임 모드 지원)"""
        try:
            # 기존 게임 확인
            existing_game = await self.redis_manager.get_game_state(room_id)
            if existing_game:
                logger.warning(f"이미 존재하는 게임: room_id={room_id}")
                return False
            
            # 게임 모드 설정 처리
            mode_type = game_settings.get("mode_type", "classic") if game_settings else "classic"
            mode_config = self.game_mode_service.get_mode_config(mode_type)
            
            if not mode_config:
                logger.error(f"존재하지 않는 게임 모드: {mode_type}")
                return False
            
            # 게임 설정 병합 (모드 설정 우선)
            merged_settings = {
                "min_players": mode_config.min_players,
                "max_players": mode_config.max_players,
                "turn_timeout": mode_config.rules.turn_time_limit,
                "max_rounds": mode_config.rules.max_rounds,
                "target_score": mode_config.rules.target_score,
                "mode_type": mode_type,
                "mode_config": mode_config.to_dict(),
                "team_mode": mode_config.team_mode,
                "spectator_mode": mode_config.spectator_mode,
                "allow_items": mode_config.rules.allow_items
            }
            
            if game_settings:
                # 사용자 설정으로 일부 오버라이드 (제한적)
                allowed_overrides = ["room_title", "password", "is_private"]
                for key in allowed_overrides:
                    if key in game_settings:
                        merged_settings[key] = game_settings[key]
            
            # 새 게임 상태 생성
            game_state = GameState(
                room_id=room_id,
                status=GamePhase.LOBBY.value,
                players=[],
                current_round=0,
                current_turn=0,
                max_rounds=merged_settings["max_rounds"],
                turn_time_limit_ms=merged_settings["turn_timeout"] * 1000,
                word_chain=WordChainState(),
                timer=None,
                game_settings=merged_settings,
                created_at=datetime.now(timezone.utc).isoformat(),
                started_at=None,
                ended_at=None
            )
            
            # Redis에 저장
            await self.redis_manager.create_game(room_id, game_state)
            self.active_games[room_id] = game_state
            
            # PostgreSQL에 게임룸 생성
            await self._create_game_room_record(room_id, creator_id, merged_settings)
            
            logger.info(f"게임 생성 완료: room_id={room_id}, creator_id={creator_id}")
            return True
            
        except Exception as e:
            logger.error(f"게임 생성 중 오류: {e}")
            return False
    
    async def join_game(self, room_id: str, user_id: int, nickname: str) -> Tuple[bool, str]:
        """게임 참가"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False, "존재하지 않는 게임입니다"
            
            # 게임 상태 확인
            if game_state.status not in [GamePhase.LOBBY.value, GamePhase.WAITING.value]:
                return False, f"게임 참가 불가 상태: {game_state.status}"
            
            # 이미 참가 중인지 확인
            for player in game_state.players:
                if player.user_id == user_id:
                    return False, "이미 게임에 참가했습니다"
            
            # 최대 인원 확인
            max_players = game_state.game_settings.get("max_players", self.config.max_players)
            if len(game_state.players) >= max_players:
                return False, f"게임이 가득 참 (최대 {max_players}명)"
            
            # 플레이어 추가
            new_player = GamePlayer(
                user_id=user_id,
                nickname=nickname,
                status="waiting",
                joined_at=datetime.now(timezone.utc).isoformat()
            )
            
            game_state.players.append(new_player)
            game_state.status = GamePhase.WAITING.value
            
            # Redis 업데이트
            await self.redis_manager.update_game_state(room_id, game_state)
            self.active_games[room_id] = game_state
            
            logger.info(f"게임 참가 완료: room_id={room_id}, user_id={user_id}")
            return True, "게임에 참가했습니다"
            
        except Exception as e:
            logger.error(f"게임 참가 중 오류: {e}")
            return False, "게임 참가 처리 중 오류가 발생했습니다"
    
    async def leave_game(self, room_id: str, user_id: int) -> Tuple[bool, str]:
        """게임 나가기"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False, "존재하지 않는 게임입니다"
            
            # 플레이어 제거
            player_found = False
            for i, player in enumerate(game_state.players):
                if player.user_id == user_id:
                    del game_state.players[i]
                    player_found = True
                    break
            
            if not player_found:
                return False, "게임에 참가하지 않은 사용자입니다"
            
            # 게임 중이면 일시정지
            if game_state.status == GamePhase.PLAYING.value:
                game_state.status = GamePhase.PAUSED.value
                await self._pause_game_timers(room_id)
            
            # 남은 플레이어 수 확인
            if len(game_state.players) == 0:
                # 모든 플레이어가 나간 경우 게임 종료
                await self.end_game(room_id, GameEndReason.PLAYER_LEFT, "모든 플레이어가 게임을 떠났습니다")
                return True, "게임을 나갔습니다 (게임 종료됨)"
            
            elif len(game_state.players) == 1 and game_state.status in [GamePhase.PLAYING.value, GamePhase.PAUSED.value]:
                # 1명만 남은 경우 게임 종료
                await self.end_game(room_id, GameEndReason.PLAYER_LEFT, "상대방이 게임을 떠났습니다")
                return True, "게임을 나갔습니다 (상대방 승리)"
            
            else:
                # 현재 턴 조정
                if game_state.current_turn >= len(game_state.players):
                    game_state.current_turn = 0
                
                # 게임이 일시정지 상태였다면 재개
                if game_state.status == GamePhase.PAUSED.value and len(game_state.players) >= self.config.min_players:
                    game_state.status = GamePhase.PLAYING.value
                    await self._resume_game_timers(room_id)
                
                await self.redis_manager.update_game_state(room_id, game_state)
                self.active_games[room_id] = game_state
            
            logger.info(f"게임 나가기 완료: room_id={room_id}, user_id={user_id}")
            return True, "게임을 나갔습니다"
            
        except Exception as e:
            logger.error(f"게임 나가기 중 오류: {e}")
            return False, "게임 나가기 처리 중 오류가 발생했습니다"
    
    async def ready_player(self, room_id: str, user_id: int, ready: bool = True) -> Tuple[bool, str]:
        """플레이어 준비 상태 변경"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False, "존재하지 않는 게임입니다"
            
            if game_state.status not in [GamePhase.WAITING.value, GamePhase.READY.value]:
                return False, f"준비 불가 상태: {game_state.status}"
            
            # 플레이어 찾기 및 상태 업데이트
            player_found = False
            for player in game_state.players:
                if player.user_id == user_id:
                    player.status = "ready" if ready else "waiting"
                    player_found = True
                    break
            
            if not player_found:
                return False, "게임에 참가하지 않은 사용자입니다"
            
            # 모든 플레이어 준비 상태 확인
            min_players = game_state.game_settings.get("min_players", self.config.min_players)
            all_ready = len(game_state.players) >= min_players and all(p.status == "ready" for p in game_state.players)
            
            if all_ready:
                game_state.status = GamePhase.READY.value
                # 자동 시작 타이머 설정
                await self._start_auto_start_timer(room_id)
            else:
                game_state.status = GamePhase.WAITING.value
                # 자동 시작 타이머 취소
                await self._cancel_auto_start_timer(room_id)
            
            await self.redis_manager.update_game_state(room_id, game_state)
            self.active_games[room_id] = game_state
            
            status_msg = "준비 완료" if ready else "준비 취소"
            logger.info(f"플레이어 준비 상태 변경: room_id={room_id}, user_id={user_id}, ready={ready}")
            return True, status_msg
            
        except Exception as e:
            logger.error(f"플레이어 준비 상태 변경 중 오류: {e}")
            return False, "준비 상태 변경 처리 중 오류가 발생했습니다"
    
    async def start_game(self, room_id: str, admin_user_id: Optional[int] = None) -> Tuple[bool, str]:
        """게임 시작"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False, "존재하지 않는 게임입니다"
            
            if game_state.status != GamePhase.READY.value:
                return False, f"게임 시작 불가 상태: {game_state.status}"
            
            # 최소 인원 확인
            min_players = game_state.game_settings.get("min_players", self.config.min_players)
            if len(game_state.players) < min_players:
                return False, f"최소 {min_players}명이 필요합니다"
            
            # 모든 플레이어 준비 확인
            if not all(p.status == "ready" for p in game_state.players):
                return False, "모든 플레이어가 준비되지 않았습니다"
            
            # 게임 모드 설정 확인
            mode_type = game_state.game_settings.get("mode_type", "classic")
            mode_config = self.game_mode_service.get_mode_config(mode_type)
            
            # 팀 구성 (팀전 모드인 경우)
            teams = []
            if mode_config and mode_config.team_mode.value != "no_teams":
                teams = await self.game_mode_service.setup_teams(
                    room_id, game_state.players, mode_config.team_mode
                )
                logger.info(f"팀 구성 완료: room_id={room_id}, teams={len(teams)}")
            
            # 게임 시작 처리
            game_state.status = GamePhase.STARTING.value
            game_state.started_at = datetime.now(timezone.utc).isoformat()
            game_state.current_round = 1
            game_state.current_turn = 0
            
            # 모든 플레이어 상태를 playing으로 변경
            for player in game_state.players:
                player.status = "playing"
            
            # 단어 체인 초기화
            game_state.word_chain = WordChainState()
            
            await self.redis_manager.update_game_state(room_id, game_state)
            self.active_games[room_id] = game_state
            
            # 게임 세션 기록 생성
            await self._create_game_session_record(room_id, game_state)
            
            # 게임 상태를 PLAYING으로 변경하고 첫 턴 시작
            game_state.status = GamePhase.PLAYING.value
            await self.redis_manager.update_game_state(room_id, game_state)
            self.active_games[room_id] = game_state
            
            logger.info(f"게임 시작 완료: room_id={room_id}, players={len(game_state.players)}")
            return True, "게임이 시작되었습니다"
            
        except Exception as e:
            logger.error(f"게임 시작 중 오류: {e}")
            return False, "게임 시작 처리 중 오류가 발생했습니다"
    
    async def next_turn(self, room_id: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """다음 턴으로 이동"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.status != GamePhase.PLAYING.value:
                return False, "게임이 진행 중이 아닙니다", None
            
            # 다음 플레이어로 턴 이동
            game_state.current_turn = (game_state.current_turn + 1) % len(game_state.players)
            
            # 라운드 완료 확인 (모든 플레이어가 한 번씩 턴을 가졌는지)
            if game_state.current_turn == 0:
                game_state.current_round += 1
                
                # 최대 라운드 확인
                if game_state.current_round > game_state.max_rounds:
                    await self.end_game(room_id, GameEndReason.COMPLETED, "최대 라운드 도달")
                    return True, "게임이 종료되었습니다", {"game_ended": True}
            
            await self.redis_manager.update_game_state(room_id, game_state)
            self.active_games[room_id] = game_state
            
            current_player = game_state.players[game_state.current_turn]
            turn_info = {
                "current_turn": game_state.current_turn,
                "current_player": {
                    "user_id": current_player.user_id,
                    "nickname": current_player.nickname
                },
                "current_round": game_state.current_round,
                "max_rounds": game_state.max_rounds,
                "last_char": game_state.word_chain.last_char
            }
            
            logger.info(f"다음 턴 이동: room_id={room_id}, turn={game_state.current_turn}, round={game_state.current_round}")
            return True, "다음 턴으로 이동했습니다", turn_info
            
        except Exception as e:
            logger.error(f"다음 턴 이동 중 오류: {e}")
            return False, "턴 이동 처리 중 오류가 발생했습니다", None
    
    async def end_game(self, room_id: str, reason: GameEndReason, message: str) -> bool:
        """게임 종료"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False
            
            # 게임 타이머 정리
            await self._cleanup_game_timers(room_id)
            
            # 게임 상태 업데이트
            game_state.status = GamePhase.FINISHED.value
            game_state.ended_at = datetime.now(timezone.utc).isoformat()
            
            # 최종 순위 계산
            results = self._calculate_final_rankings(game_state)
            
            await self.redis_manager.update_game_state(room_id, game_state)
            
            # 게임 세션 업데이트
            await self._update_game_session_record(room_id, game_state, reason.value, results)
            
            # 활성 게임에서 제거
            if room_id in self.active_games:
                del self.active_games[room_id]
            
            logger.info(f"게임 종료: room_id={room_id}, reason={reason.value}, message={message}")
            return True
            
        except Exception as e:
            logger.error(f"게임 종료 중 오류: {e}")
            return False
    
    async def get_game_state(self, room_id: str) -> Optional[GameState]:
        """게임 상태 조회"""
        if room_id in self.active_games:
            return self.active_games[room_id]
        
        return await self.redis_manager.get_game_state(room_id)
    
    def _calculate_final_rankings(self, game_state: GameState) -> List[Dict[str, Any]]:
        """최종 순위 계산"""
        results = []
        for i, player in enumerate(game_state.players):
            results.append({
                "user_id": player.user_id,
                "nickname": player.nickname,
                "score": player.score,
                "words_submitted": player.words_submitted,
                "items_used": player.items_used,
                "rank": 0  # 점수 기준으로 나중에 계산
            })
        
        # 점수 기준으로 정렬
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # 순위 할당
        for i, result in enumerate(results):
            result["rank"] = i + 1
        
        return results
    
    async def _start_auto_start_timer(self, room_id: str):
        """자동 시작 타이머 시작"""
        timer_key = f"auto_start_{room_id}"
        if timer_key in self.game_timers:
            self.game_timers[timer_key].cancel()
        
        async def auto_start():
            await asyncio.sleep(self.config.auto_start_delay)
            await self.start_game(room_id)
        
        self.game_timers[timer_key] = asyncio.create_task(auto_start())
    
    async def _cancel_auto_start_timer(self, room_id: str):
        """자동 시작 타이머 취소"""
        timer_key = f"auto_start_{room_id}"
        if timer_key in self.game_timers:
            self.game_timers[timer_key].cancel()
            del self.game_timers[timer_key]
    
    async def _pause_game_timers(self, room_id: str):
        """게임 타이머 일시정지"""
        # 실제 타이머 서비스와 연동 (Phase 3에서 구현)
        pass
    
    async def _resume_game_timers(self, room_id: str):
        """게임 타이머 재개"""
        # 실제 타이머 서비스와 연동 (Phase 3에서 구현)
        pass
    
    async def _cleanup_game_timers(self, room_id: str):
        """게임 관련 모든 타이머 정리"""
        keys_to_remove = []
        for key in self.game_timers:
            if room_id in key:
                self.game_timers[key].cancel()
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.game_timers[key]
    
    async def _create_game_room_record(self, room_id: str, creator_id: int, settings: Dict[str, Any]):
        """PostgreSQL에 게임룸 기록 생성"""
        try:
            db = next(get_db())
            
            game_room = GameRoom(
                room_id=room_id,
                creator_id=creator_id,
                max_players=settings.get("max_players", self.config.max_players),
                game_mode="word_chain",
                settings=settings,
                status="active"
            )
            
            db.add(game_room)
            db.commit()
            
        except Exception as e:
            logger.error(f"게임룸 기록 생성 중 오류: {e}")
    
    async def _create_game_session_record(self, room_id: str, game_state: GameState):
        """PostgreSQL에 게임 세션 기록 생성"""
        try:
            db = next(get_db())
            
            game_session = GameSession(
                room_id=room_id,
                player_count=len(game_state.players),
                max_rounds=game_state.max_rounds,
                started_at=datetime.fromisoformat(game_state.started_at.replace('Z', '+00:00'))
            )
            
            db.add(game_session)
            db.commit()
            
        except Exception as e:
            logger.error(f"게임 세션 기록 생성 중 오류: {e}")
    
    async def _update_game_session_record(self, room_id: str, game_state: GameState, end_reason: str, results: List[Dict[str, Any]]):
        """PostgreSQL 게임 세션 기록 업데이트"""
        try:
            db = next(get_db())
            
            # 게임 세션 조회 및 업데이트
            result = db.execute(
                select(GameSession).where(GameSession.room_id == room_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                session.ended_at = datetime.fromisoformat(game_state.ended_at.replace('Z', '+00:00'))
                session.winner_id = results[0]["user_id"] if results else None
                session.total_words = game_state.word_chain.total_words
                session.final_scores = {str(r["user_id"]): r["score"] for r in results}
                session.end_reason = end_reason
                
                db.commit()
            
        except Exception as e:
            logger.error(f"게임 세션 기록 업데이트 중 오류: {e}")
    
    async def submit_word(self, room_id: str, user_id: int, word: str) -> Tuple[bool, str, Optional[Any], Optional[Any]]:
        """단어 제출 처리"""
        try:
            # 게임 상태 조회
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return False, "게임을 찾을 수 없습니다", None, None
            
            # 게임이 진행 중인지 확인
            if game_state.status != "playing":
                return False, "게임이 진행 중이 아닙니다", None, None
            
            # 현재 턴인지 확인
            current_player = game_state.get_current_player()
            if not current_player or current_player.user_id != user_id:
                return False, "현재 당신의 차례가 아닙니다", None, None
            
            # 단어 유효성 검사 (임시로 간단히 처리)
            if len(word.strip()) < 2:
                return False, "2글자 이상의 단어를 입력해주세요", None, None
            
            # 끝말잇기 규칙 확인
            if game_state.word_chain.words:
                last_char = game_state.word_chain.current_char
                if word[0] != last_char:
                    return False, f"'{last_char}'로 시작하는 단어를 입력해주세요", None, None
            
            # 단어 체인에 추가
            game_state.word_chain.words.append(word)
            game_state.word_chain.used_words.append(word)
            game_state.word_chain.last_word = word
            game_state.word_chain.current_char = word[-1]  # 마지막 글자
            
            # 플레이어 점수 및 통계 업데이트
            current_player.words_submitted += 1
            current_player.score += 10  # 기본 점수
            
            # 플레이어 시간 감소 (매 턴마다 2초씩 감소)
            new_time = current_player.reduce_time()
            logger.info(f"플레이어 {current_player.nickname}의 남은 시간: {current_player.get_remaining_seconds()}초")
            
            # 다음 턴으로 이동
            game_state.next_turn()
            
            # 게임 상태 저장
            await self.redis_manager.save_game_state(game_state)
            
            logger.info(f"단어 제출 성공: room_id={room_id}, user_id={user_id}, word={word}, next_turn={game_state.current_turn}")
            
            return True, "단어 제출 성공", None, None
            
        except Exception as e:
            logger.error(f"단어 제출 중 오류: {e}")
            return False, "단어 제출 처리 중 오류가 발생했습니다", None, None


# 전역 게임 엔진 인스턴스
game_engine = GameEngine()


def get_game_engine() -> GameEngine:
    """게임 엔진 의존성"""
    return game_engine