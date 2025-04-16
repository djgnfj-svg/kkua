from pydantic import BaseModel
from typing import Optional, Dict, Any
import datetime
import uuid

class GuestBase(BaseModel):
    nickname: Optional[str] = None

class GuestResponse(BaseModel):
    guest_id: int
    uuid: uuid.UUID
    nickname: str
    active_game: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True
        orm_mode = True 