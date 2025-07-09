from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime
import uuid


class GuestBase(BaseModel):
    nickname: Optional[str] = None


class GuestCreateRequest(BaseModel):
    nickname: Optional[str] = None
    device_info: Optional[str] = None


class GuestLoginRequest(BaseModel):
    guest_uuid: Optional[str] = None
    nickname: Optional[str] = None
    device_info: Optional[str] = None


class GuestResponse(BaseModel):
    guest_id: int
    uuid: uuid.UUID
    nickname: str
    active_game: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None
    device_info: Optional[str] = None

    class Config:
        from_attributes = True
