"""
Authentication middleware for session-based authentication
"""

from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer
from typing import Optional
from repositories.guest_repository import GuestRepository
from models.guest_model import Guest
from db.postgres import get_db
from sqlalchemy.orm import Session
from services.session_service import get_session_store

security = HTTPBearer(auto_error=False)


def get_session_token_from_cookie(request: Request) -> Optional[str]:
    """Extract session token from cookie"""
    session_token = request.cookies.get("session_token")
    return session_token if session_token else None


def get_current_guest(request: Request, db: Session = Depends(get_db)) -> Guest:
    """Get current authenticated guest from session"""
    session_token = get_session_token_from_cookie(request)

    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required - no session token found",
        )

    # Get session data
    session_store = get_session_store()
    session_data = session_store.get_session(session_token)

    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session - session expired or not found",
        )

    # Get guest from database
    guest_repo = GuestRepository(db)
    guest = guest_repo.find_by_id(session_data["guest_id"])

    if not guest:
        # Clean up invalid session
        session_store.delete_session(session_token)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session - guest not found",
        )

    return guest


def get_optional_current_guest(
    request: Request, db: Session = Depends(get_db)
) -> Optional[Guest]:
    """Get current guest if authenticated, otherwise return None"""
    try:
        return get_current_guest(request, db)
    except HTTPException:
        return None


def require_authentication(guest: Guest = Depends(get_current_guest)) -> Guest:
    """Dependency to require authentication for protected routes"""
    return guest


def optional_authentication(
    guest: Optional[Guest] = Depends(get_optional_current_guest),
) -> Optional[Guest]:
    """Dependency for optional authentication"""
    return guest


def get_admin_user(current_user: Guest = Depends(get_current_guest)) -> Guest:
    """관리자 권한 체크"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다"
        )
    return current_user


def require_admin(admin_user: Guest = Depends(get_admin_user)) -> Guest:
    """관리자 권한 요구 의존성"""
    return admin_user
