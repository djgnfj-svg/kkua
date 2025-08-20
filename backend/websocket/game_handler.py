"""
게임 이벤트 핸들러
게임 로직 처리, 단어 검증, 아이템 사용, 점수 계산
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from database import get_db
from models.item_models import Item
from models.user_models import UserItem
from redis_models import RedisGameManager, GameState
from database import get_redis
from websocket.connection_manager import WebSocketManager
from services.game_engine import get_game_engine
from services.word_validator import get_word_validator
from services.timer_service import get_timer_service
from services.score_calculator import get_score_calculator
from services.item_service import get_item_service
from services.game_mode_service import get_game_mode_service

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
        self.item_service = get_item_service()
        self.game_mode_service = get_game_mode_service()
        
        # 룸별 활성 타이머 태스크 추적
        self.active_timer_tasks: Dict[str, asyncio.Task] = {}
        
        # 게임 설정
        self.config = GameConfig()
        
        # 활성 타이머 추적
        self.active_timers = {}
    
    async def handle_join_game(self, room_id: str, user_id: int, nickname: str) -> bool:
        """게임 참가 처리"""
        try:
            # Redis를 통한 게임 참가
            success = await self.redis_manager.add_player_to_game(room_id, user_id, nickname)
            
            if success:
                # 게임 상태 가져오기
                game_state = await self.redis_manager.get_game_state(room_id)
                
                # 현재 플레이어 찾기
                current_player = None
                for player in game_state.players:
                    if player.user_id == user_id:
                        current_player = player
                        break
                
                # 참가 성공 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_joined",
                    "data": {
                        "user_id": user_id,
                        "nickname": nickname,
                        "is_host": current_player.is_host if current_player else False,
                        "message": f"{nickname}님이 입장했습니다"
                    }
                })
                
                # 전체 게임 상태 브로드캐스트
                await self._broadcast_redis_game_state(room_id, game_state)
                
                logger.info(f"게임 참가 완료: room_id={room_id}, user_id={user_id}, is_host={current_player.is_host if current_player else False}")
            else:
                # 참가 실패 알림
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "join_game_failed",
                    "data": {"reason": "이미 게임에 참가했습니다"}
                })
                logger.warning(f"게임 참가 실패: room_id={room_id}, user_id={user_id}, reason=이미 게임에 참가했습니다")
            
            return success
                
        except Exception as e:
            logger.error(f"게임 참가 처리 중 오류: {e}")
            return False
    
    async def handle_leave_game(self, room_id: str, user_id: int) -> bool:
        """게임 나가기 처리"""
        try:
            # 사용자 타이머 정리
            await self.timer_service.cleanup_user_timers(room_id, user_id)
            
            # 게임 상태 가져오기 (나가기 전에 플레이어 정보 확인)
            game_state = await self.redis_manager.get_game_state(room_id)
            leaving_player = None
            if game_state:
                for player in game_state.players:
                    if player.user_id == user_id:
                        leaving_player = player
                        break
            
            # 나가기 알림 (연결이 끊어지기 전에 다른 사용자들에게만 전송)
            if leaving_player:
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_left",
                    "data": {
                        "user_id": user_id,
                        "nickname": leaving_player.nickname,
                        "message": f"{leaving_player.nickname}님이 퇴장했습니다"
                    }
                }, exclude_user=user_id)  # 나가는 사용자는 제외
                
                logger.info(f"게임 나가기 알림 완료: room_id={room_id}, user_id={user_id}, nickname={leaving_player.nickname}")
            
            return True
            
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
    
    async def handle_player_ready(self, room_id: str, user_id: int, ready_status: bool) -> bool:
        """플레이어 준비 상태 변경 처리"""
        try:
            # 게임 상태 가져오기
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                logger.error(f"게임 상태 없음: room_id={room_id}")
                return False
            
            # 플레이어 찾기 및 상태 업데이트
            player_found = False
            from redis_models import PlayerStatus
            
            for player in game_state.players:
                if player.user_id == user_id:
                    player.status = PlayerStatus.READY.value if ready_status else PlayerStatus.WAITING.value
                    player_found = True
                    break
            
            if not player_found:
                logger.error(f"플레이어를 찾을 수 없음: user_id={user_id}, room_id={room_id}")
                return False
            
            # 게임 상태 저장
            await self.redis_manager.save_game_state(game_state)
            
            # 플레이어 정보 찾기
            current_player = None
            for player in game_state.players:
                if player.user_id == user_id:
                    current_player = player
                    break
            
            # 준비 상태 변경 알림
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "player_ready_status",
                "data": {
                    "user_id": user_id,
                    "nickname": current_player.nickname if current_player else "Unknown",
                    "ready": ready_status
                }
            })
            
            # 전체 게임 상태 브로드캐스트
            await self._broadcast_redis_game_state(room_id, game_state)
            
            logger.info(f"플레이어 준비 상태 변경 완료: room_id={room_id}, user_id={user_id}, ready={ready_status}")
            return True
            
        except Exception as e:
            logger.error(f"플레이어 준비 처리 중 오류: {e}")
            return False

    async def handle_start_game(self, room_id: str, user_id: int) -> bool:
        """게임 시작 처리"""
        try:
            logger.info(f"게임 시작 처리: room_id={room_id}, user_id={user_id}")
            
            # 게임 상태 조회
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                logger.error(f"게임 상태 없음: room_id={room_id}")
                return False
            
            # 방장 권한 확인
            if not game_state.is_player_host(user_id):
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed",
                    "data": {"reason": "방장만 게임을 시작할 수 있습니다"}
                })
                return False
            
            # 이미 시작된 게임인지 확인
            if game_state.status == "playing":
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed",
                    "data": {"reason": "게임이 이미 시작되었습니다"}
                })
                return False
            
            # 최소 플레이어 수 확인
            if len(game_state.players) < 1:  # 테스트를 위해 1명으로 설정
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed", 
                    "data": {"reason": "최소 1명 이상의 플레이어가 필요합니다"}
                })
                return False
            
            # 모든 플레이어 준비 완료 확인
            from redis_models import PlayerStatus
            not_ready_players = [p for p in game_state.players if p.status != PlayerStatus.READY.value]
            if not_ready_players:
                not_ready_names = [p.nickname for p in not_ready_players]
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "game_start_failed",
                    "data": {"reason": f"모든 플레이어가 준비 완료해야 합니다. 대기 중: {', '.join(not_ready_names)}"}
                })
                return False
            
            # 게임 상태를 플레이 중으로 변경
            from redis_models import GameStatus
            game_state.status = GameStatus.PLAYING.value
            game_state.started_at = datetime.now(timezone.utc).isoformat()
            game_state.current_turn = 0  # 첫 번째 플레이어부터 시작
            
            # 게임 상태 저장
            await self.redis_manager.save_game_state(game_state)
            
            # 게임 시작 카운트다운 시작
            await self._start_game_countdown(room_id, game_state)
            
            logger.info(f"게임 시작 카운트다운: room_id={room_id}")
            return True
            
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
                # 업데이트된 게임 상태 가져오기
                updated_game_state = await self.redis_manager.get_game_state(room_id)
                
                # 단어 성공 알림
                current_player_name = None
                for player in updated_game_state.players if updated_game_state else []:
                    if player.user_id == user_id:
                        current_player_name = player.nickname
                        break
                
                next_player = updated_game_state.get_current_player() if updated_game_state else None
                
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "word_submitted",
                    "data": {
                        "user_id": user_id,
                        "nickname": current_player_name,
                        "word": word,
                        "status": "accepted",
                        "next_char": updated_game_state.word_chain.current_char if updated_game_state else word[-1],
                        "current_turn_user_id": next_player.user_id if next_player else None,
                        "current_turn_time_limit": updated_game_state.get_current_turn_time_seconds() if updated_game_state else 30,
                        "current_turn_remaining_time": updated_game_state.get_current_turn_time_seconds() if updated_game_state else 30,  # 프론트엔드 호환성
                        "word_info": word_info.to_dict() if word_info else None,
                        "score_breakdown": score_breakdown.to_dict() if score_breakdown else None,
                        "response_time": response_time,
                        "message": message
                    }
                })
                if updated_game_state:
                    # 다음 턴 플레이어에게 타이머 시작 (개별 시간 적용)
                    next_player = updated_game_state.get_current_player()
                    if next_player:
                        await self._start_turn_timer(room_id, next_player.user_id)
                    
                    # 게임 상태 브로드캐스트
                    await self._broadcast_redis_game_state(room_id, updated_game_state)
                
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
            # 게임 상태 확인
            game_state = await self.game_engine.get_game_state(room_id)
            if not game_state or game_state.phase not in ["playing", "ready"]:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "item_use_failed",
                    "data": {"reason": "게임 중에만 아이템을 사용할 수 있습니다"}
                })
                return False
            
            # 아이템 서비스를 통한 아이템 사용
            use_result = await self.item_service.use_item(room_id, user_id, item_id, target_user_id)
            
            if use_result.success:
                # 아이템 사용 성공 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "item_used",
                    "data": {
                        "user_id": user_id,
                        "item_id": item_id,
                        "target_user_id": target_user_id,
                        "effect": use_result.effect.to_dict() if use_result.effect else None,
                        "message": use_result.message,
                        "cooldown_until": use_result.cooldown_until.isoformat() if use_result.cooldown_until else None
                    }
                })
                
                # 게임 상태 업데이트 브로드캐스트
                updated_game_state = await self.game_engine.get_game_state(room_id)
                if updated_game_state:
                    await self._broadcast_game_state(room_id, updated_game_state)
                
                logger.info(f"아이템 사용 성공: user_id={user_id}, item_id={item_id}, effect={use_result.effect.effect_type if use_result.effect else None}")
            else:
                # 아이템 사용 실패 알림
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "item_use_failed",
                    "data": {
                        "reason": use_result.message,
                        "item_id": item_id
                    }
                })
                logger.warning(f"아이템 사용 실패: user_id={user_id}, item_id={item_id}, reason={use_result.message}")
            
            return use_result.success
                
        except Exception as e:
            logger.error(f"아이템 사용 처리 중 오류: {e}")
            await self.websocket_manager.send_to_user(user_id, {
                "type": "item_use_failed",
                "data": {"reason": "아이템 사용 중 오류가 발생했습니다"}
            })
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
    
    async def _broadcast_redis_game_state(self, room_id: str, game_state=None):
        """Redis 게임 상태 브로드캐스트"""
        try:
            if not game_state:
                game_state = await self.redis_manager.get_game_state(room_id)
            
            if not game_state:
                return
            
            # 플레이어 리스트를 프론트엔드 형식으로 변환
            players_list = []
            for player in game_state.players:
                players_list.append({
                    "id": str(player.user_id),
                    "user_id": player.user_id,
                    "nickname": player.nickname,
                    "score": player.score,
                    "isReady": player.status == "ready",
                    "isHost": player.is_host,
                    "words_submitted": player.words_submitted,
                    "max_combo": player.max_combo
                })
            
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "game_state_update",
                "data": {
                    "room_id": room_id,
                    "status": game_state.status,
                    "players": players_list,
                    "current_turn": game_state.current_turn,
                    "current_round": game_state.current_round,
                    "word_chain": {
                        "words": game_state.word_chain.words,
                        "last_word": game_state.word_chain.last_word,
                        "current_char": game_state.word_chain.current_char
                    },
                    "started_at": game_state.started_at,
                    "ended_at": game_state.ended_at
                }
            })
            
        except Exception as e:
            logger.error(f"Redis 게임 상태 브로드캐스트 중 오류: {e}")
    
    async def _broadcast_game_state(self, room_id: str, game_state=None):
        """게임 엔진 상태 브로드캐스트 (기존 메서드 - 호환성 유지)"""
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
                # 플레이어들에게 아이템 드롭
                item_drops = {}
                if final_results and "players" in final_results:
                    for player_result in final_results["players"]:
                        user_id = player_result.get("user_id")
                        if user_id:
                            # 게임 성과 기반 아이템 드롭
                            performance = {
                                "score": player_result.get("score", 0),
                                "rank": player_result.get("rank", len(final_results["players"])),
                                "max_combo": player_result.get("max_combo", 0),
                                "accuracy": player_result.get("accuracy", 0.0),
                                "words_submitted": player_result.get("words_submitted", 0)
                            }
                            
                            dropped_item = await self.item_service.drop_random_item(user_id, performance)
                            if dropped_item:
                                item_drops[user_id] = dropped_item.to_dict()
                
                # 게임 종료 알림 (아이템 드롭 정보 포함)
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "game_ended",
                    "data": {
                        "reason": reason,
                        "message": message,
                        "final_results": final_results,
                        "item_drops": item_drops
                    }
                })
                
                # 개별 아이템 드롭 알림
                for user_id, item_info in item_drops.items():
                    await self.websocket_manager.send_to_user(user_id, {
                        "type": "item_dropped",
                        "data": {
                            "item": item_info,
                            "message": f"새로운 아이템을 획득했습니다: {item_info['name']}"
                        }
                    })
                
                logger.info(f"게임 종료 완료: room_id={room_id}, reason={reason}, drops={len(item_drops)}")
            
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
                "active_players": len(game_state.players),
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
    
    async def handle_get_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """인벤토리 조회 처리"""
        try:
            inventory = await self.item_service.get_user_inventory(user_id)
            
            # 인벤토리 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "inventory_update",
                "data": {
                    "inventory": inventory,
                    "total_items": len(inventory),
                    "message": "인벤토리 조회 완료"
                }
            })
            
            logger.info(f"인벤토리 조회: user_id={user_id}, items={len(inventory)}")
            return inventory
            
        except Exception as e:
            logger.error(f"인벤토리 조회 처리 중 오류: {e}")
            return []
    
    async def handle_get_active_effects(self, room_id: str, user_id: int) -> List[Dict[str, Any]]:
        """활성 효과 조회 처리"""
        try:
            active_effects = await self.item_service.get_active_effects(room_id, user_id)
            
            effects_data = [effect.to_dict() for effect in active_effects]
            
            # 활성 효과 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "active_effects",
                "data": {
                    "effects": effects_data,
                    "count": len(effects_data)
                }
            })
            
            return effects_data
            
        except Exception as e:
            logger.error(f"활성 효과 조회 처리 중 오류: {e}")
            return []
    
    # === 게임 모드 관련 핸들러 ===
    
    async def handle_get_available_modes(self, user_id: int) -> List[Dict[str, Any]]:
        """사용 가능한 게임 모드 조회"""
        try:
            modes = self.game_mode_service.get_available_modes()
            
            # 모드 목록 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "available_modes",
                "data": {
                    "modes": modes,
                    "count": len(modes)
                }
            })
            
            return modes
            
        except Exception as e:
            logger.error(f"게임 모드 조회 중 오류: {e}")
            return []
    
    async def handle_create_game_with_mode(self, room_id: str, creator_id: int, 
                                         mode_type: str, custom_settings: Optional[Dict[str, Any]] = None) -> bool:
        """게임 모드별 게임 생성"""
        try:
            # 모드 설정 검증
            mode_config = self.game_mode_service.get_mode_config(mode_type)
            if not mode_config:
                await self.websocket_manager.send_to_user(creator_id, {
                    "type": "game_creation_failed",
                    "data": {"reason": f"존재하지 않는 게임 모드: {mode_type}"}
                })
                return False
            
            # 게임 설정 구성
            game_settings = {"mode_type": mode_type}
            if custom_settings:
                game_settings.update(custom_settings)
            
            # 게임 생성
            success = await self.game_engine.create_game(room_id, creator_id, game_settings)
            
            if success:
                # 생성 성공 알림
                await self.websocket_manager.send_to_user(creator_id, {
                    "type": "game_created",
                    "data": {
                        "room_id": room_id,
                        "mode_type": mode_type,
                        "mode_config": mode_config.to_dict(),
                        "message": f"{mode_config.mode_name} 게임이 생성되었습니다"
                    }
                })
                
                logger.info(f"모드별 게임 생성: room_id={room_id}, mode={mode_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"모드별 게임 생성 중 오류: {e}")
            return False
    
    # === 관전자 관련 핸들러 ===
    
    async def handle_join_spectator(self, room_id: str, user_id: int, nickname: str, 
                                   is_streaming: bool = False) -> bool:
        """관전자로 참가"""
        try:
            # 게임 존재 확인
            game_state = await self.game_engine.get_game_state(room_id)
            if not game_state:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "spectator_join_failed",
                    "data": {"reason": "존재하지 않는 게임입니다"}
                })
                return False
            
            # 관전 가능 여부 확인
            mode_type = game_state.game_settings.get("mode_type", "classic")
            mode_config = self.game_mode_service.get_mode_config(mode_type)
            
            if not mode_config or not self.game_mode_service.can_spectate(mode_config):
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "spectator_join_failed",
                    "data": {"reason": "관전이 허용되지 않는 모드입니다"}
                })
                return False
            
            # 라이브 스트리밍 권한 확인
            if is_streaming and not self.game_mode_service.can_live_stream(mode_config):
                is_streaming = False
            
            # 관전자 추가
            success = await self.game_mode_service.add_spectator(room_id, user_id, nickname, is_streaming)
            
            if success:
                # 관전자 추가 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "spectator_joined",
                    "data": {
                        "user_id": user_id,
                        "nickname": nickname,
                        "is_streaming": is_streaming,
                        "message": f"{nickname}님이 관전을 시작했습니다"
                    }
                })
                
                # 관전자에게 현재 게임 상태 전송
                await self._broadcast_game_state(room_id, game_state)
                
                logger.info(f"관전자 참가: room_id={room_id}, user_id={user_id}, streaming={is_streaming}")
            
            return success
            
        except Exception as e:
            logger.error(f"관전자 참가 처리 중 오류: {e}")
            return False
    
    async def handle_leave_spectator(self, room_id: str, user_id: int) -> bool:
        """관전 종료"""
        try:
            success = await self.game_mode_service.remove_spectator(room_id, user_id)
            
            if success:
                # 관전 종료 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "spectator_left", 
                    "data": {
                        "user_id": user_id,
                        "message": "관전자가 나갔습니다"
                    }
                })
                
                logger.info(f"관전 종료: room_id={room_id}, user_id={user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"관전 종료 처리 중 오류: {e}")
            return False
    
    async def handle_get_spectators(self, room_id: str, user_id: int) -> List[Dict[str, Any]]:
        """관전자 목록 조회"""
        try:
            spectators = await self.game_mode_service.get_spectators(room_id)
            spectators_data = [spec.to_dict() for spec in spectators]
            
            # 관전자 목록 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "spectators_list",
                "data": {
                    "spectators": spectators_data,
                    "count": len(spectators_data)
                }
            })
            
            return spectators_data
            
        except Exception as e:
            logger.error(f"관전자 목록 조회 중 오류: {e}")
            return []
    
    async def handle_get_teams(self, room_id: str, user_id: int) -> List[Dict[str, Any]]:
        """팀 정보 조회"""
        try:
            teams = await self.game_mode_service.get_teams(room_id)
            teams_data = [team.to_dict() for team in teams]
            
            # 팀 정보 전송
            await self.websocket_manager.send_to_user(user_id, {
                "type": "teams_info",
                "data": {
                    "teams": teams_data,
                    "count": len(teams_data)
                }
            })
            
            return teams_data
            
        except Exception as e:
            logger.error(f"팀 정보 조회 중 오류: {e}")
            return []
    
    async def get_item_multipliers(self, room_id: str, user_id: int) -> float:
        """사용자의 활성 아이템 점수 배수 조회"""
        try:
            active_effects = await self.item_service.get_active_effects(room_id, user_id)
            total_multiplier = 1.0
            
            for effect in active_effects:
                if effect.effect.effect_type == "score_multiply":
                    multiplier = effect.effect.value.get("multiplier", 1.0)
                    total_multiplier *= multiplier
            
            return min(total_multiplier, 5.0)  # 최대 5배 제한
            
        except Exception as e:
            logger.error(f"아이템 배수 조회 중 오류: {e}")
            return 1.0
    
    async def handle_word_submission(self, room_id: str, user_id: int, word: str) -> bool:
        """단어 제출 처리"""
        try:
            logger.info(f"단어 제출 처리 시작: room_id={room_id}, user_id={user_id}, word={word}")
            
            # 게임 상태 조회
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed",
                    "data": {"reason": "게임 상태를 찾을 수 없습니다"}
                })
                return False
            
            # 게임이 진행 중인지 확인
            if game_state.status != "playing":
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed", 
                    "data": {"reason": "게임이 진행 중이 아닙니다"}
                })
                return False
            
            # 현재 턴 플레이어인지 확인
            current_player = game_state.get_current_player()
            if not current_player or current_player.user_id != user_id:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed",
                    "data": {"reason": "당신의 턴이 아닙니다"}
                })
                return False
            
            # 단어 길이 검증
            if len(word) < 2:
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed",
                    "data": {"reason": "단어는 최소 2글자 이상이어야 합니다"}
                })
                return False
            
            # 끝말잇기 규칙 검증
            if not game_state.word_chain.is_valid_chain(word):
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed",
                    "data": {"reason": f"'{game_state.word_chain.current_char}'(으)로 시작하는 단어를 입력하세요"}
                })
                return False
            
            # 중복 단어 검증
            if game_state.word_chain.is_word_used(word):
                await self.websocket_manager.send_to_user(user_id, {
                    "type": "word_submission_failed",
                    "data": {"reason": "이미 사용된 단어입니다"}
                })
                return False
            
            # 단어 추가
            game_state.word_chain.add_word(word)
            current_player.words_submitted += 1
            
            # 글자 수 기반 점수 계산 (기본 글자당 10점)
            word_length = len(word)
            word_score = word_length * 10
            current_player.score += word_score
            
            logger.info(f"점수 추가: {word} ({word_length}글자) = {word_score}점")
            
            # 턴 시간 시스템으로 변경됨 - 이 부분은 더 이상 필요 없음
            
            # 다음 턴으로 이동
            game_state.next_turn()
            
            # 게임 상태 저장
            await self.redis_manager.save_game_state(game_state)
            
            # 다음 플레이어 타이머 시작
            next_player = game_state.get_current_player()
            if next_player:
                await self._start_turn_timer(room_id, next_player.user_id)

            # 단어 제출 성공 브로드캐스트
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "word_submitted",
                "data": {
                    "user_id": user_id,
                    "nickname": current_player.nickname,
                    "word": word,
                    "status": "accepted",
                    "next_char": game_state.word_chain.current_char,
                    "current_turn_user_id": next_player.user_id if next_player else None,
                    "current_turn_nickname": next_player.nickname if next_player else None,
                    "current_turn_time_limit": game_state.get_current_turn_time_seconds(),
                    "current_turn_remaining_time": game_state.get_current_turn_time_seconds(),  # 프론트엔드 호환성
                    "word_chain": game_state.word_chain.words[-5:] if len(game_state.word_chain.words) > 0 else [],
                    "scores": {p.user_id: p.score for p in game_state.players},
                }
            })
            
            logger.info(f"단어 제출 성공: {word} -> 다음 글자: {game_state.word_chain.current_char}")
            return True
            
        except Exception as e:
            logger.error(f"단어 제출 처리 중 오류: {e}")
            await self.websocket_manager.send_to_user(user_id, {
                "type": "word_submission_failed",
                "data": {"reason": "단어 처리 중 오류가 발생했습니다"}
            })
            return False
    
    async def _start_turn_timer(self, room_id: str, user_id: int):
        """턴 타이머 시작 (전체 게임 턴 시간 시스템 사용)"""
        try:
            # 기존 타이머 완전 정리 (중요!)
            await self._cancel_turn_timer(room_id)
            await self.timer_service.cancel_room_timers(room_id)
            
            # 잠깐 대기하여 타이머 정리 완료 확인
            await asyncio.sleep(0.1)
            
            # 게임 상태에서 현재 턴의 시간 가져오기
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                logger.error(f"게임 상태 없음: {room_id}")
                return
            
            current_player = None
            for player in game_state.players:
                if player.user_id == user_id:
                    current_player = player
                    break
            
            if not current_player:
                logger.error(f"플레이어 없음: user_id={user_id}")
                return
            
            # 현재 턴의 시간 제한 사용 (턴마다 5초씩 감소)
            turn_time_ms = game_state.get_current_turn_time_ms()
            turn_time_seconds = game_state.get_current_turn_time_seconds()
            
            logger.info(f"턴 타이머 시작: room_id={room_id}, user_id={user_id}, nickname={current_player.nickname}, turn={game_state.total_turns}, round={game_state.current_round}, time={turn_time_seconds}초")
            
            # 기존 태스크 취소
            task_key = f"timer_task_{room_id}"
            if task_key in self.active_timer_tasks and not self.active_timer_tasks[task_key].done():
                self.active_timer_tasks[task_key].cancel()
                logger.info(f"기존 타이머 태스크 취소: {task_key}")
            
            # 새 타이머 생성
            timer_task = asyncio.create_task(self._turn_timer_task(room_id, user_id, turn_time_seconds))
            self.active_timer_tasks[task_key] = timer_task
            
            # Redis에 타이머 정보 저장
            from redis_models import GameTimer
            timer_expires = datetime.now(timezone.utc) + timedelta(seconds=turn_time_seconds)
            timer = GameTimer(
                expires_at=timer_expires.isoformat(),
                current_player_id=user_id,
                remaining_ms=turn_time_ms,
                turn_duration_ms=turn_time_ms
            )
            
            await self.redis_manager.save_timer(room_id, timer)
            
            # 타이머 시작 브로드캐스트
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "turn_timer_started",
                "data": {
                    "room_id": room_id,
                    "user_id": user_id,
                    "time_limit": turn_time_seconds,
                    "remaining_time": turn_time_seconds,
                    "expires_at": timer_expires.isoformat()
                }
            })
            
            logger.info(f"턴 타이머 시작 완료: room_id={room_id}, user_id={user_id}, {turn_time_seconds}초")
            
        except Exception as e:
            logger.error(f"턴 타이머 시작 중 오류: {e}")
    
    async def _turn_timer_task(self, room_id: str, user_id: int, timeout_seconds: float = 30.0):
        """턴 타이머 태스크 (개별 시간 사용)"""
        try:
            # 플레이어별 개별 시간 대기
            await asyncio.sleep(timeout_seconds)
            
            # 타임아웃 처리
            await self._handle_turn_timeout(room_id, user_id)
            
        except asyncio.CancelledError:
            logger.info(f"턴 타이머 취소됨: room_id={room_id}, user_id={user_id}, time={timeout_seconds}초")
        except Exception as e:
            logger.error(f"턴 타이머 태스크 오류: {e}")
    
    async def _handle_turn_timeout(self, room_id: str, user_id: int):
        """턴 타임아웃 처리"""
        try:
            logger.info(f"턴 타임아웃 처리: room_id={room_id}, user_id={user_id}")
            
            # 게임 상태 확인
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state or game_state.status != "playing":
                return
            
            current_player = game_state.get_current_player()
            if not current_player or current_player.user_id != user_id:
                return  # 이미 다른 플레이어로 넘어간 상태
            
            # 현재 턴 시간 확인 (새로운 시스템)
            current_turn_time = game_state.get_current_turn_time_seconds()
            logger.info(f"타임아웃 처리: {current_player.nickname}, 현재 턴 시간: {current_turn_time}초")
            
            # 라운드 완료 조건: 플레이어가 제한 시간 안에 제출하지 못함 → 라운드 종료
            logger.info(f"라운드 완료: {current_player.nickname}님 시간 초과로 라운드 종료 (R{game_state.current_round})")
            
            # 타임아웃 알림 후 라운드 완료 처리
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "turn_timeout",
                "data": {
                    "room_id": room_id,
                    "timeout_user_id": user_id,
                    "timeout_nickname": current_player.nickname,
                    "round_completed": True,  # 라운드 완료됨을 알림
                    "message": f"⏰ {current_player.nickname}님이 시간 초과되었습니다. 라운드 {game_state.current_round} 종료!"
                }
            })
            
            await self._handle_round_completion(room_id, game_state)
            return
            
        except Exception as e:
            logger.error(f"턴 타임아웃 처리 중 오류: {e}")
    
    async def _handle_round_completion(self, room_id: str, game_state: GameState):
        """라운드 완료 처리"""
        try:
            logger.info(f"라운드 완료 처리: room_id={room_id}, round={game_state.current_round}")
            
            # 라운드 순위 계산
            round_rankings = sorted(game_state.players, key=lambda p: p.score, reverse=True)
            
            # 라운드 완료 브로드캐스트
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "round_completed",
                "data": {
                    "room_id": room_id,
                    "completed_round": game_state.current_round,
                    "rankings": [
                        {
                            "rank": i + 1,
                            "user_id": player.user_id,
                            "nickname": player.nickname,
                            "score": player.score
                        }
                        for i, player in enumerate(round_rankings)
                    ],
                    "message": f"라운드 {game_state.current_round} 완료!"
                }
            })
            
            # 모든 라운드 완료 확인
            if game_state.is_final_game_finished():
                await self._handle_game_completion(room_id, game_state)
            else:
                # 현재 라운드 번호 저장 (알림용)
                completed_round = game_state.current_round
                
                # 다음 라운드 준비
                game_state.complete_round()
                await self.redis_manager.save_game_state(game_state)
                
                # 타이머 완전 정리 (중요!)
                await self._cancel_turn_timer(room_id)
                await self.timer_service.cancel_room_timers(room_id)
                
                # 라운드 완료 후 1초 대기 (타이머 정리 시간)
                logger.info(f"라운드 {completed_round} 완료, 1초 후 라운드 {game_state.current_round} 준비 시작")
                
                # 대기 중 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "round_transition",
                    "data": {
                        "room_id": room_id,
                        "completed_round": completed_round,
                        "next_round": game_state.current_round,
                        "message": f"라운드 {game_state.current_round} 준비 중..."
                    }
                })
                
                await asyncio.sleep(1)
                
                # 라운드 시작 카운트다운 (3초)
                await self._start_round_countdown(room_id, game_state)
                
        except Exception as e:
            logger.error(f"라운드 완료 처리 중 오류: {e}")
    
    async def _handle_game_completion(self, room_id: str, game_state: GameState):
        """게임 완료 처리"""
        try:
            logger.info(f"게임 완료 처리: room_id={room_id}")
            
            # 최종 순위 계산 (초기화하기 전에)
            final_rankings = game_state.get_final_rankings()
            
            # 게임 완료 브로드캐스트
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "game_completed",
                "data": {
                    "room_id": room_id,
                    "final_rankings": final_rankings,
                    "winner": final_rankings[0] if final_rankings else None,
                    "total_rounds": game_state.max_rounds,
                    "message": f"🏆 게임 완료! {final_rankings[0]['nickname']}님이 우승했습니다!" if final_rankings else "게임 완료!"
                }
            })
            
            # 완전한 게임 상태 초기화 (새 게임 준비)
            game_state.reset_game_state_for_new_game()
            await self.redis_manager.save_game_state(game_state)
            
            # 타이머 정리
            await self.timer_service.cancel_room_timers(room_id)
            
            logger.info(f"게임 완료 및 초기화 완료: {final_rankings[0]['nickname']}님 우승" if final_rankings else "게임 완료 및 초기화 완료")
            
        except Exception as e:
            logger.error(f"게임 완료 처리 중 오류: {e}")
    
    async def _start_game_countdown(self, room_id: str, game_state: GameState):
        """게임 시작 카운트다운 (3초)"""
        try:
            logger.info(f"게임 시작 카운트다운: room_id={room_id}")
            
            # 3초 카운트다운
            for countdown in [3, 2, 1]:
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "game_starting_countdown",
                    "data": {
                        "room_id": room_id,
                        "countdown": countdown,
                        "message": f"게임 시작까지 {countdown}초..."
                    }
                })
                await asyncio.sleep(1)
            
            # 카운트다운 완료 후 게임 실제 시작
            current_player = game_state.get_current_player()
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "game_started",
                "data": {
                    "room_id": room_id,
                    "started_at": game_state.started_at,
                    "current_round": game_state.current_round,
                    "max_rounds": game_state.max_rounds,
                    "current_turn_user_id": current_player.user_id if current_player else None,
                    "current_turn_nickname": current_player.nickname if current_player else None,
                    "current_turn_time_limit": game_state.get_current_turn_time_seconds(),
                    "next_char": game_state.word_chain.current_char or "",  # 다음 글자 추가
                    "players": [{"user_id": p.user_id, "nickname": p.nickname, "score": p.score} for p in game_state.players],
                    "scores": {p.user_id: p.score for p in game_state.players},  # 점수 추가
                    "message": "🎮 게임 시작! 첫 번째 단어를 입력하세요.",
                }
            })
            
            # 첫 번째 턴 타이머 시작
            if current_player:
                await self._start_turn_timer(room_id, current_player.user_id)
                
        except Exception as e:
            logger.error(f"게임 시작 카운트다운 중 오류: {e}")
    
    async def _start_round_countdown(self, room_id: str, game_state: GameState):
        """라운드 시작 카운트다운 (3초)"""
        try:
            logger.info(f"라운드 {game_state.current_round} 시작 카운트다운: room_id={room_id}")
            
            # 2초 카운트다운 (간소화)
            for countdown in [2, 1]:
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "round_starting_countdown",
                    "data": {
                        "room_id": room_id,
                        "round": game_state.current_round,
                        "countdown": countdown,
                        "message": f"라운드 {game_state.current_round} 시작까지 {countdown}초..."
                    }
                })
                await asyncio.sleep(1)
            
            # 라운드 시작 전 게임 상태 재로드 및 시간 초기화
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                logger.error(f"라운드 시작 시 게임 상태 없음: {room_id}")
                return
            
            # 시간 강제 초기화 (확실히 하기 위해)  
            game_state.turn_time_limit_ms = game_state.initial_turn_time_ms
            game_state.current_turn = 0
            game_state.total_turns = 0
            await self.redis_manager.save_game_state(game_state)
            
            # 현재 턴 플레이어 정보
            first_player = game_state.get_current_player()
            
            # 카운트다운 완료 후 라운드 실제 시작
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "next_round_starting",
                "data": {
                    "room_id": room_id,
                    "round": game_state.current_round,
                    "max_rounds": game_state.max_rounds,
                    "current_turn_user_id": first_player.user_id if first_player else None,
                    "current_turn_nickname": first_player.nickname if first_player else None,
                    "current_turn_time_limit": game_state.get_current_turn_time_seconds(),
                    "next_char": game_state.word_chain.current_char or "",
                    "scores": {p.user_id: p.score for p in game_state.players},
                    "message": f"🎮 라운드 {game_state.current_round} 시작!"
                }
            })
            
            logger.info(f"라운드 {game_state.current_round} 시작: 시간 초기화 완료 ({game_state.get_current_turn_time_seconds()}초)")
            
            # 첫 번째 플레이어부터 새 라운드 시작
            first_player = game_state.get_current_player()
            if first_player:
                await self._start_turn_timer(room_id, first_player.user_id)
                
        except Exception as e:
            logger.error(f"라운드 시작 카운트다운 중 오류: {e}")
    
    async def _cancel_turn_timer(self, room_id: str):
        """턴 타이머 취소"""
        try:
            logger.info(f"타이머 취소 시작: {room_id}")
            
            # asyncio 태스크 취소
            task_key = f"timer_task_{room_id}"
            if task_key in self.active_timer_tasks and not self.active_timer_tasks[task_key].done():
                self.active_timer_tasks[task_key].cancel()
                try:
                    await self.active_timer_tasks[task_key]
                except asyncio.CancelledError:
                    pass  # 정상적인 취소
                del self.active_timer_tasks[task_key]
                logger.info(f"asyncio 타이머 태스크 취소: {task_key}")
            
            # Redis에서 타이머 삭제
            timer_key = f"timer:{room_id}"
            deleted_count = await self.redis_manager.redis.delete(timer_key)
            logger.info(f"Redis 타이머 삭제: {timer_key}, 삭제된 키: {deleted_count}개")
            
            # 타이머 서비스에서 방 타이머 모두 정리
            await self.timer_service.cancel_room_timers(room_id)
            
            logger.info(f"턴 타이머 취소 완료: {room_id}")
            
        except Exception as e:
            logger.error(f"턴 타이머 취소 중 오류: {e}")
    
    async def handle_advanced_leave_room(self, room_id: str, user_id: int, nickname: str) -> tuple[bool, str]:
        """고도화된 방 나가기 처리"""
        try:
            logger.info(f"고도화된 방 나가기 처리: room_id={room_id}, user_id={user_id}, nickname={nickname}")
            
            # 게임 상태 조회
            game_state = await self.redis_manager.get_game_state(room_id)
            if not game_state:
                return True, "일반 나가기 처리"
            
            # 나가는 플레이어 정보 확인
            leaving_player = None
            for player in game_state.players:
                if player.user_id == user_id:
                    leaving_player = player
                    break
            
            if not leaving_player:
                return True, "플레이어를 찾을 수 없음"
            
            is_host = leaving_player.is_host
            is_game_playing = game_state.status == "playing"
            remaining_players_count = len(game_state.players) - 1
            
            # 상황별 처리
            if is_host and is_game_playing:
                return await self._handle_host_leave_during_game(room_id, user_id, nickname, game_state)
            elif is_host and not is_game_playing:
                return await self._handle_host_leave_before_game(room_id, user_id, nickname, game_state)
            elif is_game_playing and remaining_players_count == 1:
                return await self._handle_last_opponent_leave(room_id, user_id, nickname, game_state)
            elif is_game_playing:
                return await self._handle_player_leave_during_game(room_id, user_id, nickname, game_state)
            else:
                return await self._handle_normal_leave(room_id, user_id, nickname, game_state)
                
        except Exception as e:
            logger.error(f"고도화된 방 나가기 처리 중 오류: {e}")
            return True, "오류로 인한 일반 처리"
    
    async def _handle_host_leave_during_game(self, room_id: str, user_id: int, nickname: str, game_state) -> tuple[bool, str]:
        """방장이 게임 중에 나가는 경우"""
        try:
            # 모든 플레이어에게 방장 나가기 알림
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "host_left_game",
                "data": {
                    "room_id": room_id,
                    "host_nickname": nickname,
                    "message": f"방장 {nickname}님이 게임을 나갔습니다. 게임이 종료됩니다.",
                    "action": "game_terminated"
                }
            }, exclude_user=user_id)
            
            # 게임 강제 종료
            game_state.status = "finished"
            game_state.ended_at = datetime.now(timezone.utc).isoformat()
            await self.redis_manager.save_game_state(game_state)
            
            # 타이머 정리
            await self.timer_service.cancel_room_timers(room_id)
            
            # 잠시 후 모든 플레이어를 로비로 이동
            asyncio.create_task(self._delayed_room_cleanup(room_id, 5))
            
            logger.info(f"방장 게임 중 나가기로 인한 게임 종료: room_id={room_id}")
            return True, "방장 나가기로 게임 종료"
            
        except Exception as e:
            logger.error(f"방장 게임 중 나가기 처리 오류: {e}")
            return True, "오류 발생"
    
    async def _handle_host_leave_before_game(self, room_id: str, user_id: int, nickname: str, game_state) -> tuple[bool, str]:
        """방장이 게임 시작 전에 나가는 경우"""
        try:
            remaining_players = [p for p in game_state.players if p.user_id != user_id]
            
            if remaining_players:
                # 다음 플레이어를 새로운 방장으로 임명
                new_host = remaining_players[0]
                new_host.is_host = True
                
                # 방장 변경 알림
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "host_changed",
                    "data": {
                        "room_id": room_id,
                        "old_host_nickname": nickname,
                        "new_host_user_id": new_host.user_id,
                        "new_host_nickname": new_host.nickname,
                        "message": f"{nickname}님이 나가서 {new_host.nickname}님이 새로운 방장이 되었습니다."
                    }
                }, exclude_user=user_id)
                
                await self.redis_manager.save_game_state(game_state)
                
                logger.info(f"방장 변경: {nickname} -> {new_host.nickname}")
                return True, f"방장 변경됨: {new_host.nickname}"
            else:
                # 마지막 플레이어이므로 방 삭제
                return True, "빈 방으로 삭제"
                
        except Exception as e:
            logger.error(f"방장 게임 전 나가기 처리 오류: {e}")
            return True, "오류 발생"
    
    async def _handle_last_opponent_leave(self, room_id: str, user_id: int, nickname: str, game_state) -> tuple[bool, str]:
        """마지막 상대가 나가는 경우 (1:1 게임에서)"""
        try:
            remaining_player = None
            for player in game_state.players:
                if player.user_id != user_id:
                    remaining_player = player
                    break
            
            # 남은 플레이어에게 승리 처리
            if remaining_player:
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "opponent_left_victory",
                    "data": {
                        "room_id": room_id,
                        "left_nickname": nickname,
                        "winner_user_id": remaining_player.user_id,
                        "winner_nickname": remaining_player.nickname,
                        "message": f"{nickname}님이 나가서 {remaining_player.nickname}님이 승리했습니다!",
                        "action": "game_won"
                    }
                }, exclude_user=user_id)
            
            # 게임 종료 처리
            game_state.status = "finished"
            game_state.ended_at = datetime.now(timezone.utc).isoformat()
            await self.redis_manager.save_game_state(game_state)
            
            # 타이머 정리
            await self.timer_service.cancel_room_timers(room_id)
            
            logger.info(f"상대방 나가기로 인한 승리 처리: winner={remaining_player.nickname if remaining_player else 'None'}")
            return True, "상대방 나가기로 승리"
            
        except Exception as e:
            logger.error(f"마지막 상대 나가기 처리 오류: {e}")
            return True, "오류 발생"
    
    async def _handle_player_leave_during_game(self, room_id: str, user_id: int, nickname: str, game_state) -> tuple[bool, str]:
        """일반 플레이어가 게임 중에 나가는 경우"""
        try:
            # 현재 턴 플레이어인지 확인
            current_player = game_state.get_current_player()
            is_current_turn = current_player and current_player.user_id == user_id
            
            if is_current_turn:
                # 현재 턴 플레이어가 나가면 다음 플레이어로 턴 이동
                game_state.next_turn()
                next_player = game_state.get_current_player()
                
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_left_during_turn",
                    "data": {
                        "room_id": room_id,
                        "left_nickname": nickname,
                        "current_turn_user_id": next_player.user_id if next_player else None,
                        "current_turn_nickname": next_player.nickname if next_player else None,
                        "current_turn_time_limit": game_state.get_current_turn_time_seconds(),
                        "current_turn_remaining_time": game_state.get_current_turn_time_seconds(),  # 프론트엔드 호환성
                        "message": f"{nickname}님이 자신의 턴에 나갔습니다. 다음 플레이어로 넘어갑니다."
                    }
                }, exclude_user=user_id)
                
                # 다음 플레이어 타이머 시작
                if next_player:
                    await self._start_turn_timer(room_id, next_player.user_id)
            else:
                # 일반적인 게임 중 나가기
                await self.websocket_manager.broadcast_to_room(room_id, {
                    "type": "player_left_game",
                    "data": {
                        "room_id": room_id,
                        "left_nickname": nickname,
                        "message": f"{nickname}님이 게임을 나갔습니다."
                    }
                }, exclude_user=user_id)
            
            await self.redis_manager.save_game_state(game_state)
            
            logger.info(f"게임 중 플레이어 나가기: {nickname}, current_turn={is_current_turn}")
            return True, "게임 중 나가기 처리"
            
        except Exception as e:
            logger.error(f"게임 중 플레이어 나가기 처리 오류: {e}")
            return True, "오류 발생"
    
    async def _handle_normal_leave(self, room_id: str, user_id: int, nickname: str, game_state) -> tuple[bool, str]:
        """일반적인 나가기 (게임 시작 전)"""
        try:
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "player_left_room",
                "data": {
                    "room_id": room_id,
                    "left_user_id": user_id,
                    "left_nickname": nickname,
                    "message": f"{nickname}님이 방을 나갔습니다."
                }
            }, exclude_user=user_id)
            
            logger.info(f"일반 방 나가기: {nickname}")
            return True, "일반 나가기"
            
        except Exception as e:
            logger.error(f"일반 나가기 처리 오류: {e}")
            return True, "오류 발생"
    
    async def _delayed_room_cleanup(self, room_id: str, delay_seconds: int):
        """지연된 방 정리"""
        try:
            await asyncio.sleep(delay_seconds)
            
            # 남은 플레이어들을 로비로 이동
            await self.websocket_manager.broadcast_to_room(room_id, {
                "type": "room_disbanded",
                "data": {
                    "room_id": room_id,
                    "message": "방이 해산되었습니다. 로비로 이동합니다.",
                    "action": "redirect_to_lobby"
                }
            })
            
            logger.info(f"방 정리 완료: room_id={room_id}")
            
        except Exception as e:
            logger.error(f"지연된 방 정리 오류: {e}")


# 전역 게임 핸들러 인스턴스
game_handler: Optional[GameEventHandler] = None


def get_game_handler(websocket_manager: WebSocketManager) -> GameEventHandler:
    """게임 핸들러 의존성"""
    global game_handler
    if game_handler is None:
        game_handler = GameEventHandler(websocket_manager)
    return game_handler