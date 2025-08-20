"""
게임 이벤트 핸들러
게임 로직 처리, 단어 검증, 아이템 사용, 점수 계산
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy import select
from database import get_db
from models.item_models import Item
from models.user_models import UserItem
from redis_models import RedisGameManager
from database import get_redis
from websocket.connection_manager import WebSocketManager
from services.game_engine import get_game_engine
from services.word_validator import get_word_validator
from services.timer_service import get_timer_service
from services.score_calculator import get_score_calculator

logger = logging.getLogger(__name__)


# 서비스에서 필요한 설정값들
class GameConfig:
    """게임 설정"""
    MIN_PLAYERS = 2
    MAX_PLAYERS = 8
    TURN_TIMEOUT = 30
    MIN_WORD_LENGTH = 2
    MAX_WORD_LENGTH = 10
    MAX_FAILED_ATTEMPTS = 3


class GameEventHandler:
    """게임 이벤트 처리 핸들러"""
    
    def __init__(self, websocket_manager: WebSocketManager):
        self.websocket_manager = websocket_manager
        self.redis_manager = RedisGameManager(get_redis())
        
        # 서비스 의존성
        self.game_engine = get_game_engine()
        self.word_validator = get_word_validator()
        self.timer_service = get_timer_service()
        self.score_calculator = get_score_calculator()
        
        # 게임 설정
        self.config = GameConfig()
        
        # 활성 타이머 추적
        self.active_timers = {}
    
    async def handle_join_game(self, room_id: str, user_id: int, nickname: str) -> bool:
        """게임 참가 처리"""
        try:
            # 게임 엔진을 통한 게임 참가
            success, message = await self.game_engine.join_game(room_id, user_id, nickname)
            
            if success:
                # 참가 성공 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_joined",
                    "data": {
                        "user_id": user_id,
                        "nickname": nickname,
                        "message": message
                    }
                })
                
                # 게임 상태 브로드캐스트
                game_state = await self.game_engine.get_game_state(room_id)
                if game_state:
                    await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"게임 참가 완료: room_id={room_id}, user_id={user_id}")
            else:
                # 참가 실패 알림
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "join_game_failed",
                    "data": {"reason": message}
                })
                logger.warning(f"게임 참가 실패: room_id={room_id}, user_id={user_id}, reason={message}")
            
            return success
                
        except Exception as e:
            logger.error(f"게임 참가 처리 중 오류: {e}")
            return False
    
    async def handle_leave_game(self, room_id: str, user_id: int) -> bool:
        """게임 나가기 처리"""
        try:
            # 사용자 타이머 정리
            await self.timer_service.cleanup_user_timers(room_id, user_id)
            
            # 게임 엔진을 통한 게임 나가기
            success, message = await self.game_engine.leave_game(room_id, user_id)
            
            if success:
                # 나가기 성공 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_left",
                    "data": {
                        "user_id": user_id,
                        "message": message
                    }
                })
                
                # 게임 상태 브로드캐스트
                game_state = await self.game_engine.get_game_state(room_id)
                if game_state:
                    await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"게임 나가기 완료: room_id={room_id}, user_id={user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"게임 나가기 처리 중 오류: {e}")
            return False
    
    async def handle_ready_game(self, room_id: str, user_id: int, ready: bool = True) -> bool:
        """게임 준비 상태 변경"""
        try:
            # 게임 엔진을 통한 준비 상태 변경
            success, message = await self.game_engine.ready_player(room_id, user_id, ready)
            
            if success:
                # 준비 상태 변경 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_ready_changed",
                    "data": {
                        "user_id": user_id,
                        "ready": ready,
                        "message": message
                    }
                })
                
                # 게임 상태 브로드캐스트
                game_state = await self.game_engine.get_game_state(room_id)
                if game_state:
                    await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"준비 상태 변경: room_id={room_id}, user_id={user_id}, ready={ready}")
            
            return success
            
        except Exception as e:
            logger.error(f"게임 준비 처리 중 오류: {e}")
            return False
    
    async def handle_start_game(self, room_id: str, user_id: int) -> bool:
        """게임 시작 처리"""
        try:
            # 게임 엔진을 통한 게임 시작
            success, message = await self.game_engine.start_game(room_id, user_id)
            
            if success:
                # 게임 시작 알림
                game_state = await self.game_engine.get_game_state(room_id)
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "game_started",
                    "data": {
                        "room_id": room_id,
                        "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
                        "current_turn": game_state.current_turn,
                        "message": message
                    }
                })
                
                # 첫 번째 턴 타이머 시작
                if game_state.current_turn:
                    await self.timer_service.create_turn_timer(
                        room_id=room_id,
                        user_id=game_state.current_turn,
                        callback=self._on_turn_timeout
                    )
                
                # 게임 상태 브로드캐스트
                await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"게임 시작 완료: room_id={room_id}, message={message}")
            else:
                # 시작 실패 알림
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed",
                    "data": {"reason": message}
                })
                logger.warning(f"게임 시작 실패: room_id={room_id}, reason={message}")
            
            return success
            
        except Exception as e:
            logger.error(f"게임 시작 처리 중 오류: {e}")
            return False
    
    async def handle_submit_word(self, room_id: str, user_id: int, word: str) -> bool:
        """단어 제출 처리"""
        try:
            # 턴 타이머 정지
            await self.timer_service.cancel_user_timers(room_id, user_id)
            
            # 응답 시간 측정
            response_start = datetime.now(timezone.utc)
            
            # 게임 엔진을 통한 단어 제출
            success, message, word_info, score_breakdown = await self.game_engine.submit_word(
                room_id, user_id, word
            )
            
            # 응답 시간 계산
            response_time = (datetime.now(timezone.utc) - response_start).total_seconds()
            
            if success:
                # 단어 성공 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "word_submitted",
                    "data": {
                        "user_id": user_id,
                        "word": word,
                        "word_info": word_info.to_dict() if word_info else None,
                        "score_breakdown": score_breakdown.to_dict() if score_breakdown else None,
                        "response_time": response_time,
                        "message": message
                    }
                })
                
                # 다음 턴 시작
                game_state = await self.game_engine.get_game_state(room_id)
                if game_state and game_state.current_turn:
                    await self.timer_service.create_turn_timer(
                        room_id=room_id,
                        user_id=game_state.current_turn,
                        callback=self._on_turn_timeout
                    )
                
                # 게임 상태 브로드캐스트
                await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"단어 제출 성공: room_id={room_id}, user_id={user_id}, word={word}")
            else:
                # 단어 실패 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "word_failed",
                    "data": {
                        "user_id": user_id,
                        "word": word,
                        "reason": message,
                        "response_time": response_time
                    }
                })
                
                logger.warning(f"단어 제출 실패: room_id={room_id}, user_id={user_id}, word={word}, reason={message}")
            
            return success
            
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
    
    async def _on_turn_timeout(self, room_id: str, user_id: int):
        """턴 타임아웃 콜백"""
        try:
            # 게임 엔진을 통한 턴 스킵
            success, message = await self.game_engine.skip_turn(room_id, user_id, "시간 초과")
            
            if success:
                # 타임아웃 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "turn_timeout",
                    "data": {
                        "user_id": user_id,
                        "message": message
                    }
                })
                
                # 다음 턴 시작
                game_state = await self.game_engine.get_game_state(room_id)
                if game_state and game_state.current_turn:
                    await self.timer_service.create_turn_timer(
                        room_id=room_id,
                        user_id=game_state.current_turn,
                        callback=self._on_turn_timeout
                    )
                
                # 게임 상태 브로드캐스트
                await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"턴 타임아웃 처리: room_id={room_id}, user_id={user_id}")
                
        except Exception as e:
            logger.error(f"턴 타임아웃 처리 중 오류: {e}")
    
    async def _broadcast_game_state(self, room_id: str, game_state=None):
        """게임 상태 브로드캐스트"""
        try:
            if not game_state:
                game_state = await self.game_engine.get_game_state(room_id)
            
            if not game_state:
                return
            
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
                            "timeouts": player.timeouts,
                            "failed_attempts": player.failed_attempts,
                            "max_combo": player.max_combo
                        }
                        for uid, player in game_state.players.items()
                    },
                    "current_turn": game_state.current_turn,
                    "word_chain": {
                        "last_word": game_state.word_chain.last_word if game_state.word_chain else None,
                        "last_char": game_state.word_chain.last_char if game_state.word_chain else None,
                        "combo_count": game_state.word_chain.combo_count if game_state.word_chain else 0,
                        "total_words": game_state.word_chain.total_words if game_state.word_chain else 0
                    },
                    "started_at": game_state.started_at.isoformat() if game_state.started_at else None,
                    "ended_at": game_state.ended_at.isoformat() if game_state.ended_at else None
                }
            })
            
        except Exception as e:
            logger.error(f"게임 상태 브로드캐스트 중 오류: {e}")
    
    async def cleanup_room_timers(self, room_id: str):
        """룸 타이머 정리"""
        try:
            await self.timer_service.cleanup_room_timers(room_id)
            if room_id in self.active_timers:
                del self.active_timers[room_id]
        except Exception as e:
            logger.error(f"룸 타이머 정리 중 오류: {e}")
    
    async def handle_get_word_hints(self, room_id: str, user_id: int, count: int = 3) -> List[str]:
        """단어 힌트 요청 처리"""
        try:
            game_state = await self.game_engine.get_game_state(room_id)
            if not game_state or not game_state.word_chain:
                return []
            
            last_char = game_state.word_chain.last_char
            if not last_char:
                return []
            
            hints = await self.word_validator.get_word_hints(last_char, count)
            
            # 힌트 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "word_hints",
                "data": {
                    "last_char": last_char,
                    "hints": hints
                }
            })
            
            return hints
            
        except Exception as e:
            logger.error(f"단어 힌트 요청 처리 중 오류: {e}")
            return []
    
    async def handle_end_game(self, room_id: str, reason: str = "게임 종료") -> bool:
        """게임 종료 처리"""
        try:
            # 모든 타이머 정리
            await self.cleanup_room_timers(room_id)
            
            # 게임 엔진을 통한 게임 종료
            success, message, final_results = await self.game_engine.end_game(room_id, reason)
            
            if success:
                # 게임 종료 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "game_ended",
                    "data": {
                        "reason": reason,
                        "message": message,
                        "final_results": final_results
                    }
                })
                
                logger.info(f"게임 종료 완료: room_id={room_id}, reason={reason}")
            
            return success
            
        except Exception as e:
            logger.error(f"게임 종료 처리 중 오류: {e}")
            return False
    
    async def handle_get_game_stats(self, room_id: str, user_id: int) -> Dict[str, Any]:
        """게임 통계 요청 처리"""
        try:
            game_state = await self.game_engine.get_game_state(room_id)
            if not game_state:
                return {}
            
            stats = {
                "game_duration": 0,
                "total_words": game_state.word_chain.total_words if game_state.word_chain else 0,
                "current_combo": game_state.word_chain.combo_count if game_state.word_chain else 0,
                "players_count": len(game_state.players),
                "active_players": len([p for p in game_state.players.values() if p.is_alive]),
                "phase": game_state.phase
            }
            
            if game_state.started_at:
                current_time = game_state.ended_at or datetime.now(timezone.utc)
                stats["game_duration"] = (current_time - game_state.started_at).total_seconds()
            
            # 통계 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "game_stats",
                "data": stats
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"게임 통계 요청 처리 중 오류: {e}")
            return {}
    
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