"""
Tests for WebSocketMessageService
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import WebSocket
from sqlalchemy.orm import Session

from services.websocket_message_service import WebSocketMessageService
from models.guest_model import Guest
from models.gameroom_model import ParticipantStatus, GameroomParticipant
from repositories.gameroom_repository import GameroomRepository
from websocket.connection_manager import GameRoomWebSocketFacade
import uuid


class TestWebSocketMessageService:
    """Test cases for WebSocketMessageService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def mock_ws_manager(self):
        """Mock WebSocket manager"""
        manager = Mock(spec=GameRoomWebSocketFacade)
        manager.broadcast_to_room = AsyncMock()
        manager.send_personal_message = AsyncMock()
        manager.broadcast_ready_status = AsyncMock()
        manager.broadcast_room_update = AsyncMock()
        manager.broadcast_word_chain_state = AsyncMock()
        manager.start_turn_timer = AsyncMock()
        manager.initialize_word_chain_game = Mock()
        manager.start_word_chain_game = Mock()
        manager.submit_word = Mock()
        manager.end_word_chain_game = Mock()
        manager.get_game_state = Mock()
        return manager

    @pytest.fixture
    def mock_repository(self):
        """Mock gameroom repository"""
        return Mock(spec=GameroomRepository)

    @pytest.fixture
    def websocket_service(self, mock_db, mock_ws_manager, mock_repository):
        """Create WebSocketMessageService instance"""
        service = WebSocketMessageService(mock_db, mock_ws_manager)
        service.repository = mock_repository
        return service

    @pytest.fixture
    def sample_guest(self):
        """Create a sample guest"""
        return Guest(
            guest_id=1,
            uuid=uuid.uuid4(),
            nickname="테스트사용자",
            device_info="test_device",
            created_at=None,
            last_login=None,
        )

    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket"""
        return Mock(spec=WebSocket)

    @pytest.fixture
    def mock_participant(self):
        """Mock participant"""
        participant = Mock(spec=GameroomParticipant)
        participant.status = ParticipantStatus.WAITING.value
        participant.is_creator = False
        participant.participant_id = 1
        return participant

    @pytest.fixture
    def mock_creator_participant(self):
        """Mock creator participant"""
        participant = Mock(spec=GameroomParticipant)
        participant.status = ParticipantStatus.WAITING.value
        participant.is_creator = True
        participant.participant_id = 1
        return participant

    async def test_handle_chat_message(
        self, websocket_service, mock_ws_manager, sample_guest
    ):
        """Test handling chat messages"""
        # Setup
        message_data = {"message": "안녕하세요!", "timestamp": "2024-01-01T12:00:00Z"}
        room_id = 1

        # Execute
        await websocket_service.handle_chat_message(message_data, room_id, sample_guest)

        # Verify
        mock_ws_manager.broadcast_to_room.assert_called_once_with(
            room_id,
            {
                "type": "chat",
                "guest_id": sample_guest.guest_id,
                "nickname": sample_guest.nickname,
                "message": "안녕하세요!",
                "timestamp": "2024-01-01T12:00:00Z",
            },
        )

    async def test_handle_chat_message_no_nickname(
        self, websocket_service, mock_ws_manager, sample_guest
    ):
        """Test handling chat messages with no nickname"""
        # Setup
        sample_guest.nickname = None
        message_data = {"message": "안녕하세요!"}
        room_id = 1

        # Execute
        await websocket_service.handle_chat_message(message_data, room_id, sample_guest)

        # Verify
        mock_ws_manager.broadcast_to_room.assert_called_once()
        call_args = mock_ws_manager.broadcast_to_room.call_args[0]
        assert call_args[1]["nickname"] == f"게스트_{sample_guest.guest_id}"

    async def test_handle_ready_toggle_normal_user(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
        mock_participant,
    ):
        """Test ready toggle for normal user"""
        # Setup
        room_id = 1
        mock_repository.find_participant.return_value = mock_participant
        mock_repository.update_participant_status.return_value = None

        # Execute
        await websocket_service.handle_ready_toggle(
            mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_repository.find_participant.assert_called_once_with(
            room_id, sample_guest.guest_id
        )
        mock_repository.update_participant_status.assert_called_once_with(
            room_id, mock_participant.participant_id, ParticipantStatus.READY.value
        )
        mock_ws_manager.broadcast_ready_status.assert_called_once_with(
            room_id, sample_guest.guest_id, True, sample_guest.nickname
        )
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "ready_status_updated", "is_ready": True}, mock_websocket
        )

    async def test_handle_ready_toggle_creator(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
        mock_creator_participant,
    ):
        """Test ready toggle for room creator"""
        # Setup
        room_id = 1
        mock_repository.find_participant.return_value = mock_creator_participant

        # Execute
        await websocket_service.handle_ready_toggle(
            mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {
                "type": "ready_status_updated",
                "is_ready": True,
                "message": "방장은 항상 준비 상태입니다.",
            },
            mock_websocket,
        )
        mock_repository.update_participant_status.assert_not_called()

    async def test_handle_ready_toggle_no_participant(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test ready toggle when participant not found"""
        # Setup
        room_id = 1
        mock_repository.find_participant.return_value = None

        # Execute
        await websocket_service.handle_ready_toggle(
            mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "준비 상태 변경 실패: 참가자 정보가 없습니다"},
            mock_websocket,
        )

    async def test_handle_ready_toggle_in_game(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
        mock_participant,
    ):
        """Test ready toggle during game"""
        # Setup
        room_id = 1
        mock_participant.status = ParticipantStatus.PLAYING.value
        mock_repository.find_participant.return_value = mock_participant

        # Execute
        await websocket_service.handle_ready_toggle(
            mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "게임 중에는 준비 상태를 변경할 수 없습니다"},
            mock_websocket,
        )

    async def test_handle_status_update_success(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
        mock_participant,
    ):
        """Test successful status update"""
        # Setup
        room_id = 1
        message_data = {"status": "READY"}
        mock_repository.find_participant.return_value = mock_participant
        mock_repository.update_participant_status.return_value = mock_participant

        # Execute
        await websocket_service.handle_status_update(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_repository.update_participant_status.assert_called_once_with(
            room_id, mock_participant.participant_id, ParticipantStatus.READY.value
        )
        mock_ws_manager.broadcast_room_update.assert_called_once()

    async def test_handle_status_update_invalid_status(
        self, websocket_service, mock_ws_manager, mock_websocket, sample_guest
    ):
        """Test status update with invalid status"""
        # Setup
        room_id = 1
        message_data = {"status": "INVALID_STATUS"}

        # Execute
        await websocket_service.handle_status_update(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "유효하지 않은 상태 값: INVALID_STATUS"},
            mock_websocket,
        )

    async def test_handle_status_update_no_participant(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test status update when participant not found"""
        # Setup
        room_id = 1
        message_data = {"status": "READY"}
        mock_repository.find_participant.return_value = None

        # Execute
        await websocket_service.handle_status_update(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "상태 업데이트 실패: 참가자 정보가 없습니다"},
            mock_websocket,
        )

    async def test_handle_word_chain_initialize_game(
        self, websocket_service, mock_websocket, sample_guest
    ):
        """Test word chain game initialization"""
        # Setup
        message_data = {"action": "initialize_game"}
        room_id = 1

        with patch.object(
            websocket_service, "_handle_initialize_game", new_callable=AsyncMock
        ) as mock_handler:
            # Execute
            await websocket_service.handle_word_chain_message(
                message_data, mock_websocket, room_id, sample_guest
            )

            # Verify
            mock_handler.assert_called_once_with(mock_websocket, room_id, sample_guest)

    async def test_handle_word_chain_start_game(
        self, websocket_service, mock_websocket, sample_guest
    ):
        """Test word chain game start"""
        # Setup
        message_data = {"action": "start_game"}
        room_id = 1

        with patch.object(
            websocket_service, "_handle_start_game", new_callable=AsyncMock
        ) as mock_handler:
            # Execute
            await websocket_service.handle_word_chain_message(
                message_data, mock_websocket, room_id, sample_guest
            )

            # Verify
            mock_handler.assert_called_once_with(
                message_data, mock_websocket, room_id, sample_guest
            )

    async def test_handle_word_chain_submit_word(
        self, websocket_service, mock_websocket, sample_guest
    ):
        """Test word chain word submission"""
        # Setup
        message_data = {"action": "submit_word"}
        room_id = 1

        with patch.object(
            websocket_service, "_handle_submit_word", new_callable=AsyncMock
        ) as mock_handler:
            # Execute
            await websocket_service.handle_word_chain_message(
                message_data, mock_websocket, room_id, sample_guest
            )

            # Verify
            mock_handler.assert_called_once_with(
                message_data, mock_websocket, room_id, sample_guest
            )

    async def test_handle_word_chain_end_game(
        self, websocket_service, mock_websocket, sample_guest
    ):
        """Test word chain game end"""
        # Setup
        message_data = {"action": "end_game"}
        room_id = 1

        with patch.object(
            websocket_service, "_handle_end_game", new_callable=AsyncMock
        ) as mock_handler:
            # Execute
            await websocket_service.handle_word_chain_message(
                message_data, mock_websocket, room_id, sample_guest
            )

            # Verify
            mock_handler.assert_called_once_with(mock_websocket, room_id, sample_guest)

    async def test_handle_initialize_game_not_creator(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test game initialization by non-creator"""
        # Setup
        room_id = 1
        mock_room = Mock()
        mock_room.created_by = 999  # Different from sample_guest.guest_id
        mock_repository.find_by_id.return_value = mock_room

        # Execute
        await websocket_service._handle_initialize_game(
            mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "방장만 게임을 초기화할 수 있습니다."},
            mock_websocket,
        )

    async def test_handle_start_game_not_creator(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test game start by non-creator"""
        # Setup
        room_id = 1
        message_data = {"first_word": "시작"}
        mock_participant = Mock()
        mock_participant.is_creator = False
        mock_repository.find_participant.return_value = mock_participant

        # Execute
        await websocket_service._handle_start_game(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "방장만 게임을 시작할 수 있습니다."},
            mock_websocket,
        )

    async def test_handle_submit_word_empty_word(
        self, websocket_service, mock_ws_manager, mock_websocket, sample_guest
    ):
        """Test word submission with empty word"""
        # Setup
        room_id = 1
        message_data = {"word": ""}

        # Execute
        await websocket_service._handle_submit_word(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "단어를 입력해주세요."}, mock_websocket
        )

    async def test_handle_submit_word_success(
        self, websocket_service, mock_ws_manager, mock_websocket, sample_guest
    ):
        """Test successful word submission"""
        # Setup
        room_id = 1
        message_data = {"word": "사과"}
        mock_ws_manager.submit_word.return_value = {
            "success": True,
            "next_player": {"id": 2, "nickname": "다른사용자"},
            "last_character": "과",
        }
        mock_ws_manager.get_game_state.return_value = {"time_limit": 15}

        # Execute
        await websocket_service._handle_submit_word(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.submit_word.assert_called_once_with(
            room_id, "사과", sample_guest.guest_id
        )
        mock_ws_manager.broadcast_room_update.assert_called_once()
        mock_ws_manager.broadcast_word_chain_state.assert_called_once_with(room_id)
        mock_ws_manager.start_turn_timer.assert_called_once_with(room_id, 15)

    async def test_handle_submit_word_failure(
        self, websocket_service, mock_ws_manager, mock_websocket, sample_guest
    ):
        """Test failed word submission"""
        # Setup
        room_id = 1
        message_data = {"word": "잘못된단어"}
        mock_ws_manager.submit_word.return_value = {
            "success": False,
            "message": "유효하지 않은 단어입니다.",
        }

        # Execute
        await websocket_service._handle_submit_word(
            message_data, mock_websocket, room_id, sample_guest
        )

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "word_chain_error", "message": "유효하지 않은 단어입니다."},
            mock_websocket,
        )

    async def test_handle_end_game_not_creator(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test game end by non-creator"""
        # Setup
        room_id = 1
        mock_participant = Mock()
        mock_participant.is_creator = False
        mock_repository.find_participant.return_value = mock_participant

        # Execute
        await websocket_service._handle_end_game(mock_websocket, room_id, sample_guest)

        # Verify
        mock_ws_manager.send_personal_message.assert_called_once_with(
            {"type": "error", "message": "방장만 게임을 종료할 수 있습니다."},
            mock_websocket,
        )

    async def test_handle_end_game_success(
        self,
        websocket_service,
        mock_repository,
        mock_ws_manager,
        mock_websocket,
        sample_guest,
    ):
        """Test successful game end"""
        # Setup
        room_id = 1
        mock_participant = Mock()
        mock_participant.is_creator = True
        mock_repository.find_participant.return_value = mock_participant
        mock_ws_manager.end_word_chain_game.return_value = True

        # Execute
        await websocket_service._handle_end_game(mock_websocket, room_id, sample_guest)

        # Verify
        mock_ws_manager.end_word_chain_game.assert_called_once_with(room_id)
        mock_ws_manager.broadcast_room_update.assert_called_once()

    async def test_handle_host_change_notification(
        self, websocket_service, mock_ws_manager
    ):
        """Test host change notification"""
        # Setup
        room_id = 1
        new_host_id = 2
        new_host_nickname = "새방장"

        # Execute
        await websocket_service.handle_host_change_notification(
            room_id, new_host_id, new_host_nickname
        )

        # Verify
        mock_ws_manager.broadcast_room_update.assert_called_once_with(
            room_id,
            "host_changed",
            {
                "new_host_id": new_host_id,
                "new_host_nickname": new_host_nickname,
                "message": f"{new_host_nickname}님이 새로운 방장이 되었습니다.",
            },
        )

    async def test_handle_participant_list_update(
        self, websocket_service, mock_repository, mock_ws_manager
    ):
        """Test participant list update"""
        # Setup
        room_id = 1
        participants = [{"guest_id": 1, "nickname": "사용자1"}]
        mock_repository.get_participants.return_value = participants

        # Execute
        await websocket_service.handle_participant_list_update(room_id)

        # Verify
        mock_repository.get_participants.assert_called_once_with(room_id)
        mock_ws_manager.broadcast_room_update.assert_called_once_with(
            room_id,
            "participant_list_updated",
            {
                "participants": participants,
                "message": "참가자 목록이 업데이트되었습니다.",
            },
        )

    def test_is_room_owner_true(self, websocket_service, mock_repository):
        """Test is_room_owner returns True for owner"""
        # Setup
        room_id = 1
        guest_id = 1
        mock_participant = Mock()
        mock_participant.is_creator = True
        mock_repository.find_participant.return_value = mock_participant

        # Execute
        result = websocket_service.is_room_owner(room_id, guest_id)

        # Verify
        assert result is True

    def test_is_room_owner_false(self, websocket_service, mock_repository):
        """Test is_room_owner returns False for non-owner"""
        # Setup
        room_id = 1
        guest_id = 1
        mock_participant = Mock()
        mock_participant.is_creator = False
        mock_repository.find_participant.return_value = mock_participant

        # Execute
        result = websocket_service.is_room_owner(room_id, guest_id)

        # Verify
        assert result is False

    def test_is_room_owner_no_participant(self, websocket_service, mock_repository):
        """Test is_room_owner returns False when participant not found"""
        # Setup
        room_id = 1
        guest_id = 1
        mock_repository.find_participant.return_value = None

        # Execute
        result = websocket_service.is_room_owner(room_id, guest_id)

        # Verify
        assert result is False
