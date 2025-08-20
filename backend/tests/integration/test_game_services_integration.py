"""
게임 서비스 통합 테스트
모든 서비스가 함께 정상 작동하는지 검증
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# 테스트용 import
from services.game_engine import GameEngine, GamePhase
from services.word_validator import WordValidator 
from services.timer_service import TimerService
from services.score_calculator import ScoreCalculator
from services.item_service import ItemService
from services.game_mode_service import GameModeService
from services.cache_service import CacheService
from services.analytics_service import AnalyticsService


class TestGameServicesIntegration:
    """게임 서비스 통합 테스트"""
    
    @pytest.fixture
    async def services(self):
        """테스트용 서비스 인스턴스 생성"""
        # Redis mock
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = True
        redis_mock.exists.return_value = False
        
        # 서비스 인스턴스 생성
        game_engine = GameEngine()
        word_validator = WordValidator()
        timer_service = TimerService()
        score_calculator = ScoreCalculator()
        item_service = ItemService()
        game_mode_service = GameModeService()
        cache_service = CacheService()
        analytics_service = AnalyticsService()
        
        # Redis 클라이언트 mock 설정
        game_engine.redis = redis_mock
        cache_service.redis_client = redis_mock
        analytics_service.redis_client = redis_mock
        
        return {
            'game_engine': game_engine,
            'word_validator': word_validator,
            'timer_service': timer_service,
            'score_calculator': score_calculator,
            'item_service': item_service,
            'game_mode_service': game_mode_service,
            'cache_service': cache_service,
            'analytics_service': analytics_service
        }
    
    @pytest.mark.asyncio
    async def test_full_game_lifecycle(self, services):
        """전체 게임 생명주기 테스트"""
        game_engine = services['game_engine']
        analytics = services['analytics_service']
        
        room_id = "test_room_001"
        
        # 1. 게임 생성
        success, message = await game_engine.create_game(room_id, max_players=4)
        assert success == True
        assert "생성되었습니다" in message
        
        # 2. 플레이어 참가
        for i in range(3):
            success, msg = await game_engine.join_game(room_id, i+1, f"player_{i+1}")
            assert success == True
        
        # 3. 게임 시작
        success, msg = await game_engine.start_game(room_id)
        assert success == True
        
        # 4. 게임 상태 확인
        game_state = await game_engine.get_game_state(room_id)
        assert game_state is not None
        assert game_state.phase == GamePhase.PLAYING
        
        # 5. 분석 이벤트 추적 확인
        await analytics.track_event("game_started", 1, {
            "room_id": room_id,
            "players_count": 3,
            "mode_type": "classic"
        })
        
        # 6. 게임 종료
        success, msg = await game_engine.end_game(room_id, "manual_end")
        assert success == True
    
    @pytest.mark.asyncio
    async def test_word_validation_with_caching(self, services):
        """단어 검증과 캐싱 통합 테스트"""
        word_validator = services['word_validator']
        cache_service = services['cache_service']
        
        # 캐시 mock 설정
        cache_service.redis_client.get.return_value = None
        cache_service.redis_client.setex.return_value = True
        
        word = "사과"
        
        # 첫 번째 검증 (캐시 미스)
        result1 = await word_validator.validate_word_basic(word)
        assert result1.is_valid == True
        
        # 캐시에 저장 확인
        await cache_service.set("word_validation", word, {
            "is_valid": True,
            "definition": "과일의 한 종류"
        })
        
        # 두 번째 검증 (캐시 히트 시뮬레이션)
        cache_service.redis_client.get.return_value = '{"is_valid": true, "definition": "과일의 한 종류"}'
        cached_result = await cache_service.get("word_validation", word)
        assert cached_result["is_valid"] == True
    
    @pytest.mark.asyncio  
    async def test_item_system_integration(self, services):
        """아이템 시스템 통합 테스트"""
        item_service = services['item_service']
        timer_service = services['timer_service']
        analytics = services['analytics_service']
        
        room_id = "test_room_002"
        user_id = 1
        item_id = 1  # 시간 연장 아이템
        
        # Redis mock 설정
        item_service.redis.hget.return_value = '{"item_id": 1, "name": "시간 연장", "effect_type": "extend_time"}'
        item_service.redis.exists.return_value = False  # 쿨다운 없음
        
        # 아이템 사용
        result = await item_service.use_item(room_id, user_id, item_id)
        assert result.success == True
        assert result.effect_applied == True
        
        # 분석 이벤트 추적
        await analytics.track_event("item_used", user_id, {
            "item_id": item_id,
            "item_type": "extend_time",
            "room_id": room_id
        })
        
        # 쿨다운 확인
        cooldown_key = f"item_cooldown:{user_id}:{item_id}"
        item_service.redis.setex.assert_called()
    
    @pytest.mark.asyncio
    async def test_game_mode_with_teams(self, services):
        """게임 모드와 팀전 통합 테스트"""
        game_mode_service = services['game_mode_service']
        game_engine = services['game_engine']
        
        room_id = "test_team_room"
        
        # 팀전 모드 설정
        team_mode = await game_mode_service.get_mode_config("team_battle")
        assert team_mode is not None
        assert team_mode.supports_teams == True
        
        # 4명 플레이어로 게임 생성
        await game_engine.create_game(room_id, max_players=4)
        
        # 플레이어 참가
        players = []
        for i in range(4):
            player_id = i + 1
            await game_engine.join_game(room_id, player_id, f"player_{player_id}")
            players.append({
                'user_id': player_id,
                'nickname': f"player_{player_id}"
            })
        
        # 팀 구성
        from services.game_mode_service import TeamMode
        teams = await game_mode_service.setup_teams(room_id, players, TeamMode.AUTO_BALANCE)
        
        assert len(teams) == 2  # 2개 팀
        assert len(teams[0].members) == 2  # 각 팀에 2명
        assert len(teams[1].members) == 2
    
    @pytest.mark.asyncio
    async def test_score_calculation_integration(self, services):
        """점수 계산 통합 테스트"""
        score_calculator = services['score_calculator']
        word_validator = services['word_validator']
        
        # 단어 정보 mock
        word_info = Mock()
        word_info.word = "컴퓨터"
        word_info.length = 4
        word_info.difficulty_score = 3
        word_info.rarity_score = 2
        word_info.is_valid = True
        
        # 단어 체인 상태 mock
        word_chain_state = Mock()
        word_chain_state.consecutive_success = 2
        word_chain_state.last_word = "터미널"
        
        # 점수 계산
        response_time = 5.0  # 5초
        score_breakdown = score_calculator.calculate_word_score(
            word_info, response_time, word_chain_state
        )
        
        assert score_breakdown.base_score > 0
        assert score_breakdown.speed_bonus > 0  # 빠른 응답 보너스
        assert score_breakdown.combo_bonus > 0  # 콤보 보너스
        assert score_breakdown.total_score > score_breakdown.base_score
    
    @pytest.mark.asyncio
    async def test_timer_service_integration(self, services):
        """타이머 서비스 통합 테스트"""
        timer_service = services['timer_service']
        
        room_id = "test_timer_room"
        user_id = 1
        
        # 콜백 함수 mock
        callback_executed = False
        
        def timer_callback():
            nonlocal callback_executed
            callback_executed = True
        
        # 타이머 생성 (짧은 시간으로 테스트)
        timer_id = await timer_service.create_turn_timer(
            room_id, user_id, duration_seconds=1, callback=timer_callback
        )
        
        assert timer_id is not None
        
        # 타이머 상태 확인
        timer = timer_service.get_timer(timer_id)
        assert timer is not None
        
        # 잠시 대기 후 콜백 실행 확인
        await asyncio.sleep(1.5)
        assert callback_executed == True
    
    @pytest.mark.asyncio
    async def test_analytics_integration(self, services):
        """분석 서비스 통합 테스트"""
        analytics = services['analytics_service']
        
        # 다양한 이벤트 추적
        events = [
            ("game_started", 1, {"room_id": "room1", "mode_type": "classic"}),
            ("word_submitted", 1, {"word": "사과", "score": 10}),
            ("item_used", 1, {"item_id": 1, "item_type": "extend_time"}),
            ("game_ended", 1, {"duration": 300, "winner_score": 150})
        ]
        
        for event_type, user_id, data in events:
            await analytics.track_event(event_type, user_id, data)
        
        # 메트릭 조회 테스트
        game_metrics = await analytics.get_game_metrics()
        assert game_metrics is not None
        
        user_metrics = await analytics.get_user_behavior_metrics()
        assert user_metrics is not None
        
        performance_metrics = await analytics.get_performance_metrics()
        assert performance_metrics is not None
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, services):
        """캐시 성능 테스트"""
        cache_service = services['cache_service']
        
        # 대량 데이터 캐싱 테스트
        test_data = {}
        for i in range(100):
            key = f"test_key_{i}"
            value = f"test_value_{i}"
            test_data[key] = value
            await cache_service.set("performance_test", key, value)
        
        # 배치 조회 테스트
        keys = list(test_data.keys())
        results = await cache_service.batch_get("performance_test", keys)
        
        # 결과 검증 (mock이므로 실제 데이터는 없지만 구조 확인)
        assert isinstance(results, dict)
        
        # 캐시 통계 확인
        stats = cache_service.get_stats()
        assert stats.sets > 0
    
    @pytest.mark.asyncio
    async def test_spectator_mode(self, services):
        """관전 모드 통합 테스트"""
        game_mode_service = services['game_mode_service']
        analytics = services['analytics_service']
        
        room_id = "test_spectator_room"
        spectator_id = 999
        
        # 관전자 추가
        success = await game_mode_service.add_spectator(room_id, spectator_id, "spectator_1")
        assert success == True
        
        # 관전자 목록 확인
        spectators = await game_mode_service.get_spectators(room_id)
        assert len(spectators) >= 1
        
        # 분석 이벤트 추적
        await analytics.track_event("spectator_join", spectator_id, {
            "room_id": room_id,
            "spectator_count": len(spectators)
        })
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, services):
        """에러 처리 통합 테스트"""
        game_engine = services['game_engine']
        
        # 존재하지 않는 방 참가 시도
        success, message = await game_engine.join_game("nonexistent_room", 1, "player")
        assert success == False
        assert "존재하지 않습니다" in message
        
        # 중복 플레이어 참가 시도
        room_id = "error_test_room"
        await game_engine.create_game(room_id, max_players=2)
        await game_engine.join_game(room_id, 1, "player1")
        
        # 같은 플레이어가 다시 참가 시도
        success, message = await game_engine.join_game(room_id, 1, "player1")
        assert success == False
        assert "이미 참가" in message
    
    def test_service_dependencies(self, services):
        """서비스 의존성 확인 테스트"""
        # 모든 서비스가 정상 생성되었는지 확인
        required_services = [
            'game_engine', 'word_validator', 'timer_service',
            'score_calculator', 'item_service', 'game_mode_service',
            'cache_service', 'analytics_service'
        ]
        
        for service_name in required_services:
            assert service_name in services
            assert services[service_name] is not None
        
        # 서비스 간 순환 참조 없는지 확인
        game_engine = services['game_engine']
        assert hasattr(game_engine, 'redis')
        
        cache_service = services['cache_service']
        assert hasattr(cache_service, 'redis_client')


class TestWebSocketGameHandlerIntegration:
    """WebSocket 게임 핸들러 통합 테스트"""
    
    @pytest.fixture
    def game_handler(self):
        """테스트용 게임 핸들러"""
        from websocket.game_handler import GameHandler
        from websocket.websocket_manager import WebSocketManager
        
        # WebSocket 매니저 mock
        ws_manager = Mock()
        handler = GameHandler(ws_manager)
        
        return handler
    
    def test_handler_services_initialization(self, game_handler):
        """핸들러 서비스 초기화 테스트"""
        # 모든 서비스가 lazy loading으로 초기화되는지 확인
        assert hasattr(game_handler, '_game_engine')
        assert hasattr(game_handler, '_word_validator')
        assert hasattr(game_handler, '_timer_service')
        assert hasattr(game_handler, '_score_calculator')
        assert hasattr(game_handler, '_item_service')
        assert hasattr(game_handler, '_game_mode_service')
        
        # lazy loading 프로퍼티 접근 테스트
        game_engine = game_handler.game_engine
        assert game_engine is not None
        
        word_validator = game_handler.word_validator  
        assert word_validator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])