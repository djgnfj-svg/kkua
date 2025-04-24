import pytest
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from models.gameroom_model import Gameroom, GameStatus, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest

class TestGameroomModel:
    def test_gameroom_creation(self, db_session: Session):
        """Test basic gameroom creation with required fields."""
        # Create a guest first (for foreign key)
        guest = Guest(nickname="GameCreator")
        db_session.add(guest)
        db_session.flush()
        
        # Create a gameroom
        room = Gameroom(
            title="Test Room",
            max_players=8,
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.commit()
        
        # Verify room was created with correct values
        assert room.room_id is not None
        assert room.title == "Test Room"
        assert room.max_players == 8
        assert room.status == GameStatus.WAITING.value
        assert room.created_by == guest.guest_id
        assert room.participant_count == 0
        assert room.room_type == "normal"
        
    def test_gameroom_default_values(self, db_session: Session):
        """Test that default values are set correctly."""
        # Create a guest first
        guest = Guest(nickname="DefaultTester")
        db_session.add(guest)
        db_session.flush()
        
        # Create room with minimal parameters
        room = Gameroom(
            title="Default Test",
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.commit()
        
        # Check default values
        assert room.max_players == 8  # Default value in schema
        assert room.status == GameStatus.WAITING.value
        assert room.participant_count == 0
        assert room.room_type == "normal"
        assert room.created_at is not None
        assert room.updated_at is not None
        assert room.started_at is None
        assert room.ended_at is None
        
    def test_gameroom_status_enum(self, db_session: Session):
        """Test that GameStatus enum values work correctly."""
        # Create a guest first
        guest = Guest(nickname="EnumTester")
        db_session.add(guest)
        db_session.flush()
        
        # Create room
        room = Gameroom(
            title="Enum Test",
            created_by=guest.guest_id,
            status=GameStatus.PLAYING.value
        )
        db_session.add(room)
        db_session.commit()
        
        # Check enum value
        assert room.status == GameStatus.PLAYING.value
        
        # Update to another enum value
        room.status = GameStatus.FINISHED.value
        db_session.commit()
        db_session.refresh(room)
        
        assert room.status == GameStatus.FINISHED.value

    def test_gameroom_relationship(self, db_session: Session):
        """Test the relationship between Gameroom and Guest (creator)."""
        # Create a guest
        guest = Guest(nickname="RelationshipTester")
        db_session.add(guest)
        db_session.flush()
        
        # Create room
        room = Gameroom(
            title="Relationship Test",
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.commit()
        
        # Test relationship from room to creator
        assert room.creator is not None
        assert room.creator.guest_id == guest.guest_id
        assert room.creator.nickname == "RelationshipTester" 