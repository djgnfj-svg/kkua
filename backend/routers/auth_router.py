"""
Authentication router for handling login, logout, and profile management
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from db.postgres import get_db
from repositories.guest_repository import GuestRepository
from services.auth_service import AuthService
from middleware.auth_middleware import require_authentication, optional_authentication
from schemas.auth_schema import (
    LoginRequest, LoginResponse, ProfileUpdateRequest, 
    ProfileResponse, AuthStatusResponse, LogoutResponse
)
from models.guest_model import Guest
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency to get AuthService instance"""
    guest_repo = GuestRepository(db)
    return AuthService(guest_repo)


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login or create a new guest account
    """
    try:
        guest, session_token = auth_service.login(login_data.nickname)
        auth_service.set_auth_cookies(response, session_token)
        
        return LoginResponse(
            guest_id=guest.guest_id,
            guest_uuid=str(guest.uuid),
            nickname=guest.nickname,
            message="Login successful",
            last_login=guest.last_login
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout and clear authentication cookies
    """
    result = auth_service.logout(request, response)
    return LogoutResponse(message=result["message"])


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_guest: Guest = Depends(require_authentication)):
    """
    Get current user profile
    """
    return ProfileResponse(
        guest_id=current_guest.guest_id,
        guest_uuid=str(current_guest.uuid),
        nickname=current_guest.nickname,
        last_login=current_guest.last_login
    )


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Update current user profile
    """
    try:
        updated_guest = auth_service.update_profile(request, profile_data.nickname)
        
        return ProfileResponse(
            guest_id=updated_guest.guest_id,
            guest_uuid=str(updated_guest.uuid),
            nickname=updated_guest.nickname,
            last_login=updated_guest.last_login
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Profile update failed: {str(e)}"
        )


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Check authentication status
    """
    auth_status = auth_service.check_auth_status(request)
    
    if auth_status["authenticated"]:
        return AuthStatusResponse(
            authenticated=True,
            guest=ProfileResponse(
                guest_id=auth_status["guest"]["guest_id"],
                guest_uuid=auth_status["guest"]["uuid"],
                nickname=auth_status["guest"]["nickname"],
                last_login=auth_status["guest"]["last_login"]
            )
        )
    else:
        return AuthStatusResponse(authenticated=False, guest=None)