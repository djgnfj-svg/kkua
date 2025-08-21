"""
실시간 타이머 서비스
턴별 시간 제한, 비동기 타이머, 자동 턴 넘김, 아이템 시간 조절
"""

import asyncio
import logging
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass
from enum import Enum
from redis_models import RedisGameManager, GameTimer
from database import get_redis

logger = logging.getLogger(__name__)


class TimerStatus(str, Enum):
    """타이머 상태"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    EXPIRED = "expired"


class TimerType(str, Enum):
    """타이머 타입"""
    TURN_TIMER = "turn_timer"        # 턴 제한 타이머
    GAME_TIMER = "game_timer"        # 전체 게임 시간 제한
    ITEM_EFFECT = "item_effect"      # 아이템 효과 지속시간
    COOLDOWN = "cooldown"            # 쿨다운 타이머


@dataclass
class TimerConfig:
    """타이머 설정"""
    timer_id: str
    duration_seconds: int
    callback: Optional[Callable] = None
    auto_restart: bool = False
    warning_threshold: int = 5  # 경고 알림 시점 (초)


class TimerInstance:
    """게임 타이머 클래스"""
    
    def __init__(self, config: TimerConfig):
        self.config = config
        self.status = TimerStatus.STOPPED
        self.start_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.remaining_seconds = config.duration_seconds
        self.task: Optional[asyncio.Task] = None
        self.warning_sent = False
    
    async def start(self) -> bool:
        """타이머 시작"""
        if self.status == TimerStatus.RUNNING:
            return False
        
        self.status = TimerStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)
        self.warning_sent = False
        
        # 비동기 타이머 작업 시작
        self.task = asyncio.create_task(self._timer_loop())
        
        logger.info(f"타이머 시작: {self.config.timer_id}, duration={self.remaining_seconds}s")
        return True
    
    async def pause(self) -> bool:
        """타이머 일시정지"""
        if self.status != TimerStatus.RUNNING:
            return False
        
        self.status = TimerStatus.PAUSED
        self.pause_time = datetime.now(timezone.utc)
        
        # 남은 시간 계산
        if self.start_time:
            elapsed = (self.pause_time - self.start_time).total_seconds()
            self.remaining_seconds = max(0, self.config.duration_seconds - elapsed)
        
        if self.task:
            self.task.cancel()
            self.task = None
        
        logger.info(f"타이머 일시정지: {self.config.timer_id}, remaining={self.remaining_seconds}s")
        return True
    
    async def resume(self) -> bool:
        """타이머 재개"""
        if self.status != TimerStatus.PAUSED:
            return False
        
        self.status = TimerStatus.RUNNING
        self.start_time = datetime.now(timezone.utc)
        self.pause_time = None
        
        # 남은 시간으로 타이머 재시작
        self.task = asyncio.create_task(self._timer_loop())
        
        logger.info(f"타이머 재개: {self.config.timer_id}, remaining={self.remaining_seconds}s")
        return True
    
    async def stop(self) -> bool:
        """타이머 정지"""
        if self.status == TimerStatus.STOPPED:
            return False
        
        self.status = TimerStatus.STOPPED
        
        if self.task:
            self.task.cancel()
            self.task = None
        
        logger.info(f"타이머 정지: {self.config.timer_id}")
        return True
    
    async def extend(self, additional_seconds: int) -> bool:
        """시간 연장"""
        if additional_seconds <= 0:
            return False
        
        if self.status == TimerStatus.RUNNING:
            # 실행 중인 경우 남은 시간에 추가
            current_time = datetime.now(timezone.utc)
            if self.start_time:
                elapsed = (current_time - self.start_time).total_seconds()
                self.remaining_seconds = max(0, self.config.duration_seconds - elapsed) + additional_seconds
                
                # 새로운 지속시간으로 타이머 재시작
                await self.stop()
                self.config.duration_seconds = int(self.remaining_seconds)
                await self.start()
        else:
            # 정지/일시정지 중인 경우 남은 시간에 추가
            self.remaining_seconds += additional_seconds
            self.config.duration_seconds = int(self.remaining_seconds)
        
        logger.info(f"시간 연장: {self.config.timer_id}, +{additional_seconds}s, total={self.remaining_seconds}s")
        return True
    
    async def reduce(self, reduction_seconds: int) -> bool:
        """시간 단축"""
        if reduction_seconds <= 0:
            return False
        
        if self.status == TimerStatus.RUNNING:
            current_time = datetime.now(timezone.utc)
            if self.start_time:
                elapsed = (current_time - self.start_time).total_seconds()
                self.remaining_seconds = max(1, self.config.duration_seconds - elapsed - reduction_seconds)
                
                # 새로운 지속시간으로 타이머 재시작
                await self.stop()
                self.config.duration_seconds = int(self.remaining_seconds)
                await self.start()
        else:
            # 정지/일시정지 중인 경우 남은 시간에서 차감 (최소 1초)
            self.remaining_seconds = max(1, self.remaining_seconds - reduction_seconds)
            self.config.duration_seconds = int(self.remaining_seconds)
        
        logger.info(f"시간 단축: {self.config.timer_id}, -{reduction_seconds}s, remaining={self.remaining_seconds}s")
        return True
    
    def get_remaining_seconds(self) -> int:
        """남은 시간 조회"""
        if self.status == TimerStatus.RUNNING and self.start_time:
            current_time = datetime.now(timezone.utc)
            elapsed = (current_time - self.start_time).total_seconds()
            remaining = max(0, self.config.duration_seconds - elapsed)
            return int(remaining)
        elif self.status == TimerStatus.PAUSED:
            return int(self.remaining_seconds)
        else:
            return 0
    
    async def _timer_loop(self):
        """타이머 루프"""
        try:
            # 남은 시간 또는 설정 시간만큼 대기
            duration = self.remaining_seconds if self.remaining_seconds > 0 else self.config.duration_seconds
            
            # 경고 시점까지 대기
            warning_delay = max(0, duration - self.config.warning_threshold)
            if warning_delay > 0:
                await asyncio.sleep(warning_delay)
                
                # 경고 콜백 호출
                if not self.warning_sent and self.config.callback:
                    self.warning_sent = True
                    try:
                        await self.config.callback(self.config.timer_id, "warning", self.config.warning_threshold)
                    except Exception as e:
                        logger.error(f"경고 콜백 실행 중 오류: {e}")
            
            # 나머지 시간 대기
            remaining_delay = min(duration, self.config.warning_threshold)
            if remaining_delay > 0:
                await asyncio.sleep(remaining_delay)
            
            # 타이머 만료
            self.status = TimerStatus.EXPIRED
            logger.info(f"타이머 만료: {self.config.timer_id}")
            
            # 만료 콜백 호출
            if self.config.callback:
                try:
                    await self.config.callback(self.config.timer_id, "expired", 0)
                except Exception as e:
                    logger.error(f"만료 콜백 실행 중 오류: {e}")
            
            # 자동 재시작
            if self.config.auto_restart:
                self.remaining_seconds = self.config.duration_seconds
                await self.start()
                
        except asyncio.CancelledError:
            logger.debug(f"타이머 캔슬됨: {self.config.timer_id}")
        except Exception as e:
            logger.error(f"타이머 루프 중 오류: {e}")


class TimerService:
    """타이머 서비스 관리자"""
    
    def __init__(self):
        self.redis_manager = RedisGameManager(get_redis())
        self.active_timers: Dict[str, TimerInstance] = {}
        
        # 기본 타이머 설정
        self.default_turn_duration = 30  # 30초
        self.default_game_duration = 1800  # 30분
    
    async def create_turn_timer(self, room_id: str, user_id: int, duration_seconds: Optional[int] = None, 
                               callback: Optional[Callable] = None) -> str:
        """턴 타이머 생성"""
        timer_id = f"turn_{room_id}_{user_id}"
        duration = duration_seconds or self.default_turn_duration
        
        config = TimerConfig(
            timer_id=timer_id,
            duration_seconds=duration,
            callback=callback or self._default_turn_callback,
            warning_threshold=5
        )
        
        timer = TimerInstance(config)
        self.active_timers[timer_id] = timer
        
        # Redis에 타이머 정보 저장
        await self._save_timer_to_redis(timer_id, {
            "type": TimerType.TURN_TIMER.value,
            "room_id": room_id,
            "user_id": user_id,
            "duration": duration,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"턴 타이머 생성: {timer_id}, duration={duration}s")
        return timer_id
    
    async def extend_timer(self, room_id: str, user_id: int, extra_seconds: int) -> bool:
        """타이머 시간 연장"""
        timer_id = f"turn_{room_id}_{user_id}"
        timer = self.active_timers.get(timer_id)
        
        if not timer or timer.status != TimerStatus.RUNNING:
            return False
        
        try:
            # 남은 시간 연장
            timer.remaining_seconds += extra_seconds
            
            logger.info(f"타이머 연장: {timer_id}, +{extra_seconds}초, 총 {timer.remaining_seconds}초")
            return True
            
        except Exception as e:
            logger.error(f"타이머 연장 중 오류: {e}")
            return False
    
    async def reduce_timer(self, room_id: str, user_id: int, reduce_seconds: int) -> bool:
        """타이머 시간 단축"""
        timer_id = f"turn_{room_id}_{user_id}"
        timer = self.active_timers.get(timer_id)
        
        if not timer or timer.status != TimerStatus.RUNNING:
            return False
        
        try:
            # 시간 단축 (최소 1초는 유지)
            timer.remaining_seconds = max(1, timer.remaining_seconds - reduce_seconds)
            
            logger.info(f"타이머 단축: {timer_id}, -{reduce_seconds}초, 남은 시간 {timer.remaining_seconds}초")
            return True
            
        except Exception as e:
            logger.error(f"타이머 단축 중 오류: {e}")
            return False
    
    async def create_game_timer(self, room_id: str, duration_seconds: Optional[int] = None, 
                               callback: Optional[Callable] = None) -> str:
        """게임 타이머 생성"""
        timer_id = f"game_{room_id}"
        duration = duration_seconds or self.default_game_duration
        
        config = TimerConfig(
            timer_id=timer_id,
            duration_seconds=duration,
            callback=callback or self._default_game_callback,
            warning_threshold=60  # 1분 전 경고
        )
        
        timer = TimerInstance(config)
        self.active_timers[timer_id] = timer
        
        await self._save_timer_to_redis(timer_id, {
            "type": TimerType.GAME_TIMER.value,
            "room_id": room_id,
            "duration": duration,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"게임 타이머 생성: {timer_id}, duration={duration}s")
        return timer_id
    
    async def create_item_timer(self, room_id: str, user_id: int, item_id: int, duration_seconds: int,
                               callback: Optional[Callable] = None) -> str:
        """아이템 효과 타이머 생성"""
        timer_id = f"item_{room_id}_{user_id}_{item_id}"
        
        config = TimerConfig(
            timer_id=timer_id,
            duration_seconds=duration_seconds,
            callback=callback or self._default_item_callback,
            warning_threshold=0  # 아이템은 경고 없음
        )
        
        timer = TimerInstance(config)
        self.active_timers[timer_id] = timer
        
        await self._save_timer_to_redis(timer_id, {
            "type": TimerType.ITEM_EFFECT.value,
            "room_id": room_id,
            "user_id": user_id,
            "item_id": item_id,
            "duration": duration_seconds,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        logger.info(f"아이템 타이머 생성: {timer_id}, duration={duration_seconds}s")
        return timer_id
    
    async def start_timer(self, timer_id: str) -> bool:
        """타이머 시작"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            logger.warning(f"존재하지 않는 타이머: {timer_id}")
            return False
        
        return await timer.start()
    
    async def pause_timer(self, timer_id: str) -> bool:
        """타이머 일시정지"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return False
        
        return await timer.pause()
    
    async def resume_timer(self, timer_id: str) -> bool:
        """타이머 재개"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return False
        
        return await timer.resume()
    
    async def stop_timer(self, timer_id: str) -> bool:
        """타이머 정지"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return False
        
        result = await timer.stop()
        
        # Redis에서 제거
        await self._remove_timer_from_redis(timer_id)
        
        # 메모리에서 제거
        if timer_id in self.active_timers:
            del self.active_timers[timer_id]
        
        return result
    
    async def extend_timer(self, timer_id: str, additional_seconds: int) -> bool:
        """타이머 시간 연장"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return False
        
        return await timer.extend(additional_seconds)
    
    async def reduce_timer(self, timer_id: str, reduction_seconds: int) -> bool:
        """타이머 시간 단축"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return False
        
        return await timer.reduce(reduction_seconds)
    
    def get_timer_status(self, timer_id: str) -> Optional[Dict[str, Any]]:
        """타이머 상태 조회"""
        timer = self.active_timers.get(timer_id)
        if not timer:
            return None
        
        return {
            "timer_id": timer_id,
            "status": timer.status.value,
            "remaining_seconds": timer.get_remaining_seconds(),
            "duration_seconds": timer.config.duration_seconds,
            "warning_threshold": timer.config.warning_threshold
        }
    
    async def cleanup_room_timers(self, room_id: str):
        """룸의 모든 타이머 정리"""
        timers_to_remove = []
        
        for timer_id in self.active_timers:
            if room_id in timer_id:
                timers_to_remove.append(timer_id)
        
        for timer_id in timers_to_remove:
            await self.stop_timer(timer_id)
        
        logger.info(f"룸 타이머 정리 완료: room_id={room_id}, count={len(timers_to_remove)}")
    
    async def cancel_room_timers(self, room_id: str):
        """룸의 모든 타이머 취소 (cleanup_room_timers 별칭)"""
        await self.cleanup_room_timers(room_id)
    
    async def cleanup_user_timers(self, room_id: str, user_id: int):
        """사용자의 모든 타이머 정리"""
        timers_to_remove = []
        
        for timer_id in self.active_timers:
            if room_id in timer_id and str(user_id) in timer_id:
                timers_to_remove.append(timer_id)
        
        for timer_id in timers_to_remove:
            await self.stop_timer(timer_id)
        
        logger.info(f"사용자 타이머 정리 완료: room_id={room_id}, user_id={user_id}, count={len(timers_to_remove)}")
    
    def get_active_timers(self, room_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """활성 타이머 목록 조회"""
        result = {}
        
        for timer_id, timer in self.active_timers.items():
            if room_id and room_id not in timer_id:
                continue
                
            result[timer_id] = {
                "status": timer.status.value,
                "remaining_seconds": timer.get_remaining_seconds(),
                "duration_seconds": timer.config.duration_seconds
            }
        
        return result
    
    async def _save_timer_to_redis(self, timer_id: str, timer_info: Dict[str, Any]):
        """Redis에 타이머 정보 저장"""
        try:
            key = f"timer:{timer_id}"
            import json
            await self.redis_manager.redis.setex(
                key, 
                7200,  # 2시간 TTL
                json.dumps(timer_info, ensure_ascii=False)
            )
        except Exception as e:
            logger.error(f"타이머 Redis 저장 중 오류: {e}")
    
    async def _remove_timer_from_redis(self, timer_id: str):
        """Redis에서 타이머 정보 제거"""
        try:
            key = f"timer:{timer_id}"
            await self.redis_manager.redis.delete(key)
        except Exception as e:
            logger.error(f"타이머 Redis 제거 중 오류: {e}")
    
    async def _default_turn_callback(self, timer_id: str, event: str, remaining: int):
        """기본 턴 타이머 콜백"""
        try:
            # timer_id에서 room_id와 user_id 추출
            parts = timer_id.split('_')
            if len(parts) >= 3:
                room_id = parts[1]
                user_id = int(parts[2])
                
                if event == "warning":
                    # 경고 이벤트는 별도 처리하지 않음 (WebSocket에서 처리)
                    pass
                elif event == "expired":
                    # 턴 타임아웃 처리는 게임 엔진에서 담당
                    logger.info(f"턴 타임아웃: room_id={room_id}, user_id={user_id}")
                    
        except Exception as e:
            logger.error(f"턴 타이머 콜백 중 오류: {e}")
    
    async def _default_game_callback(self, timer_id: str, event: str, remaining: int):
        """기본 게임 타이머 콜백"""
        try:
            # timer_id에서 room_id 추출
            parts = timer_id.split('_')
            if len(parts) >= 2:
                room_id = parts[1]
                
                if event == "warning":
                    logger.info(f"게임 시간 경고: room_id={room_id}, remaining={remaining}s")
                elif event == "expired":
                    logger.info(f"게임 시간 초과: room_id={room_id}")
                    
        except Exception as e:
            logger.error(f"게임 타이머 콜백 중 오류: {e}")
    
    async def _default_item_callback(self, timer_id: str, event: str, remaining: int):
        """기본 아이템 타이머 콜백"""
        try:
            if event == "expired":
                # 아이템 효과 종료
                logger.info(f"아이템 효과 종료: {timer_id}")
                
        except Exception as e:
            logger.error(f"아이템 타이머 콜백 중 오류: {e}")


# 전역 타이머 서비스 인스턴스
timer_service = TimerService()


def get_timer_service() -> TimerService:
    """타이머 서비스 의존성"""
    return timer_service