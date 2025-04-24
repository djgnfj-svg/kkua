import pytest
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.guest_model import Guest

class TestGuestModel:
    def test_guest_creation(self, db_session: Session):
        """Test basic guest creation with minimal parameters."""
        # Create a guest with only required fields
        guest = Guest()
        db_session.add(guest)
        db_session.commit()
        
        # Verify guest was created with an ID and default values
        assert guest.guest_id is not None
        assert isinstance(guest.uuid, uuid.UUID)
        assert guest.nickname is None
        assert isinstance(guest.created_at, datetime)
        
    def test_guest_with_all_fields(self, db_session: Session):
        """Test guest creation with all fields specified."""
        # Create a custom UUID
        test_uuid = uuid.uuid4()
        test_nickname = "TestUser"
        test_device = "Test Device"
        
        # Create guest with all fields
        guest = Guest(
            uuid=test_uuid,
            nickname=test_nickname,
            device_info=test_device
        )
        db_session.add(guest)
        db_session.commit()
        
        # Verify all fields were set correctly
        assert guest.guest_id is not None
        assert guest.uuid == test_uuid
        assert guest.nickname == test_nickname
        assert guest.device_info == test_device
        
    def test_guest_last_login_update(self, db_session: Session):
        """Test updating a guest's last login time."""
        # Create guest
        guest = Guest(nickname="LoginTest")
        db_session.add(guest)
        db_session.commit()
        
        # Initially last_login should be None
        assert guest.last_login is None
        
        # Update last_login
        now = datetime.utcnow()
        guest.last_login = now
        db_session.commit()
        db_session.refresh(guest)
        
        # Verify last_login was updated
        assert guest.last_login is not None
        # Allow for small time differences in datetime comparison
        assert abs((guest.last_login - now).total_seconds()) < 1 