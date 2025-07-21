"""
게임 타이머 관리 서비스
"""

import asyncio
import logging
from typing import Dict, Set, Any, Callable
from datetime import datetime

logger = logging.getLogger(__name__)


class GameTimerManager:
    """게임 턴 타이머 관리"""
    
    def __init__(self):
        self.turn_timers: Dict[int, asyncio.Task] = {}  # room_id별 타이머 태스크
        self.background_tasks: Set[asyncio.Task] = set()  # 메모리 누수 방지
        
    def has_active_timer(self, room_id: int) -> bool:
        """활성 타이머 존재 여부 확인"""
        return room_id in self.turn_timers and not self.turn_timers[room_id].done()
    
    async def start_turn_timer(
        self, 
        room_id: int, 
        duration: int, 
        on_timeout: Callable[[int], Any],
        on_time_update: Callable[[int, int], Any] = None
    ):
        """턴 타이머 시작"""
        # 기존 타이머가 있으면 취소
        await self.cancel_timer(room_id)
        
        # 새 타이머 시작
        timer_task = asyncio.create_task(
            self._timer_countdown(room_id, duration, on_timeout, on_time_update)
        )
        self.turn_timers[room_id] = timer_task
        self.background_tasks.add(timer_task)
        
        # 완료된 태스크 자동 정리
        timer_task.add_done_callback(lambda t: self.background_tasks.discard(t))
        
        logger.info(f"타이머 시작: room_id={room_id}, duration={duration}초")
    
    async def cancel_timer(self, room_id: int):
        """특정 룸의 타이머 취소"""
        if room_id in self.turn_timers:
            timer_task = self.turn_timers[room_id]
            if not timer_task.done():
                timer_task.cancel()
                try:
                    await timer_task
                except asyncio.CancelledError:
                    pass  # 예상된 취소
                except Exception as e:
                    logger.warning(f"타이머 태스크 정리 중 오류: {e}")
            
            del self.turn_timers[room_id]
            logger.debug(f"타이머 취소: room_id={room_id}")
    
    async def cancel_all_timers(self):
        """모든 타이머 취소"""
        room_ids = list(self.turn_timers.keys())
        for room_id in room_ids:
            await self.cancel_timer(room_id)
        
        # 남은 백그라운드 태스크 정리
        if self.background_tasks:
            try:
                await asyncio.gather(*self.background_tasks, return_exceptions=True)
            except Exception as e:
                logger.warning(f"백그라운드 태스크 정리 중 오류: {e}")
        
        self.background_tasks.clear()
        logger.info("모든 타이머 취소 완료")
    
    async def _timer_countdown(
        self, 
        room_id: int, 
        duration: int, 
        on_timeout: Callable,
        on_time_update: Callable = None
    ):
        """타이머 카운트다운 실행"""
        try:
            time_left = duration
            
            while time_left > 0:
                await asyncio.sleep(1)
                time_left -= 1
                
                # 중요한 시점에서 시간 업데이트 브로드캐스트
                if time_left in [10, 5, 3, 2, 1] and on_time_update:
                    try:
                        await on_time_update(room_id, time_left)
                    except Exception as e:
                        logger.error(f"시간 업데이트 브로드캐스트 실패: {e}")
            
            # 시간 초과 처리
            logger.info(f"타이머 만료: room_id={room_id}")
            await on_timeout(room_id)
            
        except asyncio.CancelledError:
            logger.info(f"타이머 취소됨: room_id={room_id}")
            raise
        except Exception as e:
            logger.error(f"타이머 오류: room_id={room_id}, error={e}", exc_info=True)
        finally:
            # 타이머 딕셔너리에서 제거
            if room_id in self.turn_timers:
                del self.turn_timers[room_id]
    
    def get_remaining_time(self, room_id: int) -> int:
        """남은 시간 조회 (실제로는 Redis에서 조회해야 함)"""
        if self.has_active_timer(room_id):
            return 0  # 실제 구현에서는 Redis에서 조회
        return 0
    
    def get_active_timers_count(self) -> int:
        """활성 타이머 개수"""
        return len([timer for timer in self.turn_timers.values() if not timer.done()])