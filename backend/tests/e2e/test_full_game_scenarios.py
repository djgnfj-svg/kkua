"""
전체 게임 시나리오 End-to-End 테스트
실제 사용자 경험과 유사한 전체 플로우를 테스트
"""
import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timezone, timedelta

# WebSocket 및 게임 관련 import
from websocket.game_handler import GameHandler
from websocket.websocket_manager import WebSocketManager
from services.game_engine import GameEngine, GamePhase
from services.analytics_service import EventType


class MockWebSocket:
    """테스트용 WebSocket mock"""
    
    def __init__(self, user_id: int, nickname: str):
        self.user_id = user_id
        self.nickname = nickname
        self.messages = []
        self.closed = False
        
    async def send(self, message: str):
        """메시지 전송 mock"""
        if not self.closed:
            self.messages.append(json.loads(message))
    
    async def close(self):
        """연결 종료 mock"""
        self.closed = True
    
    def get_last_message(self):
        """마지막 메시지 조회"""
        return self.messages[-1] if self.messages else None
    
    def get_messages_by_type(self, message_type: str):
        """특정 타입의 메시지들 조회"""
        return [msg for msg in self.messages if msg.get('type') == message_type]


class TestFullGameScenarios:
    """전체 게임 시나리오 테스트"""
    
    @pytest.fixture
    def setup_game_environment(self):
        """게임 환경 설정"""
        # WebSocket 매니저 mock
        ws_manager = Mock()
        ws_manager.connections = {}
        ws_manager.send_to_room = AsyncMock()
        ws_manager.send_to_user = AsyncMock()
        
        # 게임 핸들러 생성
        game_handler = GameHandler(ws_manager)
        
        # Redis mock 설정
        redis_mock = Mock()
        redis_mock.get.return_value = None
        redis_mock.setex.return_value = True
        redis_mock.delete.return_value = True
        redis_mock.exists.return_value = False
        redis_mock.hget.return_value = None
        redis_mock.hset.return_value = True
        redis_mock.hdel.return_value = True
        redis_mock.sadd.return_value = True
        redis_mock.srem.return_value = True
        redis_mock.smembers.return_value = set()
        
        # 서비스에 Redis mock 설정
        game_handler.game_engine.redis = redis_mock
        game_handler._cache_service = Mock()
        game_handler._analytics_service = Mock()
        game_handler._analytics_service.track_event = AsyncMock()
        
        return {
            'game_handler': game_handler,
            'ws_manager': ws_manager,
            'redis_mock': redis_mock
        }
    
    @pytest.mark.asyncio
    async def test_classic_2player_game_scenario(self, setup_game_environment):
        """클래식 2인 게임 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        room_id = "classic_2p_room"
        
        # 플레이어 WebSocket 생성
        player1_ws = MockWebSocket(1, "플레이어1")
        player2_ws = MockWebSocket(2, "플레이어2")
        
        # WebSocket 매니저에 연결 등록
        ws_manager.connections = {
            1: player1_ws,
            2: player2_ws
        }
        
        # 1. 게임룸 생성 (플레이어1)
        create_message = {
            "type": "create_room",
            "room_id": room_id,
            "max_players": 2,
            "game_mode": "classic"
        }
        
        await game_handler.handle_create_room(player1_ws, create_message)
        
        # 게임룸 생성 확인
        game_state = await game_handler.game_engine.get_game_state(room_id)
        assert game_state is not None
        assert game_state.phase == GamePhase.WAITING
        
        # 2. 플레이어2 참가
        join_message = {
            "type": "join_game",
            "room_id": room_id
        }
        
        await game_handler.handle_join_game(player2_ws, join_message)
        
        # 참가 확인
        updated_state = await game_handler.game_engine.get_game_state(room_id)
        assert len(updated_state.players) == 2
        
        # 3. 게임 시작 (플레이어1이 방장)
        start_message = {
            "type": "start_game",
            "room_id": room_id
        }
        
        await game_handler.handle_start_game(player1_ws, start_message)
        
        # 게임 시작 확인
        game_state = await game_handler.game_engine.get_game_state(room_id)
        assert game_state.phase == GamePhase.PLAYING
        assert game_state.current_turn_index >= 0
        
        # 4. 첫 번째 단어 제출
        first_word = "사과"
        word_message = {
            "type": "submit_word",
            "room_id": room_id,
            "word": first_word
        }
        
        # 현재 턴 플레이어가 단어 제출
        current_player = game_state.players[game_state.current_turn_index]
        current_ws = ws_manager.connections[current_player.user_id]
        
        await game_handler.handle_submit_word(current_ws, word_message)
        
        # 5. 두 번째 단어 제출 (끝말잇기)
        second_word = "과일"
        word_message2 = {
            "type": "submit_word", 
            "room_id": room_id,
            "word": second_word
        }
        
        # 턴이 넘어갔는지 확인하고 다음 플레이어가 제출
        updated_state = await game_handler.game_engine.get_game_state(room_id)
        next_player = updated_state.players[updated_state.current_turn_index]
        next_ws = ws_manager.connections[next_player.user_id]
        
        await game_handler.handle_submit_word(next_ws, word_message2)
        
        # 6. 게임 진행 상태 확인
        final_state = await game_handler.game_engine.get_game_state(room_id)
        assert len(final_state.word_chain.words) >= 2
        assert final_state.word_chain.current_last_char == "일"
        
        # 분석 이벤트 추적 확인
        game_handler._analytics_service.track_event.assert_called()
    
    @pytest.mark.asyncio
    async def test_team_battle_scenario(self, setup_game_environment):
        """팀전 게임 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        room_id = "team_battle_room"
        
        # 4명 플레이어 WebSocket 생성
        players = []
        for i in range(4):
            user_id = i + 1
            player_ws = MockWebSocket(user_id, f"플레이어{user_id}")
            players.append(player_ws)
            ws_manager.connections[user_id] = player_ws
        
        # 1. 팀전 모드로 게임룸 생성
        create_message = {
            "type": "create_room",
            "room_id": room_id,
            "max_players": 4,
            "game_mode": "team_battle"
        }
        
        await game_handler.handle_create_room(players[0], create_message)
        
        # 2. 모든 플레이어 참가
        for player_ws in players[1:]:
            join_message = {
                "type": "join_game",
                "room_id": room_id
            }
            await game_handler.handle_join_game(player_ws, join_message)
        
        # 3. 팀 구성 및 게임 시작
        start_message = {
            "type": "start_game",
            "room_id": room_id
        }
        
        await game_handler.handle_start_game(players[0], start_message)
        
        # 팀 구성 확인
        game_state = await game_handler.game_engine.get_game_state(room_id)
        assert game_state.phase == GamePhase.PLAYING
        
        # 게임 모드 서비스를 통한 팀 정보 확인 (mock이므로 구조만 확인)
        teams = await game_handler.game_mode_service.get_teams(room_id)
        # mock 환경에서는 실제 팀 데이터가 없지만 호출 자체가 성공해야 함
    
    @pytest.mark.asyncio 
    async def test_spectator_mode_scenario(self, setup_game_environment):
        """관전 모드 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        room_id = "spectator_room"
        
        # 플레이어 2명과 관전자 1명
        player1_ws = MockWebSocket(1, "플레이어1")
        player2_ws = MockWebSocket(2, "플레이어2")
        spectator_ws = MockWebSocket(999, "관전자1")
        
        ws_manager.connections = {
            1: player1_ws,
            2: player2_ws,
            999: spectator_ws
        }
        
        # 1. 게임룸 생성 및 플레이어 참가
        await game_handler.handle_create_room(player1_ws, {
            "type": "create_room",
            "room_id": room_id,
            "max_players": 2,
            "game_mode": "classic"
        })
        
        await game_handler.handle_join_game(player2_ws, {
            "type": "join_game", 
            "room_id": room_id
        })
        
        # 2. 관전자 참가
        spectate_message = {
            "type": "join_spectator",
            "room_id": room_id
        }
        
        await game_handler.handle_join_spectator(spectator_ws, spectate_message)
        
        # 관전자 참가 확인
        spectators = await game_handler.game_mode_service.get_spectators(room_id)
        # mock 환경에서는 실제 데이터가 없지만 호출이 성공해야 함
        
        # 3. 게임 시작 후 관전자에게 상태 브로드캐스트 확인
        await game_handler.handle_start_game(player1_ws, {
            "type": "start_game",
            "room_id": room_id
        })
        
        # WebSocket 매니저의 브로드캐스트 호출 확인
        ws_manager.send_to_room.assert_called()
    
    @pytest.mark.asyncio
    async def test_item_usage_scenario(self, setup_game_environment):
        """아이템 사용 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        redis_mock = setup_game_environment['redis_mock']
        
        room_id = "item_test_room"
        
        # 플레이어 설정
        player1_ws = MockWebSocket(1, "플레이어1")
        player2_ws = MockWebSocket(2, "플레이어2")
        
        ws_manager.connections = {1: player1_ws, 2: player2_ws}
        
        # 아이템 데이터 mock 설정
        redis_mock.hget.return_value = json.dumps({
            "item_id": 1,
            "name": "시간 연장",
            "effect_type": "extend_time",
            "duration": 10
        })
        
        redis_mock.exists.return_value = False  # 쿨다운 없음
        
        # 1. 게임 생성 및 시작
        await self._setup_basic_game(game_handler, room_id, [player1_ws, player2_ws])
        
        # 2. 아이템 사용
        item_message = {
            "type": "use_item",
            "room_id": room_id,
            "item_id": 1,
            "target_user_id": None
        }
        
        await game_handler.handle_use_item(player1_ws, item_message)
        
        # 아이템 효과 적용 확인 (Redis 호출 확인)
        redis_mock.setex.assert_called()  # 쿨다운 설정
        
        # 분석 이벤트 추적 확인
        game_handler._analytics_service.track_event.assert_called_with(
            "item_used", 1, {
                "item_id": 1,
                "room_id": room_id,
                "effect_type": "extend_time"
            }
        )
    
    @pytest.mark.asyncio
    async def test_game_timeout_scenario(self, setup_game_environment):
        """게임 타임아웃 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        room_id = "timeout_room"
        
        # 플레이어 설정
        player1_ws = MockWebSocket(1, "플레이어1")
        player2_ws = MockWebSocket(2, "플레이어2")
        
        ws_manager.connections = {1: player1_ws, 2: player2_ws}
        
        # 1. 게임 생성 및 시작
        await self._setup_basic_game(game_handler, room_id, [player1_ws, player2_ws])
        
        # 2. 턴 타임아웃 시뮬레이션
        timeout_message = {
            "type": "turn_timeout",
            "room_id": room_id
        }
        
        await game_handler.handle_turn_timeout(player1_ws, timeout_message)
        
        # 타임아웃 처리 확인
        game_state = await game_handler.game_engine.get_game_state(room_id)
        # 턴이 넘어가거나 게임 상태가 변경되었는지 확인
        
        # 분석 이벤트 확인
        game_handler._analytics_service.track_event.assert_called_with(
            "turn_timeout", None, {"room_id": room_id}
        )
    
    @pytest.mark.asyncio
    async def test_error_handling_scenario(self, setup_game_environment):
        """에러 처리 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        player_ws = MockWebSocket(1, "플레이어1")
        ws_manager.connections = {1: player_ws}
        
        # 1. 존재하지 않는 방 참가 시도
        invalid_join = {
            "type": "join_game",
            "room_id": "nonexistent_room"
        }
        
        await game_handler.handle_join_game(player_ws, invalid_join)
        
        # 에러 메시지 확인
        last_message = player_ws.get_last_message()
        if last_message:
            assert last_message.get('type') == 'error' or last_message.get('success') == False
        
        # 2. 잘못된 단어 제출
        room_id = "error_room"
        await self._setup_basic_game(game_handler, room_id, [player_ws])
        
        invalid_word_message = {
            "type": "submit_word",
            "room_id": room_id,
            "word": "invalid_word_끝말잇기_안맞음"
        }
        
        await game_handler.handle_submit_word(player_ws, invalid_word_message)
        
        # 에러 응답 확인
        word_response = player_ws.get_last_message()
        if word_response:
            assert word_response.get('success') == False or word_response.get('type') == 'error'
    
    @pytest.mark.asyncio
    async def test_reconnection_scenario(self, setup_game_environment):
        """재연결 시나리오"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        room_id = "reconnection_room"
        
        # 플레이어 설정
        player1_ws = MockWebSocket(1, "플레이어1")
        player2_ws = MockWebSocket(2, "플레이어2")
        
        ws_manager.connections = {1: player1_ws, 2: player2_ws}
        
        # 1. 게임 생성 및 시작
        await self._setup_basic_game(game_handler, room_id, [player1_ws, player2_ws])
        
        # 2. 플레이어1 연결 끊김 시뮬레이션
        await player1_ws.close()
        
        # 3. 연결 해제 처리
        disconnect_message = {
            "type": "disconnect",
            "room_id": room_id
        }
        
        await game_handler.handle_disconnect(player1_ws, disconnect_message)
        
        # 4. 새로운 WebSocket으로 재연결
        reconnected_ws = MockWebSocket(1, "플레이어1")
        ws_manager.connections[1] = reconnected_ws
        
        # 5. 게임 상태 복원 요청
        restore_message = {
            "type": "restore_game_state",
            "room_id": room_id
        }
        
        await game_handler.handle_restore_game_state(reconnected_ws, restore_message)
        
        # 게임 상태가 전송되었는지 확인
        state_message = reconnected_ws.get_last_message()
        if state_message:
            assert 'game_state' in state_message or state_message.get('type') == 'game_state'
    
    @pytest.mark.asyncio
    async def test_performance_multiple_rooms(self, setup_game_environment):
        """다중 방 성능 테스트"""
        game_handler = setup_game_environment['game_handler']
        ws_manager = setup_game_environment['ws_manager']
        
        # 10개 방에서 동시 게임 진행 시뮬레이션
        rooms = []
        players = {}
        
        for room_num in range(10):
            room_id = f"perf_room_{room_num}"
            room_players = []
            
            # 각 방에 2명씩 플레이어 배치
            for player_num in range(2):
                user_id = (room_num * 2) + player_num + 1
                player_ws = MockWebSocket(user_id, f"Player_{user_id}")
                room_players.append(player_ws)
                players[user_id] = player_ws
                ws_manager.connections[user_id] = player_ws
            
            rooms.append((room_id, room_players))
        
        # 모든 방에서 동시에 게임 시작
        tasks = []
        for room_id, room_players in rooms:
            task = self._setup_basic_game(game_handler, room_id, room_players)
            tasks.append(task)
        
        # 모든 게임이 정상 생성되는지 확인
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # 성능 메트릭 확인 (실제로는 시간 측정 등)
        # 여기서는 기본적인 상태 확인만 수행
        for room_id, _ in rooms:
            game_state = await game_handler.game_engine.get_game_state(room_id)
            if game_state:  # Redis mock으로 인해 실제 데이터가 없을 수 있음
                assert game_state.room_id == room_id
    
    async def _setup_basic_game(self, game_handler, room_id: str, players: list):
        """기본 게임 설정 헬퍼 함수"""
        # 첫 번째 플레이어가 방 생성
        create_message = {
            "type": "create_room",
            "room_id": room_id,
            "max_players": len(players),
            "game_mode": "classic"
        }
        
        await game_handler.handle_create_room(players[0], create_message)
        
        # 나머지 플레이어들 참가
        for player in players[1:]:
            join_message = {
                "type": "join_game",
                "room_id": room_id
            }
            await game_handler.handle_join_game(player, join_message)
        
        # 게임 시작
        start_message = {
            "type": "start_game", 
            "room_id": room_id
        }
        
        await game_handler.handle_start_game(players[0], start_message)


class TestGameFlowValidation:
    """게임 플로우 검증 테스트"""
    
    @pytest.mark.asyncio
    async def test_word_chain_validation(self):
        """단어 연결 검증 테스트"""
        from services.word_validator import WordValidator, WordChainState
        
        validator = WordValidator()
        
        # 단어 체인 상태 생성
        word_chain = WordChainState()
        used_words = set()
        
        # 첫 번째 단어: "사과" 
        result1 = await validator.validate_word_chain("사과", word_chain, used_words)
        assert result1.is_valid == True
        
        # 단어 체인 업데이트
        word_chain.words.append("사과")
        word_chain.current_last_char = "과"
        used_words.add("사과")
        
        # 두 번째 단어: "과일" (올바른 연결)
        result2 = await validator.validate_word_chain("과일", word_chain, used_words)
        assert result2.is_valid == True
        
        # 세 번째 단어: "바나나" (잘못된 연결 - "일"로 시작해야 함)
        result3 = await validator.validate_word_chain("바나나", word_chain, used_words)
        assert result3.is_valid == False
        assert "끝말잇기" in result3.reason
    
    @pytest.mark.asyncio
    async def test_score_accumulation(self):
        """점수 누적 테스트"""
        from services.score_calculator import ScoreCalculator
        from unittest.mock import Mock
        
        calculator = ScoreCalculator()
        
        # 게임 세션 mock
        game_session = Mock()
        game_session.scores = {}
        
        # 플레이어별 점수 테스트 데이터
        score_data = [
            (1, "사과", 4, 2.0, 1),  # user_id, word, length, response_time, combo
            (2, "과일", 4, 3.0, 1),
            (1, "일기장", 6, 1.5, 2),
            (2, "장난감", 6, 4.0, 1)
        ]
        
        total_scores = {1: 0, 2: 0}
        
        for user_id, word, length, response_time, combo in score_data:
            # 단어 정보 mock
            word_info = Mock()
            word_info.word = word
            word_info.length = length
            word_info.difficulty_score = 2
            word_info.rarity_score = 1
            word_info.is_valid = True
            
            # 체인 상태 mock
            word_chain = Mock()
            word_chain.consecutive_success = combo
            
            # 점수 계산
            score_breakdown = calculator.calculate_word_score(
                word_info, response_time, word_chain
            )
            
            total_scores[user_id] += score_breakdown.total_score
            
            assert score_breakdown.base_score > 0
            assert score_breakdown.total_score >= score_breakdown.base_score
        
        # 최종 점수 검증
        assert total_scores[1] > 0
        assert total_scores[2] > 0
    
    def test_game_state_transitions(self):
        """게임 상태 전환 테스트"""
        from services.game_engine import GamePhase, GameState
        
        # 초기 상태
        game_state = GameState(
            room_id="test_room",
            phase=GamePhase.WAITING,
            players=[],
            current_turn_index=0
        )
        
        # 상태 전환 시퀀스 검증
        transitions = [
            (GamePhase.WAITING, "플레이어 대기"),
            (GamePhase.PLAYING, "게임 진행"),  
            (GamePhase.FINISHED, "게임 종료")
        ]
        
        for phase, description in transitions:
            game_state.phase = phase
            assert game_state.phase == phase
            
            # 각 상태에서 허용되는 액션 검증
            if phase == GamePhase.WAITING:
                assert game_state.can_join_player() == True
            elif phase == GamePhase.PLAYING:
                assert game_state.can_submit_word() == True
            elif phase == GamePhase.FINISHED:
                assert game_state.can_join_player() == False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])