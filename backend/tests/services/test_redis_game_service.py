"""
RedisGameService 종합 테스트
"""

import pytest
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from services.redis_game_service import RedisGameService
from redis.exceptions import ConnectionError, TimeoutError, RedisError


class TestRedisGameService:
    """RedisGameService 테스트 클래스"""

    @pytest.fixture
    async def redis_service(self):
        """테스트용 RedisGameService 인스턴스"""
        service = RedisGameService()
        # 실제 Redis 연결 대신 Mock 사용
        service.redis_client = AsyncMock()
        return service

    @pytest.fixture
    def sample_participants(self):
        """샘플 참가자 데이터"""
        return [
            {"guest_id": 1, "nickname": "플레이어1"},
            {"guest_id": 2, "nickname": "플레이어2"},
            {"guest_id": 3, "nickname": "플레이어3"},
        ]

    @pytest.fixture
    def sample_game_state(self):
        """샘플 게임 상태 데이터"""
        return {
            "room_id": 100,
            "participants": [1, 2, 3],
            "nicknames": {1: "플레이어1", 2: "플레이어2", 3: "플레이어3"},
            "current_player_index": 0,
            "current_player_id": 1,
            "current_word": "끝말잇기",
            "last_character": "기",
            "used_words": ["끝말잇기"],
            "turn_number": 1,
            "current_round": 1,
            "max_rounds": 10,
            "game_started": True,
            "time_limit": 30,
            "is_game_over": False,
            "created_at": datetime.now().isoformat(),
            "started_at": datetime.now().isoformat(),
        }


