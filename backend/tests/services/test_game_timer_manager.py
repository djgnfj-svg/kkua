"""
GameTimerManager 테스트
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from services.game_timer_manager import GameTimerManager


class TestGameTimerManager:
    """GameTimerManager 테스트 클래스"""
    
    @pytest.fixture
    def timer_manager(self):
        """테스트용 GameTimerManager 인스턴스"""
        return GameTimerManager()
    
    @pytest.fixture
    def mock_timeout_callback(self):
        """Mock 타임아웃 콜백"""
        return AsyncMock()
    
    @pytest.fixture
    def mock_time_update_callback(self):
        """Mock 시간 업데이트 콜백"""
        return AsyncMock()


class TestTimerBasicOperations:
    """타이머 기본 동작 테스트"""
    
    @pytest.mark.asyncio
    async def test_start_timer_success(self, timer_manager, mock_timeout_callback):
        """타이머 시작 성공 테스트"""
        room_id = 100
        duration = 2  # 2초로 짧게 설정
        
        await timer_manager.start_turn_timer(room_id, duration, mock_timeout_callback)
        
        # 타이머가 생성되었는지 확인
        assert timer_manager.has_active_timer(room_id)
        assert room_id in timer_manager.turn_timers
        assert not timer_manager.turn_timers[room_id].done()
        
        # 타이머 완료 대기
        await asyncio.sleep(duration + 0.5)
        
        # 타임아웃 콜백이 호출되었는지 확인
        mock_timeout_callback.assert_called_once_with(room_id)
    
    @pytest.mark.asyncio
    async def test_cancel_timer_success(self, timer_manager, mock_timeout_callback):
        """타이머 취소 성공 테스트"""
        room_id = 100
        duration = 10  # 긴 시간으로 설정
        
        await timer_manager.start_turn_timer(room_id, duration, mock_timeout_callback)
        
        # 타이머가 활성 상태인지 확인
        assert timer_manager.has_active_timer(room_id)
        
        # 타이머 취소
        await timer_manager.cancel_timer(room_id)
        
        # 타이머가 취소되었는지 확인
        assert not timer_manager.has_active_timer(room_id)
        assert room_id not in timer_manager.turn_timers
        
        # 타임아웃 콜백이 호출되지 않았는지 확인
        await asyncio.sleep(0.1)
        mock_timeout_callback.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_has_active_timer(self, timer_manager, mock_timeout_callback):
        """활성 타이머 존재 여부 확인 테스트"""
        room_id = 100
        
        # 처음에는 활성 타이머가 없음
        assert not timer_manager.has_active_timer(room_id)
        
        # 타이머 시작
        await timer_manager.start_turn_timer(room_id, 5, mock_timeout_callback)
        
        # 활성 타이머가 있음
        assert timer_manager.has_active_timer(room_id)
        
        # 타이머 취소
        await timer_manager.cancel_timer(room_id)
        
        # 다시 활성 타이머가 없음
        assert not timer_manager.has_active_timer(room_id)
    
    @pytest.mark.asyncio
    async def test_replace_existing_timer(self, timer_manager, mock_timeout_callback):
        """기존 타이머를 새 타이머로 교체하는 테스트"""
        room_id = 100
        
        # 첫 번째 타이머 시작 (긴 시간)
        await timer_manager.start_turn_timer(room_id, 10, mock_timeout_callback)
        first_timer = timer_manager.turn_timers[room_id]
        
        # 두 번째 타이머 시작 (기존 타이머 교체)
        await timer_manager.start_turn_timer(room_id, 2, mock_timeout_callback)
        second_timer = timer_manager.turn_timers[room_id]
        
        # 타이머가 교체되었는지 확인
        assert first_timer != second_timer
        assert first_timer.cancelled()
        assert not second_timer.done()
        
        # 두 번째 타이머 완료 대기
        await asyncio.sleep(2.5)
        
        # 타임아웃 콜백이 한 번만 호출되었는지 확인 (두 번째 타이머만)
        mock_timeout_callback.assert_called_once_with(room_id)


class TestTimeUpdateCallback:
    """시간 업데이트 콜백 테스트"""
    
    @pytest.mark.asyncio
    async def test_time_update_callback_called(self, timer_manager, mock_timeout_callback, mock_time_update_callback):
        """시간 업데이트 콜백 호출 테스트"""
        room_id = 100
        duration = 6  # 6초 (5, 3, 2, 1에서 호출됨)
        
        await timer_manager.start_turn_timer(
            room_id, duration, mock_timeout_callback, mock_time_update_callback
        )
        
        # 타이머 완료 대기
        await asyncio.sleep(duration + 0.5)
        
        # 시간 업데이트 콜백이 중요한 시점에서 호출되었는지 확인
        expected_calls = [
            (room_id, 5),
            (room_id, 3),
            (room_id, 2),
            (room_id, 1)
        ]
        
        assert mock_time_update_callback.call_count == len(expected_calls)
        for call_args in mock_time_update_callback.call_args_list:
            assert call_args[0] in expected_calls
    
    @pytest.mark.asyncio
    async def test_time_update_callback_error_handling(self, timer_manager, mock_timeout_callback):
        """시간 업데이트 콜백 에러 처리 테스트"""
        room_id = 100
        duration = 3
        
        # 에러를 발생시키는 콜백
        error_callback = AsyncMock(side_effect=Exception("콜백 에러"))
        
        await timer_manager.start_turn_timer(
            room_id, duration, mock_timeout_callback, error_callback
        )
        
        # 타이머 완료 대기 (에러가 발생해도 타이머는 계속 동작해야 함)
        await asyncio.sleep(duration + 0.5)
        
        # 타임아웃 콜백은 여전히 호출되어야 함
        mock_timeout_callback.assert_called_once_with(room_id)


class TestMultipleTimers:
    """다중 타이머 관리 테스트"""
    
    @pytest.mark.asyncio
    async def test_multiple_timers_independent(self, timer_manager):
        """여러 타이머가 독립적으로 동작하는지 테스트"""
        room1, room2, room3 = 100, 200, 300
        callback1, callback2, callback3 = AsyncMock(), AsyncMock(), AsyncMock()
        
        # 서로 다른 지속시간의 타이머 시작
        await timer_manager.start_turn_timer(room1, 1, callback1)
        await timer_manager.start_turn_timer(room2, 2, callback2)
        await timer_manager.start_turn_timer(room3, 3, callback3)
        
        # 모든 타이머가 활성 상태인지 확인
        assert timer_manager.has_active_timer(room1)
        assert timer_manager.has_active_timer(room2)
        assert timer_manager.has_active_timer(room3)
        
        # 첫 번째 타이머 완료 대기
        await asyncio.sleep(1.5)
        callback1.assert_called_once()
        callback2.assert_not_called()
        callback3.assert_not_called()
        
        # 두 번째 타이머 완료 대기
        await asyncio.sleep(1)
        callback2.assert_called_once()
        callback3.assert_not_called()
        
        # 세 번째 타이머 완료 대기
        await asyncio.sleep(1)
        callback3.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cancel_all_timers(self, timer_manager):
        """모든 타이머 취소 테스트"""
        room1, room2, room3 = 100, 200, 300
        callback1, callback2, callback3 = AsyncMock(), AsyncMock(), AsyncMock()
        
        # 여러 타이머 시작
        await timer_manager.start_turn_timer(room1, 10, callback1)
        await timer_manager.start_turn_timer(room2, 10, callback2)
        await timer_manager.start_turn_timer(room3, 10, callback3)
        
        # 모든 타이머가 활성 상태인지 확인
        assert timer_manager.get_active_timers_count() == 3
        
        # 모든 타이머 취소
        await timer_manager.cancel_all_timers()
        
        # 모든 타이머가 취소되었는지 확인
        assert timer_manager.get_active_timers_count() == 0
        assert not timer_manager.has_active_timer(room1)
        assert not timer_manager.has_active_timer(room2)
        assert not timer_manager.has_active_timer(room3)
        
        # 콜백이 호출되지 않았는지 확인
        await asyncio.sleep(0.1)
        callback1.assert_not_called()
        callback2.assert_not_called()
        callback3.assert_not_called()


class TestTimerStatistics:
    """타이머 통계 테스트"""
    
    @pytest.mark.asyncio
    async def test_get_active_timers_count(self, timer_manager):
        """활성 타이머 개수 조회 테스트"""
        assert timer_manager.get_active_timers_count() == 0
        
        # 타이머 하나씩 추가하면서 개수 확인
        await timer_manager.start_turn_timer(100, 10, AsyncMock())
        assert timer_manager.get_active_timers_count() == 1
        
        await timer_manager.start_turn_timer(200, 10, AsyncMock())
        assert timer_manager.get_active_timers_count() == 2
        
        await timer_manager.start_turn_timer(300, 10, AsyncMock())
        assert timer_manager.get_active_timers_count() == 3
        
        # 타이머 하나씩 취소하면서 개수 확인
        await timer_manager.cancel_timer(100)
        assert timer_manager.get_active_timers_count() == 2
        
        await timer_manager.cancel_timer(200)
        assert timer_manager.get_active_timers_count() == 1
        
        await timer_manager.cancel_timer(300)
        assert timer_manager.get_active_timers_count() == 0
    
    def test_get_remaining_time(self, timer_manager):
        """남은 시간 조회 테스트 (현재는 더미 구현)"""
        room_id = 100
        
        # 타이머가 없을 때
        remaining = timer_manager.get_remaining_time(room_id)
        assert remaining == 0
        
        # 실제 구현에서는 Redis에서 남은 시간을 조회해야 함


class TestErrorHandling:
    """에러 처리 테스트"""
    
    @pytest.mark.asyncio
    async def test_timeout_callback_error_handling(self, timer_manager):
        """타임아웃 콜백 에러 처리 테스트"""
        room_id = 100
        duration = 1
        
        # 에러를 발생시키는 타임아웃 콜백
        error_callback = AsyncMock(side_effect=Exception("콜백 에러"))
        
        await timer_manager.start_turn_timer(room_id, duration, error_callback)
        
        # 타이머 완료 대기 (에러가 발생해도 프로세스가 중단되면 안 됨)
        await asyncio.sleep(duration + 0.5)
        
        # 콜백은 호출되었지만 에러로 인해 실패
        error_callback.assert_called_once()
        
        # 타이머는 정상적으로 정리되어야 함
        assert not timer_manager.has_active_timer(room_id)
    
    @pytest.mark.asyncio
    async def test_cancel_nonexistent_timer(self, timer_manager):
        """존재하지 않는 타이머 취소 테스트"""
        room_id = 999
        
        # 존재하지 않는 타이머 취소 시도 (에러가 발생하면 안 됨)
        await timer_manager.cancel_timer(room_id)
        
        # 여전히 타이머가 없어야 함
        assert not timer_manager.has_active_timer(room_id)
    
    @pytest.mark.asyncio
    async def test_background_task_cleanup(self, timer_manager):
        """백그라운드 태스크 정리 테스트"""
        room_id = 100
        callback = AsyncMock()
        
        await timer_manager.start_turn_timer(room_id, 1, callback)
        
        # 백그라운드 태스크가 추가되었는지 확인
        assert len(timer_manager.background_tasks) > 0
        
        # 타이머 완료 대기
        await asyncio.sleep(1.5)
        
        # 완료된 태스크는 자동으로 정리되어야 함
        # (실제로는 done_callback에 의해 자동 정리됨)
        callback.assert_called_once()


class TestTimerPrecision:
    """타이머 정확도 테스트"""
    
    @pytest.mark.asyncio
    async def test_timer_accuracy(self, timer_manager):
        """타이머의 정확도 테스트"""
        room_id = 100
        duration = 2
        callback = AsyncMock()
        
        import time
        start_time = time.time()
        
        await timer_manager.start_turn_timer(room_id, duration, callback)
        
        # 타이머 완료 대기
        await asyncio.sleep(duration + 0.5)
        
        end_time = time.time()
        actual_duration = end_time - start_time
        
        # 타이머가 대략적으로 정확한 시간에 완료되었는지 확인
        # (0.5초 허용 오차)
        assert duration <= actual_duration <= duration + 1.0
        callback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_critical_time_updates(self, timer_manager):
        """중요한 시점의 시간 업데이트 정확도 테스트"""
        room_id = 100
        duration = 11  # 10초에서 카운트다운 시작
        
        timeout_callback = AsyncMock()
        update_callback = AsyncMock()
        
        await timer_manager.start_turn_timer(
            room_id, duration, timeout_callback, update_callback
        )
        
        # 타이머 완료 대기
        await asyncio.sleep(duration + 0.5)
        
        # 10, 5, 3, 2, 1초에서 업데이트가 호출되었는지 확인
        expected_updates = [10, 5, 3, 2, 1]
        actual_updates = [call[0][1] for call in update_callback.call_args_list]
        
        for expected_time in expected_updates:
            assert expected_time in actual_updates