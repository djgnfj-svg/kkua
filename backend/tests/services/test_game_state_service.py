"""
Tests for GameStateService
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from services.game_state_service import GameStateService
from repositories.gameroom_repository import GameroomRepository
from models.gameroom_model import Gameroom, GameStatus, ParticipantStatus, GameroomParticipant
from models.guest_model import Guest
import uuid


class TestGameStateService:
    """Test cases for GameStateService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        db = Mock(spec=Session)
        db.commit = Mock()
        db.rollback = Mock()
        return db
    
    @pytest.fixture
    def mock_repository(self):
        """Mock gameroom repository"""
        return Mock(spec=GameroomRepository)
    
    @pytest.fixture
    def game_state_service(self, mock_db, mock_repository):
        """Create GameStateService instance"""
        service = GameStateService(mock_db)
        service.repository = mock_repository
        return service
    
    @pytest.fixture
    def sample_room(self):
        """Create a sample game room"""
        return Gameroom(
            room_id=1,
            room_name="테스트방",
            created_by=1,
            max_players=4,
            status=GameStatus.WAITING,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    @pytest.fixture
    def sample_guest(self):
        """Create a sample guest"""
        return Guest(
            guest_id=1,
            uuid=uuid.uuid4(),
            nickname="테스트사용자",
            device_info="test_device",
            created_at=None,
            last_login=None
        )
    
    @pytest.fixture
    def sample_participants(self, sample_guest):
        """Create sample participants"""
        creator = Mock(spec=GameroomParticipant)
        creator.guest_id = 1
        creator.is_creator = True
        creator.status = ParticipantStatus.READY.value
        creator.updated_at = datetime.now()
        
        participant = Mock(spec=GameroomParticipant)
        participant.guest_id = 2
        participant.is_creator = False
        participant.status = ParticipantStatus.READY.value
        participant.updated_at = datetime.now()
        
        return [creator, participant]
    
    def test_start_game_success(self, game_state_service, mock_db, mock_repository, sample_room, sample_participants):
        """Test successful game start"""
        # Setup
        room_id = 1
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.return_value = sample_participants
        
        # Execute
        result = game_state_service.start_game(room_id)
        
        # Verify
        assert result is True
        assert sample_room.status == GameStatus.PLAYING
        assert sample_room.started_at is not None
        assert sample_room.updated_at is not None
        
        # Verify all participants are in PLAYING state
        for participant in sample_participants:
            assert participant.status == ParticipantStatus.PLAYING.value
            assert participant.updated_at is not None
        
        mock_db.commit.assert_called_once()
    
    def test_start_game_room_not_found(self, game_state_service, mock_repository):
        """Test start game when room not found"""
        # Setup
        room_id = 999
        mock_repository.find_by_id.return_value = None
        
        # Execute
        result = game_state_service.start_game(room_id)
        
        # Verify
        assert result is False
    
    def test_start_game_exception(self, game_state_service, mock_db, mock_repository, sample_room):
        """Test start game with exception"""
        # Setup
        room_id = 1
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.side_effect = Exception("Database error")
        
        # Execute
        result = game_state_service.start_game(room_id)
        
        # Verify
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_end_game_success(self, game_state_service, mock_db, mock_repository, sample_room, sample_participants):
        """Test successful game end"""
        # Setup
        room_id = 1
        sample_room.status = GameStatus.PLAYING
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.return_value = sample_participants
        
        # Execute
        result = game_state_service.end_game(room_id)
        
        # Verify
        assert result is True
        assert sample_room.status == GameStatus.WAITING
        assert sample_room.ended_at is not None
        assert sample_room.updated_at is not None
        
        # Verify creator is READY, others are WAITING
        creator = sample_participants[0]
        participant = sample_participants[1]
        assert creator.status == ParticipantStatus.READY.value
        assert participant.status == ParticipantStatus.WAITING.value
        
        mock_db.commit.assert_called_once()
    
    def test_end_game_room_not_found(self, game_state_service, mock_repository):
        """Test end game when room not found"""
        # Setup
        room_id = 999
        mock_repository.find_by_id.return_value = None
        
        # Execute
        result = game_state_service.end_game(room_id)
        
        # Verify
        assert result is False
    
    def test_end_game_exception(self, game_state_service, mock_db, mock_repository, sample_room):
        """Test end game with exception"""
        # Setup
        room_id = 1
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.side_effect = Exception("Database error")
        
        # Execute
        result = game_state_service.end_game(room_id)
        
        # Verify
        assert result is False
        mock_db.rollback.assert_called_once()
    
    def test_check_all_ready_success(self, game_state_service, mock_repository, sample_room):
        """Test check all ready when all participants are ready"""
        # Setup
        room_id = 1
        sample_room.created_by = 1
        mock_repository.find_by_id.return_value = sample_room
        
        # Create participants - creator (excluded) and ready participant
        participants = [
            Mock(guest_id=1, is_creator=True, status=ParticipantStatus.READY.value),  # Creator
            Mock(guest_id=2, is_creator=False, status=ParticipantStatus.READY.value),  # Ready participant
        ]
        mock_repository.find_room_participants.return_value = participants
        
        # Execute
        result = game_state_service.check_all_ready(room_id)
        
        # Verify
        assert result is True
    
    def test_check_all_ready_not_all_ready(self, game_state_service, mock_repository, sample_room):
        """Test check all ready when not all participants are ready"""
        # Setup
        room_id = 1
        sample_room.created_by = 1
        mock_repository.find_by_id.return_value = sample_room
        
        # Create participants - one not ready
        participants = [
            Mock(guest_id=1, is_creator=True, status=ParticipantStatus.READY.value),  # Creator
            Mock(guest_id=2, is_creator=False, status=ParticipantStatus.READY.value),  # Ready participant
            Mock(guest_id=3, is_creator=False, status=ParticipantStatus.WAITING.value),  # Not ready
        ]
        mock_repository.find_room_participants.return_value = participants
        
        # Execute
        result = game_state_service.check_all_ready(room_id)
        
        # Verify
        assert result is False
    
    def test_check_all_ready_no_participants(self, game_state_service, mock_repository, sample_room):
        """Test check all ready when no participants (excluding creator)"""
        # Setup
        room_id = 1
        sample_room.created_by = 1
        mock_repository.find_by_id.return_value = sample_room
        
        # Only creator, no other participants
        participants = [
            Mock(guest_id=1, is_creator=True, status=ParticipantStatus.READY.value),  # Creator only
        ]
        mock_repository.find_room_participants.return_value = participants
        
        # Execute
        result = game_state_service.check_all_ready(room_id)
        
        # Verify
        assert result is False
    
    def test_check_all_ready_room_not_found(self, game_state_service, mock_repository):
        """Test check all ready when room not found"""
        # Setup
        room_id = 999
        mock_repository.find_by_id.return_value = None
        
        # Execute
        result = game_state_service.check_all_ready(room_id)
        
        # Verify
        assert result is False
    
    def test_check_all_ready_exception(self, game_state_service, mock_repository, sample_room):
        """Test check all ready with exception"""
        # Setup
        room_id = 1
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.side_effect = Exception("Database error")
        
        # Execute
        result = game_state_service.check_all_ready(room_id)
        
        # Verify
        assert result is False
    
    def test_can_start_game_success(self, game_state_service, mock_repository, sample_room):
        """Test can start game when all conditions are met"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.WAITING
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.return_value = [Mock(), Mock()]  # 2 participants
        
        with patch.object(game_state_service, 'check_all_ready', return_value=True):
            # Execute
            can_start, message = game_state_service.can_start_game(room_id, host_id)
            
            # Verify
            assert can_start is True
            assert message == "게임 시작 가능"
    
    def test_can_start_game_room_not_found(self, game_state_service, mock_repository):
        """Test can start game when room not found"""
        # Setup
        room_id = 999
        host_id = 1
        mock_repository.find_by_id.return_value = None
        
        # Execute
        can_start, message = game_state_service.can_start_game(room_id, host_id)
        
        # Verify
        assert can_start is False
        assert message == "존재하지 않는 방입니다."
    
    def test_can_start_game_not_host(self, game_state_service, mock_repository, sample_room):
        """Test can start game when not host"""
        # Setup
        room_id = 1
        host_id = 2  # Different from room creator
        sample_room.created_by = 1
        mock_repository.find_by_id.return_value = sample_room
        
        # Execute
        can_start, message = game_state_service.can_start_game(room_id, host_id)
        
        # Verify
        assert can_start is False
        assert message == "방장만 게임을 시작할 수 있습니다."
    
    def test_can_start_game_already_playing(self, game_state_service, mock_repository, sample_room):
        """Test can start game when already playing"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.PLAYING
        mock_repository.find_by_id.return_value = sample_room
        
        # Execute
        can_start, message = game_state_service.can_start_game(room_id, host_id)
        
        # Verify
        assert can_start is False
        assert message == "이미 게임이 진행 중입니다."
    
    def test_can_start_game_not_enough_players(self, game_state_service, mock_repository, sample_room):
        """Test can start game with not enough players"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.WAITING
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.return_value = [Mock()]  # Only 1 participant
        
        # Execute
        can_start, message = game_state_service.can_start_game(room_id, host_id)
        
        # Verify
        assert can_start is False
        assert message == "게임 시작을 위해 최소 2명의 플레이어가 필요합니다."
    
    def test_can_start_game_not_all_ready(self, game_state_service, mock_repository, sample_room):
        """Test can start game when not all players are ready"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.WAITING
        mock_repository.find_by_id.return_value = sample_room
        mock_repository.find_room_participants.return_value = [Mock(), Mock()]  # 2 participants
        
        with patch.object(game_state_service, 'check_all_ready', return_value=False):
            # Execute
            can_start, message = game_state_service.can_start_game(room_id, host_id)
            
            # Verify
            assert can_start is False
            assert message == "모든 플레이어가 준비 상태여야 합니다."
    
    def test_can_end_game_success(self, game_state_service, mock_repository, sample_room):
        """Test can end game when all conditions are met"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.PLAYING
        mock_repository.find_by_id.return_value = sample_room
        
        # Execute
        result = game_state_service.can_end_game(room_id, host_id)
        
        # Verify
        assert result is True
    
    def test_can_end_game_room_not_found(self, game_state_service, mock_repository):
        """Test can end game when room not found"""
        # Setup
        room_id = 999
        host_id = 1
        mock_repository.find_by_id.return_value = None
        
        # Execute
        result = game_state_service.can_end_game(room_id, host_id)
        
        # Verify
        assert result is False
    
    def test_can_end_game_not_host(self, game_state_service, mock_repository, sample_room):
        """Test can end game when not host"""
        # Setup
        room_id = 1
        host_id = 2  # Different from room creator
        sample_room.created_by = 1
        sample_room.status = GameStatus.PLAYING
        mock_repository.find_by_id.return_value = sample_room
        
        # Execute
        result = game_state_service.can_end_game(room_id, host_id)
        
        # Verify
        assert result is False
    
    def test_can_end_game_not_playing(self, game_state_service, mock_repository, sample_room):
        """Test can end game when not playing"""
        # Setup
        room_id = 1
        host_id = 1
        sample_room.created_by = host_id
        sample_room.status = GameStatus.WAITING
        mock_repository.find_by_id.return_value = sample_room
        
        # Execute
        result = game_state_service.can_end_game(room_id, host_id)
        
        # Verify
        assert result is False