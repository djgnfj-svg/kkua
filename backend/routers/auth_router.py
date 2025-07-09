"""
Authentication router for handling login, logout, and profile management
"""

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from sqlalchemy.orm import Session
from db.postgres import get_db
from services.auth_service import AuthService
from middleware.auth_middleware import require_authentication, optional_authentication
from schemas.auth_schema import (
    LoginRequest, LoginResponse, ProfileUpdateRequest, 
    ProfileResponse, AuthStatusResponse, LogoutResponse
)
from models.guest_model import Guest
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Login or create a new guest account
    """
    auth_service = AuthService(db)
    
    try:
        guest, guest_uuid = auth_service.login_or_create_guest(login_data.nickname)
        auth_service.set_auth_cookies(response, guest_uuid)
        
        return LoginResponse(
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
async def logout(response: Response):
    """
    Logout and clear authentication cookies
    """
    auth_service = AuthService(db=None)  # No DB needed for logout
    auth_service.logout(response)
    
    return LogoutResponse(message="Logout successful")


@router.get("/me", response_model=ProfileResponse)
async def get_profile(current_guest: Guest = Depends(require_authentication)):
    """
    Get current user profile
    """
    return ProfileResponse(
        guest_uuid=str(current_guest.uuid),
        nickname=current_guest.nickname,
        last_login=current_guest.last_login
    )


@router.put("/me", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdateRequest,
    current_guest: Guest = Depends(require_authentication),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    """
    auth_service = AuthService(db)
    
    try:
        updated_guest = auth_service.update_guest_profile(
            str(current_guest.uuid), 
            profile_data.nickname
        )
        
        return ProfileResponse(
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
async def get_auth_status(current_guest: Optional[Guest] = Depends(optional_authentication)):
    """
    Check authentication status
    """
    if current_guest:
        return AuthStatusResponse(
            authenticated=True,
            guest=ProfileResponse(
                guest_uuid=str(current_guest.uuid),
                nickname=current_guest.nickname,
                last_login=current_guest.last_login
            )
        )
    else:
        return AuthStatusResponse(authenticated=False, guest=None)