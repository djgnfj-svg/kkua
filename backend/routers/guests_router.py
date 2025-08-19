"""
Simplified guests router - authentication moved to auth_router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from db.postgres import get_db
from repositories.guest_repository import GuestRepository
from services.guest_service import GuestService
from schemas.guest_schema import GuestResponse
from middleware.auth_middleware import require_authentication
from models.guest_model import Guest

router = APIRouter(prefix="/guests", tags=["guests"])


def get_guest_service(db: Session = Depends(get_db)) -> GuestService:
    repository = GuestRepository(db)
    return GuestService(repository)


@router.get("/me", response_model=GuestResponse)
def get_current_guest(
    current_guest: Guest = Depends(require_authentication),
) -> GuestResponse:
    """Get current guest information"""
    return GuestResponse(
        guest_uuid=current_guest.guest_uuid,
        nickname=current_guest.nickname,
        last_login=current_guest.last_login,
    )


@router.get("/{guest_uuid}", response_model=GuestResponse)
def get_guest_by_uuid(
    guest_uuid: str, service: GuestService = Depends(get_guest_service)
) -> GuestResponse:
    """Get guest by UUID (public endpoint)"""
    guest = service.get_guest_by_uuid(guest_uuid)
    if not guest:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Guest not found"
        )
    return guest
