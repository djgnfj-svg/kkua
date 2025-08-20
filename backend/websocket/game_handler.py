"""
게임 이벤트 핸들러
게임 로직 처리, 단어 검증, 아이템 사용, 점수 계산
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.dictionary_models import KoreanDictionary
from models.item_models import Item
from models.user_models import User, UserItem
from redis_models import RedisGameManager, GameState, GamePlayer, WordChainState
from database import get_redis
from websocket.connection_manager import WebSocketManager
import re

logger = logging.getLogger(__name__)


class GamePhase(str, Enum):
    """게임 단계"""
    WAITING = "waiting"        # 플레이어 대기
    READY = "ready"           # 준비 완료
    PLAYING = "playing"       # 게임 중
    PAUSED = "paused"         # 일시정지
    FINISHED = "finished"     # 게임 종료


class WordValidationResult(str, Enum):
    """단어 검증 결과"""
    VALID = "valid"           # 유효함
    INVALID_WORD = "invalid_word"        # 사전에 없는 단어
    INVALID_CHAIN = "invalid_chain"      # 끝말잇기 규칙 위반
    ALREADY_USED = "already_used"        # 이미 사용된 단어
    TOO_SHORT = "too_short"              # 너무 짧음 (2글자 미만)
    FORBIDDEN = "forbidden"              # 금지된 단어


class GameEventHandler:
    """게임 이벤트 처리 핸들러"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.redis_manager = RedisGameManager(get_redis())
        
        # 게임 설정
        self.min_word_length = 2
        self.max_word_length = 10
        self.turn_timeout = 30  # 30초
        self.max_players = 4
        self.min_players = 2
        
        # 금지된 단어 패턴 (욕설, 비속어 등)
        self.forbidden_patterns = [
            r'.*시발.*', r'.*씨발.*', r'.*개새.*', r'.*병신.*'
        ]
        
        # 활성 타이머 추적
        self.active_timers: Dict[str, asyncio.Task] = {}
    
    async def handle_join_game(self, room_id: str, user_id: int, nickname: str) -> bool:
        """게임 참가 처리"""
        try:
            # 게임 상태 확인
            game_state = await self.redis_manager.get_game_state(room_id)
            
            if not game_state:
                # 새 게임 생성
                game_state = GameState(
                    room_id=room_id,
                    phase=GamePhase.WAITING,
                    created_at=datetime.now(timezone.utc),
                    max_players=self.max_players
                )
                await self.redis_manager.create_game(room_id, game_state)
                logger.info(f"새 게임 생성: room_id={room_id}")
            
            # 게임 참가 가능 확인
            if game_state.phase not in [GamePhase.WAITING, GamePhase.READY]:
                logger.warning(f"게임 참가 불가 (진행 중): room_id={room_id}, phase={game_state.phase}")
                return False
            
            if len(game_state.players) >= self.max_players:
                logger.warning(f"게임 참가 불가 (인원 초과): room_id={room_id}")
                return False
            
            # 플레이어 추가
            await self.redis_manager.add_player_to_game(room_id, user_id, nickname)
            
            # 게임 상태 브로드캐스트
            updated_game_state = await self.redis_manager.get_game_state(room_id)
            await self._broadcast_game_state(room_id, updated_game_state)
            
            logger.info(f"게임 참가 완료: room_id={room_id}, user_id={user_id}")
            return True
                
        except Exception as e:
            logger.error(f"게임 참가 처리 중 오류: {e}")
            return False
    
    async def handle_leave_game(self, room_id: str, user_id: int) -> bool:
        """게임 나가기 처리"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return True  # 게임이 없으면 성공으로 처리
            
            # 게임 중이면 일시정지
            if game_state.phase == GamePhase.PLAYING:
                game_state.phase = GamePhase.PAUSED
                await self.redis_manager.update_game_state(room_id, game_state)
                
                # 타이머 정지
                await self._stop_turn_timer(room_id)
            
            # 플레이어 제거
            await self.redis_manager.remove_player_from_game(room_id, user_id)
            
            # 남은 플레이어 확인
            updated_game_state = await self.redis_manager.get_game_state(room_id)
            if not updated_game_state or len(updated_game_state.players) == 0:
                # 게임 종료
                await self._end_game(room_id, "모든 플레이어가 나갔습니다")
            else:
                # 게임 상태 브로드캐스트
                await self._broadcast_game_state(room_id, updated_game_state)
            
            logger.info(f"게임 나가기 완료: room_id={room_id}, user_id={user_id}")
            return True
            
        except Exception as e:
            logger.error(f"게임 나가기 처리 중 오류: {e}")
            return False
    
    async def handle_ready_game(self, room_id: str, user_id: int, ready: bool = True) -> bool:
        """게임 준비 상태 변경"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.phase not in [GamePhase.WAITING, GamePhase.READY]:
                return False
            
            # 플레이어 준비 상태 업데이트
            player = game_state.players.get(str(user_id))
            if not player:
                return False
            
            player.is_ready = ready
            await self.redis_manager.update_player_status(room_id, user_id, {"is_ready": ready})
            
            # 모든 플레이어가 준비되었는지 확인
            all_ready = all(p.is_ready for p in game_state.players.values())
            min_players_met = len(game_state.players) >= self.min_players
            
            if all_ready and min_players_met:
                game_state.phase = GamePhase.READY
                await self.redis_manager.update_game_state(room_id, game_state)
                
                # 5초 후 자동 시작
                asyncio.create_task(self._auto_start_game(room_id))
            else:
                game_state.phase = GamePhase.WAITING
                await self.redis_manager.update_game_state(room_id, game_state)
            
            await self._broadcast_game_state(room_id, game_state)
            
            logger.info(f"준비 상태 변경: room_id={room_id}, user_id={user_id}, ready={ready}")
            return True
            
        except Exception as e:
            logger.error(f"게임 준비 처리 중 오류: {e}")
            return False
    
    async def handle_start_game(self, room_id: str, user_id: int) -> bool:
        """게임 시작 처리"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.phase != GamePhase.READY:
                return False
            
            # 게임 시작 조건 확인
            if len(game_state.players) < self.min_players:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed",
                    "data": {"reason": f"최소 {self.min_players}명이 필요합니다"}
                })
                return False
            
            # 게임 상태 업데이트
            game_state.phase = GamePhase.PLAYING
            game_state.started_at = datetime.now(timezone.utc)
            
            # 첫 번째 플레이어 선택
            player_ids = list(game_state.players.keys())
            game_state.current_turn = int(player_ids[0])
            
            # 단어 체인 초기화
            word_chain = WordChainState()
            game_state.word_chain = word_chain
            
            await self.redis_manager.update_game_state(room_id, game_state)
            
            # 게임 시작 알림
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "game_started",
                "data": {
                    "room_id": room_id,
                    "started_at": game_state.started_at.isoformat(),
                    "current_turn": game_state.current_turn,
                    "turn_timeout": self.turn_timeout
                }
            })
            
            # 첫 번째 턴 시작
            await self._start_turn(room_id)
            
            logger.info(f"게임 시작: room_id={room_id}, players={len(game_state.players)}")
            return True
            
        except Exception as e:
            logger.error(f"게임 시작 처리 중 오류: {e}")
            return False
    
    async def handle_submit_word(self, room_id: str, user_id: int, word: str) -> bool:
        """단어 제출 처리"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.phase != GamePhase.PLAYING:
                await self._send_word_result(room_id, user_id, word, WordValidationResult.INVALID_WORD, "게임이 진행 중이 아닙니다")
                return False
            
            # 턴 확인
            if game_state.current_turn != user_id:
                await self._send_word_result(room_id, user_id, word, WordValidationResult.INVALID_WORD, "현재 턴이 아닙니다")
                return False
            
            # 단어 검증
            validation_result, message = await self._validate_word(room_id, word, game_state.word_chain)
            
            if validation_result == WordValidationResult.VALID:
                # 단어 추가 및 점수 계산
                await self._add_word_to_chain(room_id, user_id, word, game_state)
                
                # 다음 턴으로 이동
                await self._next_turn(room_id)
            else:
                # 실패 처리
                await self._handle_word_failure(room_id, user_id, validation_result)
            
            # 결과 전송
            await self._send_word_result(room_id, user_id, word, validation_result, message)
            
            logger.info(f"단어 제출 처리: room_id={room_id}, user_id={user_id}, word={word}, result={validation_result}")
            return validation_result == WordValidationResult.VALID
            
        except Exception as e:
            logger.error(f"단어 제출 처리 중 오류: {e}")
            return False
    
    async def handle_use_item(self, room_id: str, user_id: int, item_id: int, target_user_id: Optional[int] = None) -> bool:
        """아이템 사용 처리"""
        try:
            db = next(get_db())
            # 사용자 아이템 확인
            result = db.execute(
                select(UserItem, Item)
                .join(Item, UserItem.item_id == Item.item_id)
                .where(UserItem.user_id == user_id, UserItem.item_id == item_id, UserItem.quantity > 0)
            )
            user_item_data = result.first()
                
            if not user_item_data:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "item_use_failed",
                    "data": {"reason": "아이템을 보유하고 있지 않습니다"}
                })
                return False
            
            user_item, item = user_item_data
            
            # 게임 상태 확인
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.phase != GamePhase.PLAYING:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "item_use_failed",
                    "data": {"reason": "게임 중에만 아이템을 사용할 수 있습니다"}
                })
                return False
            
            # 쿨다운 확인
            if await self._is_item_on_cooldown(user_id, item_id):
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "item_use_failed",
                    "data": {"reason": "아이템이 쿨다운 중입니다"}
                })
                return False
            
            # 아이템 효과 실행
            success = await self._execute_item_effect(room_id, user_id, item, target_user_id)
            
            if success:
                # 아이템 소모
                user_item.quantity -= 1
                db.commit()
                
                # 쿨다운 설정
                await self._set_item_cooldown(user_id, item_id, item.cooldown_seconds)
                
                # 아이템 사용 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "item_used",
                    "data": {
                        "user_id": user_id,
                        "item_id": item_id,
                        "item_name": item.name,
                        "target_user_id": target_user_id,
                        "effect_description": item.description
                    }
                })
                
                logger.info(f"아이템 사용 완료: user_id={user_id}, item_id={item_id}")
            
            return success
                
        except Exception as e:
            logger.error(f"아이템 사용 처리 중 오류: {e}")
            return False
    
    async def _validate_word(self, room_id: str, word: str, word_chain: WordChainState) -> Tuple[WordValidationResult, str]:
        """단어 검증"""
        try:
            # 기본 검증
            if len(word) < self.min_word_length:
                return WordValidationResult.TOO_SHORT, f"단어는 최소 {self.min_word_length}글자 이상이어야 합니다"
            
            if len(word) > self.max_word_length:
                return WordValidationResult.TOO_SHORT, f"단어는 최대 {self.max_word_length}글자까지 가능합니다"
            
            # 금지어 확인
            for pattern in self.forbidden_patterns:
                if re.match(pattern, word):
                    return WordValidationResult.FORBIDDEN, "사용할 수 없는 단어입니다"
            
            # 이미 사용된 단어 확인
            if word in word_chain.used_words:
                return WordValidationResult.ALREADY_USED, "이미 사용된 단어입니다"
            
            # 끝말잇기 규칙 확인
            if word_chain.last_char:
                if word[0] != word_chain.last_char:
                    return WordValidationResult.INVALID_CHAIN, f"'{word_chain.last_char}'(으)로 시작하는 단어여야 합니다"
            
            # 사전 확인
            db = next(get_db())
            result = db.execute(
                select(KoreanDictionary).where(KoreanDictionary.word == word)
            )
            dict_entry = result.scalar_one_or_none()
                
            if not dict_entry:
                return WordValidationResult.INVALID_WORD, "사전에 없는 단어입니다"
            
            return WordValidationResult.VALID, "유효한 단어입니다"
            
        except Exception as e:
            logger.error(f"단어 검증 중 오류: {e}")
            return WordValidationResult.INVALID_WORD, "단어 검증 중 오류가 발생했습니다"
    
    async def _add_word_to_chain(self, room_id: str, user_id: int, word: str, game_state: GameState):
        """단어 체인에 추가 및 점수 계산"""
        try:
            db = next(get_db())
            # 단어 정보 조회
            result = db.execute(
                select(KoreanDictionary).where(KoreanDictionary.word == word)
            )
            dict_entry = result.scalar_one_or_none()
                
            if dict_entry:
                # 점수 계산
                base_score = dict_entry.calculate_score()
                word_chain = game_state.word_chain
                    
                # 연속 성공 보너스
                combo_bonus = min(word_chain.combo_count * 10, 100)
                
                # 시간 보너스 (빠른 답변)
                time_bonus = 0  # 타이머 구현 후 추가
                
                total_score = base_score + combo_bonus + time_bonus
                
                # 플레이어 점수 업데이트
                player = game_state.players[str(user_id)]
                player.score += total_score
                player.words_submitted += 1
                
                # 단어 체인 업데이트
                word_chain.used_words.add(word)
                word_chain.last_word = word
                word_chain.last_char = word[-1]
                word_chain.combo_count += 1
                word_chain.total_words += 1
                
                # Redis 업데이트
                await self.redis_manager.update_game_state(room_id, game_state)
                
                logger.info(f"단어 추가 완료: room_id={room_id}, user_id={user_id}, word={word}, score={total_score}")
            
        except Exception as e:
            logger.error(f"단어 체인 추가 중 오류: {e}")
    
    async def _next_turn(self, room_id: str):
        """다음 턴으로 이동"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return
            
            # 다음 플레이어 선택
            player_ids = list(game_state.players.keys())
            current_index = player_ids.index(str(game_state.current_turn))
            next_index = (current_index + 1) % len(player_ids)
            game_state.current_turn = int(player_ids[next_index])
            
            await self.redis_manager.update_game_state(room_id, game_state)
            
            # 턴 시작
            await self._start_turn(room_id)
            
        except Exception as e:
            logger.error(f"다음 턴 이동 중 오류: {e}")
    
    async def _start_turn(self, room_id: str):
        """턴 시작"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return
            
            # 현재 턴 알림
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "turn_started",
                "data": {
                    "current_turn": game_state.current_turn,
                    "nickname": game_state.players[str(game_state.current_turn)].nickname,
                    "timeout": self.turn_timeout,
                    "last_char": game_state.word_chain.last_char if game_state.word_chain else None
                }
            })
            
            # 턴 타이머 시작
            await self._start_turn_timer(room_id)
            
        except Exception as e:
            logger.error(f"턴 시작 중 오류: {e}")
    
    async def _start_turn_timer(self, room_id: str):
        """턴 타이머 시작"""
        try:
            # 기존 타이머 정지
            await self._stop_turn_timer(room_id)
            
            # 새 타이머 시작
            timer_task = asyncio.create_task(self._turn_timeout_handler(room_id))
            self.active_timers[room_id] = timer_task
            
        except Exception as e:
            logger.error(f"턴 타이머 시작 중 오류: {e}")
    
    async def _stop_turn_timer(self, room_id: str):
        """턴 타이머 정지"""
        if room_id in self.active_timers:
            timer_task = self.active_timers[room_id]
            if not timer_task.done():
                timer_task.cancel()
            del self.active_timers[room_id]
    
    async def _turn_timeout_handler(self, room_id: str):
        """턴 타임아웃 처리"""
        try:
            await asyncio.sleep(self.turn_timeout)
            
            # 타임아웃 처리
            game_state = await self.redis_manager.get_game_state(room_id)
            if game_state and game_state.phase == GamePhase.PLAYING:
                # 현재 플레이어 페널티
                current_player = game_state.players.get(str(game_state.current_turn))
                if current_player:
                    current_player.timeouts += 1
                
                # 타임아웃 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "turn_timeout",
                    "data": {
                        "user_id": game_state.current_turn,
                        "nickname": current_player.nickname if current_player else "알 수 없음"
                    }
                })
                
                # 다음 턴으로 이동
                await self._next_turn(room_id)
                
        except asyncio.CancelledError:
            pass  # 타이머 취소됨
        except Exception as e:
            logger.error(f"턴 타임아웃 처리 중 오류: {e}")
    
    async def _auto_start_game(self, room_id: str):
        """자동 게임 시작 (5초 후)"""
        try:
            await asyncio.sleep(5)
            
            game_state = await self.redis_manager.get_game_state(room_id)
            if game_state and game_state.phase == GamePhase.READY:
                await self.handle_start_game(room_id, list(game_state.players.keys())[0])
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"자동 게임 시작 중 오류: {e}")
    
    async def _broadcast_game_state(self, room_id: str, game_state: GameState):
        """게임 상태 브로드캐스트"""
        try:
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "game_state_update",
                "data": {
                    "room_id": room_id,
                    "phase": game_state.phase,
                    "players": {
                        str(uid): {
                            "user_id": player.user_id,
                            "nickname": player.nickname,
                            "score": player.score,
                            "is_ready": player.is_ready,
                            "is_alive": player.is_alive,
                            "words_submitted": player.words_submitted,
                            "timeouts": player.timeouts
                        }
                        for uid, player in game_state.players.items()
                    },
                    "current_turn": game_state.current_turn,
                    "word_chain": {
                        "last_word": game_state.word_chain.last_word if game_state.word_chain else None,
                        "last_char": game_state.word_chain.last_char if game_state.word_chain else None,
                        "combo_count": game_state.word_chain.combo_count if game_state.word_chain else 0,
                        "total_words": game_state.word_chain.total_words if game_state.word_chain else 0
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"게임 상태 브로드캐스트 중 오류: {e}")
    
    async def _send_word_result(self, room_id: str, user_id: int, word: str, result: WordValidationResult, message: str):
        """단어 검증 결과 전송"""
        await self.websocket_manager.broadcast_to_room(room_id, {
            "type": "word_validation_result",
            "data": {
                "user_id": user_id,
                "word": word,
                "result": result,
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        })
    
    async def _handle_word_failure(self, room_id: str, user_id: int, result: WordValidationResult):
        """단어 실패 처리"""
        try:
            game_state = await self.redis_manager.get_game_state(room_id)
            if game_state:
                player = game_state.players.get(str(user_id))
                if player:
                    player.failed_attempts += 1
                    
                    # 3번 실패시 탈락
                    if player.failed_attempts >= 3:
                        player.is_alive = False
                        
                        await self.websocket_manager.broadcast_to_room(room_id, {
                            "type": "player_eliminated",
                            "data": {
                                "user_id": user_id,
                                "nickname": player.nickname,
                                "reason": "3회 연속 실패"
                            }
                        })
                    
                    await self.redis_manager.update_game_state(room_id, game_state)
            
        except Exception as e:
            logger.error(f"단어 실패 처리 중 오류: {e}")
    
    async def _end_game(self, room_id: str, reason: str = "게임 종료"):
        """게임 종료"""
        try:
            # 타이머 정지
            await self._stop_turn_timer(room_id)
            
            # 게임 상태 업데이트
            game_state = await self.redis_manager.get_game_state(room_id)
            if game_state:
                game_state.phase = GamePhase.FINISHED
                game_state.ended_at = datetime.now(timezone.utc)
                await self.redis_manager.update_game_state(room_id, game_state)
                
                # 최종 결과 계산
                results = []
                for player in game_state.players.values():
                    results.append({
                        "user_id": player.user_id,
                        "nickname": player.nickname,
                        "score": player.score,
                        "words_submitted": player.words_submitted,
                        "is_alive": player.is_alive
                    })
                
                # 점수순 정렬
                results.sort(key=lambda x: x["score"], reverse=True)
                
                # 게임 종료 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "game_ended",
                    "data": {
                        "reason": reason,
                        "duration": (game_state.ended_at - game_state.started_at).total_seconds() if game_state.started_at else 0,
                        "results": results,
                        "total_words": game_state.word_chain.total_words if game_state.word_chain else 0
                    }
                })
            
            logger.info(f"게임 종료: room_id={room_id}, reason={reason}")
            
        except Exception as e:
            logger.error(f"게임 종료 처리 중 오류: {e}")
    
    async def _execute_item_effect(self, room_id: str, user_id: int, item: Item, target_user_id: Optional[int]) -> bool:
        """아이템 효과 실행"""
        try:
            # 아이템별 효과 처리 (임시 구현)
            logger.info(f"아이템 효과 실행: item_id={item.item_id}, name={item.name}")
            return True
            
        except Exception as e:
            logger.error(f"아이템 효과 실행 중 오류: {e}")
            return False
    
    async def _is_item_on_cooldown(self, user_id: int, item_id: int) -> bool:
        """아이템 쿨다운 확인"""
        # Redis에서 쿨다운 확인 (임시 구현)
        return False
    
    async def _set_item_cooldown(self, user_id: int, item_id: int, cooldown_seconds: int):
        """아이템 쿨다운 설정"""
        # Redis에 쿨다운 설정 (임시 구현)
        pass


# 전역 게임 핸들러 인스턴스
game_handler: Optional[GameEventHandler] = None


def get_game_handler(websocket_manager: WebSocketManager) -> GameEventHandler:
    """게임 핸들러 의존성"""
    global game_handler
    if game_handler is None:
        game_handler = GameEventHandler(websocket_manager)
    return game_handler