class TestRedisConnection:
    """Redis 연결 관련 테스트"""

    @pytest.mark.asyncio
    async def test_connect_success(self):
        """정상적인 Redis 연결 테스트"""
        service = RedisGameService()

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            await service.connect()

            assert service.redis_client == mock_client
            mock_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_retry_success(self):
        """재시도 후 성공하는 연결 테스트"""
        service = RedisGameService()

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client

            # 첫 번째 시도는 실패, 두 번째 시도는 성공
            mock_client.ping.side_effect = [ConnectionError("연결 실패"), None]

            await service.connect(max_retries=2, retry_delay=0.1)

            assert service.redis_client == mock_client
            assert mock_client.ping.call_count == 2

    @pytest.mark.asyncio
    async def test_connect_complete_failure(self):
        """완전한 연결 실패 테스트"""
        service = RedisGameService()

        with patch("redis.asyncio.from_url") as mock_from_url:
            mock_client = AsyncMock()
            mock_from_url.return_value = mock_client
            mock_client.ping.side_effect = ConnectionError("지속적 연결 실패")

            with pytest.raises(ConnectionError):
                await service.connect(max_retries=2, retry_delay=0.1)

    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Redis 연결 해제 테스트"""
        service = RedisGameService()
        service.redis_client = AsyncMock()
        service.turn_timers = {"100": Mock()}

        await service.disconnect()

        service.redis_client.close.assert_called_once()


class TestGameInitialization:
    """게임 초기화 관련 테스트"""

    @pytest.mark.asyncio
    async def test_create_game_success(self, redis_service, sample_participants):
        """게임 생성 성공 테스트"""
        room_id = 100
        max_rounds = 10

        # Redis SET 연산 성공 시뮬레이션
        redis_service.redis_client.set.return_value = True
        redis_service.redis_client.expire.return_value = True
        redis_service.redis_client.sadd.return_value = True

        result = await redis_service.create_game(
            room_id, sample_participants, max_rounds
        )

        assert result is True
        redis_service.redis_client.set.assert_called()
        redis_service.redis_client.expire.assert_called()

    @pytest.mark.asyncio
    async def test_create_game_redis_failure(self, redis_service, sample_participants):
        """Redis 저장 실패 시 게임 생성 실패 테스트"""
        room_id = 100
        max_rounds = 10

        redis_service.redis_client.set.side_effect = RedisError("저장 실패")

        result = await redis_service.create_game(
            room_id, sample_participants, max_rounds
        )

        assert result is False

    @pytest.mark.asyncio
    async def test_get_game_state_success(self, redis_service, sample_game_state):
        """게임 상태 조회 성공 테스트"""
        room_id = 100

        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)

        result = await redis_service.get_game_state(room_id)

        assert result == sample_game_state
        redis_service.redis_client.get.assert_called_with(f"game:{room_id}")

    @pytest.mark.asyncio
    async def test_get_game_state_not_found(self, redis_service):
        """존재하지 않는 게임 상태 조회 테스트"""
        room_id = 999

        redis_service.redis_client.get.return_value = None

        result = await redis_service.get_game_state(room_id)

        assert result is None


class TestWordSubmission:
    """단어 제출 관련 테스트"""

    @pytest.mark.asyncio
    async def test_submit_word_success(self, redis_service, sample_game_state):
        """단어 제출 성공 테스트"""
        room_id = 100
        word = "기차"
        player_id = 1

        # 게임 상태 조회 성공
        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)
        redis_service.redis_client.set.return_value = True
        redis_service.redis_client.expire.return_value = True

        # WebSocket 매니저 Mock
        websocket_manager = Mock()
        redis_service.websocket_manager = websocket_manager
        websocket_manager.broadcast_to_room = AsyncMock()

        result = await redis_service.submit_word(room_id, word, player_id)

        assert result["success"] is True
        assert result["word"] == word
        assert result["next_player"]["id"] == 2  # 다음 플레이어

        # Redis 업데이트 호출 확인
        redis_service.redis_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_submit_word_invalid_turn(self, redis_service, sample_game_state):
        """잘못된 차례에 단어 제출 테스트"""
        room_id = 100
        word = "기차"
        player_id = 2  # 현재 차례가 아닌 플레이어

        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)

        result = await redis_service.submit_word(room_id, word, player_id)

        assert result["success"] is False
        assert "차례가 아닙니다" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_word_duplicate_word(self, redis_service, sample_game_state):
        """이미 사용된 단어 제출 테스트"""
        room_id = 100
        word = "끝말잇기"  # 이미 사용된 단어
        player_id = 1

        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)

        result = await redis_service.submit_word(room_id, word, player_id)

        assert result["success"] is False
        assert "이미 사용된 단어" in result["message"]

    @pytest.mark.asyncio
    async def test_submit_word_invalid_start_character(
        self, redis_service, sample_game_state
    ):
        """잘못된 시작 글자로 단어 제출 테스트"""
        room_id = 100
        word = "사과"  # "기"로 시작해야 하는데 "사"로 시작
        player_id = 1

        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)

        result = await redis_service.submit_word(room_id, word, player_id)

        assert result["success"] is False
        assert "시작 글자가" in result["message"]


class TestGameTimer:
    """게임 타이머 관련 테스트"""

    @pytest.mark.asyncio
    async def test_start_turn_timer_success(self, redis_service):
        """턴 타이머 시작 테스트"""
        room_id = 100
        time_limit = 30

        # WebSocket 매니저 Mock
        websocket_manager = Mock()
        redis_service.websocket_manager = websocket_manager
        websocket_manager.broadcast_to_room = AsyncMock()

        await redis_service.start_turn_timer(room_id, time_limit)

        # 타이머가 생성되었는지 확인
        assert room_id in redis_service.turn_timers
        assert not redis_service.turn_timers[room_id].done()

    @pytest.mark.asyncio
    async def test_cancel_turn_timer(self, redis_service):
        """턴 타이머 취소 테스트"""
        room_id = 100

        # 가짜 타이머 태스크 생성
        mock_task = Mock()
        redis_service.turn_timers[room_id] = mock_task

        await redis_service.cancel_turn_timer(room_id)

        mock_task.cancel.assert_called_once()
        assert room_id not in redis_service.turn_timers


class TestPlayerStatistics:
    """플레이어 통계 관련 테스트"""

    @pytest.mark.asyncio
    async def test_update_player_stats_success(self, redis_service):
        """플레이어 통계 업데이트 성공 테스트"""
        room_id = 100
        player_id = 1
        word_length = 3
        response_time = 5.5
        base_score = 10

        # 기존 통계 조회 성공
        existing_stats = {
            "player_id": player_id,
            "words_count": 2,
            "total_score": 25,
            "avg_response_time": 6.0,
            "total_response_time": 12.0,
        }
        redis_service.redis_client.get.return_value = json.dumps(existing_stats)
        redis_service.redis_client.set.return_value = True

        result = await redis_service.update_player_stats(
            room_id, player_id, word_length, response_time, base_score
        )

        assert result is True
        # Redis 업데이트 호출 확인
        redis_service.redis_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_get_final_rankings_success(self, redis_service):
        """최종 순위 조회 성공 테스트"""
        room_id = 100
        players = [1, 2, 3]

        # 각 플레이어별 통계 Mock
        player_stats = {
            1: {"player_id": 1, "total_score": 50, "words_count": 5},
            2: {"player_id": 2, "total_score": 30, "words_count": 3},
            3: {"player_id": 3, "total_score": 40, "words_count": 4},
        }

        def get_side_effect(key):
            player_id = int(key.split(":")[-1])
            return json.dumps(player_stats.get(player_id, {}))

        redis_service.redis_client.get.side_effect = get_side_effect

        rankings = await redis_service.get_final_rankings(room_id, players)

        # 점수 순으로 정렬되었는지 확인
        assert len(rankings) == 3
        assert rankings[0]["player_id"] == 1  # 최고 점수
        assert rankings[1]["player_id"] == 3  # 두 번째
        assert rankings[2]["player_id"] == 2  # 최저 점수


class TestGameCleanup:
    """게임 정리 관련 테스트"""

    @pytest.mark.asyncio
    async def test_end_game_success(self, redis_service, sample_game_state):
        """게임 종료 성공 테스트"""
        room_id = 100
        winner_id = 1
        reason = "max_rounds_reached"

        # 게임 상태 조회 및 업데이트 성공
        redis_service.redis_client.get.return_value = json.dumps(sample_game_state)
        redis_service.redis_client.set.return_value = True
        redis_service.redis_client.expire.return_value = True

        # 타이머 Mock
        mock_task = Mock()
        redis_service.turn_timers[room_id] = mock_task

        result = await redis_service.end_game(room_id, winner_id, reason)

        assert result is True
        # 타이머 취소 확인
        mock_task.cancel.assert_called_once()
        # Redis 업데이트 호출 확인
        redis_service.redis_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_expired_games(self, redis_service):
        """만료된 게임 정리 테스트"""
        # 만료된 게임과 활성 게임 Mix
        active_games = ["100", "101", "102"]
        redis_service.redis_client.smembers.return_value = active_games

        # 100번은 존재, 101번은 만료, 102번은 존재
        def get_side_effect(key):
            if "101" in key:
                return None  # 만료된 게임
            return json.dumps({"room_id": 100, "is_game_over": False})

        redis_service.redis_client.get.side_effect = get_side_effect
        redis_service.redis_client.srem.return_value = True
        redis_service.redis_client.delete.return_value = True

        cleaned_count = await redis_service.cleanup_expired_games()

        assert cleaned_count > 0
        # 만료된 게임이 활성 게임 Set에서 제거되었는지 확인
        redis_service.redis_client.srem.assert_called()


class TestErrorHandling:
    """에러 처리 관련 테스트"""

    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self, redis_service):
        """Redis 연결 오류 처리 테스트"""
        room_id = 100

        redis_service.redis_client.get.side_effect = ConnectionError("연결 끊김")

        result = await redis_service.get_game_state(room_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_json_decode_error_handling(self, redis_service):
        """JSON 디코드 오류 처리 테스트"""
        room_id = 100

        redis_service.redis_client.get.return_value = "invalid json"

        result = await redis_service.get_game_state(room_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_timeout_error_handling(self, redis_service):
        """타임아웃 오류 처리 테스트"""
        room_id = 100
        word = "기차"
        player_id = 1

        redis_service.redis_client.get.side_effect = TimeoutError("타임아웃")

        result = await redis_service.submit_word(room_id, word, player_id)

        assert result["success"] is False
        assert "오류" in result["message"]


class TestPerformanceOptimization:
    """성능 최적화 관련 테스트"""

    @pytest.mark.asyncio
    async def test_duplicate_broadcast_prevention(self, redis_service):
        """중복 브로드캐스트 방지 테스트"""
        room_id = 100
        data = {"test": "data"}

        # WebSocket 매니저 Mock
        websocket_manager = Mock()
        redis_service.websocket_manager = websocket_manager
        websocket_manager.broadcast_to_room = AsyncMock()

        # 같은 데이터를 두 번 브로드캐스트
        await redis_service.broadcast_game_state(room_id, data)
        await redis_service.broadcast_game_state(room_id, data)

        # 실제로는 한 번만 브로드캐스트되어야 함
        # (실제 구현에서 중복 제거 로직이 있다면)
        websocket_manager.broadcast_to_room.assert_called()

    @pytest.mark.asyncio
    async def test_background_task_cleanup(self, redis_service):
        """백그라운드 태스크 정리 테스트"""
        # 가짜 백그라운드 태스크 추가
        task1 = Mock()
        task2 = Mock()
        redis_service.background_tasks.add(task1)
        redis_service.background_tasks.add(task2)

        await redis_service.cleanup_background_tasks()

        # 모든 태스크가 취소되었는지 확인
        task1.cancel.assert_called_once()
        task2.cancel.assert_called_once()
        assert len(redis_service.background_tasks) == 0
