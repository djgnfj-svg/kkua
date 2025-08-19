"""
Authentication-related Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    """Schema for login request"""

    nickname: Optional[str] = Field(
        None, min_length=1, max_length=20, description="Optional nickname for the guest"
    )


class LoginResponse(BaseModel):
    """Schema for login response"""

    guest_id: int = Field(..., description="Guest's database ID")
    guest_uuid: str = Field(..., description="Unique identifier for the guest")
    nickname: str = Field(..., description="Guest's nickname")
    message: str = Field(..., description="Success message")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Schema for profile update request"""

    nickname: str = Field(
        ..., min_length=1, max_length=20, description="New nickname for the guest"
    )


class ProfileResponse(BaseModel):
    """Schema for profile response"""

    guest_id: int = Field(..., description="Guest's database ID")
    guest_uuid: str = Field(..., description="Unique identifier for the guest")
    nickname: str = Field(..., description="Guest's nickname")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        from_attributes = True


class AuthStatusResponse(BaseModel):
    """Schema for authentication status response"""

    authenticated: bool = Field(..., description="Whether the user is authenticated")
    guest: Optional[ProfileResponse] = Field(
        None, description="Guest information if authenticated"
    )
    redirect_url: Optional[str] = Field(
        None, description="Recommended URL to redirect to after authentication"
    )


class LogoutResponse(BaseModel):
    """Schema for logout response"""

    message: str = Field(..., description="Logout success message")
