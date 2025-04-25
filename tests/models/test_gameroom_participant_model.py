from sqlalchemy.orm import Session
from app.models import Guest, Gameroom

class TestGameroomParticipantModel:
    def test_participant_creation(self, db_session: Session):
        """Test basic participant creation."""
        # Create a guest
        guest = Guest(nickname="Participant")
        db_session.add(guest)
        db_session.flush()

        # Now that guest_id is created, it can be used for Gameroom
        room = Gameroom(
            title="Participation Test",
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.flush()
        
        # Rest of the test code remains the same...

    def test_participant_status_enum(self, db_session: Session):
        """Test that ParticipantStatus enum values work correctly."""
        # Create a guest
        guest = Guest(nickname="StatusTester")
        db_session.add(guest)
        db_session.flush()
        
        # Create a gameroom
        room = Gameroom(
            title="Status Test",
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.flush()
        
        # Rest of the test code remains the same...

    def test_participant_relationships(self, db_session: Session):
        """Test the relationships between GameroomParticipant, Gameroom, and Guest."""
        # Create a guest
        guest = Guest(nickname="RelationshipTest")
        db_session.add(guest)
        db_session.flush()
        
        # Create a gameroom
        room = Gameroom(
            title="Relationship Test Room",
            created_by=guest.guest_id
        )
        db_session.add(room)
        db_session.flush()
        
        # Rest of the test code remains the same...