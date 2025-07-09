"""
Authentication service for managing user authentication and sessions
"""

import uuid
from datetime import datetime
from typing import Optional
from fastapi import HTTPException, status, Response
from sqlalchemy.orm import Session
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.guest_repo = GuestRepository(db)

    def login_or_create_guest(self, nickname: Optional[str] = None) -> tuple[Guest, str]:
        """
        Create a new guest or login existing guest
        Returns: (Guest object, guest_uuid)
        """
        guest_uuid = str(uuid.uuid4())
        
        # Check if nickname is provided and unique
        if nickname:
            existing_guest = self.guest_repo.find_by_nickname(nickname)
            if existing_guest:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nickname already exists"
                )
        
        # Create new guest
        import uuid as uuid_module
        nickname = nickname or f"Guest_{guest_uuid[:8]}"
        guest_uuid_obj = uuid_module.UUID(guest_uuid)
        
        guest = self.guest_repo.create(guest_uuid_obj, nickname)
        # Update last login after creation
        self.guest_repo.update_last_login(guest_uuid_obj)
        return guest, guest_uuid

    def authenticate_guest(self, guest_uuid: str) -> Optional[Guest]:
        """
        Authenticate guest by UUID
        Returns: Guest object if valid, None otherwise
        """
        try:
            # Validate UUID format
            uuid.UUID(guest_uuid)
        except ValueError:
            return None
        
        guest = self.guest_repo.find_by_uuid(guest_uuid)
        if guest:
            # Update last login
            self.guest_repo.update_last_login(guest.guest_uuid)
        
        return guest

    def set_auth_cookies(self, response: Response, guest_uuid: str) -> None:
        """Set authentication cookies in response"""
        response.set_cookie(
            key="guest_uuid",
            value=guest_uuid,
            max_age=86400 * 30,  # 30 days
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax"
        )

    def logout(self, response: Response) -> None:
        """Clear authentication cookies"""
        response.delete_cookie(key="guest_uuid")

    def get_guest_by_uuid(self, guest_uuid: str) -> Optional[Guest]:
        """Get guest by UUID"""
        return self.guest_repo.find_by_uuid(guest_uuid)

    def update_guest_profile(self, guest_uuid: str, nickname: str) -> Guest:
        """Update guest profile"""
        # Check if nickname is already taken by another guest
        existing_guest = self.guest_repo.find_by_nickname(nickname)
        if existing_guest and str(existing_guest.uuid) != guest_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nickname already exists"
            )
        
        guest_uuid_obj = uuid.UUID(guest_uuid)
        guest = self.guest_repo.update_nickname(guest_uuid_obj, nickname)
        if not guest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Guest not found"
            )
        
        return guest