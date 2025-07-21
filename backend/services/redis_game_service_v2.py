"""
Redis 기반 실시간 게임 상태 관리 서비스 (리팩토링 버전)
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .game_redis_client import GameRedisClient
from .game_timer_manager import GameTimerManager
from .game_state_manager import GameStateManager

logger = logging.getLogger(__name__)


class RedisGameServiceV2:
    """Redis 기반 게임 상태 관리 (개선된 구조)"""
    
    def __init__(self):
        # 의존성 주입으로 각 컴포넌트 분리
        self.redis_client = GameRedisClient()
        self.timer_manager = GameTimerManager()
        self.state_manager = GameStateManager()
        
        # Redis 키 패턴
        self.GAME_KEY_PREFIX = "game:"
        self.PLAYER_KEY_PREFIX = "player:"
        self.STATS_KEY_PREFIX = "stats:"
        self.ACTIVE_GAMES_SET = "active_games"
        
        # WebSocket 브로드캐스트 함수 (외부에서 주입)
        self._broadcast_function = None
        
        logger.info("RedisGameServiceV2 초기화 완료")
    
    def set_broadcast_function(self, broadcast_func):
        """WebSocket 브로드캐스트 함수 설정"""
        self._broadcast_function = broadcast_func
    
    # === 연결 관리 ===
    async def connect(self):
        """Redis 연결"""
        return await self.redis_client.connect()
    
    async def disconnect(self):
        """연결 해제 및 정리"""
        await self.timer_manager.cancel_all_timers()
        await self.redis_client.disconnect()
    
    async def is_connected(self) -> bool:
        """연결 상태 확인"""
        return await self.redis_client.is_connected()
    
    # === 게임 생명주기 관리 ===
    async def create_game(self, room_id: int, participants: List[Dict]) -> bool:
        """새 게임 생성"""
        try:
            await self.redis_client.ensure_connection()
            
            # 초기 게임 상태 생성
            game_state = self.state_manager.create_initial_game_state(room_id, participants)
            
            # Redis에 저장
            game_key = f"{self.GAME_KEY_PREFIX}{room_id}"
            await self.redis_client.redis_client.setex(
                game_key, 
                86400,  # 24시간 TTL
                json.dumps(game_state)
            )
            
            # 활성 게임 목록에 추가
            await self.redis_client.redis_client.sadd(self.ACTIVE_GAMES_SET, room_id)
            
            # 플레이어별 참여 게임 추적
            for participant in participants:
                player_key = f"{self.PLAYER_KEY_PREFIX}{participant['guest_id']}"
                await self.redis_client.redis_client.sadd(player_key, room_id)
                await self.redis_client.redis_client.expire(player_key, 86400)
            
            logger.info(f"게임 생성 성공: room_id={room_id}, 참가자={len(participants)}명")
            return True
            
        except Exception as e:
            logger.error(f"게임 생성 실패: room_id={room_id}, error={e}", exc_info=True)
            return False
    
    async def start_game(self, room_id: int, first_word: str = "끝말잇기") -> bool:
        """게임 시작"""
        try:
            # 현재 게임 상태 조회
            game_state = await self.get_game_state(room_id)
            if not game_state:
                logger.error(f"게임 상태를 찾을 수 없음: room_id={room_id}")
                return False
            
            # 게임 시작 상태로 변경
            game_state = self.state_manager.start_game(game_state, first_word)
            
            # Redis에 저장
            await self._save_game_state(room_id, game_state)
            
            # 턴 타이머 시작
            await self.timer_manager.start_turn_timer(
                room_id=room_id,
                duration=30,
                on_timeout=self._handle_turn_timeout,
                on_time_update=self._handle_time_update
            )
            
            # 게임 시작 브로드캐스트
            if self._broadcast_function:
                await self._broadcast_game_started(room_id, game_state)
            
            logger.info(f"게임 시작: room_id={room_id}, 첫 단어='{first_word}'")
            return True
            
        except Exception as e:
            logger.error(f"게임 시작 실패: room_id={room_id}, error={e}", exc_info=True)
            return False
    
    async def submit_word(self, room_id: int, player_id: int, word: str) -> Dict[str, Any]:
        """단어 제출"""
        try:
            # 게임 상태 조회
            game_state = await self.get_game_state(room_id)
            if not game_state:
                return {'success': False, 'message': '게임을 찾을 수 없습니다'}
            
            # 게임 상태 검증
            if game_state.get('status') != 'playing':
                return {'success': False, 'message': '진행 중인 게임이 아닙니다'}
            
            # 현재 플레이어 검증
            current_player = self.state_manager.get_current_player(game_state)
            if current_player.get('guest_id') != player_id:
                return {'success': False, 'message': '당신의 차례가 아닙니다'}
            
            # 단어 유효성 검증
            is_valid, message = self.state_manager.is_word_valid(game_state, word)
            if not is_valid:
                return {'success': False, 'message': message}
            
            # 단어를 게임 상태에 추가
            game_state = self.state_manager.add_word_to_chain(game_state, word, player_id)
            
            # 다음 플레이어로 턴 이동
            game_state = self.state_manager.move_to_next_player(game_state)
            
            # Redis에 저장
            await self._save_game_state(room_id, game_state)
            
            # 새로운 턴 타이머 시작
            await self.timer_manager.start_turn_timer(
                room_id=room_id,
                duration=30,
                on_timeout=self._handle_turn_timeout,
                on_time_update=self._handle_time_update
            )
            
            # 단어 제출 브로드캐스트
            if self._broadcast_function:
                await self._broadcast_word_submitted(room_id, game_state, word, player_id)
            
            logger.info(f"단어 제출 성공: room_id={room_id}, word='{word}', player_id={player_id}")
            return {
                'success': True, 
                'message': '단어가 성공적으로 제출되었습니다',
                'next_player': self.state_manager.get_current_player(game_state)
            }
            
        except Exception as e:
            logger.error(f"단어 제출 실패: room_id={room_id}, word='{word}', error={e}", exc_info=True)
            return {'success': False, 'message': '단어 제출 중 오류가 발생했습니다'}
    
    async def end_game(self, room_id: int, reason: str = "completed") -> bool:
        """게임 종료"""
        try:
            # 타이머 취소
            await self.timer_manager.cancel_timer(room_id)
            
            # 게임 상태 조회 및 종료 처리
            game_state = await self.get_game_state(room_id)
            if game_state:
                game_state = self.state_manager.end_game(game_state, reason)
                await self._save_game_state(room_id, game_state)
                
                # 게임 종료 브로드캐스트
                if self._broadcast_function:
                    stats = self.state_manager.calculate_game_statistics(game_state)
                    await self._broadcast_game_over(room_id, stats)
            
            # 활성 게임 목록에서 제거
            await self.redis_client.redis_client.srem(self.ACTIVE_GAMES_SET, room_id)
            
            logger.info(f"게임 종료: room_id={room_id}, reason='{reason}'")
            return True
            
        except Exception as e:
            logger.error(f"게임 종료 실패: room_id={room_id}, error={e}", exc_info=True)
            return False
    
    # === 데이터 조회 ===
    async def get_game_state(self, room_id: int) -> Optional[Dict]:
        """게임 상태 조회"""
        try:
            game_key = f"{self.GAME_KEY_PREFIX}{room_id}"
            state_str = await self.redis_client.redis_client.get(game_key)
            
            if state_str:
                return json.loads(state_str)
            return None
            
        except Exception as e:
            logger.error(f"게임 상태 조회 실패: room_id={room_id}, error={e}")
            return None
    
    async def get_game_statistics(self, room_id: int) -> Dict[str, Any]:
        """게임 통계 조회"""
        game_state = await self.get_game_state(room_id)
        if game_state:
            return self.state_manager.calculate_game_statistics(game_state)
        return {}
    
    # === 내부 헬퍼 메서드 ===
    async def _save_game_state(self, room_id: int, game_state: Dict):
        """게임 상태 저장"""
        try:
            game_key = f"{self.GAME_KEY_PREFIX}{room_id}"
            await self.redis_client.redis_client.setex(
                game_key, 
                86400, 
                json.dumps(game_state)
            )
        except Exception as e:
            logger.error(f"게임 상태 저장 실패: room_id={room_id}, error={e}")
    
    async def _handle_turn_timeout(self, room_id: int):
        """턴 타임아웃 처리"""
        try:
            game_state = await self.get_game_state(room_id)
            if game_state and game_state.get('status') == 'playing':
                # 현재 플레이어를 탈락시키고 다음 플레이어로
                game_state = self.state_manager.move_to_next_player(game_state)
                await self._save_game_state(room_id, game_state)
                
                # 타임아웃 브로드캐스트
                if self._broadcast_function:
                    await self._broadcast_turn_timeout(room_id, game_state)
                
                # 새로운 턴 시작
                await self.timer_manager.start_turn_timer(
                    room_id=room_id,
                    duration=30,
                    on_timeout=self._handle_turn_timeout,
                    on_time_update=self._handle_time_update
                )
        except Exception as e:
            logger.error(f"턴 타임아웃 처리 실패: room_id={room_id}, error={e}")
    
    async def _handle_time_update(self, room_id: int, time_left: int):
        """시간 업데이트 처리"""
        if self._broadcast_function:
            await self._broadcast_time_update(room_id, time_left)
    
    # === 브로드캐스트 헬퍼 메서드 ===
    async def _broadcast_game_started(self, room_id: int, game_state: Dict):
        """게임 시작 브로드캐스트"""
        message = {
            'type': 'game_started',
            'participants': game_state['participants'],
            'current_player': game_state['current_player'],
            'first_word': game_state['last_word']
        }
        await self._broadcast_function(room_id, message)
    
    async def _broadcast_word_submitted(self, room_id: int, game_state: Dict, word: str, player_id: int):
        """단어 제출 브로드캐스트"""
        message = {
            'type': 'word_submitted',
            'word': word,
            'player_id': player_id,
            'next_player': game_state['current_player'],
            'last_char': game_state['last_char']
        }
        await self._broadcast_function(room_id, message)
    
    async def _broadcast_game_over(self, room_id: int, stats: Dict):
        """게임 종료 브로드캐스트"""
        message = {
            'type': 'game_over',
            'statistics': stats,
            'final_scores': stats.get('players', [])
        }
        await self._broadcast_function(room_id, message)
    
    async def _broadcast_turn_timeout(self, room_id: int, game_state: Dict):
        """턴 타임아웃 브로드캐스트"""
        message = {
            'type': 'turn_timeout',
            'next_player': game_state['current_player']
        }
        await self._broadcast_function(room_id, message)
    
    async def _broadcast_time_update(self, room_id: int, time_left: int):
        """시간 업데이트 브로드캐스트"""
        message = {
            'type': 'time_update',
            'time_left': time_left
        }
        await self._broadcast_function(room_id, message)