"""
Authentication middleware for centralized authentication logic
"""

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
import uuid
from typing import Optional
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest
from db.postgres import get_db
from sqlalchemy.orm import Session

security = HTTPBearer(auto_error=False)


def get_guest_uuid_from_cookie(request: Request) -> Optional[str]:
    """Extract guest UUID from cookie"""
    guest_uuid = request.cookies.get("guest_uuid")
    if not guest_uuid:
        return None
    
    try:
        # Validate UUID format
        uuid.UUID(guest_uuid)
        return guest_uuid
    except ValueError:
        return None


def get_current_guest(
    request: Request,
    db: Session = Depends(get_db)
) -> Guest:
    """Get current authenticated guest from cookie"""
    guest_uuid = get_guest_uuid_from_cookie(request)
    
    if not guest_uuid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required - no guest UUID found"
        )
    
    guest_repo = GuestRepository(db)
    guest = guest_repo.find_by_uuid(guest_uuid)
    
    if not guest:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication - guest not found"
        )
    
    return guest


def get_optional_current_guest(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[Guest]:
    """Get current guest if authenticated, otherwise return None"""
    try:
        return get_current_guest(request, db)
    except HTTPException:
        return None


def require_authentication(guest: Guest = Depends(get_current_guest)) -> Guest:
    """Dependency to require authentication for protected routes"""
    return guest


def optional_authentication(guest: Optional[Guest] = Depends(get_optional_current_guest)) -> Optional[Guest]:
    """Dependency for optional authentication"""
    return guest