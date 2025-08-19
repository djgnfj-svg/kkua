"""
Simplified Guest service focused on guest management only
Authentication logic moved to auth_service
"""

from repositories.guest_repository import GuestRepository
from schemas.guest_schema import GuestResponse
from fastapi import HTTPException, status
from typing import Optional
import uuid


class GuestService:
    def __init__(self, repository: GuestRepository):
        self.repository = repository

    def get_guest_by_uuid(self, guest_uuid: str) -> Optional[GuestResponse]:
        """Get guest by UUID"""
        try:
            uuid_obj = self._parse_uuid(guest_uuid)
            guest = self.repository.find_by_uuid(uuid_obj)

            if guest:
                return GuestResponse(
                    guest_uuid=guest.guest_uuid,
                    nickname=guest.nickname,
                    last_login=guest.last_login,
                )
            return None
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format"
            )

    def update_guest_nickname(self, guest_uuid: str, nickname: str) -> GuestResponse:
        """Update guest nickname"""
        try:
            uuid_obj = self._parse_uuid(guest_uuid)

            # Check if nickname is already taken
            existing_guest = self.repository.find_by_nickname(nickname)
            if existing_guest and existing_guest.guest_uuid != guest_uuid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nickname already exists",
                )

            guest = self.repository.update_nickname(uuid_obj, nickname)
            if not guest:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found"
                )

            return GuestResponse(
                guest_uuid=guest.guest_uuid,
                nickname=guest.nickname,
                last_login=guest.last_login,
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid UUID format"
            )

    def _parse_uuid(self, uuid_str: str) -> uuid.UUID:
        """Parse UUID string to UUID object"""
        try:
            return uuid.UUID(uuid_str)
        except ValueError:
            raise ValueError("Invalid UUID format")
