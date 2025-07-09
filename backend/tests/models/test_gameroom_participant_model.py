from datetime import datetime
from sqlalchemy.orm import Session
from models.gameroom_model import Gameroom, GameroomParticipant, ParticipantStatus
from models.guest_model import Guest


class TestGameroomParticipantModel:
    def test_participant_creation(self, db_session: Session):
        """Test basic participant creation."""
        # Create a guest
        guest = Guest(nickname="Participant")
        db_session.add(guest)
        db_session.flush()

        # Create a gameroom
        room = Gameroom(title="Participation Test", created_by=guest.guest_id)
        db_session.add(room)
        db_session.flush()

        # Create participant
        participant = GameroomParticipant(
            room_id=room.room_id, guest_id=guest.guest_id, is_creator=True
        )
        db_session.add(participant)
        db_session.commit()

        # Verify participant was created with correct values
        assert participant.participant_id is not None
        assert participant.room_id == room.room_id
        assert participant.guest_id == guest.guest_id
        assert participant.status == ParticipantStatus.WAITING.value
        assert participant.is_creator is True
        assert participant.joined_at is not None
        assert participant.left_at is None

    def test_participant_status_enum(self, db_session: Session):
        """Test that ParticipantStatus enum values work correctly."""
        # Create a guest
        guest = Guest(nickname="StatusTester")
        db_session.add(guest)
        db_session.flush()

        # Create a gameroom
        room = Gameroom(title="Status Test", created_by=guest.guest_id)
        db_session.add(room)
        db_session.flush()

        # Create participant with specific status
        participant = GameroomParticipant(
            room_id=room.room_id,
            guest_id=guest.guest_id,
            status=ParticipantStatus.READY.value,
        )
        db_session.add(participant)
        db_session.commit()

        # Check enum value
        assert participant.status == ParticipantStatus.READY.value

        # Update to another enum value
        participant.status = ParticipantStatus.PLAYING.value
        db_session.commit()
        db_session.refresh(participant)

        assert participant.status == ParticipantStatus.PLAYING.value

    def test_participant_relationships(self, db_session: Session):
        """Test the relationships between GameroomParticipant, Gameroom, and Guest."""
        # Create a guest
        guest = Guest(nickname="RelationshipTest")
        db_session.add(guest)
        db_session.flush()

        # Create a gameroom
        room = Gameroom(title="Relationship Test Room", created_by=guest.guest_id)
        db_session.add(room)
        db_session.flush()

        # Create participant
        participant = GameroomParticipant(room_id=room.room_id, guest_id=guest.guest_id)
        db_session.add(participant)
        db_session.commit()

        # Test relationship from participant to room
        assert participant.gameroom is not None
        assert participant.gameroom.room_id == room.room_id
        assert participant.gameroom.title == "Relationship Test Room"

        # Test relationship from participant to guest
        assert participant.guest is not None
        assert participant.guest.guest_id == guest.guest_id
        assert participant.guest.nickname == "RelationshipTest"

        # Test relationship from room to participant
        assert room.participants is not None
        assert len(room.participants) == 1
        assert room.participants[0].participant_id == participant.participant_id

    def test_should_redirect_to_game(self, db_session: Session):
        """Test the should_redirect_to_game class method."""
        # Create a guest
        guest = Guest(nickname="RedirectTester")
        db_session.add(guest)
        db_session.flush()

        # Create a gameroom
        room = Gameroom(title="Redirect Test Room", created_by=guest.guest_id)
        db_session.add(room)
        db_session.flush()

        # Create active participant
        participant = GameroomParticipant(
            room_id=room.room_id,
            guest_id=guest.guest_id,
            status=ParticipantStatus.PLAYING.value,
        )
        db_session.add(participant)
        db_session.commit()

        # Test redirect logic - should return True and room_id
        should_redirect, redirect_room_id = GameroomParticipant.should_redirect_to_game(
            db_session, guest.guest_id
        )
        assert should_redirect is True
        assert redirect_room_id == room.room_id

        # Change participant to LEFT status
        participant.status = ParticipantStatus.LEFT.value
        participant.left_at = datetime.now()
        db_session.commit()

        # Test redirect logic after leaving - should return False
        should_redirect, redirect_room_id = GameroomParticipant.should_redirect_to_game(
            db_session, guest.guest_id
        )
        assert should_redirect is False
        assert redirect_room_id is None
